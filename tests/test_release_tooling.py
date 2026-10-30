# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Release tooling guards (#485, #487).

`release.sh` mutates versions, regenerates the release manifest, commits and
tags. These tests pin the guards that make it refuse to run on a dirty tree or
an existing tag, and the rule that the AppStream entry comes from the CHANGELOG
instead of a placeholder.
"""

import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RELEASE = REPO_ROOT / "build-aux" / "release.sh"
GENERATOR = REPO_ROOT / "build-aux" / "generate_release_notes.py"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


def _load_generator():
    spec = importlib.util.spec_from_file_location("generate_release_notes", GENERATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = _load_generator()


def test_release_script_has_the_preflight_guards():
    source = RELEASE.read_text(encoding="utf-8")

    assert 'git -C "$PROJECT_ROOT" status --porcelain' in source
    assert "refs/tags/v$VERSION" in source
    assert "RELEASE_BRANCH" in source


def test_release_script_no_longer_writes_placeholder_notes():
    source = RELEASE.read_text(encoding="utf-8")

    assert "TODO: Add release notes before publishing" not in source
    assert "<p>Release $VERSION.</p>" not in source
    assert "--metainfo" in source


def test_generator_emits_a_valid_release_entry():
    entry = generator.metainfo_release_entry(CHANGELOG, "0.2.1", "2026-10-20")

    release = ET.fromstring(f"<releases>{entry}</releases>").find("release")
    assert release is not None
    assert release.get("version") == "0.2.1"
    assert release.get("date") == "2026-10-20"
    assert release.find("description") is not None
    assert "TODO" not in entry
    # Snake_case identifiers must survive (the HTML variant strips underscores).
    assert "test_history_expansion_real.py" in entry


def test_generator_refuses_a_version_without_notes():
    with pytest.raises(SystemExit):
        generator.metainfo_release_entry(CHANGELOG, "9.9.9", "2026-10-20")


def test_markdown_release_notes_come_from_the_changelog():
    """The GitHub release body mirrors the CHANGELOG section (#489)."""
    body = generator.markdown_release_notes(CHANGELOG, "0.2.1", "2026-10-20")

    assert body.startswith("## Anura v0.2.1 — 2026-10-20")
    assert "### Added" in body
    assert "tests/test_history_expansion_real.py" in body


def test_markdown_release_notes_refuse_a_missing_version():
    with pytest.raises(SystemExit):
        generator.markdown_release_notes(CHANGELOG, "9.9.9", "2026-10-20")
