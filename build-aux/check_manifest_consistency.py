#!/usr/bin/env python3
# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Compare complete local and release Flatpak manifests."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_RELEASE = REPO_ROOT / "flatpak" / "io.github.d3m_sudo.anura.json"
MANIFEST_LOCAL = REPO_ROOT / "flatpak" / "io.github.d3m_sudo.anura.local.json"
LOCAL_ONLY_KEYS = ("branch", "separate-locales")


def normalize_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize only documented local/release differences."""
    normalized = copy.deepcopy(data)
    for key in LOCAL_ONLY_KEYS:
        normalized.pop(key, None)

    app_modules = [m for m in normalized.get("modules", []) if m.get("name") == "anura"]
    if len(app_modules) != 1:
        raise ValueError(f"expected exactly one 'anura' module, found {len(app_modules)}")
    app_modules[0]["sources"] = [{"type": "git", "url": "<app-source>", "tag": "<release-tag>"}]
    return normalized


def _differences(left: Any, right: Any, path: str = "$") -> list[str]:
    if isinstance(left, dict) and isinstance(right, dict):
        result: list[str] = []
        for key in sorted(set(left) | set(right)):
            child = f"{path}.{key}"
            if key not in left or key not in right:
                result.append(child)
            else:
                result.extend(_differences(left[key], right[key], child))
        return result
    if isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            return [f"{path} (length {len(left)} != {len(right)})"]
        result = []
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            result.extend(_differences(a, b, f"{path}[{index}]"))
        return result
    return [] if left == right else [path]


def check_consistency(local_path: Path = MANIFEST_LOCAL, release_path: Path = MANIFEST_RELEASE) -> list[str]:
    local = json.loads(local_path.read_text(encoding="utf-8"))
    release = json.loads(release_path.read_text(encoding="utf-8"))
    return _differences(normalize_manifest(local), normalize_manifest(release))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local", type=Path, default=MANIFEST_LOCAL)
    parser.add_argument("--release", type=Path, default=MANIFEST_RELEASE)
    args = parser.parse_args()

    for path in (args.local, args.release):
        if not path.is_file():
            print(f"ERROR: {path} not found", file=sys.stderr)
            return 2
    try:
        differences = check_consistency(args.local, args.release)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: cannot compare manifests: {exc}", file=sys.stderr)
        return 2

    if differences:
        print("FAIL: release manifest differs from local source of truth")
        for path in differences:
            print(f"  {path}")
        return 1
    print("PASS: complete release manifest matches local source of truth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
