# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""A share provider must not promise a transfer it cannot perform (#579).

`share_providers` has no GTK dependency, so these assertions run in the default
headless gate rather than the GTK tier.
"""

from anura.services.share_providers import PROVIDERS, generate_share_link


def _repository_root():
    from pathlib import Path

    return Path(__file__).resolve().parents[1]


def _share_icon_directory():
    return _repository_root() / "data" / "icons" / "scalable" / "actions"


def test_reddit_does_not_duplicate_the_text():
    link = generate_share_link("reddit", "short text")

    assert link.count("short") == 1
    assert "title=" not in link


def test_reddit_sends_the_text_as_selftext():
    assert generate_share_link("reddit", "a b") == "https://www.reddit.com/submit?selftext=a%20b"


def test_discord_is_not_offered():
    assert "discord" not in {provider.id for provider in PROVIDERS}
    assert generate_share_link("discord", "x") == ""


def test_every_provider_produces_a_link_for_its_own_text():
    for provider in PROVIDERS:
        link = generate_share_link(provider.id, "hello world")
        assert link, f"{provider.id} produced no link"
        assert " " not in link, f"{provider.id} left an unescaped space: {link}"


def test_share_icon_inventory_matches_active_providers_and_resources():
    icon_directory = _share_icon_directory()
    provider_ids = {provider.id for provider in PROVIDERS}
    expected_files = {f"share-{provider_id}-symbolic.svg" for provider_id in provider_ids}
    actual_files = {path.name for path in icon_directory.glob("*.svg")}
    assert actual_files == expected_files

    expected_resources = {f"icons/scalable/actions/{filename}" for filename in expected_files}
    with open(_repository_root() / "data" / "io.github.d3m_sudo.anura.gresource.xml", encoding="utf-8") as manifest_file:
        manifest = manifest_file.read()
    actual_resources = {
        entry.split("</file>", 1)[0]
        for entry in manifest.split("<file>")[1:]
        if entry.startswith("icons/scalable/actions/")
    }
    assert actual_resources == expected_resources


def test_share_icons_use_a_uniform_theme_aware_symbolic_format():
    import xml.etree.ElementTree as ET

    for icon_path in _share_icon_directory().glob("*.svg"):
        root = ET.parse(icon_path).getroot()
        assert root.attrib["width"] == "24"
        assert root.attrib["height"] == "24"
        assert root.attrib["viewBox"] == "0 0 24 24"
        paths = list(root)
        assert paths
        assert all(path.tag.endswith("path") for path in paths)
        assert all(path.attrib.get("class") == "foreground" for path in paths)
        assert all("d" in path.attrib for path in paths)
