#!/usr/bin/env python3
# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Generate the release Flatpak manifest from the local source of truth."""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
from typing import Any

APP_SOURCE_URL = "https://github.com/D3M-Sudo/Anura.git"
LOCAL_ONLY_KEYS = ("branch", "separate-locales")
VERSION_RE = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?")


def generate_release_manifest(
    local_manifest: dict[str, Any],
    version: str,
    *,
    source_path: str | None = None,
    source_commit: str | None = None,
) -> dict[str, Any]:
    """Return a release manifest derived from the local manifest.

    CI may supply a local repository path and exact commit so it can build the
    same release manifest without fetching a tag. Real releases use v<version>.
    """
    if not VERSION_RE.fullmatch(version):
        raise ValueError(f"invalid release version: {version!r}")
    if (source_path is None) != (source_commit is None):
        raise ValueError("--source-path and --source-commit must be supplied together")
    if source_commit is not None and not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be a full 40-character lowercase SHA")
    if source_path is not None and (not source_path or Path(source_path).is_absolute()):
        raise ValueError("--source-path must be a non-empty relative path")

    manifest = copy.deepcopy(local_manifest)
    for key in LOCAL_ONLY_KEYS:
        manifest.pop(key, None)

    app_modules = [m for m in manifest.get("modules", []) if m.get("name") == "anura"]
    if len(app_modules) != 1:
        raise ValueError(f"expected exactly one 'anura' module, found {len(app_modules)}")

    if source_path is None:
        app_modules[0]["sources"] = [
            {"type": "git", "url": APP_SOURCE_URL, "tag": f"v{version}"}
        ]
    else:
        app_modules[0]["sources"] = [
            {"type": "git", "path": source_path, "commit": source_commit}
        ]
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--source-path")
    parser.add_argument("--source-commit")
    args = parser.parse_args()

    try:
        local = json.loads(args.input.read_text(encoding="utf-8"))
        generated = generate_release_manifest(
            local,
            args.version,
            source_path=args.source_path,
            source_commit=args.source_commit,
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(generated, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"ERROR: cannot generate release manifest: {exc}", file=sys.stderr)
        return 1

    print(f"Generated {args.output} from {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
