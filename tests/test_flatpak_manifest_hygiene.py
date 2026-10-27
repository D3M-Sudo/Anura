# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Manifest hygiene for the Flatpak runtime (#542, #543, #546, #480, #482).

These are static assertions on the local manifest; the actual build is validated
by the `flatpak-builder` job, which is why they pin the intent (no unrecognized
configure options, no architecture-specific paths, no development or build-only
artefacts in the final prefix).
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


def _module(manifest: dict, name: str) -> dict:
    return next(module for module in manifest["modules"] if module["name"] == name)


def test_imlib2_does_not_pass_unrecognized_options(manifest: dict) -> None:
    """#542: 1.12.6 rejects these, so they must not be in the manifest."""
    opts = _module(manifest, "imlib2")["config-opts"]

    for flag in ("--without-bmp", "--without-xbm", "--without-xpm"):
        assert flag not in opts, f"{flag} is not recognized by imlib2 1.12.6"
    assert not [opt for opt in opts if opt.startswith("--with-loader-dir")]


def test_imlib2_drops_helper_binaries_and_demo_data(manifest: dict) -> None:
    """#546: only the runtime library and the PNG loader are needed."""
    cleanup = _module(manifest, "imlib2").get("cleanup", [])

    assert "/bin" in cleanup
    assert "/share/imlib2/data" in cleanup


def test_tesseract_does_not_use_unsupported_training_flag(manifest: dict) -> None:
    """#543: the flag is ignored, so the training tools are removed instead."""
    tesseract = _module(manifest, "tesseract")

    assert "--disable-training" not in tesseract["config-opts"]
    cleanup = tesseract.get("cleanup", [])
    assert "/bin/lstmtraining" in cleanup
    assert "/bin/text2image" in cleanup


def test_environment_paths_are_architecture_neutral(manifest: dict) -> None:
    """#480: no literal x86_64 (or aarch64) path in the build environment."""
    env = manifest["build-options"]["env"]

    assert "x86_64" not in json.dumps(env)
    assert "aarch64" not in json.dumps(env)
    assert env["LD_LIBRARY_PATH"] == "/app/lib"


def test_build_only_python_tooling_is_removed(manifest: dict) -> None:
    """#482: the compilers' Python helpers must not ship in the runtime."""
    cleanup = " ".join(manifest["cleanup"])

    for module in ("scikit_build_core", "pybind11", "nanobind"):
        assert module in cleanup, f"{module} is not removed from the runtime"
