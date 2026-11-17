"""Tests for the [Unreleased] changelog integrity guard."""

from collections import Counter
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "build-aux" / "check_changelog_integrity.py"
SPEC = importlib.util.spec_from_file_location("changelog_guard", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_extracts_only_unreleased_bullets_and_stops_at_next_version():
    content = "# Changelog\n## [Unreleased]\n### Fixed\n- keep\n## [1.0.0]\n- released\n"
    assert MODULE.unreleased_entries(content) == ["keep"]


def test_missing_unreleased_section_is_rejected():
    with pytest.raises(MODULE.ChangelogError, match="Unreleased"):
        MODULE.unreleased_entries("# Changelog\n")


def test_detects_removed_bullet():
    base = "## [Unreleased]\n- keep\n- lost\n"
    head = "## [Unreleased]\n- keep\n"
    assert MODULE.check_entries(base, head, Counter()) == ["lost (removed 1 time(s))"]


def test_allows_exact_authorized_removal():
    base = "## [Unreleased]\n- lost\n"
    head = "## [Unreleased]\n"
    assert MODULE.check_entries(base, head, Counter({"lost": 1})) == []


def test_duplicate_bullets_are_counted():
    base = "## [Unreleased]\n- same\n- same\n"
    head = "## [Unreleased]\n- same\n"
    assert MODULE.check_entries(base, head, Counter()) == ["same (removed 1 time(s))"]


def test_authorization_requires_reason_and_reference(tmp_path):
    path = tmp_path / "allow.json"
    valid = {
        "version": 1,
        "authorized_removals": [
            {
                "entry": "old entry",
                "reason": "No longer applies after the replacement shipped.",
                "reference": "#123",
            }
        ],
    }
    path.write_text(json.dumps(valid), encoding="utf-8")
    assert MODULE.load_authorized_removals(path) == Counter({"old entry": 1})

    valid["authorized_removals"][0]["reason"] = "short"
    path.write_text(json.dumps(valid), encoding="utf-8")
    with pytest.raises(MODULE.ChangelogError, match="reason"):
        MODULE.load_authorized_removals(path)
