# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for the Flatpak license inventory checker (#493)."""

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "build-aux" / "check_license_inventory.py"
MANIFEST = REPO_ROOT / "flatpak" / "io.github.d3msudo.anura.local.json"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_license_inventory", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


checker = _load_module()


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST.read_text())


def test_expected_licenses_come_from_the_manifest(manifest: dict) -> None:
    expected = checker.expected_licenses(MANIFEST)

    modules = {module for module, _dest in expected}
    assert "python3-loguru" in modules
    assert "python3-requests" in modules
    # Every declared destination is unique.
    destinations = [dest for _module, dest in expected]
    assert len(destinations) == len(set(destinations))


def test_inventory_passes_when_all_licenses_exist(tmp_path):
    expected = checker.expected_licenses(MANIFEST)
    for _module, relative in expected:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("license text\n", encoding="utf-8")

    entries, problems = checker.build_inventory(tmp_path, expected)

    assert problems == []
    assert len(entries) == len(expected)


def test_inventory_fails_on_a_missing_license(tmp_path):
    expected = checker.expected_licenses(MANIFEST)
    # Create every license except the first one.
    for _module, relative in expected[1:]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("license text\n", encoding="utf-8")

    _entries, problems = checker.build_inventory(tmp_path, expected)

    assert len(problems) == 1
    assert "missing license" in problems[0]


def test_inventory_fails_on_an_empty_license(tmp_path):
    expected = checker.expected_licenses(MANIFEST)
    for _module, relative in expected:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("license text\n", encoding="utf-8")
    first = expected[0][1]
    (tmp_path / first).write_text("", encoding="utf-8")

    _entries, problems = checker.build_inventory(tmp_path, expected)

    assert problems == [f"empty license for {expected[0][0]}: {first}"]


def test_main_writes_the_inventory_and_exit_code(tmp_path):
    expected = checker.expected_licenses(MANIFEST)
    for _module, relative in expected:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("license text\n", encoding="utf-8")
    output = tmp_path / "inventory.json"

    code = checker.main(["--root", str(tmp_path), "--output", str(output)])

    assert code == 0
    assert len(json.loads(output.read_text())) == len(expected)
