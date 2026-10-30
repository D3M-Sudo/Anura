# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for the Flatpak license inventory checker (#493)."""

import importlib.util
import json
from pathlib import Path

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


def _populate(tmp_path: Path, *, skip: str | None = None, empty: str | None = None) -> tuple[str, list]:
    """Create a complete license tree, optionally skipping or emptying one file."""
    app_id = checker.app_id_from_manifest(MANIFEST)
    expected = checker.expected_licenses(MANIFEST)

    for _module, relative in expected:
        if relative == skip:
            continue
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("" if relative == empty else "license text\n", encoding="utf-8")

    app_license = tmp_path / "share" / "licenses" / app_id / "LICENSE"
    app_license.parent.mkdir(parents=True, exist_ok=True)
    app_license.write_text("MIT License\n", encoding="utf-8")

    for name in checker.NATIVE_LICENSE_MODULES:
        directory = tmp_path / "share" / "licenses" / app_id / name
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "COPYING").write_text("native license\n", encoding="utf-8")

    return app_id, expected


def test_expected_licenses_come_from_the_manifest():
    expected = checker.expected_licenses(MANIFEST)

    modules = {module for module, _dest in expected}
    assert "python3-loguru" in modules
    assert "python3-requests" in modules
    destinations = [dest for _module, dest in expected]
    assert len(destinations) == len(set(destinations))


def test_inventory_passes_when_everything_is_present(tmp_path):
    app_id, expected = _populate(tmp_path)

    entries, problems = checker.build_inventory(tmp_path, expected, app_id)

    assert problems == []
    assert len(entries) == len(expected) + 1 + len(checker.NATIVE_LICENSE_MODULES)


def test_inventory_fails_on_a_missing_module_license(tmp_path):
    app_id, expected = _populate(tmp_path, skip=checker.expected_licenses(MANIFEST)[0][1])

    _entries, problems = checker.build_inventory(tmp_path, expected, app_id)

    assert len(problems) == 1
    assert "missing license" in problems[0]


def test_inventory_fails_on_an_empty_module_license(tmp_path):
    first = checker.expected_licenses(MANIFEST)[0][1]
    app_id, expected = _populate(tmp_path, empty=first)

    _entries, problems = checker.build_inventory(tmp_path, expected, app_id)

    assert problems == [f"empty license for {checker.expected_licenses(MANIFEST)[0][0]}: {first}"]


def test_inventory_requires_the_application_license(tmp_path):
    app_id, expected = _populate(tmp_path)
    (tmp_path / "share" / "licenses" / app_id / "LICENSE").unlink()

    _entries, problems = checker.build_inventory(tmp_path, expected, app_id)

    assert any("application license" in problem for problem in problems)


def test_inventory_requires_each_native_license(tmp_path):
    app_id, expected = _populate(tmp_path)
    native = checker.NATIVE_LICENSE_MODULES[0]
    (tmp_path / "share" / "licenses" / app_id / native / "COPYING").unlink()

    _entries, problems = checker.build_inventory(tmp_path, expected, app_id)

    assert any(native in problem for problem in problems)


def test_main_writes_the_inventory_and_exit_code(tmp_path):
    _populate(tmp_path)
    output = tmp_path / "inventory.json"

    code = checker.main(["--root", str(tmp_path), "--output", str(output)])

    assert code == 0
    payload = json.loads(output.read_text())
    assert payload["app_id"] == "io.github.d3msudo.anura"
    assert payload["problems"] == []
    assert payload["required"]
    assert payload["all_license_files"]


def test_main_fails_on_a_missing_license(tmp_path):
    app_id, _expected = _populate(tmp_path)
    (tmp_path / "share" / "licenses" / app_id / "LICENSE").unlink()

    assert checker.main(["--root", str(tmp_path)]) == 1


def test_build_only_modules_are_not_required(tmp_path):
    """Licences removed by the app cleanup must not be required (#482)."""
    expected = checker.expected_licenses(MANIFEST)
    excluded = checker.excluded_licenses(MANIFEST)

    expected_dests = " ".join(dest for _module, dest in expected)
    excluded_dests = " ".join(dest for _module, dest in excluded)

    for name in ("scikit-build-core", "pybind11", "nanobind"):
        assert f"/{name}/LICENSE" in excluded_dests
        assert f"/{name}/LICENSE" not in expected_dests


def test_a_module_without_cleanup_is_required(tmp_path):
    """Without a cleanup rule the declared licence stays part of the inventory."""
    manifest = {
        "app-id": "io.github.d3msudo.anura",
        "cleanup": [],
        "modules": [
            {
                "name": "python3-tool",
                "build-commands": [
                    'install -Dm0644 LICENSE "$FLATPAK_DEST/share/licenses/io.github.d3msudo.anura/tool/LICENSE"'
                ],
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert checker.expected_licenses(manifest_path) == [
        ("python3-tool", "share/licenses/io.github.d3msudo.anura/tool/LICENSE")
    ]
    assert checker.excluded_licenses(manifest_path) == []


def test_a_module_removed_by_cleanup_is_excluded(tmp_path):
    manifest = {
        "app-id": "io.github.d3msudo.anura",
        "cleanup": ["/share/licenses/io.github.d3msudo.anura/tool"],
        "modules": [
            {
                "name": "python3-tool",
                "build-commands": [
                    'install -Dm0644 LICENSE "$FLATPAK_DEST/share/licenses/io.github.d3msudo.anura/tool/LICENSE"'
                ],
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert checker.expected_licenses(manifest_path) == []
    assert checker.excluded_licenses(manifest_path) == [
        ("python3-tool", "share/licenses/io.github.d3msudo.anura/tool/LICENSE")
    ]
