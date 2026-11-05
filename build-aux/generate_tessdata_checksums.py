#!/usr/bin/env python3
# build-aux/generate_tessdata_checksums.py
"""Generate the pinned raw-content SHA-256 manifest for tessdata models."""

import argparse
import hashlib
from http.client import IncompleteRead
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
BASE_URLS = (TESSDATA_URL, TESSDATA_STANDARD_URL, TESSDATA_BEST_URL)
MANIFEST_VERSION = 2
MANIFEST_ALGORITHM = "sha256"
DOWNLOAD_CHUNK_SIZE = 64 * 1024
MAX_DOWNLOAD_ATTEMPTS = 3
RETRY_BACKOFF_BASE = 2
TREE_API_TIMEOUT = 60
DOWNLOAD_TIMEOUT = 60


class GeneratorError(RuntimeError):
    """Raised when the manifest cannot be generated or validated."""


def _fetch_json(api_url: str, token: str | None, timeout: int) -> dict:
    """Fetch and decode a GitHub REST JSON response with bounded retries."""
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
            # nosec B310 - HTTPS URL is derived from the repository's pinned config.
            with urlopen(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("GitHub tree API response must be a JSON object")
            return payload
        except (HTTPError, URLError, OSError, ValueError, IncompleteRead) as error:
            last_error = error
            if attempt == MAX_DOWNLOAD_ATTEMPTS:
                break
            time.sleep(RETRY_BACKOFF_BASE**attempt)
    raise GeneratorError(f"Failed to fetch {api_url}: {last_error}")


def _download_sha256(url: str, token: str | None, advertised_size: int) -> str:
    """Stream raw model bytes, hash incrementally, and retry interrupted transfers."""
    if type(advertised_size) is not int or advertised_size <= 0:
        raise GeneratorError(f"Invalid advertised size for {url}: {advertised_size!r}")
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
            # nosec B310 - HTTPS URL is derived from a pinned tessdata base URL.
            response = urlopen(request, timeout=DOWNLOAD_TIMEOUT)
            while True:
                chunk = response.read(DOWNLOAD_CHUNK_SIZE)
                if not chunk:
                    break
                received += len(chunk)
                if received > advertised_size:
                    raise GeneratorError(
                        f"Oversized stream from {url}: received {received} bytes, advertised size is {advertised_size}"
                    )
                hasher.update(chunk)
            if received != advertised_size:
                raise IncompleteRead(b"", advertised_size - received)
            return hasher.hexdigest()
        except GeneratorError:
            raise
        except (HTTPError, URLError, OSError, ValueError, IncompleteRead) as error:
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
    """Collect and hash every flat *.traineddata blob in one pinned repository."""
    repo = repo_key_from_url(base_url)
    ref = ref_from_url(base_url)
    api_url = tree_api_url(base_url)
    if repo is None or ref is None or api_url is None:
        raise GeneratorError(f"Malformed tessdata base URL in anura/config.py: {base_url}")

    tree = _fetch_json(api_url, token, TREE_API_TIMEOUT)
    if not isinstance(tree, dict):
        raise GeneratorError(f"GitHub returned a malformed tree response for {repo}@{ref}")
    if tree.get("truncated") is not False:
        raise GeneratorError(f"GitHub returned a truncated or incomplete tree for {repo}@{ref}")
    entries = tree.get("tree")
    if not isinstance(entries, list):
        raise GeneratorError(f"GitHub returned no valid tree entry list for {repo}@{ref}")

    files: dict[str, dict[str, int | str]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            raise GeneratorError(f"GitHub returned a malformed tree entry for {repo}@{ref}")
        if entry.get("type") != "blob":
            continue
        path = entry.get("path")
        if not isinstance(path, str):
            raise GeneratorError(f"GitHub returned a tree entry without a valid path for {repo}@{ref}")
        if not path.endswith(".traineddata"):
            continue
        if path != Path(path).name or path in {".", ".."} or "\\" in path:
            raise GeneratorError(f"Unsupported tessdata model path from GitHub: {path!r}")
        advertised_size = entry.get("size")
        if type(advertised_size) is not int or advertised_size <= 0:
            raise GeneratorError(f"Invalid advertised size for {repo}/{path}: {advertised_size!r}")
        if path in files:
            raise GeneratorError(f"Duplicate tessdata model path in {repo}@{ref}: {path}")
        digest = _download_sha256(f"{base_url}{path}", token, advertised_size)
        files[path] = {"size": advertised_size, "sha256": digest}

    if not files:
        raise GeneratorError(f"No *.traineddata files found in {repo}@{ref}")
    return {"url": base_url, "tag": ref, "files": dict(sorted(files.items()))}


def build_manifest(token: str | None) -> dict:
    """Build the version 2 SHA-256 manifest for all configured repositories."""
    repositories = {}
    for base_url in sorted(BASE_URLS):
        repo_key = repo_key_from_url(base_url)
        if repo_key is None:
            raise GeneratorError(f"Malformed tessdata base URL: {base_url}")
        if repo_key in repositories:
            raise GeneratorError(f"Duplicate configured tessdata repository: {repo_key}")
        repositories[repo_key] = collect_repository(base_url, token)
    return {
        "version": MANIFEST_VERSION,
        "algorithm": MANIFEST_ALGORITHM,
        "repositories": repositories,
    }


def _atomic_write(path: Path, content: str) -> None:
    """Write to a sibling temporary file and atomically replace the destination."""
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
    """Generate the manifest and write it only after every model validates."""
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"))
    args = parser.parse_args()

    try:
        manifest = build_manifest(args.token)
    except GeneratorError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    total = sum(len(repository["files"]) for repository in manifest["repositories"].values())
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
