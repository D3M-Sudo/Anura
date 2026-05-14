# test_release_notes_generation.py
#
# Tests for build-aux/generate_release_notes.py
# Specifically guards against the libxml parse error in the Adw.AboutDialog
# "Novità" window when the regex fails to match CHANGELOG sections that contain
# "### Subsection" headers (the original `[^#]*?` content pattern stopped at
# the first `#`, leaving RELEASE_NOTES empty and CURRENT_NOTES = bare text).

from pathlib import Path
import sys
import textwrap

import pytest

# Add build-aux to import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "build-aux"))

from generate_release_notes import parse_changelog  # noqa: E402


@pytest.fixture
def sample_changelog(tmp_path: Path) -> Path:
    changelog = tmp_path / "CHANGELOG.md"
    changelog.write_text(
        textwrap.dedent(
            """\
            # Changelog

            ## [Unreleased]

            ## [0.1.4.3] - 2026-05-09

            ### Added

            - Feature A
            - Feature B with **markdown** that should be stripped

            ### Fixed

            - Bug fix one
            - Bug fix two

            ## [0.1.4.2] - 2026-05-05

            ### Fixed

            - Earlier fix
            """,
        ),
    )
    return changelog


def test_parse_changelog_finds_sections_with_subsections(sample_changelog: Path) -> None:
    """Section content containing '### Added' must be captured (regression test)."""
    releases = parse_changelog(sample_changelog)
    assert "0.1.4.3" in releases, "Top version must be parsed"
    assert "0.1.4.2" in releases, "Older version must be parsed"


def test_parse_changelog_output_starts_with_xml_element(sample_changelog: Path) -> None:
    """Adw.AboutDialog requires markup that begins with an element. Bare text
    triggers the libxml error 'The document must start with an element'."""
    releases = parse_changelog(sample_changelog)
    notes = releases["0.1.4.3"]
    assert notes.lstrip().startswith("<"), f"Notes must begin with an XML element, got: {notes[:60]!r}"


def test_parse_changelog_includes_subsection_items(sample_changelog: Path) -> None:
    """Items under '### Added' must appear in the output."""
    releases = parse_changelog(sample_changelog)
    notes = releases["0.1.4.3"]
    assert "Feature A" in notes
    assert "Bug fix one" in notes
    # markdown emphasis should be stripped
    assert "**" not in notes


def test_parse_real_changelog_has_current_version() -> None:
    """The real CHANGELOG.md must yield a non-empty entry for the project version."""
    real_changelog = PROJECT_ROOT / "CHANGELOG.md"
    if not real_changelog.exists():
        pytest.skip("CHANGELOG.md not present in checkout")
    releases = parse_changelog(real_changelog)
    assert releases, "Real changelog must produce at least one parsed release"
    # Every parsed entry must be Pango-friendly
    for version, html_str in releases.items():
        assert html_str.lstrip().startswith("<"), f"Release {version} produced bare text: {html_str[:60]!r}"
