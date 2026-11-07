#!/usr/bin/env python3
"""Fail when a PR silently removes existing [Unreleased] changelog bullets."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST = ROOT / ".github" / "changelog-removals.json"


class ChangelogError(ValueError):
    """Invalid changelog or removal authorization data."""


def unreleased_entries(content: str) -> list[str]:
    """Return normalized bullet text from the first [Unreleased] section."""
    lines = content.splitlines()
    start = next(
        (index for index, line in enumerate(lines) if line.strip() == "## [Unreleased]"),
        None,
    )
    if start is None:
        raise ChangelogError("Missing ## [Unreleased] section")

    entries = []
    for line in lines[start + 1 :]:
        if re.match(r"^##\s+", line):
            break
        match = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if match:
            entries.append(" ".join(match.group(1).split()))
    return entries


def load_authorized_removals(path: Path = ALLOWLIST) -> Counter[str]:
    """Load exact removed bullets with mandatory rationale and issue/PR reference."""
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ChangelogError(f"Invalid authorization file: {exc}") from exc

    if not isinstance(data, dict) or data.get("version") != 1 or not isinstance(data.get("authorized_removals"), list):
        raise ChangelogError("Expected version 1 and authorized_removals list")

    authorized: Counter[str] = Counter()
    for index, item in enumerate(data["authorized_removals"]):
        if not isinstance(item, dict):
            raise ChangelogError(f"Record {index} must be an object")

        entry = item.get("entry")
        reason = item.get("reason")
        reference = item.get("reference")
        if not isinstance(entry, str) or not entry.strip():
            raise ChangelogError(f"Record {index}: entry is required")
        if not isinstance(reason, str) or len(reason.strip()) < 20:
            raise ChangelogError(f"Record {index}: reason must contain at least 20 characters")
        if not isinstance(reference, str) or not re.fullmatch(
            r"(?:#\d+|https://github\.com/[^/]+/[^/]+/(?:issues|pull)/\d+)",
            reference,
        ):
            raise ChangelogError(f"Record {index}: reference must be #number or GitHub issue/PR URL")

        normalized = " ".join(entry.split())
        if normalized in authorized:
            raise ChangelogError(f"Duplicate authorization for: {normalized}")
        authorized[normalized] += 1

    return authorized


def read_git_file(ref: str) -> str:
    """Read CHANGELOG.md from a commit without relying on the worktree version."""
    result = subprocess.run(
        ["git", "show", f"{ref}:CHANGELOG.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode:
        raise ChangelogError(f"Cannot read CHANGELOG.md at {ref}: {result.stderr.strip()}")
    return result.stdout


def check_entries(base_content: str, head_content: str, authorized: Counter[str]) -> list[str]:
    """Return undocumented removals, counting identical bullets separately."""
    removed = Counter(unreleased_entries(base_content)) - Counter(unreleased_entries(head_content))
    remaining_authorizations = authorized.copy()
    violations = []

    for entry, count in sorted(removed.items()):
        permitted = min(count, remaining_authorizations[entry])
        remaining_authorizations[entry] -= permitted
        if count > permitted:
            violations.append(f"{entry} (removed {count - permitted} time(s))")

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--head-ref", required=True)
    args = parser.parse_args()

    try:
        base_content = read_git_file(args.base_ref)
        head_content = read_git_file(args.head_ref)
        violations = check_entries(base_content, head_content, load_authorized_removals())
    except ChangelogError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2

    if violations:
        print("::error::Undocumented [Unreleased] removals:")
        for violation in violations:
            print(f"  - {violation}")
        print(
            "Authorize intentional removals in .github/changelog-removals.json "
            "with exact text, rationale and issue/PR reference."
        )
        return 1

    print("Changelog integrity check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
