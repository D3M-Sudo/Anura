# tests/test_unit_language_manager_enterprise.py
import pytest
import os
import shutil
from unittest.mock import MagicMock, patch
from anura.services.settings import settings
from anura.language_manager import LanguageManager
from anura.types.download_state import DownloadState

class TestLanguageManagerEnterprise:
    """
    Enterprise-grade unit tests for LanguageManager.
    """

    @pytest.fixture
    def manager(self, tmp_path):
        # Patch TESSDATA_DIR to a temporary directory for each test
        with patch('anura.language_manager.TESSDATA_DIR', str(tmp_path)), \
             patch('anura.language_manager.TESSDATA_SYSTEM_DIR', str(tmp_path / "system")):
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
        assert manager._need_update_cache is True

    @pytest.mark.parametrize("invalid_code", [
        "../../../etc/passwd",
        "eng; rm -rf /",
        "eng`whoami`",
        "",
        None,
    ])
    def test_remove_language_security(self, manager, invalid_code):
        """Test that remove_language rejects dangerous codes (path traversal, injection)."""
        with patch('os.remove') as mock_remove:
            manager.remove_language(invalid_code)
            mock_remove.assert_not_called()

    def test_init_tessdata_cleanup(self, manager, tmp_path):
        """Test that init_tessdata cleans up orphaned .tmp files."""
        orphan = tmp_path / "eng.traineddata.tmp"
        orphan.touch()

        with patch('shutil.which', return_value="/usr/bin/tesseract"):
            manager.init_tessdata()
            assert not orphan.exists()

    @patch('requests.get')
    def test_download_begin_success(self, mock_get, manager, tmp_path):
        """Test successful download path."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {'content-length': '100'}
        mock_response.iter_content.return_value = [b"data"]
        mock_get.return_value = mock_response

        with patch('shutil.which', return_value="/usr/bin/tesseract"):
            result = manager.download_begin("fra")
            assert result == "fra"
            assert (tmp_path / "fra.traineddata").exists()

    @patch('requests.get')
    def test_download_begin_failure(self, mock_get, manager):
        """Test download failure handling."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection refused")

        with patch('shutil.which', return_value="/usr/bin/tesseract"):
            result = manager.download_begin("fra")
            assert result is None

    def test_download_duplicate_prevention(self, manager):
        """Test that multiple downloads for the same code are ignored."""
        manager.loading_languages["eng"] = DownloadState()
        with patch('anura.gobject_worker.GObjectWorker.call') as mock_worker:
            manager.download("eng")
            mock_worker.assert_not_called()
