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


def test_detects_duplicate_unreleased_categories():
    content = "## [Unreleased]\n### Changed\n- first\n### Fixed\n- second\n### Changed\n- third\n"
    assert MODULE.duplicate_unreleased_categories(content) == ["Changed"]


def test_allows_distinct_unreleased_categories():
    content = "## [Unreleased]\n### Changed\n- one\n### Fixed\n- two\n"
    assert MODULE.duplicate_unreleased_categories(content) == []


def test_duplicate_categories_after_next_release_are_ignored():
    content = "## [Unreleased]\n### Changed\n- current\n## [1.0.0]\n### Fixed\n- old\n### Fixed\n- older\n"
    assert MODULE.duplicate_unreleased_categories(content) == []


def test_detects_exact_duplicate_bullets_after_whitespace_normalization():
    content = "## [Unreleased]\n### Fixed\n- repeated   wording\n-   repeated wording  \n"
    assert MODULE.duplicate_unreleased_entries(content) == ["repeated wording"]


def test_allows_distinct_bullets_without_semantic_matching():
    content = "## [Unreleased]\n### Fixed\n- Fix the scanner cache\n- Fix scanner cache\n- FIX the scanner cache\n"
    assert MODULE.duplicate_unreleased_entries(content) == []


def test_duplicate_bullets_after_next_release_are_ignored():
    content = "## [Unreleased]\n### Fixed\n- current\n## [1.0.0]\n### Fixed\n- old\n- old\n"
    assert MODULE.duplicate_unreleased_entries(content) == []


def test_accepts_well_formed_unreleased_structure():
    content = "# Changelog\n\n## [Unreleased]\n### Added\n- one\n### Fixed\n- two\n## [1.0.0]\n"
    assert MODULE.validate_unreleased_structure(content) == []


def test_rejects_empty_category():
    content = "## [Unreleased]\n### Added\n### Fixed\n- valid\n"
    assert any("Empty [Unreleased] category: Added" in e for e in MODULE.validate_unreleased_structure(content))


def test_rejects_empty_category_heading():
    content = "## [Unreleased]\n###   \n- entry\n"
    assert any("Empty category heading" in e for e in MODULE.validate_unreleased_structure(content))


@pytest.mark.parametrize("bullet", ["-", "-   ", "-no-space", "* alternate", "+ alternate"])
def test_rejects_empty_or_malformed_bullets(bullet):
    content = f"## [Unreleased]\n### Fixed\n{bullet}\n"
    assert any("Malformed or empty bullet" in e for e in MODULE.validate_unreleased_structure(content))


def test_rejects_bullet_outside_category():
    content = "## [Unreleased]\n- orphan\n### Fixed\n- valid\n"
    assert any("Bullet outside a category" in e for e in MODULE.validate_unreleased_structure(content))


def test_rejects_malformed_heading_level():
    content = "## [Unreleased]\n#### Subheading\n- entry\n"
    assert any("Malformed heading" in e for e in MODULE.validate_unreleased_structure(content))


def test_rejects_duplicate_unreleased_header():
    content = "## [Unreleased]\n### Fixed\n- entry\n## [Unreleased]\n"
    with pytest.raises(MODULE.ChangelogError, match="exactly one"):
        MODULE.unreleased_section_lines(content)


def test_requires_unreleased_to_be_first_release_section():
    content = "## [1.0.0]\n- old\n## [Unreleased]\n### Fixed\n- current\n"
    with pytest.raises(MODULE.ChangelogError, match="first release section"):
        MODULE.unreleased_section_lines(content)
