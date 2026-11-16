#!/usr/bin/env python3
# tests/test_fedc_certifi.py
"""Regression tests for the FEDC certifi update helper.

Regression: the weekly FEDC workflow updated only the certifi source URL and
checksum, while the module's build-commands kept installing the previous
tarball. The Flatpak build then failed with "No such file or directory"
(PR #460: certifi 2026.7.22 -> 2026.10.18).
"""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / ".github" / "scripts" / "fedc_certifi.py"
OLD_FILENAME = "certifi-2026.7.22.tar.gz"
NEW_FILENAME = "certifi-2026.10.18.tar.gz"
BASE_URL = "https://files.pythonhosted.org/packages/xx/"
OLD_URL = f"{BASE_URL}{OLD_FILENAME}"
NEW_URL = f"{BASE_URL}{NEW_FILENAME}"
LICENSE_COMMAND = "bash -c 'find /app/lib/python3.*/site-packages/certifi-*.dist-info -iname \"*icense*\"'"


def _load_fedc_certifi():
    spec = importlib.util.spec_from_file_location("fedc_certifi", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fedc_certifi = _load_fedc_certifi()


def _manifest(*, build_commands: list[str] | None = None, **extra) -> dict:
    module: dict = {
        "name": "python3-certifi",
        "sources": [{"type": "file", "url": OLD_URL, "sha256": "old-sha"}],
    }
    if build_commands is not None:
        module["build-commands"] = list(build_commands)
    module.update(extra)
    return {
        "app-id": "io.github.d3msudo.anura",
        "modules": [
            {"name": "python3-pillow", "sources": [{"url": f"{BASE_URL}pillow-11.0.0.tar.gz"}]},
            module,
        ],
    }


def _write_manifest_pair(tmp_path: Path, real_manifest: dict) -> tuple[Path, Path]:
    real = tmp_path / "real.json"
    updated = tmp_path / "updated.json"
    real.write_text(json.dumps(real_manifest, indent=4) + "\n")

    isolated = {
        "app-id": "io.github.d3msudo.anura",
        "modules": [
            {
                "name": "python3-certifi",
                "sources": [
                    {
                        "type": "file",
                        "url": NEW_URL,
                        "sha256": "new-sha",
                        "x-checker-data": {"type": "pypi", "name": "certifi"},
                    }
                ],
            }
        ],
    }
    updated.write_text(json.dumps(isolated, indent=4) + "\n")
    return real, updated


def _certifi_module(manifest: dict) -> dict:
    return next(module for module in manifest["modules"] if module["name"] == "python3-certifi")


def test_replace_rewrites_certifi_build_command(tmp_path):
    install = f"pip3 install --no-deps --prefix=/app --ignore-installed {OLD_FILENAME}"
    real, updated = _write_manifest_pair(tmp_path, _manifest(build_commands=[install, LICENSE_COMMAND]))

    fedc_certifi.replace_certifi_source(str(real), str(updated))

    module = _certifi_module(json.loads(real.read_text()))
    assert module["build-commands"][0] == install.replace(OLD_FILENAME, NEW_FILENAME)
    assert module["sources"][0]["url"] == NEW_URL
    assert module["sources"][0]["sha256"] == "new-sha"
    assert "x-checker-data" not in module["sources"][0]


def test_replace_leaves_unrelated_commands_untouched(tmp_path):
    install = f"pip3 install --no-deps --prefix=/app {OLD_FILENAME}"
    real, updated = _write_manifest_pair(tmp_path, _manifest(build_commands=[install, LICENSE_COMMAND]))

    fedc_certifi.replace_certifi_source(str(real), str(updated))

    module = _certifi_module(json.loads(real.read_text()))
    assert module["build-commands"][1] == LICENSE_COMMAND


def test_replace_without_build_commands_does_not_crash(tmp_path):
    real, updated = _write_manifest_pair(tmp_path, _manifest())

    fedc_certifi.replace_certifi_source(str(real), str(updated))

    module = _certifi_module(json.loads(real.read_text()))
    assert "build-commands" not in module
    assert module["sources"][0]["url"] == NEW_URL


def test_replace_fails_closed_when_old_filename_is_still_referenced(tmp_path):
    install = f"pip3 install --no-deps --prefix=/app {OLD_FILENAME}"
    real_manifest = _manifest(build_commands=[install], post_install=[f"cp {OLD_FILENAME} /tmp/"])
    real, updated = _write_manifest_pair(tmp_path, real_manifest)

    with pytest.raises(SystemExit, match="still references the previous source filename"):
        fedc_certifi.replace_certifi_source(str(real), str(updated))


def test_sync_build_command_filenames_noop_when_filename_is_unchanged():
    module = {"build-commands": [f"pip3 install {OLD_FILENAME}"]}

    fedc_certifi.sync_build_command_filenames(module, OLD_FILENAME, OLD_FILENAME)

    assert module["build-commands"] == [f"pip3 install {OLD_FILENAME}"]


def test_local_manifest_installs_the_certifi_source_it_declares():
    repo_root = Path(__file__).resolve().parents[1]
    manifest_path = repo_root / "flatpak" / "io.github.d3msudo.anura.local.json"
    if not manifest_path.exists():
        pytest.skip("local manifest not available")

    manifest = json.loads(manifest_path.read_text())
    module = _certifi_module(manifest)
    source_filename = module["sources"][0]["url"].rsplit("/", 1)[-1]
    install_commands = [command for command in module.get("build-commands", []) if "pip3 install" in command]

    assert install_commands, "certifi module has no pip3 install build-command"
    assert any(source_filename in command for command in install_commands), (
        f"certifi build-command does not install {source_filename}: {install_commands!r}"
    )
