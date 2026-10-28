# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Check the license inventory of a built Flatpak prefix (#493).

The manifest declares, per module, where the license text must be installed
under ``/app/share/licenses/<app-id>/<name>/LICENSE``. This script derives the
expected list from the manifest and verifies it against a real prefix (for
example ``.flatpak-builder/build/<app>/files`` after a build, or ``/app`` inside
the container), failing when a file is missing or empty.

Usage:
    python3 build-aux/check_license_inventory.py --root builddir/files
    python3 build-aux/check_license_inventory.py --root /app --output inventory.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys

LICENSE_DEST_RE = re.compile(r"share/licenses/([^/\"]+)/([^/\"]+)/LICENSE")


def expected_licenses(manifest_path: Path) -> list[tuple[str, str]]:
    """Return (module, destination) pairs declared by the manifest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected: list[tuple[str, str]] = []

    for module in manifest.get("modules", []):
        for command in module.get("build-commands") or []:
            if "share/licenses" not in command:
                continue
            match = LICENSE_DEST_RE.search(command)
            if match:
                app_id, name = match.groups()
                expected.append((module["name"], f"share/licenses/{app_id}/{name}/LICENSE"))

    return expected


def build_inventory(root: Path, expected: list[tuple[str, str]]) -> tuple[list[dict], list[str]]:
    """Return the inventory entries and the list of problems found."""
    entries: list[dict] = []
    problems: list[str] = []

    for module, relative in expected:
        path = root / relative
        if not path.is_file():
            problems.append(f"missing license for {module}: {relative}")
            continue
        size = path.stat().st_size
        if size == 0:
            problems.append(f"empty license for {module}: {relative}")
            continue
        entries.append({"module": module, "path": relative, "bytes": size})

    return entries, problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("flatpak/io.github.d3msudo.anura.local.json"),
        help="manifest to read the expected licenses from",
    )
    parser.add_argument(
        "--root",
        type=Path,
        required=True,
        help="root of the installed prefix (contains share/licenses/...)",
    )
    parser.add_argument("--output", type=Path, help="write the inventory as JSON to this path")
    args = parser.parse_args(argv)

    if not args.manifest.is_file():
        print(f"FAIL: manifest not found: {args.manifest}")
        return 1
    if not args.root.is_dir():
        print(f"FAIL: prefix not found: {args.root}")
        return 1

    expected = expected_licenses(args.manifest)
    entries, problems = build_inventory(args.root, expected)

    if args.output:
        args.output.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")

    for entry in entries:
        print(f"OK   {entry['module']:28} {entry['bytes']:>7} B  {entry['path']}")
    for problem in problems:
        print(f"FAIL {problem}")

    print(f"\n{len(entries)}/{len(expected)} licenses present")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
