#!/usr/bin/env python3
# tests/test_export_files.py
"""Headless security tests for anura.utils.export_files (audit item F3)."""

import os
from pathlib import Path
import stat
import time

import pytest

from anura.utils.export_files import (
    cleanup_stale_export_files,
    get_exports_dir,
    write_export_file,
)


@pytest.fixture
def runtime_exports(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point XDG_RUNTIME_DIR at a temp dir, like a desktop session would."""
    runtime = tmp_path / "runtime"
    runtime.mkdir()
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    return runtime / "anura" / "exports"


class TestExportsDir:
    def test_prefers_xdg_runtime_dir(self, runtime_exports: Path) -> None:
        assert get_exports_dir() == runtime_exports
        assert runtime_exports.is_dir()

    def test_runtime_dir_mode_is_private(self, runtime_exports: Path) -> None:
        get_exports_dir()
        assert stat.S_IMODE(runtime_exports.stat().st_mode) == 0o700

    def test_falls_back_to_per_user_cache_not_tmp(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
        exports = get_exports_dir()
        assert exports == tmp_path / "cache" / "anura" / "exports"
        assert stat.S_IMODE(exports.stat().st_mode) == 0o700
        assert str(exports).startswith(str(tmp_path))


class TestWriteExportFile:
    def test_writes_content_in_private_dir(self, runtime_exports: Path) -> None:
        path = write_export_file("hello ocr")
        assert path.read_text(encoding="utf-8") == "hello ocr"
        assert path.parent == runtime_exports
        assert stat.S_IMODE(path.stat().st_mode) & 0o077 == 0

    def test_names_are_unguessable(self, runtime_exports: Path) -> None:
        first = write_export_file("a")
        second = write_export_file("b")
        assert first != second
        assert "extracted_" in first.name

    def test_failed_write_removes_file(self, runtime_exports: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        class FailingHandle:
            def __init__(self, fd: int) -> None:
                self._fd = fd

            def __enter__(self):
                raise OSError("disk full")

            def __exit__(self, *_a) -> None:
                pass

        monkeypatch.setattr("anura.utils.export_files.os.fdopen", lambda fd, *_a, **_k: FailingHandle(fd))
        with pytest.raises(OSError):
            write_export_file("never persisted")
        assert list(runtime_exports.iterdir()) == []


class TestCleanup:
    def test_removes_only_stale_files(self, runtime_exports: Path) -> None:
        fresh = write_export_file("fresh")
        stale = write_export_file("stale")
        old = time.time() - 7200
        os.utime(stale, (old, old))

        assert cleanup_stale_export_files(time.time() - 3600) == 1
        assert not stale.exists()
        assert fresh.exists()

    def test_never_removes_symlinks(self, tmp_path: Path, runtime_exports: Path) -> None:
        outside = tmp_path / "outside.txt"
        outside.write_text("precious", encoding="utf-8")
        get_exports_dir()  # ensure the exports dir exists for the symlink
        link = runtime_exports / "extracted_link.txt"
        link.symlink_to(outside)
        os.utime(link, (1, 1))

        removed = cleanup_stale_export_files(time.time() - 3600)
        assert removed == 0
        assert link.is_symlink()
        assert outside.read_text(encoding="utf-8") == "precious"

    def test_no_dir_is_safe(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("XDG_RUNTIME_DIR", raising=False)
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "empty"))
        # get_exports_dir creates it, so removing it afterwards must not raise
        exports = get_exports_dir()
        exports.rmdir()
        assert cleanup_stale_export_files(time.time()) == 0
