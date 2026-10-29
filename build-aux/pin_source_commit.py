#!/usr/bin/env python3
# build-aux/pin_source_commit.py
"""Pin the release manifest's Anura source to a commit (#501).

The repository's release manifest points the `anura` module at the release tag.
A tag can be moved, so the manifest used for the Flathub submission should also
carry the commit the tag resolved to when the release was cut. This script
resolves that commit with git and writes it into the manifest (`tag` is kept for
readability).

Usage:
    build-aux/pin_source_commit.py --tag v0.2.1
    build-aux/pin_source_commit.py --tag v0.2.1 --manifest path/to/manifest.json
    build-aux/pin_source_commit.py --check --tag v0.2.1
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

DEFAULT_MANIFEST = Path("flatpak/io.github.d3msudo.anura.json")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


class PinError(RuntimeError):
    """Raised when the manifest or the tag cannot be pinned."""


def anura_source(manifest: dict) -> dict:
    """Return the `anura` module's git source."""
    for module in manifest.get("modules", []):
        if module.get("name") != "anura":
            continue
        for source in module.get("sources") or []:
            if source.get("type") == "git":
                return source
        raise PinError("the anura module has no git source")
    raise PinError("the manifest has no 'anura' module")


def resolve_commit(tag: str) -> str:
    """Return the full commit SHA the local *tag* points at."""
    result = subprocess.run(
        ["git", "rev-parse", f"{tag}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    commit = result.stdout.strip()
    if result.returncode != 0 or not COMMIT_RE.match(commit):
        raise PinError(f"cannot resolve tag '{tag}': {result.stderr.strip() or 'not found'}")
    return commit


def pin_source(manifest: dict, commit: str, tag: str | None = None) -> str:
    """Set `commit` (and optionally `tag`) on the anura git source."""
    if not COMMIT_RE.match(commit):
        raise PinError(f"not a full commit SHA: {commit!r}")

    source = anura_source(manifest)
    if tag:
        source["tag"] = tag
    source["commit"] = commit
    return source.get("tag", "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--tag", help="release tag (default: the tag already in the manifest)")
    parser.add_argument("--commit", help="commit SHA (default: resolved from the tag with git)")
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the pin instead of writing it",
    )
    args = parser.parse_args(argv)

    if not args.manifest.is_file():
        print(f"FAIL: manifest not found: {args.manifest}")
        return 1

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))

    try:
        source = anura_source(manifest)
        tag = args.tag or source.get("tag")
        if not tag:
            raise PinError("no tag in the manifest and none passed with --tag")
        commit = args.commit or resolve_commit(tag)

        if args.check:
            pinned = source.get("commit")
            if pinned != commit:
                print(f"FAIL: {args.manifest} pins {pinned!r}, expected {commit} for {tag}")
                return 1
            print(f"OK: {args.manifest} pins {tag} at {commit}")
            return 0

        pin_source(manifest, commit, tag)
    except PinError as error:
        print(f"FAIL: {error}")
        return 1

    args.manifest.write_text(json.dumps(manifest, indent=4) + "\n", encoding="utf-8")
    print(f"Pinned {args.manifest}: {tag} -> {commit}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
