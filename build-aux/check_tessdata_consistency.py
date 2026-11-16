#!/usr/bin/env python3
# build-aux/check_tessdata_consistency.py
"""Check tessdata refs and the complete SHA-256 integrity manifest.

This stdlib-only checker resolves literal URL assignments and simple aliases in
anura/config.py, validates the Flatpak pins, and verifies that the integrity
manifest contains the expected three upstream repositories and model counts.
It deliberately does not download upstream models.
"""

import ast
from http.client import IncompleteRead
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PY = REPO_ROOT / "anura" / "config.py"
MANIFEST_MAIN = REPO_ROOT / "flatpak" / "io.github.d3m_sudo.anura.json"
MANIFEST_LOCAL = REPO_ROOT / "flatpak" / "io.github.d3m_sudo.anura.local.json"
CHECKSUMS_MANIFEST = REPO_ROOT / "anura" / "data" / "tessdata_checksums.json"

TESSDATA_URL_PATTERN = re.compile(r"github\.com/tesseract-ocr/tessdata[^/]*/raw/([A-Za-z0-9._-]+)/")
CONFIG_TESSDATA_PATTERN = re.compile(r"TESSDATA_BEST_URL\s*=\s*[\"']https?://[^\"']*/raw/([A-Za-z0-9._-]+)/")
SHA256_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")

# Inventory for the pinned upstream 4.1.0 trees.
EXPECTED_REPOSITORY_COUNTS = {
    "tessdata": 166,
    "tessdata_best": 161,
    "tessdata_fast": 162,
}
EXPECTED_MANIFEST_KEYS = {"version", "algorithm", "repositories"}
EXPECTED_REPOSITORY_FIELDS = {"url", "tag", "files"}
EXPECTED_ENTRY_FIELDS = {"size", "sha256"}


def extract_sha_from_config(config_path: Path) -> str | None:
    """Extract the tessdata ref from the literal TESSDATA_BEST_URL."""
    match = CONFIG_TESSDATA_PATTERN.search(config_path.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def extract_shas_from_manifest(manifest_path: Path) -> list[str]:
    """Extract tessdata refs from Flatpak tessdata module sources."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    shas = []
    for module in data.get("modules", []):
        if not isinstance(module, dict) or module.get("name") != "tessdata":
            continue
        for source in module.get("sources", []):
            if not isinstance(source, dict):
                continue
            url = source.get("url", "")
            if not isinstance(url, str):
                continue
            match = TESSDATA_URL_PATTERN.search(url)
            if match:
                shas.append(match.group(1))
    return shas


def extract_tessdata_urls_from_config(config_path: Path) -> dict[str, str]:
    """Resolve configured tessdata URLs, including simple name aliases.

    Only top-level assignments of the expected constants are considered.
    Alias resolution is deliberately limited to previously resolved string
    constants; arbitrary Python expressions are never evaluated.
    """
    tree = ast.parse(config_path.read_text(encoding="utf-8"), filename=str(config_path))
    values: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            name = target.id
            if not (name.startswith("TESSDATA") and name.endswith("_URL")):
                continue
            value: str | None = None
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                value = node.value.value
            elif isinstance(node.value, ast.Name):
                value = values.get(node.value.id)
            if value is not None:
                values[name] = value

    urls: dict[str, str] = {}
    for value in values.values():
        parsed = urlsplit(value)
        parts = [part for part in parsed.path.split("/") if part]
        if (
            parsed.scheme != "https"
            or parsed.netloc != "github.com"
            or len(parts) != 4
            or parts[0] != "tesseract-ocr"
            or parts[2] != "raw"
            or not parts[3]
        ):
            continue
        repository = parts[1]
        if repository.startswith("tessdata"):
            urls[repository] = value
    return urls


def _fetch_upstream_model_names(base_url: str) -> set[str]:
    """Fetch the pinned Git tree and return its exact flat traineddata inventory.

    The checker fails closed on API errors or truncated trees: counts alone
    cannot prove that a manifest contains the correct model filenames.
    """
    parsed = urlsplit(base_url)
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or len(parts) != 4
        or parts[0] != "tesseract-ocr"
        or parts[2] != "raw"
    ):
        raise ValueError(f"Invalid pinned tessdata URL: {base_url!r}")
    repository, ref = parts[1], parts[3]
    api_url = f"https://api.github.com/repos/tesseract-ocr/{repository}/git/trees/{ref}?recursive=1"
    request = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Anura-tessdata-consistency-check/1.0",
        },
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, OSError, ValueError, IncompleteRead) as error:
        raise RuntimeError(f"Unable to verify upstream inventory for {repository}@{ref}: {error}") from error
    if not isinstance(payload, dict) or payload.get("truncated") is not False:
        raise RuntimeError(f"GitHub returned a malformed or truncated tree for {repository}@{ref}")
    entries = payload.get("tree")
    if not isinstance(entries, list):
        raise RuntimeError(f"GitHub returned no valid tree entries for {repository}@{ref}")

    names: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise RuntimeError(f"GitHub returned a malformed tree entry for {repository}@{ref}")
        if entry.get("type") != "blob":
            continue
        filename = entry.get("path")
        if not isinstance(filename, str):
            raise RuntimeError(f"GitHub returned a tree entry without a path for {repository}@{ref}")
        if not filename.endswith(".traineddata"):
            continue
        model_path = PurePosixPath(filename)
        if (
            filename.startswith("/")
            or str(model_path) != filename
            or any(part in {"", ".", ".."} for part in model_path.parts)
            or "\\" in filename
        ):
            raise RuntimeError(f"Unsupported traineddata path in upstream tree: {filename!r}")
        if filename in names:
            raise RuntimeError(f"Duplicate traineddata path in upstream tree: {filename!r}")
        names.add(filename)
    if not names:
        raise RuntimeError(f"No traineddata models found in upstream tree for {repository}@{ref}")
    return names


def _validate_checksum_entry(repo_name: str, filename: str, entry: Any) -> list[str]:
    errors: list[str] = []
    label = f"{repo_name}/{filename}"
    if not isinstance(entry, dict):
        return [f"Checksums manifest entry for '{label}' is not an object"]
    if set(entry) != EXPECTED_ENTRY_FIELDS:
        errors.append(f"Checksums manifest entry for '{label}' must contain exactly {sorted(EXPECTED_ENTRY_FIELDS)}")
    size = entry.get("size")
    if type(size) is not int or size <= 0:
        errors.append(f"Checksums manifest entry for '{label}' has invalid size {size!r}")
    digest = entry.get("sha256")
    if not isinstance(digest, str) or not SHA256_DIGEST_PATTERN.fullmatch(digest):
        errors.append(f"Checksums manifest entry for '{label}' has invalid raw SHA-256 digest")
    return errors


def _repository_name_from_url(url: Any) -> str | None:
    if not isinstance(url, str):
        return None
    parsed = urlsplit(url)
    parts = [part for part in parsed.path.split("/") if part]
    if (
        parsed.scheme != "https"
        or parsed.netloc != "github.com"
        or len(parts) != 4
        or parts[0] != "tesseract-ocr"
        or parts[2] != "raw"
        or not parts[3]
    ):
        return None
    return parts[1]


def check_checksums_manifest() -> list[str]:
    """Validate manifest schema, configured pins, repository identities and inventory."""
    if not CHECKSUMS_MANIFEST.exists():
        return [f"Missing tessdata integrity manifest: {CHECKSUMS_MANIFEST}"]
    try:
        manifest = json.loads(CHECKSUMS_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"Cannot read tessdata integrity manifest {CHECKSUMS_MANIFEST}: {error}"]
    if not isinstance(manifest, dict):
        return [f"Tessdata integrity manifest {CHECKSUMS_MANIFEST} is not a JSON object"]

    errors: list[str] = []
    if set(manifest) != EXPECTED_MANIFEST_KEYS:
        errors.append(f"Manifest must contain exactly {sorted(EXPECTED_MANIFEST_KEYS)}")
    if manifest.get("version") != 2:
        errors.append(f"Manifest must use version 2 (got {manifest.get('version')!r})")
    if manifest.get("algorithm") != "sha256":
        errors.append(f"Manifest must declare algorithm 'sha256' (got {manifest.get('algorithm')!r})")

    repositories = manifest.get("repositories")
    if not isinstance(repositories, dict):
        errors.append("Manifest repositories must be an object")
        return errors

    try:
        configured_urls = extract_tessdata_urls_from_config(CONFIG_PY)
    except (OSError, SyntaxError, UnicodeError) as error:
        return [f"Cannot parse tessdata URLs from {CONFIG_PY}: {error}"]

    if set(configured_urls) != set(EXPECTED_REPOSITORY_COUNTS):
        errors.append(f"Configured tessdata repositories differ from the expected set: {sorted(configured_urls)}")
    if set(repositories) != set(EXPECTED_REPOSITORY_COUNTS):
        errors.append(f"Manifest repository keys differ from the expected set: {sorted(repositories)}")

    for repo_name, repository in repositories.items():
        if repo_name not in EXPECTED_REPOSITORY_COUNTS:
            errors.append(f"Unexpected tessdata repository key: {repo_name!r}")
        if not isinstance(repository, dict):
            errors.append(f"Manifest repository '{repo_name}' is not an object")
            continue
        if set(repository) != EXPECTED_REPOSITORY_FIELDS:
            errors.append(
                f"Manifest repository '{repo_name}' must contain exactly {sorted(EXPECTED_REPOSITORY_FIELDS)}"
            )

        url = repository.get("url")
        actual_name = _repository_name_from_url(url)
        if actual_name != repo_name:
            errors.append(f"Manifest repository key '{repo_name}' does not match URL repository {actual_name!r}")
        if configured_urls.get(repo_name) != url:
            errors.append(f"Manifest URL for '{repo_name}' does not match anura/config.py")
        parsed = urlsplit(url) if isinstance(url, str) else None
        parts = [part for part in parsed.path.split("/") if part] if parsed else []
        expected_tag = parts[3] if len(parts) == 4 else None
        if repository.get("tag") != expected_tag or expected_tag is None:
            errors.append(f"Manifest tag for '{repo_name}' does not match its configured URL ref")

        files = repository.get("files")
        if not isinstance(files, dict):
            errors.append(f"Manifest files for '{repo_name}' must be an object")
            continue
        expected_count = EXPECTED_REPOSITORY_COUNTS.get(repo_name)
        if expected_count is not None and len(files) != expected_count:
            errors.append(f"Repository '{repo_name}' must contain {expected_count} models; found {len(files)}")
        if isinstance(url, str) and actual_name == repo_name:
            try:
                upstream_names = _fetch_upstream_model_names(url)
            except (RuntimeError, ValueError) as error:
                errors.append(str(error))
            else:
                manifest_names = set(files)
                if manifest_names != upstream_names:
                    errors.append(
                        f"Repository '{repo_name}' model inventory differs from upstream: "
                        f"missing={sorted(upstream_names - manifest_names)}, "
                        f"unexpected={sorted(manifest_names - upstream_names)}"
                    )
        for filename, entry in files.items():
            if (
                not isinstance(filename, str)
                or not filename.endswith(".traineddata")
                or filename.startswith("/")
                or str(PurePosixPath(filename)) != filename
                or any(part in {"", ".", ".."} for part in PurePosixPath(filename).parts)
                or "\\" in filename
            ):
                errors.append(f"Invalid tessdata model filename in '{repo_name}': {filename!r}")
            errors.extend(_validate_checksum_entry(repo_name, filename, entry))

    return errors


def main() -> int:
    """Check tessdata consistency. Returns 0 if consistent, 1 if drift detected."""
    config_sha = extract_sha_from_config(CONFIG_PY)
    if config_sha is None:
        print(f"ERROR: Could not extract TESSDATA_BEST_URL ref from {CONFIG_PY}", file=sys.stderr)
        return 2
    main_shas = extract_shas_from_manifest(MANIFEST_MAIN)
    local_shas = extract_shas_from_manifest(MANIFEST_LOCAL)
    if not main_shas:
        print(f"ERROR: No tessdata refs found in {MANIFEST_MAIN}", file=sys.stderr)
        return 2
    if not local_shas:
        print(f"ERROR: No tessdata refs found in {MANIFEST_LOCAL}", file=sys.stderr)
        return 2

    errors: list[str] = []
    unique_main = set(main_shas)
    unique_local = set(local_shas)
    if unique_main != unique_local:
        errors.append("Main vs Local manifest tessdata ref mismatch")
    if config_sha not in unique_main:
        errors.append(f"config.py tessdata ref ({config_sha}) not found in main Flatpak manifest")
    if config_sha not in unique_local:
        errors.append(f"config.py tessdata ref ({config_sha}) not found in local Flatpak manifest")
    errors.extend(check_checksums_manifest())

    if errors:
        print("FAIL: Tessdata consistency check failed")
        for error in errors:
            print(f"  {error}")
        return 1
    print(f"PASS: Tessdata refs and SHA-256 manifest are consistent ({config_sha[:12]}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
