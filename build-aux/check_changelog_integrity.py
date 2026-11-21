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


def unreleased_section_lines(content: str) -> list[str]:
    """Return lines belonging to the unique, first [Unreleased] section."""
    lines = content.splitlines()
    headings = [i for i, line in enumerate(lines) if line.strip() == "## [Unreleased]"]
    if len(headings) != 1:
        raise ChangelogError(f"Expected exactly one ## [Unreleased] heading (found {len(headings)})")
    start = headings[0]
    release_headings = [line.strip() for line in lines if re.match(r"^##\s+", line)]
    if not release_headings or release_headings[0] != "## [Unreleased]":
        raise ChangelogError("[Unreleased] must be the first release section")
    for index in range(start + 1, len(lines)):
        if re.match(r"^##\s+", lines[index]):
            return lines[start + 1 : index]
    return lines[start + 1 :]


def unreleased_entries(content: str) -> list[str]:
    """Return whitespace-normalized bullet text from [Unreleased]."""
    entries = []
    for line in unreleased_section_lines(content):
        match = re.match(r"^\s*-\s+(.+?)\s*$", line)
        if match:
            entries.append(" ".join(match.group(1).split()))
    return entries


def duplicate_unreleased_entries(content: str) -> list[str]:
    """Return exact duplicate bullets after whitespace normalization."""
    counts = Counter(unreleased_entries(content))
    return sorted(entry for entry, count in counts.items() if count > 1)


def duplicate_unreleased_categories(content: str) -> list[str]:
    """Return repeated category headings in [Unreleased]."""
    categories = []
    for line in unreleased_section_lines(content):
        match = re.match(r"^###\s+(.+?)\s*$", line)
        if match:
            categories.append(" ".join(match.group(1).split()))
    counts = Counter(categories)
    return sorted(category for category, count in counts.items() if count > 1)


def validate_unreleased_structure(content: str) -> list[str]:
    """Validate category placement, non-empty categories and canonical bullets."""
    lines = unreleased_section_lines(content)
    errors: list[str] = []
    category = None
    category_has_bullet = False

    def finish_category() -> None:
        if category is not None and not category_has_bullet:
            errors.append(f"Empty [Unreleased] category: {category}")

    for number, line in enumerate(lines, start=1):
        if re.match(r"^####+\s+", line):
            errors.append(f"Malformed heading at [Unreleased] line {number}: {line.strip()}")
            continue
        heading = re.match(r"^###\s*(.*?)\s*$", line)
        if heading:
            finish_category()
            category = " ".join(heading.group(1).split())
            category_has_bullet = False
            if not category:
                errors.append(f"Empty category heading at [Unreleased] line {number}")
            continue
        if re.match(r"^#{2,}\s+", line):
            errors.append(f"Malformed heading at [Unreleased] line {number}: {line.strip()}")
            continue
        if re.match(r"^\s*[-*+]\s*", line) or re.match(r"^\s*[-*+][^\s]", line):
            bullet = re.match(r"^-\s+(\S.*)$", line)
            if bullet is None:
                errors.append(f"Malformed or empty bullet at [Unreleased] line {number}")
            elif category is None:
                errors.append(f"Bullet outside a category at [Unreleased] line {number}")
            else:
                category_has_bullet = True
    finish_category()
    return errors


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
        structure_errors = validate_unreleased_structure(head_content)
        duplicate_categories = duplicate_unreleased_categories(head_content)
        duplicate_entries = duplicate_unreleased_entries(head_content)
        if structure_errors or duplicate_categories or duplicate_entries:
            if structure_errors:
                print("::error::Invalid [Unreleased] structure:")
                for error in structure_errors:
                    print(f"  - {error}")
            if duplicate_categories:
                print("::error::Duplicate [Unreleased] category headings:")
                for category in duplicate_categories:
                    print(f"  - ### {category}")
            if duplicate_entries:
                print("::error::Duplicate [Unreleased] bullets (exact text after whitespace normalization):")
                for entry in duplicate_entries:
                    print(f"  - {entry}")
            return 1
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
