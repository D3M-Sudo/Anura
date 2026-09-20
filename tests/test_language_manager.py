# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")


import hashlib
import os
from unittest.mock import MagicMock, patch

from anura.models.download_state import DownloadState
from anura.models.tessdata_checksum import TessdataChecksum
from anura.services.language_manager import LanguageManager


class TestLanguageManagerEnterprise:
    """
    Enterprise-grade unit tests for LanguageManager.
    """

    @pytest.fixture
    def manager(self, tmp_path):
        # Patch TESSDATA_DIR to a temporary directory for each test
        with (
            patch("anura.config.TESSDATA_DIR", str(tmp_path)),
            patch("anura.config.TESSDATA_SYSTEM_DIR", str(tmp_path / "system")),
            patch("anura.services.language_manager.TESSDATA_DIR", str(tmp_path), create=True),
            patch("anura.services.language_manager.TESSDATA_SYSTEM_DIR", str(tmp_path / "system"), create=True),
            patch("anura.services.language.cache_manager.TESSDATA_DIR", str(tmp_path), create=True),
            patch("anura.services.language.cache_manager.TESSDATA_SYSTEM_DIR", str(tmp_path / "system"), create=True),
            patch("anura.services.language.download_manager.TESSDATA_DIR", str(tmp_path), create=True),
        ):
            os.makedirs(tmp_path / "system", exist_ok=True)
            yield LanguageManager()

    def test_get_language_happy_path(self, manager):
        """Test human-readable name lookup."""
        assert manager.get_language("eng") == "English"
        assert manager.get_language("ita") == "Italian"
        assert manager.get_language("non-existent") == "non-existent"

    def test_get_language_item(self, manager):
        """Test LanguageItem generation."""
        item = manager.get_language_item("eng")
        assert item.code == "eng"
        assert item.title == "English"

        assert manager.get_language_item("invalid") is None

    def test_get_downloaded_codes_caching(self, manager, tmp_path):
        """Test that downloaded codes are cached and updated correctly."""
        # Initial state: empty
        assert manager.get_downloaded_codes() == []

        # Add a file manually
        (tmp_path / "eng.traineddata").touch()

        # Should still be empty if cache not reset
        assert manager.get_downloaded_codes() == []

        # Force update
        assert manager.get_downloaded_codes(force=True) == ["eng"]

        # Add another file
        (tmp_path / "system" / "ita.traineddata").touch()
        assert manager.get_downloaded_codes(force=True) == ["eng", "ita"]

    def test_remove_language_happy_path(self, manager, tmp_path):
        """Test successful language removal."""
        lang_file = tmp_path / "ita.traineddata"
        lang_file.touch()
        assert lang_file.exists()

        manager.remove_language("ita")
        assert not lang_file.exists()
        assert manager._cache_manager._need_update_cache is True

    @pytest.mark.parametrize(
        "invalid_code",
        [
            "../../../etc/passwd",
            "eng; rm -rf /",
            "eng`whoami`",
            "",
            None,
        ],
    )
    def test_remove_language_security(self, manager, invalid_code):
        """Test that remove_language rejects dangerous codes (path traversal, injection)."""
        with patch("os.remove") as mock_remove:
            manager.remove_language(invalid_code)
            mock_remove.assert_not_called()

    def test_init_tessdata_cleanup(self, manager, tmp_path):
        """Test that init_tessdata cleans up orphaned .tmp files."""
        import time

        orphan = tmp_path / "eng.traineddata.tmp"
        orphan.touch()

        # Set mtime to 2 hours ago to trigger age-based cleanup
        old_time = time.time() - 7200
        os.utime(orphan, (old_time, old_time))

        with patch("shutil.which", return_value="/usr/bin/tesseract"):
            manager.init_tessdata()
            assert not orphan.exists()

    @patch("requests.Session.get")
    def test_download_begin_success(self, mock_get, manager, tmp_path):
        """Test successful download path.

        The download manager verifies both the announced Content-Length and
        the streamed git-blob SHA-1 against the pinned manifest before
        installing (NEW-F1/F2, fail-closed). The mock body cannot match the
        real pinned ``fra.traineddata`` identity (14 MB upstream), so this
        test derives a synthetic pinned checksum from the mock body itself —
        exercising the full verification pipeline with a self-consistent
        identity. Real-manifest correctness is covered by
        tests/test_tessdata_checksums.py.
        """
        body = b"anura-test-model\n" * 8
        blob_sha1 = hashlib.sha1(b"blob %d\x00" % len(body) + body).hexdigest()
        synthetic = TessdataChecksum(filename="fra.traineddata", size=len(body), sha1=blob_sha1)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-length": str(len(body))}
        mock_response.iter_content.return_value = [body]
        mock_get.return_value = mock_response

        with (
            patch("shutil.which", return_value="/usr/bin/tesseract"),
            patch(
                "anura.services.language.download_manager.get_expected_checksum",
                return_value=synthetic,
            ),
        ):
            result = manager._download_manager.download_begin("fra")
            assert result == "fra"
            assert (tmp_path / "fra.traineddata").exists()

    @patch("requests.Session.get")
    def test_download_begin_failure(self, mock_get, manager):
        """Test download failure handling."""
        import requests

        mock_get.side_effect = requests.RequestException("Connection refused")

        with patch("shutil.which", return_value="/usr/bin/tesseract"):
            result = manager._download_manager.download_begin("fra")
            assert result is None

    def test_download_duplicate_prevention(self, manager):
        """Test that multiple downloads for the same code are ignored."""
        manager.loading_languages["eng"] = DownloadState()
        with patch("anura.core.atomic_task_manager.get_atomic_manager") as mock_get_manager:
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            manager.download("eng")
            mock_manager.execute.assert_not_called()

    def test_invalidate_cache_resets_need_update(self, manager):
        """Test that invalidate_cache() marks the cache as needing a rescan."""
        # Prime the cache with a scan so the flag is cleared.
        assert manager.get_downloaded_codes() == []
        assert manager._cache_manager._need_update_cache is False

        manager.invalidate_cache()

        assert manager._cache_manager._need_update_cache is True

    def test_invalidate_cache_public_method(self, manager):
        """Test that invalidate_cache() is accessible via LanguageManager and works."""
        # After invalidation, get_downloaded_codes() should rescan
        assert manager.get_downloaded_codes() == []

    def test_get_downloaded_codes_reflects_invalidation(self, manager, tmp_path):
        """Test that invalidating the cache forces a fresh scan of language models.

        Regression test for Bug #2: languages 'disappeared' when changing model quality
        because CacheManager's cache was never invalidated when switching quality.
        """
        # Initial state: empty cache, no files
        assert manager.get_downloaded_codes() == []

        # Add a language file
        (tmp_path / "eng.traineddata").touch()

        # Without invalidation, cache is stale — still empty
        assert manager.get_downloaded_codes() == []

        # After invalidate_cache(), the next call rescans and finds the file
        manager.invalidate_cache()
        assert manager.get_downloaded_codes() == ["eng"]

        # Adding another file: cache is again stale
        (tmp_path / "system" / "ita.traineddata").touch()
        assert manager.get_downloaded_codes() == ["eng"]

        # Invalidate again to rescan — now both files are found
        manager.invalidate_cache()
        assert manager.get_downloaded_codes() == ["eng", "ita"]

    def test_downloaded_codes_follow_selected_quality(self, manager, tmp_path):
        """The installed list must reflect the *currently selected* model quality.

        Regression test for VM bug #2: switching the quality selector wrote the
        new ``tessdata-model`` setting but never invalidated CacheManager, so the
        list kept showing the scan from the previous quality. Files for different
        qualities coexist on disk (base dir = fast, tessdata/ = standard,
        tessdata_best/ = best), so the cache must be rescanned on every switch.
        """
        # fast (base dir) holds French; best (tessdata_best/) holds English.
        (tmp_path / "fra.traineddata").touch()
        (tmp_path / "tessdata_best").mkdir()
        (tmp_path / "tessdata_best" / "eng.traineddata").touch()

        with patch("anura.services.language.cache_manager.settings") as mock_settings:
            mock_settings.get_string.return_value = "fast"
            manager.invalidate_cache()
            assert manager.get_downloaded_codes() == ["fra"]

            # Simulate _on_model_quality_changed(): new quality + cache invalidation.
            mock_settings.get_string.return_value = "best"
            manager.invalidate_cache()
            assert manager.get_downloaded_codes() == ["eng"]
