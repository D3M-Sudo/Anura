#!/usr/bin/env python3
# build-aux/generate_tessdata_checksums.py
"""Generate the pinned integrity manifest for runtime tessdata downloads.

This produces ``anura/data/tessdata_checksums.json`` in manifest format v2
(``version``: 2, ``algorithm``: "sha256"). For every tessdata repository pinned
in ``anura/config.py`` it:

1. Queries the GitHub REST API tree of the pinned ref to enumerate every
   ``*.traineddata`` file and its advertised byte size.
2. Downloads each model's *raw* bytes over streaming HTTP and computes the
   raw-content SHA-256 incrementally, in bounded chunks. The downloaded bytes
   feed a running hash and are then discarded; the model is never stored to
   disk permanently.
3. Verifies the actual downloaded byte count equals the advertised size, and
   rejects oversized or truncated streams.
4. Writes the manifest to a temporary file and atomically replaces the previous
   manifest (``os.replace``) only once every repository has been fully
   validated. On any failure the previous manifest is left untouched.

The SHA-1 values published by the GitHub tree API are git-blob digests
(``sha1("blob <size>\\0<data>")``), not raw-content SHA-256 digests, and are
never used as integrity values. A model is only pinned after its raw bytes have
been downloaded and hashed.

Usage:
    uv run python3 build-aux/generate_tessdata_checksums.py [--output PATH] [--token TOKEN]

Environment:
    GITHUB_TOKEN   optional; raises the GitHub API rate limit from 60 to
                   5000 requests/hour

Note: run this through the project environment (``uv run``) — it imports the
``anura`` package to keep URL parsing in a single place.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from anura.config import (  # noqa: E402
    TESSDATA_BEST_URL,
    TESSDATA_STANDARD_URL,
    TESSDATA_URL,
)
from anura.utils.tessdata_integrity import (  # noqa: E402
    ref_from_url,
    repo_key_from_url,
    tree_api_url,
)

DEFAULT_OUTPUT = REPO_ROOT / "anura" / "data" / "tessdata_checksums.json"

#: Repositories to pin. Order is irrelevant: the manifest is written with sorted keys.
BASE_URLS = (TESSDATA_URL, TESSDATA_STANDARD_URL, TESSDATA_BEST_URL)

#: Manifest version emitted by this generator.
MANIFEST_VERSION = 2
#: Hash algorithm used for every model digest.
MANIFEST_ALGORITHM = "sha256"

#: Size of each streaming chunk read from the network (bytes).
DOWNLOAD_CHUNK_SIZE = 64 * 1024
#: Maximum number of download attempts per model (initial attempt + retries).
MAX_DOWNLOAD_ATTEMPTS = 3
#: Base backoff (seconds) between retries; actual backoff doubles each attempt.
RETRY_BACKOFF_BASE = 2
#: Timeout for the GitHub tree API request (seconds).
TREE_API_TIMEOUT = 60
#: Timeout for each individual model download request (seconds).
DOWNLOAD_TIMEOUT = 60


class GeneratorError(RuntimeError):
    """Raised when the manifest cannot be generated or validated."""


def _fetch_json(api_url: str, token: str | None, timeout: int) -> dict:
    """Fetch and decode a JSON response from the GitHub REST API.

    Network errors are retried up to :data:`MAX_DOWNLOAD_ATTEMPTS` with
    exponential backoff before giving up.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Anura-checksums-generator/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(api_url, headers=headers)
    last_error: Exception | None = None
    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
        try:
            # nosec B310 - scheme is https, URL built from anura/config.py constants
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, OSError, ValueError) as error:
            last_error = error
            if attempt == MAX_DOWNLOAD_ATTEMPTS:
                break
            time.sleep(RETRY_BACKOFF_BASE**attempt)
    raise GeneratorError(f"Failed to fetch {api_url}: {last_error}")


def _download_sha256(url: str, token: str | None, advertised_size: int) -> str:
    """Stream raw model bytes from ``url`` and return their SHA-256 hex digest.

    The response is read in bounded chunks; each chunk feeds the running hash,
    updates the byte counter, and is then discarded. The model is never stored
    to disk permanently.

    Raises :class:`GeneratorError` if the download fails, is truncated, or
    delivers more bytes than the advertised size. Transient network errors are
    retried up to :data:`MAX_DOWNLOAD_ATTEMPTS`; size mismatches are not
    retried because they are deterministic for a given URL.
    """
    headers = {"User-Agent": "Anura-checksums-generator/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    last_error: Exception | None = None
    for attempt in range(1, MAX_DOWNLOAD_ATTEMPTS + 1):
        hasher = hashlib.sha256()
        received = 0
        response = None
        try:
            # nosec B310 - scheme is https, URL built from anura/config.py constants
            response = urlopen(request, timeout=DOWNLOAD_TIMEOUT)
            while True:
                chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                hasher.update(chunk)
                received += len(chunk)
                if received > advertised_size:
                    raise GeneratorError(
                        f"Oversized stream from {url}: received {received} bytes, advertised size is {advertised_size}"
                    )
            if received != advertised_size:
                raise GeneratorError(
                    f"Truncated download from {url}: received {received} bytes, advertised size is {advertised_size}"
                )
            return hasher.hexdigest()
        except GeneratorError:
            raise
        except (HTTPError, URLError, OSError, ValueError) as error:
            last_error = error
            if attempt == MAX_DOWNLOAD_ATTEMPTS:
                break
            time.sleep(RETRY_BACKOFF_BASE**attempt)
        finally:
            if response is not None:
                try:
                    response.close()
                except (OSError, ValueError):
                    pass
    raise GeneratorError(f"Failed to download {url}: {last_error}")


def collect_repository(base_url: str, token: str | None) -> dict:
    """Return the manifest entry describing one upstream repository.

    Every ``*.traineddata`` blob in the pinned tree is downloaded, its raw
    bytes hashed with SHA-256, and its advertised size verified against the
    actual byte count.
    """
    repo = repo_key_from_url(base_url)
    ref = ref_from_url(base_url)
    api_url = tree_api_url(base_url)
    if repo is None or ref is None or api_url is None:
        raise GeneratorError(f"Malformed tessdata base URL in anura/config.py: {base_url}")

    tree = _fetch_json(api_url, token, TREE_API_TIMEOUT)
    if tree.get("truncated"):
        # A truncated listing would silently drop models from the manifest,
        # turning every download of a missing entry into a hard failure.
        raise GeneratorError(f"GitHub returned a truncated tree for {repo}@{ref}")

    files: dict[str, dict[str, int | str]] = {}
    for entry in tree.get("tree", []):
        path = entry.get("path", "")
        if entry.get("type") != "blob" or not path.endswith(".traineddata"):
            continue
        advertised_size = int(entry["size"])
        digest = _download_sha256(f"{base_url}{path}", token, advertised_size)
        files[path] = {"size": advertised_size, "sha256": digest}

    if not files:
        raise GeneratorError(f"No *.traineddata files found in {repo}@{ref}")

    return {"url": base_url, "tag": ref, "files": dict(sorted(files.items()))}


def build_manifest(token: str | None) -> dict:
    """Build the SHA-256 manifest (version 2) for every configured repository."""
    repositories = {}
    for base_url in sorted(BASE_URLS):
        repositories[repo_key_from_url(base_url) or base_url] = collect_repository(base_url, token)

    return {
        "version": MANIFEST_VERSION,
        "algorithm": MANIFEST_ALGORITHM,
        "repositories": repositories,
    }


def _atomic_write(path: Path, content: str) -> None:
    """Write ``content`` to ``path`` via a temp file then ``os.replace``.

    The previous manifest is preserved if any step fails.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp:
            tmp.write(content)
            tmp.flush()
            os.fsync(tmp.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def main() -> int:
    """Generate the manifest and write it to disk."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"output manifest path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub API token (default: $GITHUB_TOKEN)",
    )
    args = parser.parse_args()

    try:
        manifest = build_manifest(args.token)
    except GeneratorError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    total = sum(len(repo["files"]) for repo in manifest["repositories"].values())
    content = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    try:
        _atomic_write(args.output, content)
    except OSError as error:
        print(f"ERROR: Failed to write manifest {args.output}: {error}", file=sys.stderr)
        return 1

    print(f"Wrote {total} model checksums for {len(manifest['repositories'])} repositories to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
