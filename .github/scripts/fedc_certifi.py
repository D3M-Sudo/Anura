#!/usr/bin/env python3
# .github/scripts/fedc_certifi.py
"""Helpers for isolating the certifi source for FEDC updates.

The real manifest intentionally does not need x-checker-data. The temporary
manifest does: FEDC needs explicit PyPI checker metadata in order to inspect
the isolated certifi source.
"""

import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def is_certifi_source(source: dict[str, Any]) -> bool:
    """Return True when a source is a certifi Python artifact."""
    url = source.get("url", "")
    if not url:
        return False
    filename = os.path.basename(url)
    return filename.startswith("certifi-") and filename.endswith(
        (".whl", ".tar.gz", ".zip")
    )


def find_certifi_sources(manifest: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Find exactly one certifi source in a Flatpak manifest."""
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
    """Create a temporary manifest containing only certifi.

    FEDC requires x-checker-data to select its PyPI checker. This metadata is
    deliberately added only to the temporary manifest and is stripped again
    by replace_certifi_source(), so the production Flatpak manifest remains
    unchanged except for the URL/checksum update.
    """
    real_manifest = json.loads(Path(real_manifest_path).read_text())
    module_name, certifi_source = find_certifi_sources(real_manifest)[0]

    isolated_source = copy.deepcopy(certifi_source)
    isolated_source["x-checker-data"] = {
        "type": "pypi",
        "name": "certifi",
    }

    isolated = {
        "app-id": real_manifest.get("app-id", "io.github.d3msudo.anura"),
        "modules": [
            {
                "name": module_name,
                "sources": [isolated_source],
            }
        ],
    }

    Path(output_path).write_text(json.dumps(isolated, indent=4) + "\n")


def replace_certifi_source(real_manifest_path: str, updated_manifest_path: str) -> None:
    """Replace the real certifi source with the FEDC-updated source.

    x-checker-data is temporary FEDC metadata and must never be copied into
    the real manifest.
    """
    real_manifest = json.loads(Path(real_manifest_path).read_text())
    updated_manifest = json.loads(Path(updated_manifest_path).read_text())

    module_name, _ = find_certifi_sources(real_manifest)[0]
    updated_module_name, updated_source = find_certifi_sources(updated_manifest)[0]
    if module_name != updated_module_name:
        raise SystemExit(
            f"Certifi module mismatch: real={module_name!r}, updated={updated_module_name!r}"
        )

    source_to_insert = copy.deepcopy(updated_source)
    source_to_insert.pop("x-checker-data", None)

    replaced = False
    for module in real_manifest.get("modules", []):
        if module.get("name") != module_name:
            continue
        for i, source in enumerate(module.get("sources", [])):
            if is_certifi_source(source):
                module["sources"][i] = source_to_insert
                replaced = True
                break

    if not replaced:
        raise SystemExit("Failed to replace certifi source in real manifest")

    Path(real_manifest_path).write_text(json.dumps(real_manifest, indent=4) + "\n")


def verify_certifi_only_change(manifest_path: str) -> None:
    """Run git diff --check for the target manifest."""
    result = subprocess.run(
        ["git", "diff", "--check", manifest_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("Error: git diff --check failed with the following diff:")
        subprocess.run(["git", "diff", manifest_path])
        raise SystemExit("Manifest contains invalid changes.")


def count_certifi_sources(manifest_path: str) -> None:
    """Print the number of certifi sources in a manifest."""
    manifest = json.loads(Path(manifest_path).read_text())
    print(len(find_certifi_sources(manifest)))


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python fedc_certifi.py <command> [args]")
        print("Commands: isolate, replace, verify, count")
        sys.exit(1)

    command = sys.argv[1]
    try:
        if command == "isolate" and len(sys.argv) == 4:
            create_isolated_manifest(sys.argv[2], sys.argv[3])
        elif command == "replace" and len(sys.argv) == 4:
            replace_certifi_source(sys.argv[2], sys.argv[3])
        elif command == "verify" and len(sys.argv) == 3:
            verify_certifi_only_change(sys.argv[2])
        elif command == "count" and len(sys.argv) == 3:
            count_certifi_sources(sys.argv[2])
        else:
            raise SystemExit(f"Invalid arguments for command: {command}")
    except SystemExit as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
