# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Static checks of the AppStream metadata and desktop entry (#497, #499).

`appstreamcli validate` is the authoritative check and is wired into CI
separately (#483). These assertions catch the regressions that matter for the
Flathub submission and that no other test looks at: the id must match the
desktop file, the summary and description must be present, the screenshots must
be pinned to the release tag instead of a mutable branch, and the gettext
catalogues must exist for every declared locale.
"""

from pathlib import Path
import re
import xml.etree.ElementTree as ET

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
METAINFO = REPO_ROOT / "data" / "io.github.d3msudo.anura.metainfo.xml.in"
DESKTOP = REPO_ROOT / "data" / "io.github.d3msudo.anura.desktop.in"
MESON = REPO_ROOT / "meson.build"
LINGUAS = REPO_ROOT / "po" / "LINGUAS"

APP_ID = "io.github.d3msudo.anura"


@pytest.fixture(scope="module")
def metainfo() -> ET.Element:
    return ET.parse(METAINFO).getroot()


def _project_version() -> str:
    match = re.search(r"version:\s*'([^']+)'", MESON.read_text(encoding="utf-8"))
    assert match, "version not found in meson.build"
    return match.group(1)


def test_component_identity_matches_the_desktop_entry(metainfo: ET.Element) -> None:
    assert metainfo.get("type") == "desktop-application"
    assert metainfo.findtext("id") == APP_ID
    assert (REPO_ROOT / "data" / f"{APP_ID}.desktop.in").is_file()

    launchable = metainfo.find("launchable")
    assert launchable is not None
    assert launchable.get("type") == "desktop-id"
    assert launchable.text == f"{APP_ID}.desktop"


def test_summary_and_description_are_present(metainfo: ET.Element) -> None:
    summary = metainfo.findtext("summary", "").strip()
    description = metainfo.find("description")

    assert 0 < len(summary) <= 80
    assert description is not None
    paragraphs = [p for p in description.findall("p") if (p.text or "").strip()]
    assert paragraphs, "description needs at least one paragraph"


def test_licenses_developer_and_rating_are_declared(metainfo: ET.Element) -> None:
    assert metainfo.findtext("metadata_license") == "CC0-1.0"
    assert metainfo.findtext("project_license") == "MIT"

    developer = metainfo.find("developer")
    assert developer is not None
    assert developer.get("id")
    assert (developer.findtext("name") or "").strip()

    rating = metainfo.find("content_rating")
    assert rating is not None
    assert rating.get("type") == "oars-1.1"


def test_screenshots_are_pinned_to_the_release_tag(metainfo: ET.Element) -> None:
    version = _project_version()
    screenshots = metainfo.findall("screenshots/screenshot")

    assert screenshots, "at least one screenshot is required"
    for shot in screenshots:
        image = (shot.findtext("image") or "").strip()
        assert image.startswith("https://"), image
        # A mutable branch would silently change the published screenshots.
        assert f"/v{version}/data/screenshots/" in image, image
        assert (shot.findtext("caption") or "").strip(), f"missing caption for {image}"


def test_releases_include_the_current_version(metainfo: ET.Element) -> None:
    version = _project_version()
    releases = metainfo.findall("releases/release")
    versions = [release.get("version") for release in releases]

    assert releases, "at least one release is required"
    assert version in versions, f'no <release version="{version}"> entry'
    # The current release is what Flathub shows: it needs real notes, not a
    # placeholder. Older entries may predate that rule.
    latest = releases[0]
    notes = " ".join(text.strip() for text in latest.itertext() if text.strip())
    assert latest.get("date")
    assert "TODO" not in notes
    assert not re.fullmatch(r"Release \d+\.\d+\.\d+\.?", notes), f"placeholder notes: {notes!r}"


def test_desktop_entry_has_the_required_keys() -> None:
    entries = {}
    for line in DESKTOP.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("["):
            key, value = line.split("=", 1)
            entries[key] = value

    assert entries["Type"] == "Application"
    assert entries["Icon"] == APP_ID
    assert entries["Exec"].split()[0] == "anura"
    assert entries["Terminal"] == "false"
    assert set(entries["Categories"].rstrip(";").split(";")) >= {"Graphics", "Utility"}


def test_every_declared_locale_has_a_catalogue() -> None:
    locales = [line.strip() for line in LINGUAS.read_text(encoding="utf-8").splitlines() if line.strip()]

    assert locales, "po/LINGUAS is empty"
    # English is the source language, so it is not listed on purpose.
    assert "en" not in locales
    missing = [code for code in locales if not (REPO_ROOT / "po" / f"{code}.po").is_file()]
    assert missing == [], f"missing .po files for: {missing}"
