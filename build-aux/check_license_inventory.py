# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Check the license inventory of a built Flatpak prefix (#493).

Three things are verified against a real prefix:

* every Python/native module that declares an install command in the manifest
  has its ``share/licenses/<app-id>/<name>/LICENSE``;
* application's own license is at ``share/licenses/<app-id>/LICENSE`` (installed
  by Meson);
* the native modules whose license flatpak-builder records automatically
  (imlib2, scrot, libportal, tessdata_fast) have at least one non-empty file in
  their directory, whatever upstream names it.

The full directory listing is included in the JSON output as evidence for the
release review.

Usage:
    python3 build-aux/check_license_inventory.py --root builddir/files
    python3 build-aux/check_license_inventory.py --root /app --output inventory.json
"""

from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
import re
import sys

LICENSE_DEST_RE = re.compile(r"share/licenses/([^/\"]+)/([^/\"]+)/LICENSE")

# Licenses flatpak-builder records automatically from the extracted sources; the
# file name differs per project (COPYING, COPYING-PLAIN, LICENSE), so only the
# presence of a non-empty file is required.
NATIVE_LICENSE_MODULES = ("imlib2", "scrot", "libportal", "tessdata_fast")


def _manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def removed_license_dirs(manifest_path: Path) -> set[str]:
    """Directories under share/licenses/<app-id>/ removed by the app cleanup.

    Build-only modules (scikit-build-core, pybind11, nanobind) install a licence
    and are then removed from the runtime together with it (#482): requiring
    their licence would fail a correct bundle.
    """
    manifest = _manifest(manifest_path)
    prefix = f"/share/licenses/{manifest['app-id']}/"
    return {entry[len(prefix) :].strip("/") for entry in manifest.get("cleanup") or [] if entry.startswith(prefix)}


def _is_removed(name: str, removed: set[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in removed)


def _declared_licenses(manifest_path: Path) -> list[tuple[str, str, str]]:
    """Return (module, directory, destination) for every declared licence."""
    manifest = _manifest(manifest_path)
    declared: list[tuple[str, str, str]] = []

    for module in manifest.get("modules", []):
        for command in module.get("build-commands") or []:
            if "share/licenses" not in command:
                continue
            match = LICENSE_DEST_RE.search(command)
            if match:
                app_id, name = match.groups()
                declared.append((module["name"], name, f"share/licenses/{app_id}/{name}/LICENSE"))

    return declared


def expected_licenses(manifest_path: Path) -> list[tuple[str, str]]:
    """Return (module, destination) pairs that must exist in the bundle.

    Licences removed by the app-level cleanup are excluded: those modules are
    not distributed.
    """
    removed = removed_license_dirs(manifest_path)
    return [
        (module, destination)
        for module, name, destination in _declared_licenses(manifest_path)
        if not _is_removed(name, removed)
    ]


def excluded_licenses(manifest_path: Path) -> list[tuple[str, str]]:
    """Return (module, destination) pairs intentionally removed from the runtime."""
    removed = removed_license_dirs(manifest_path)
    return [
        (module, destination)
        for module, name, destination in _declared_licenses(manifest_path)
        if _is_removed(name, removed)
    ]


def app_id_from_manifest(manifest_path: Path) -> str:
    return _manifest(manifest_path)["app-id"]


def scan_licenses(root: Path, app_id: str) -> list[dict]:
    """Return every file under share/licenses/<app-id>, for the release evidence."""
    base = root / "share" / "licenses" / app_id
    if not base.is_dir():
        return []

    return [
        {"path": str(path.relative_to(root)), "bytes": path.stat().st_size}
        for path in sorted(base.rglob("*"))
        if path.is_file()
    ]


def build_inventory(
    root: Path,
    expected: list[tuple[str, str]],
    app_id: str,
) -> tuple[list[dict], list[str]]:
    """Return the required inventory entries and the list of problems found."""
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

    base = root / "share" / "licenses" / app_id

    app_license = base / "LICENSE"
    if not app_license.is_file():
        problems.append(f"missing application license: share/licenses/{app_id}/LICENSE")
    elif app_license.stat().st_size == 0:
        problems.append(f"empty application license: share/licenses/{app_id}/LICENSE")
    else:
        entries.append(
            {
                "module": "anura",
                "path": f"share/licenses/{app_id}/LICENSE",
                "bytes": app_license.stat().st_size,
            }
        )

    for name in NATIVE_LICENSE_MODULES:
        directory = base / name
        files = (
            [path for path in directory.iterdir() if path.is_file() and path.stat().st_size > 0]
            if directory.is_dir()
            else []
        )
        if not files:
            problems.append(f"missing license for native module {name}: share/licenses/{app_id}/{name}/")
            continue
        entries.append(
            {
                "module": name,
                "path": str(files[0].relative_to(root)),
                "bytes": files[0].stat().st_size,
            }
        )

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

    app_id = app_id_from_manifest(args.manifest)
    expected = expected_licenses(args.manifest)
    entries, problems = build_inventory(args.root, expected, app_id)

    if args.output:
        payload = {
            "app_id": app_id,
            "required": entries,
            "problems": problems,
            "excluded_build_only": [
                {"module": module, "path": destination} for module, destination in excluded_licenses(args.manifest)
            ],
            "all_license_files": scan_licenses(args.root, app_id),
        }
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    for module, destination in excluded_licenses(args.manifest):
        print(f"SKIP {module:28} {destination} (build-only, removed from the runtime)")

    for entry in entries:
        print(f"OK   {entry['module']:28} {entry['bytes']:>7} B  {entry['path']}")
    for problem in problems:
        print(f"FAIL {problem}")

    print(f"\n{len(entries)}/{len(expected) + 1 + len(NATIVE_LICENSE_MODULES)} required licenses present")
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
