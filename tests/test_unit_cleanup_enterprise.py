# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")


# tests/test_unit_cleanup_enterprise.py
import os
import time
from unittest.mock import patch

from anura.utils.cleanup import cleanup_orphaned_resources, get_cache_info


class TestCleanupEnterprise:
    """
    Enterprise-grade unit tests for cleanup utilities.
    """

    @pytest.fixture
    def mock_dirs(self, tmp_path):
        tts_dir = tmp_path / "cache" / "anura"
        tessdata_dir = tmp_path / "tessdata"
        tts_dir.mkdir(parents=True)
        tessdata_dir.mkdir()

        with (
            patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path / "cache")}),
            patch("anura.utils.cleanup.TESSDATA_DIR", str(tessdata_dir)),
        ):
            yield tts_dir, tessdata_dir

    def test_cleanup_orphaned_resources_happy_path(self, mock_dirs):
        """Test that old files are removed and new ones are kept."""
        tts_dir, tessdata_dir = mock_dirs

        # Create files
        old_time = time.time() - 7200  # 2 hours ago
        new_time = time.time() - 600  # 10 mins ago

        old_mp3 = tts_dir / "old.mp3"
        new_mp3 = tts_dir / "new.mp3"
        old_tmp = tessdata_dir / "old.tmp"
        new_tmp = tessdata_dir / "new.tmp"

        for f in [old_mp3, new_mp3, old_tmp, new_tmp]:
            f.touch()

        os.utime(old_mp3, (old_time, old_time))
        os.utime(old_tmp, (old_time, old_time))
        os.utime(new_mp3, (new_time, new_time))
        os.utime(new_tmp, (new_time, new_time))

        cleanup_orphaned_resources()

        assert not old_mp3.exists()
        assert not old_tmp.exists()
        assert new_mp3.exists()
        assert new_tmp.exists()

    def test_cleanup_handles_missing_dir(self, tmp_path):
        """Test cleanup doesn't crash when directories don't exist."""
        with (
            patch.dict(os.environ, {"XDG_CACHE_HOME": str(tmp_path / "nonexistent")}),
            patch("anura.utils.cleanup.TESSDATA_DIR", str(tmp_path / "nonexistent_tess")),
        ):
            cleanup_orphaned_resources()  # Should not raise

    def test_get_cache_info(self, mock_dirs):
        """Test cache info gathering."""
        tts_dir, tessdata_dir = mock_dirs

        (tts_dir / "test1.mp3").write_bytes(b"data")
        (tts_dir / "test2.mp3").write_bytes(b"more data")
        (tessdata_dir / "download.tmp").touch()

        info = get_cache_info()
        assert info["tts_files"] == 2
        assert info["tts_size_bytes"] == 4 + 9
        assert info["temp_files"] == 1

    def test_cleanup_permission_error(self, mock_dirs):
        """Test that cleanup handles permission errors gracefully."""
        tts_dir, _ = mock_dirs
        old_mp3 = tts_dir / "restricted.mp3"
        old_mp3.touch()
        old_time = time.time() - 7200
        os.utime(old_mp3, (old_time, old_time))

        with patch("os.remove", side_effect=PermissionError("Denied")), patch("loguru.logger.warning") as mock_log:
            cleanup_orphaned_resources()
            mock_log.assert_called()
            assert old_mp3.exists()
