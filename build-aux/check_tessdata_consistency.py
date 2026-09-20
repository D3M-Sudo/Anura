#!/usr/bin/env python3
# build-aux/check_tessdata_consistency.py
"""Check tessdata ref (tag or SHA) consistency across configuration files.

Verifies that the tessdata git refs are consistent between:

- anura/config.py (TESSDATA_BEST_URL)
- flatpak/io.github.d3msudo.anura.json (tessdata module sources)
- flatpak/io.github.d3msudo.anura.local.json (tessdata module sources)

and that the committed integrity manifest
(anura/data/tessdata_checksums.json) still describes the repositories pinned in
anura/config.py — otherwise a re-pinned tag would ship with stale hashes and
every runtime model download would be refused (fail closed).

The tessdata module in the Flatpak manifests uses tessdata_fast URLs
with a specific commit SHA that must match TESSDATA_BEST_URL in config.py.

stdlib only: release.sh runs this with the system python3.
"""

import json
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PY = REPO_ROOT / "anura" / "config.py"
MANIFEST_MAIN = REPO_ROOT / "flatpak" / "io.github.d3msudo.anura.json"
MANIFEST_LOCAL = REPO_ROOT / "flatpak" / "io.github.d3msudo.anura.local.json"
CHECKSUMS_MANIFEST = REPO_ROOT / "anura" / "data" / "tessdata_checksums.json"

# Regex to extract tessdata git ref (commit SHA or release tag, e.g. "4.1.0")
# from tessdata GitHub URLs. Refs may be tags since Bug #6 (2026-09): upstream
# repos rewrite history, orphaning hardcoded commit SHAs.
# Matches patterns like: tessdata_fast/raw/<ref>/filename
TESSDATA_URL_PATTERN = re.compile(
    r"github\.com/tesseract-ocr/tessdata[^/]*/raw/([A-Za-z0-9._-]+)/"
)

# Regex to extract tessdata git ref from config.py TESSDATA_BEST_URL
CONFIG_TESSDATA_PATTERN = re.compile(
    r"TESSDATA_BEST_URL\s*=\s*[\"']https?://[^\"']*/raw/([A-Za-z0-9._-]+)/"
)

# Regex to extract the pinned base URLs (TESSDATA_URL, TESSDATA_BEST_URL,
# TESSDATA_STANDARD_URL) declared in config.py
CONFIG_TESSDATA_URLS_PATTERN = re.compile(
    r"^TESSDATA(?:_BEST|_STANDARD)?_URL\s*=\s*[\"'](https://github\.com/tesseract-ocr/"
    r"tessdata[^\"']*/raw/[A-Za-z0-9._-]+/)[\"']",
    re.MULTILINE,
)


def extract_sha_from_config(config_path: Path) -> str | None:
    """Extract the tessdata commit SHA from config.py TESSDATA_BEST_URL."""
    content = config_path.read_text()
    match = CONFIG_TESSDATA_PATTERN.search(content)
    return match.group(1) if match else None


def extract_shas_from_manifest(manifest_path: Path) -> list[str]:
    """Extract tessdata commit SHAs from manifest tessdata module sources."""
    data = json.loads(manifest_path.read_text())
    shas = []

    for module in data.get("modules", []):
        if module.get("name") != "tessdata":
            continue
        for source in module.get("sources", []):
            url = source.get("url", "")
            match = TESSDATA_URL_PATTERN.search(url)
            if match:
                shas.append(match.group(1))

    return shas


def extract_tessdata_urls_from_config(config_path: Path) -> set[str]:
    """Extract the pinned tessdata base URLs declared in config.py."""
    return set(CONFIG_TESSDATA_URLS_PATTERN.findall(config_path.read_text()))


def extract_urls_from_checksums_manifest(manifest_path: Path) -> set[str]:
    """Extract the repository URLs pinned in the integrity manifest."""
    data = json.loads(manifest_path.read_text())
    repositories = data.get("repositories", {})
    return {repo["url"] for repo in repositories.values() if isinstance(repo, dict) and "url" in repo}


def check_checksums_manifest() -> list[str]:
    """Verify the integrity manifest still matches the URLs in config.py.

    A re-pinned tag (or an added/removed repository) without regenerating
    anura/data/tessdata_checksums.json would make every runtime download fail
    closed, so this is a release blocker rather than a runtime surprise.
    """
    if not CHECKSUMS_MANIFEST.exists():
        return [f"Missing tessdata integrity manifest: {CHECKSUMS_MANIFEST}"]

    try:
        manifest_urls = extract_urls_from_checksums_manifest(CHECKSUMS_MANIFEST)
    except (OSError, ValueError) as error:
        return [f"Cannot read tessdata integrity manifest {CHECKSUMS_MANIFEST}: {error}"]

    try:
        config_urls = extract_tessdata_urls_from_config(CONFIG_PY)
    except OSError as error:
        return [f"Cannot read {CONFIG_PY}: {error}"]

    if not config_urls:
        return [f"Could not extract tessdata URLs from {CONFIG_PY}"]

    if manifest_urls != config_urls:
        return [
            "Tessdata integrity manifest is out of date:",
            f"  config.py:  {sorted(config_urls)}",
            f"  manifest:   {sorted(manifest_urls)}",
            "  Regenerate it with build-aux/generate_tessdata_checksums.py",
        ]

    return []


def main() -> int:
    """Check tessdata consistency. Returns 0 if consistent, 1 if drift detected."""
    errors: list[str] = []

    # Extract SHAs from config.py
    config_sha = extract_sha_from_config(CONFIG_PY)
    if config_sha is None:
        print(f"ERROR: Could not extract TESSDATA_BEST_URL SHA from {CONFIG_PY}", file=sys.stderr)
        return 2

    # Extract SHAs from manifests
    main_shas = extract_shas_from_manifest(MANIFEST_MAIN)
    local_shas = extract_shas_from_manifest(MANIFEST_LOCAL)

    if not main_shas:
        print(f"ERROR: No tessdata SHAs found in {MANIFEST_MAIN}", file=sys.stderr)
        return 2

    if not local_shas:
        print(f"ERROR: No tessdata SHAs found in {MANIFEST_LOCAL}", file=sys.stderr)
        return 2

    # Get unique SHAs from each source
    unique_main = set(main_shas)
    unique_local = set(local_shas)

    # Check consistency
    if unique_main != unique_local:
        errors.append("Main vs Local manifest tessdata SHA mismatch:")
        errors.append(f"  main:  {unique_main}")
        errors.append(f"  local: {unique_local}")

    if config_sha not in unique_main:
        errors.append(f"config.py TESSDATA_BEST_URL SHA ({config_sha}) not found in main manifest tessdata sources")

    if config_sha not in unique_local:
        errors.append(f"config.py TESSDATA_BEST_URL SHA ({config_sha}) not found in local manifest tessdata sources")

    # Verify that the committed integrity manifest still matches config.py
    errors.extend(check_checksums_manifest())

    if errors:
        print("FAIL: Tessdata consistency check failed")
        for error in errors:
            print(f"  {error}")
        return 1

    print(f"PASS: Tessdata SHAs are consistent (commit: {config_sha[:12]}...)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
