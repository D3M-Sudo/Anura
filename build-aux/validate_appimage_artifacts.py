#!/usr/bin/env python3
# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
# SPDX-License-Identifier: MIT
"""Validate a complete pair of AppImage and zsync assets for each architecture."""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ARCHITECTURES = ("x86_64", "aarch64")


def expected_assets(version: str) -> set[str]:
    return {
        f"Anura-{version}-{arch}{suffix}"
        for arch in ARCHITECTURES
        for suffix in (".AppImage", ".AppImage.zsync")
    }


def validate_appimage_artifacts(directory: Path, version: str) -> list[tuple[str, int, str]]:
    """Return exact asset names, sizes and SHA-256 hashes after strict validation."""
    if not directory.is_dir():
        raise ValueError(f"artifact directory does not exist: {directory}")
    expected = expected_assets(version)
    entries = list(directory.iterdir())
    actual = {entry.name for entry in entries}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing assets: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected assets: {', '.join(unexpected)}")
        raise ValueError("; ".join(details))
    results = []
    for name in sorted(expected):
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"asset is not a regular file: {name}")
        size = path.stat().st_size
        if size <= 0:
            raise ValueError(f"asset is empty: {name}")
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        results.append((name, size, digest.hexdigest()))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--checksum-file", required=True, type=Path)
    args = parser.parse_args()
    try:
        results = validate_appimage_artifacts(args.directory, args.version)
        args.checksum_file.write_text(
            "".join(f"{digest}  {name}\n" for name, _, digest in results),
            encoding="utf-8",
        )
    except (OSError, ValueError) as exc:
        print(f"ERROR: AppImage artifact validation failed: {exc}", file=sys.stderr)
        return 1
    for name, size, digest in results:
        print(f"PASS: {name} ({size} bytes, SHA-256 {digest})")
    print(f"PASS: exactly {len(results)} AppImage/zsync assets validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
