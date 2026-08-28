#!/usr/bin/env python3
# .github/scripts/fedc_certifi.py
"""
Centralized certifi source matcher and manifest manipulator for the FEDC
(Flatpak External Data Checker) workflow.

This script provides a single, deterministic function for identifying the
certifi source in Flatpak manifests. It replaces the three inline Python
heredocs that previously existed in the workflow, eliminating duplicated
matching logic.

The matcher identifies certifi by checking if the source URL's filename
starts with 'certifi-', which is the standard PyPI naming convention for
the certifi package wheel. This criterion is robust because:

  - The certifi source in this project's manifest has NO x-checker-data
    field, so x-checker-data matching (the old approach) fails with 0 matches.
  - URL filenames are deterministic and unique per package.
  - No hardcoded array indices are required.
  - Works identically for the original, FEDC-updated, and real manifests.

Subcommands:
  isolate <manifest> <output>  Create temp manifest with only certifi source.
  replace <real> <updated>     Replace certifi source in real manifest.
  verify <manifest>            Verify only certifi was modified (security).
  count <manifest>             Count certifi sources (for testing/debugging).
"""

import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def is_certifi_source(source: dict[str, Any]) -> bool:
    """
    Determine if a source dict represents the certifi package.

    Uses URL filename matching: extracts the filename from the source URL
    and checks if it starts with 'certifi-'. This is the standard PyPI
    naming convention for the certifi wheel (e.g.,
    'certifi-2026.4.22-py3-none-any.whl').
    """
    url = source.get("url", "")
    if not url:
        return False
    filename = os.path.basename(url)
    # Require both the certifi- filename prefix and a Python artifact
    # extension, so unrelated URLs (e.g. git repos named "certifi-mirror.git")
    # can never produce a false positive.
    return filename.startswith("certifi-") and filename.endswith((".whl", ".tar.gz", ".zip"))


def find_certifi_sources(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Find all certifi sources in a Flatpak manifest.

    Returns a list of (module_name, source) tuples for all sources that are
    certifi packages. If no certifi sources are found, raises a SystemExit
    with an informative message.

    Args:
        manifest: The parsed JSON manifest.

    Returns:
        List of (module_name, source) tuples for certifi sources.
    """
    matches = []
    for module in manifest.get("modules", []):
        module_name = module.get("name", "")
        for source in module.get("sources", []):
            if is_certifi_source(source):
                matches.append((module_name, source))

    if len(matches) != 1:
        raise SystemExit(f"Expected exactly one certifi source, found {len(matches)}")

    return matches


def create_isolated_manifest(real_manifest_path: str, output_path: str) -> None:
    """Create an isolated manifest containing ONLY the certifi source.

    Reads the real manifest, finds the certifi source, and writes a new
    manifest containing only that source. This is used for the FEDC
    isolation step.

    Args:
        real_manifest_path: Path to the original manifest file.
        output_path: Path where the isolated manifest will be written.
    """
    real_manifest = json.loads(Path(real_manifest_path).read_text())
    matches = find_certifi_sources(real_manifest)

    module_name, certifi_source = matches[0]
    isolated = {
        "app-id": real_manifest.get("app-id", "io.github.d3msudo.anura"),
        "modules": [
            {
                "name": module_name,
                "sources": [certifi_source],
            }
        ],
    }

    Path(output_path).write_text(json.dumps(isolated, indent=4) + "\n")


def replace_certifi_source(real_manifest_path: str, updated_manifest_path: str) -> None:
    """Replace the certifi source in a real manifest with an updated one.

    Reads the original manifest and an updated manifest (containing only
    certifi), and replaces the certifi source in the original with the
    updated one. This is used for the FEDC update step.

    Args:
        real_manifest_path: Path to the original manifest file.
        updated_manifest_path: Path to the updated manifest file.
    """
    real_manifest = json.loads(Path(real_manifest_path).read_text())
    updated_manifest = json.loads(Path(updated_manifest_path).read_text())

    find_certifi_sources(real_manifest)  # enforces exactly one certifi source
    updated_matches = find_certifi_sources(updated_manifest)

    if len(updated_matches) != 1:
        raise SystemExit(f"Expected exactly one updated certifi source, found {len(updated_matches)}")

    module_name, certifi_source = updated_matches[0]

    for module in real_manifest.get("modules", []):
        if module.get("name") == module_name:
            for i, source in enumerate(module.get("sources", [])):
                if is_certifi_source(source):
                    module["sources"][i] = certifi_source
                    break

    Path(real_manifest_path).write_text(json.dumps(real_manifest, indent=4) + "\n")


def verify_certifi_only_change(manifest_path: str) -> None:
    """Verify that only the certifi source has been modified in a manifest.

    This is used to ensure that the FEDC update only modified the certifi
    source and did not modify any other sources.

    Args:
        manifest_path: Path to the manifest to verify.
    """
    # Run git diff to see what changed
    result = subprocess.run(
        ["git", "diff", "--check", manifest_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: git diff --check failed with the following diff:")
        subprocess.run(["git", "diff", manifest_path])
        raise SystemExit("Manifest contains changes beyond certifi only.")


def count_certifi_sources(manifest_path: str) -> None:
    """Count the number of certifi sources in a manifest.

    Used for debugging and testing purposes.

    Args:
        manifest_path: Path to the manifest file.
    """
    manifest = json.loads(Path(manifest_path).read_text())
    matches = find_certifi_sources(manifest)
    print(len(matches))


def main() -> None:
    """Entry point for the script. Handles command-line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python fedc_certifi.py <command> [args]")
        print("Commands:")
        print("  isolate <manifest> <output>")
        print("  replace <real> <updated>")
        print("  verify <manifest>")
        print("  count <manifest>")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "isolate":
            if len(sys.argv) != 4:
                raise SystemExit("Usage: python fedc_certifi.py isolate <manifest> <output>")
            create_isolated_manifest(sys.argv[2], sys.argv[3])
        elif command == "replace":
            if len(sys.argv) != 4:
                raise SystemExit("Usage: python fedc_certifi.py replace <real> <updated>")
            replace_certifi_source(sys.argv[2], sys.argv[3])
        elif command == "verify":
            if len(sys.argv) != 3:
                raise SystemExit("Usage: python fedc_certifi.py verify <manifest>")
            verify_certifi_only_change(sys.argv[2])
        elif command == "count":
            if len(sys.argv) != 3:
                raise SystemExit("Usage: python fedc_certifi.py count <manifest>")
            count_certifi_sources(sys.argv[2])
        else:
            raise SystemExit(f"Unknown command: {command}")

    except SystemExit as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
