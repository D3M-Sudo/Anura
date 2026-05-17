import os
import pytest
from unittest.mock import patch, MagicMock
from anura.language_manager import LanguageManager
from anura.types.language_item import LanguageItem
import requests

class TestAuditLanguageManager:
    @pytest.fixture
    def manager(self):
        with patch('gi.repository.GLib.idle_add'):
            return LanguageManager()

    def test_init_tessdata(self, manager, tmp_path):
        tessdata_dir = tmp_path / "tessdata"
        with patch('anura.language_manager.TESSDATA_DIR', str(tessdata_dir)):
            manager.init_tessdata()
            assert tessdata_dir.exists()

            tmp_file = tessdata_dir / "test.tmp"
            tmp_file.write_text("temp")
            manager.init_tessdata()
            assert not tmp_file.exists()

    def test_get_downloaded_codes(self, manager, tmp_path):
        user_dir = tmp_path / "user"
        system_dir = tmp_path / "system"
        user_dir.mkdir()
        system_dir.mkdir()

        (user_dir / "eng.traineddata").write_text("eng")
        (system_dir / "ita.traineddata").write_text("ita")
        (user_dir / "osd.traineddata").write_text("osd")

        with patch('anura.language_manager.TESSDATA_DIR', str(user_dir)), \
             patch('anura.language_manager.TESSDATA_SYSTEM_DIR', str(system_dir)):
            codes = manager.get_downloaded_codes(force=True)
            assert "eng" in codes
            assert "ita" in codes
            assert "osd" not in codes

    def test_remove_language_security(self, manager, tmp_path):
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()

        target_file = tessdata_dir / "eng.traineddata"
        target_file.write_text("data")

        outside_file = tmp_path / "secret.txt"
        outside_file.write_text("secret")

        with patch('anura.language_manager.TESSDATA_DIR', str(tessdata_dir)):
            manager.remove_language("eng")
            assert not target_file.exists()

            manager.remove_language("../secret.txt")
            assert outside_file.exists()

    @patch('requests.get')
    @patch('shutil.which')
    def test_download_begin_failures(self, mock_which, mock_get, manager, tmp_path):
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()

        with patch('anura.language_manager.TESSDATA_DIR', str(tessdata_dir)):
            mock_which.return_value = None
            assert manager.download_begin("eng") is None

            mock_which.return_value = "/usr/bin/tesseract"
            mock_get.side_effect = requests.RequestException("Network down")
            assert manager.download_begin("eng") is None
