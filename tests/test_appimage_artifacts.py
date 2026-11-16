from __future__ import annotations

import hashlib
from pathlib import Path
import runpy

import pytest

VALIDATOR = runpy.run_path(str(Path(__file__).resolve().parents[1] / "build-aux" / "validate_appimage_artifacts.py"))
validate_appimage_artifacts = VALIDATOR["validate_appimage_artifacts"]


def make_assets(directory: Path, version: str = "0.2.1") -> None:
    for arch in ("x86_64", "aarch64"):
        (directory / f"Anura-{version}-{arch}.AppImage").write_bytes(f"image-{arch}".encode())
        (directory / f"Anura-{version}-{arch}.AppImage.zsync").write_text(f"zsync-{arch}", encoding="utf-8")


def test_validates_exact_appimage_and_zsync_pairs(tmp_path: Path) -> None:
    make_assets(tmp_path)
    result = validate_appimage_artifacts(tmp_path, "0.2.1")
    assert len(result) == 4
    assert {name for name, _, _ in result} == {
        f"Anura-{version}-{arch}{suffix}"
        for version in ("0.2.1",)
        for arch in ("x86_64", "aarch64")
        for suffix in (".AppImage", ".AppImage.zsync")
    }


def test_rejects_missing_zsync_file(tmp_path: Path) -> None:
    make_assets(tmp_path)
    (tmp_path / "Anura-0.2.1-aarch64.AppImage.zsync").unlink()
    with pytest.raises(ValueError, match="missing"):
        validate_appimage_artifacts(tmp_path, "0.2.1")


def test_rejects_unexpected_assets(tmp_path: Path) -> None:
    make_assets(tmp_path)
    (tmp_path / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        validate_appimage_artifacts(tmp_path, "0.2.1")


def test_rejects_empty_assets(tmp_path: Path) -> None:
    make_assets(tmp_path)
    (tmp_path / "Anura-0.2.1-x86_64.AppImage").write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        validate_appimage_artifacts(tmp_path, "0.2.1")


def test_checksums_are_sha256(tmp_path: Path) -> None:
    make_assets(tmp_path)
    results = validate_appimage_artifacts(tmp_path, "0.2.1")
    image = next(item for item in results if item[0].endswith("x86_64.AppImage"))
    assert image[2] == hashlib.sha256(b"image-x86_64").hexdigest()
