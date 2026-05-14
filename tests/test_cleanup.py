# tests/test_cleanup.py
#
# Unit tests for anura/utils/cleanup.py
# No GTK/GLib required — pure Python only.

import os
import tempfile
import time
from unittest.mock import patch

from anura.utils.cleanup import (
    _cleanup_tessdata_temp_files,
    _cleanup_tts_cache,
    cleanup_orphaned_resources,
    get_cache_info,
)


class TestCleanupOrphanedResources:
    """Test cleanup_orphaned_resources function."""

    def test_cleanup_old_files_removed(self):
        """Test that old files (>1 hour) are removed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create old TTS cache directory and files
            tts_cache_dir = os.path.join(temp_dir, "anura")
            os.makedirs(tts_cache_dir)

            # Create old MP3 file (2 hours ago)
            old_mp3 = os.path.join(tts_cache_dir, "old.mp3")
            with open(old_mp3, "w") as f:
                f.write("fake mp3 content")
            # Set modification time to 2 hours ago
            old_time = time.time() - 7200  # 2 hours
            os.utime(old_mp3, (old_time, old_time))

            # Create old temp file in tessdata
            tessdata_dir = os.path.join(temp_dir, "tessdata")
            os.makedirs(tessdata_dir)

            old_tmp = os.path.join(tessdata_dir, "old.tmp")
            with open(old_tmp, "w") as f:
                f.write("temp content")
            os.utime(old_tmp, (old_time, old_time))

            # Mock environment variables and config
            with (
                patch.dict(os.environ, {"XDG_CACHE_HOME": temp_dir}),
                patch("anura.utils.cleanup.TESSDATA_DIR", tessdata_dir),
            ):
                cleanup_orphaned_resources()

                # Files should be removed
                assert not os.path.exists(old_mp3)
                assert not os.path.exists(old_tmp)

    def test_cleanup_recent_files_preserved(self):
        """Test that recent files (<1 hour) are NOT removed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create TTS cache directory and recent files
            tts_cache_dir = os.path.join(temp_dir, "anura")
            os.makedirs(tts_cache_dir)

            # Create recent MP3 file (10 minutes ago)
            recent_mp3 = os.path.join(tts_cache_dir, "recent.mp3")
            with open(recent_mp3, "w") as f:
                f.write("fake mp3 content")
            # Set modification time to 10 minutes ago
            recent_time = time.time() - 600  # 10 minutes
            os.utime(recent_mp3, (recent_time, recent_time))

            # Create recent temp file in tessdata
            tessdata_dir = os.path.join(temp_dir, "tessdata")
            os.makedirs(tessdata_dir)

            recent_tmp = os.path.join(tessdata_dir, "recent.tmp")
            with open(recent_tmp, "w") as f:
                f.write("temp content")
            os.utime(recent_tmp, (recent_time, recent_time))

            # Mock environment variables and config
            with (
                patch.dict(os.environ, {"XDG_CACHE_HOME": temp_dir}),
                patch("anura.utils.cleanup.TESSDATA_DIR", tessdata_dir),
            ):
                cleanup_orphaned_resources()

                # Files should be preserved
                assert os.path.exists(recent_mp3)
                assert os.path.exists(recent_tmp)

    def test_cleanup_missing_directories_no_crash(self):
        """Test that missing directories don't cause crashes."""
        with (
            patch.dict(os.environ, {"XDG_CACHE_HOME": "/nonexistent/cache"}),
            patch("anura.utils.cleanup.TESSDATA_DIR", "/nonexistent/tessdata"),
        ):
            # Should not raise any exceptions
            cleanup_orphaned_resources()

    def test_cleanup_ignores_non_target_files(self):
        """Test that files with wrong extensions are ignored."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create directories
            tts_cache_dir = os.path.join(temp_dir, "anura")
            os.makedirs(tts_cache_dir)
            tessdata_dir = os.path.join(temp_dir, "tessdata")
            os.makedirs(tessdata_dir)

            # Create files with wrong extensions (old)
            old_time = time.time() - 7200  # 2 hours

            wrong_tts = os.path.join(tts_cache_dir, "old.txt")
            with open(wrong_tts, "w") as f:
                f.write("text file")
            os.utime(wrong_tts, (old_time, old_time))

            wrong_tess = os.path.join(tessdata_dir, "old.log")
            with open(wrong_tess, "w") as f:
                f.write("log file")
            os.utime(wrong_tess, (old_time, old_time))

            # Mock environment variables and config
            with (
                patch.dict(os.environ, {"XDG_CACHE_HOME": temp_dir}),
                patch("anura.utils.cleanup.TESSDATA_DIR", tessdata_dir),
            ):
                cleanup_orphaned_resources()

                # Wrong extension files should be preserved
                assert os.path.exists(wrong_tts)
                assert os.path.exists(wrong_tess)

    def test_cleanup_handles_permission_errors(self):
        """Test that permission errors are handled gracefully."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tts_cache_dir = os.path.join(temp_dir, "anura")
            os.makedirs(tts_cache_dir)

            # Create a file
            test_file = os.path.join(tts_cache_dir, "test.mp3")
            with open(test_file, "w") as f:
                f.write("content")

            old_time = time.time() - 7200
            os.utime(test_file, (old_time, old_time))

            # Mock os.remove to raise PermissionError
            with (
                patch.dict(os.environ, {"XDG_CACHE_HOME": temp_dir}),
                patch("anura.utils.cleanup.TESSDATA_DIR", "/tmp"),
                patch("os.remove", side_effect=PermissionError("Permission denied")),
            ):
                # Should not raise exception
                cleanup_orphaned_resources()


class TestTTSCacheCleanup:
    """Test _cleanup_tts_cache function specifically."""

    def test_tts_cache_cleanup_counting(self):
        """Test that TTS cache cleanup counts removed files correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tts_cache_dir = os.path.join(temp_dir, "anura")
            os.makedirs(tts_cache_dir)

            # Create multiple old files
            old_time = time.time() - 7200
            for i in range(3):
                old_file = os.path.join(tts_cache_dir, f"old{i}.mp3")
                with open(old_file, "w") as f:
                    f.write(f"content {i}")
                os.utime(old_file, (old_time, old_time))

            with (
                patch.dict(os.environ, {"XDG_CACHE_HOME": temp_dir}),
                patch("anura.utils.cleanup.logger") as mock_logger,
            ):
                _cleanup_tts_cache(time.time() - 3600)  # 1 hour ago
                mock_logger.info.assert_called_once_with("Anura Cleanup: Removed 3 old TTS cache files")


class TestTessdataCleanup:
    """Test _cleanup_tessdata_temp_files function specifically."""

    def test_tessdata_cleanup_counting(self):
        """Test that tessdata cleanup counts removed files correctly."""
        with tempfile.TemporaryDirectory() as tessdata_dir:
            # Create multiple old temp files
            old_time = time.time() - 7200
            for i in range(2):
                old_file = os.path.join(tessdata_dir, f"old{i}.tmp")
                with open(old_file, "w") as f:
                    f.write(f"temp content {i}")
                os.utime(old_file, (old_time, old_time))

            with (
                patch("anura.utils.cleanup.TESSDATA_DIR", tessdata_dir),
                patch("anura.utils.cleanup.logger") as mock_logger,
            ):
                _cleanup_tessdata_temp_files(time.time() - 3600)  # 1 hour ago
                mock_logger.info.assert_called_once_with("Anura Cleanup: Removed 2 orphaned temporary files")


class TestGetCacheInfo:
    """Test get_cache_info function."""

    def test_get_cache_info_with_files(self):
        """Test get_cache_info returns correct counts and sizes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tts_cache_dir = os.path.join(temp_dir, "anura")
            os.makedirs(tts_cache_dir)
            tessdata_dir = os.path.join(temp_dir, "tessdata")
            os.makedirs(tessdata_dir)

            # Create test files
            mp3_file = os.path.join(tts_cache_dir, "test.mp3")
            with open(mp3_file, "w") as f:
                f.write("x" * 100)  # 100 bytes

            tmp_file = os.path.join(tessdata_dir, "test.tmp")
            with open(tmp_file, "w") as f:
                f.write("temp")

            # Create a file that should be ignored
            with open(os.path.join(tts_cache_dir, "ignore.txt"), "w") as f:
                f.write("ignore")

            with (
                patch.dict(os.environ, {"XDG_CACHE_HOME": temp_dir}),
                patch("anura.utils.cleanup.TESSDATA_DIR", tessdata_dir),
            ):
                info = get_cache_info()
                assert info["tts_files"] == 1
                assert info["tts_size_bytes"] == 100
                assert info["temp_files"] == 1

    def test_get_cache_info_missing_directories(self):
        """Test get_cache_info handles missing directories gracefully."""
        with (
            patch.dict(os.environ, {"XDG_CACHE_HOME": "/nonexistent/cache"}),
            patch("anura.utils.cleanup.TESSDATA_DIR", "/nonexistent/tessdata"),
        ):
            info = get_cache_info()
            assert info == {"tts_files": 0, "tts_size_bytes": 0, "temp_files": 0}

    def test_get_cache_info_handles_errors(self):
        """Test get_cache_info handles os errors gracefully."""
        with patch("os.listdir", side_effect=OSError("Permission denied")):
            info = get_cache_info()
            assert info == {"tts_files": 0, "tts_size_bytes": 0, "temp_files": 0}
