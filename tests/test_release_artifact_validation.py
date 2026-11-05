# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tests for strict multi-architecture release artifact validation."""

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "build-aux" / "validate_release_artifacts.py"

spec = importlib.util.spec_from_file_location("validate_release_artifacts", SCRIPT)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def _write_bundles(directory: Path) -> None:
    (directory / "io.github.d3m_sudo.anura-x86_64.flatpak").write_bytes(b"x86 bundle")
    (directory / "io.github.d3m_sudo.anura-aarch64.flatpak").write_bytes(b"arm bundle")


def test_validates_both_architectures_and_returns_sha256(tmp_path):
    _write_bundles(tmp_path)

    results = validator.validate_release_artifacts(tmp_path)

    assert {name for name, _size, _digest in results} == validator.EXPECTED_BUNDLES
    assert all(size > 0 and len(digest) == 64 for _name, size, digest in results)


def test_rejects_a_missing_architecture_bundle(tmp_path):
    (tmp_path / "io.github.d3m_sudo.anura-x86_64.flatpak").write_bytes(b"x86 bundle")

    with pytest.raises(ValueError, match="missing bundles"):
        validator.validate_release_artifacts(tmp_path)


def test_rejects_unexpected_entries(tmp_path):
    _write_bundles(tmp_path)
    (tmp_path / "unexpected.txt").write_text("unexpected", encoding="utf-8")

    with pytest.raises(ValueError, match="unexpected entries"):
        validator.validate_release_artifacts(tmp_path)


def test_rejects_empty_bundles(tmp_path):
    _write_bundles(tmp_path)
    (tmp_path / "io.github.d3m_sudo.anura-aarch64.flatpak").write_bytes(b"")

    with pytest.raises(ValueError, match="empty"):
        validator.validate_release_artifacts(tmp_path)


def test_rejects_symlinked_bundles(tmp_path):
    _write_bundles(tmp_path)
    arm = tmp_path / "io.github.d3m_sudo.anura-aarch64.flatpak"
    arm.unlink()
    arm.symlink_to(tmp_path / "io.github.d3m_sudo.anura-x86_64.flatpak")

    with pytest.raises(ValueError, match="regular file"):
        validator.validate_release_artifacts(tmp_path)
