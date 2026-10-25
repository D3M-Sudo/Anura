# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Filesystem-permission tests for persisted OCR history (#527).

The history file stores extracted text, so it must not be readable by other
local accounts: the directory is 0700 and the JSON file 0600, regardless of the
process umask or of the modes an older version left behind.
"""

import os
import stat

import pytest

from anura.services.history_service import HistoryService

pytestmark = pytest.mark.skipif(os.name != "posix", reason="POSIX permission semantics")


def _mode(path) -> int:
    return stat.S_IMODE(path.stat().st_mode)


def test_history_dir_and_file_are_private_under_permissive_umask(tmp_path):
    previous_umask = os.umask(0o022)
    try:
        service = HistoryService(base_dir=tmp_path / "history")
        service.record("confidential text", "eng")
    finally:
        os.umask(previous_umask)

    assert _mode(tmp_path / "history") == 0o700
    assert _mode(tmp_path / "history" / "history.json") == 0o600


def test_existing_permissive_directory_is_tightened(tmp_path):
    base = tmp_path / "history"
    base.mkdir(parents=True)
    os.chmod(base, 0o755)

    service = HistoryService(base_dir=base)
    service.record("confidential text", "eng")

    assert _mode(base) == 0o700
    assert _mode(base / "history.json") == 0o600


def test_permissions_are_preserved_across_rewrites(tmp_path):
    base = tmp_path / "history"
    service = HistoryService(base_dir=base)
    service.record("first", "eng")
    service.record("second", "ita")
    service.clear()

    assert _mode(base) == 0o700
    assert _mode(base / "history.json") == 0o600
