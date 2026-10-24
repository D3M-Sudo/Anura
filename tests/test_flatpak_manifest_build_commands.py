# tests/test_flatpak_manifest_build_commands.py
"""Regression tests for the Flatpak manifest's build-time Python modules.

Regression (#427): FEDC replaced the scikit-build-core 1.0.1 wheel source with
the 1.1.1 sdist, but the module's ``build-commands`` still installed the old
wheel by filename, so the Flatpak build could not find it. zxing-cpp 3.1 also
moved its Python bindings from pybind11 to nanobind, which requires a
``python3-nanobind`` module and no longer needs ``pybind11_DIR``.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "flatpak" / "io.github.d3msudo.anura.local.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.skip("local manifest not available")
    return json.loads(MANIFEST_PATH.read_text())


def _modules(manifest: dict) -> dict[str, dict]:
    return {module["name"]: module for module in manifest["modules"]}


def _source_filename(module: dict) -> str:
    return module["sources"][0]["url"].rsplit("/", 1)[-1]


def test_wheel_modules_install_the_wheel_they_declare(manifest: dict) -> None:
    """Every module whose source is a wheel must install that exact filename."""
    checked = 0
    for module in manifest["modules"]:
        sources = module.get("sources") or []
        if not sources or sources[0].get("type") != "file":
            continue

        filename = _source_filename(module)
        if not filename.endswith(".whl"):
            continue

        checked += 1
        install_commands = [command for command in module.get("build-commands", []) if "pip3 install" in command]
        assert install_commands, f"{module['name']} has no pip3 install build-command"
        assert any(filename in command for command in install_commands), (
            f"{module['name']} build-command does not install {filename}: {install_commands!r}"
        )

    assert checked > 0, "no wheel-based module found in the local manifest"


def test_zxing_cpp_uses_nanobind_not_pybind11(manifest: dict) -> None:
    """zxing-cpp >=3.1 builds with nanobind, not the pybind11_DIR workaround."""
    modules = _modules(manifest)
    zxing = modules["python3-zxing-cpp"]

    assert "python3-nanobind" in modules
    assert not any("pybind11" in command for command in zxing.get("build-commands", []))


def test_build_time_helpers_precede_the_modules_that_import_them(manifest: dict) -> None:
    """Pillow imports pybind11 and zxing-cpp imports nanobind at build time."""
    order = {module["name"]: index for index, module in enumerate(manifest["modules"])}

    assert order["python3-pybind11"] < order["python3-pillow"]
    assert order["python3-nanobind"] < order["python3-zxing-cpp"]
    assert order["python3-scikit-build-core"] < order["python3-zxing-cpp"]


def test_zxing_cpp_installs_the_sdist_it_declares(manifest: dict) -> None:
    zxing = _modules(manifest)["python3-zxing-cpp"]
    filename = _source_filename(zxing)

    assert filename.endswith(".tar.gz")
    install_commands = [command for command in zxing.get("build-commands", []) if "pip3 install" in command]
    assert any("pip3 install" in command and command.rstrip().endswith(".") for command in install_commands), (
        f"zxing-cpp build-command does not build the extracted sdist: {install_commands!r}"
    )
