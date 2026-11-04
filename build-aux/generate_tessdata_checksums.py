#!/usr/bin/env python3
# build-aux/generate_tessdata_checksums.py
"""Generate the pinned integrity manifest for runtime tessdata downloads.

For every tessdata repository referenced by ``anura/config.py`` this fetches the
tree listing of the pinned git ref from the GitHub REST API and records the git
blob SHA-1 and byte size of each ``*.traineddata`` file into
``anura/data/tessdata_checksums.json``. Those hashes are what
``DownloadManager`` verifies runtime downloads against (see
``anura/utils/tessdata_integrity.py``).

Blob ids are content-addressed, so the whole manifest — roughly 500 models
across the three upstream repositories — can be regenerated without downloading
a single model. Re-run this script whenever the pinned refs in ``anura/config.py``
change and commit the result: ``build-aux/check_tessdata_consistency.py`` fails
the release when the manifest and ``config.py`` drift apart.

Usage:
    uv run python3 build-aux/generate_tessdata_checksums.py [--output PATH] [--token TOKEN]

Environment:
    GITHUB_TOKEN   optional; raises the API rate limit from 60 to 5000 req/h

Note: run this through the project environment (``uv run``) — it imports the
``anura`` package to keep URL parsing in a single place. The release-time check
that consumes the manifest is stdlib only, because release.sh runs it with the
system python3.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
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

_API_TIMEOUT_SECONDS = 60
_DOWNLOAD_TIMEOUT_SECONDS = 120
_CHUNK_SIZE = 65536


class ApiError(RuntimeError):
    """Raised when the GitHub API cannot be queried or returns unusable data."""


def fetch_tree(api_url: str, token: str | None) -> dict:
    """Fetch a recursive git tree from the GitHub API.

    Args:
        api_url: GitHub ``/git/trees/<ref>?recursive=1`` endpoint.
        token: Optional bearer token (raises the anonymous rate limit).

    Returns:
        The decoded JSON response.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Anura-checksums-generator/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(api_url, headers=headers)  # nosec B310 - fixed https://api.github.com URL
    try:
        # nosec B310 - scheme is https, URL built from anura/config.py constants
        with urlopen(request, timeout=_API_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, ValueError) as error:
        raise ApiError(f"Failed to fetch {api_url}: {error}") from error


def _raw_url(base_url: str, path: str) -> str:
    """Return the raw.githubusercontent.com URL for a tree path."""
    return base_url.rstrip("/") + "/" + path


def download_and_compute_sha256(url: str, expected_size: int) -> tuple[str, int]:
    """Stream-download ``url`` and return ``(sha256_hex, actual_size)``.

    The digest is computed incrementally, so the binary is never held entirely
    in memory. The received byte count is compared against ``expected_size``
    from the tree listing; a mismatch raises ``ApiError`` so a corrupted or
    truncated download never produces a manifest entry.

    Args:
        url: raw.githubusercontent.com URL of the model file.
        expected_size: byte size from the GitHub tree listing.

    Returns:
        Tuple of (lowercase hex SHA-256 digest, actual byte count received).
    """
    request = Request(url, headers={"User-Agent": "Anura-checksums-generator/1.0"})  # nosec B310
    digest = hashlib.sha256(usedforsecurity=True)
    received = 0
    try:
        with urlopen(request, timeout=_DOWNLOAD_TIMEOUT_SECONDS) as response:
            while True:
                chunk = response.read(_CHUNK_SIZE)
                if not chunk:
                    break
                digest.update(chunk)
                received += len(chunk)
                if received > expected_size:
                    raise ApiError(
                        f"Download of {url} exceeded expected size {expected_size} bytes (received {received})."
                    )
    except (HTTPError, URLError, OSError, ValueError) as error:
        raise ApiError(f"Failed to download {url}: {error}") from error

    if received != expected_size:
        raise ApiError(f"Download of {url} received {received} bytes, tree listing expects {expected_size} bytes.")

    return digest.hexdigest(), received


def collect_repository(base_url: str, token: str | None) -> dict:
    """Return the manifest entry describing one upstream repository."""
    repo = repo_key_from_url(base_url)
    ref = ref_from_url(base_url)
    api_url = tree_api_url(base_url)
    if repo is None or ref is None or api_url is None:
        raise ApiError(f"Malformed tessdata base URL in anura/config.py: {base_url}")

    tree = fetch_tree(api_url, token)
    if tree.get("truncated"):
        # A truncated listing would silently drop models from the manifest,
        # turning every download of a missing entry into a hard failure.
        raise ApiError(f"GitHub returned a truncated tree for {repo}@{ref}")

    files: dict[str, dict[str, int | str]] = {}
    for entry in tree.get("tree", []):
        path = entry.get("path", "")
        if entry.get("type") != "blob" or not path.endswith(".traineddata"):
            continue

        size = int(entry["size"])
        sha1 = str(entry["sha"])

        # Download the real binary contents to compute the actual SHA-256
        # digest. This is the release-time cost of the integrity guarantee.
        url = _raw_url(base_url, path)
        sha256, actual_size = download_and_compute_sha256(url, size)

        files[path] = {"size": actual_size, "sha1": sha1, "sha256": sha256}

    if not files:
        raise ApiError(f"No *.traineddata files found in {repo}@{ref}")

    return {"url": base_url, "tag": ref, "files": dict(sorted(files.items()))}


def build_manifest(token: str | None) -> dict:
    """Build the manifest for every configured repository."""
    repositories = {}
    for base_url in sorted(BASE_URLS):
        repositories[repo_key_from_url(base_url) or base_url] = collect_repository(base_url, token)

    return {
        "version": 2,
        "comment": (
            "Pinned git blob SHA-1, SHA-256 and size of every Tesseract model published by the refs in "
            "anura/config.py. Generated by build-aux/generate_tessdata_checksums.py — do not edit by hand. "
            "SHA-256 is the primary integrity anchor; SHA-1 is retained as a defence-in-depth check."
        ),
        "repositories": repositories,
    }


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
    except ApiError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    total = sum(len(repo["files"]) for repo in manifest["repositories"].values())
    print(f"Wrote {total} model checksums for {len(manifest['repositories'])} repositories to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
