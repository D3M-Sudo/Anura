# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Startup pool cleanup must not delete assets a live task is using (#521).

The cleanup removed every top-level `.traineddata` that did not match the active
language, and every task directory older than one hour. A concurrent OCR task or
a second Anura instance could therefore lose its models while Tesseract was
reading them.
"""

import os
from pathlib import Path
import time

import pytest

import anura.utils.cleanup as cleanup


@pytest.fixture
def pool(tmp_path, monkeypatch):
    pool_dir = tmp_path / "pool"
    pool_dir.mkdir()
    monkeypatch.setattr(cleanup, "TESSDATA_POOL_DIR", str(pool_dir))
    return pool_dir


def _age(path: Path, seconds: int) -> None:
    old = time.time() - seconds
    os.utime(path, (old, old))


def test_live_owner_directory_is_preserved(pool):
    task = pool / "task-live"
    task.mkdir()
    (task / "owner.pid").write_text(str(os.getpid()), encoding="utf-8")
    _age(task, 7 * 24 * 3600)  # old, but its owner is alive

    cleanup._cleanup_tessdata_pool("eng")

    assert task.exists()


def test_dead_owner_directory_is_removed(pool):
    task = pool / "task-dead"
    task.mkdir()
    (task / "owner.pid").write_text("999999", encoding="utf-8")

    cleanup._cleanup_tessdata_pool("eng")

    assert not task.exists()


def test_legacy_directory_is_kept_until_it_is_a_day_old(pool):
    task = pool / "task-legacy"
    task.mkdir()
    _age(task, 3600)

    cleanup._cleanup_tessdata_pool("eng")

    assert task.exists()


def test_legacy_directory_older_than_a_day_is_removed(pool):
    task = pool / "task-legacy-old"
    task.mkdir()
    _age(task, 25 * 3600)

    cleanup._cleanup_tessdata_pool("eng")

    assert not task.exists()


def test_top_level_models_are_never_deleted(pool):
    for code in ("eng", "ita"):
        (pool / f"{code}.traineddata").write_text("model", encoding="utf-8")
    _age(pool / "ita.traineddata", 30 * 24 * 3600)

    cleanup._cleanup_tessdata_pool("eng")

    assert (pool / "eng.traineddata").exists()
    assert (pool / "ita.traineddata").exists()


def test_malformed_lease_falls_back_to_age(pool):
    task = pool / "task-junk"
    task.mkdir()
    (task / "owner.pid").write_text("not-a-pid", encoding="utf-8")
    _age(task, 25 * 3600)

    cleanup._cleanup_tessdata_pool("eng")

    assert not task.exists()


def test_task_pool_creation_writes_the_lease():
    """The lease is what lets cleanup tell a live task from a leftover."""
    source = Path("anura/services/language_manager.py").read_text(encoding="utf-8")

    assert "TESSDATA_POOL_LEASE" in source
    assert "os.getpid()" in source
