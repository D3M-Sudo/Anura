#!/usr/bin/env python3
# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Validate the two Flatpak bundles downloaded for a multi-architecture release."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

EXPECTED_BUNDLES = {
    "io.github.d3m_sudo.anura-x86_64.flatpak",
    "io.github.d3m_sudo.anura-aarch64.flatpak",
}


def validate_release_artifacts(directory: Path) -> list[tuple[str, int, str]]:
    """Return bundle names, sizes and SHA-256 digests after strict validation."""
    if not directory.is_dir():
        raise ValueError(f"artifact directory does not exist: {directory}")

    entries = list(directory.iterdir())
    actual_names = {entry.name for entry in entries}
    if actual_names != EXPECTED_BUNDLES:
        missing = sorted(EXPECTED_BUNDLES - actual_names)
        unexpected = sorted(actual_names - EXPECTED_BUNDLES)
        details = []
        if missing:
            details.append(f"missing bundles: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected entries: {', '.join(unexpected)}")
        raise ValueError("; ".join(details))

    results = []
    for name in sorted(EXPECTED_BUNDLES):
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"bundle is not a regular file: {name}")
        size = path.stat().st_size
        if size <= 0:
            raise ValueError(f"bundle is empty: {name}")

        digest = hashlib.sha256()
        with path.open("rb") as bundle:
            for chunk in iter(lambda: bundle.read(1024 * 1024), b""):
                digest.update(chunk)
        results.append((name, size, digest.hexdigest()))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--checksum-file", required=True, type=Path)
    args = parser.parse_args()

    try:
        results = validate_release_artifacts(args.directory)
        lines = [f"{digest}  {name}" for name, _size, digest in results]
        args.checksum_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except (OSError, ValueError) as exc:
        print(f"ERROR: release artifact validation failed: {exc}", file=sys.stderr)
        return 1

    for name, size, digest in results:
        print(f"PASS: {name} ({size} bytes, SHA-256 {digest})")
    print(f"PASS: exactly {len(results)} architecture bundles validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
