# tests/test_reliability_enterprise.py
import pytest
from unittest.mock import MagicMock, patch
import os
import requests
from anura.services.tts import TTSService
from anura.language_manager import LanguageManager

class TestReliabilityEnterprise:
    """
    Enterprise-grade reliability and chaos tests.
    """

    @pytest.fixture
    def tts_service(self):
        with patch('gi.repository.Gst.init'):
            return TTSService()

    @pytest.fixture
    def lang_manager(self, tmp_path):
        with patch('anura.language_manager.TESSDATA_DIR', str(tmp_path)):
            return LanguageManager()

    def test_tts_network_outage(self, tts_service):
        """Test TTSService behavior when gTTS/network is unreachable."""
        with patch('gtts.gTTS.save', side_effect=requests.RequestException("Connection timeout")), \
             patch('loguru.logger.error') as mock_log:

            result = tts_service.generate("Hello", "en")

            assert result == ""
            mock_log.assert_called()
            # Verify no partial file left behind
            assert not any(f.endswith(".mp3") for f in os.listdir(tts_service._speech_dir))

    def test_ocr_missing_binary(self):
        """Test ScreenshotService behavior when tesseract binary is missing."""
        from anura.services.screenshot_service import ScreenshotService

        # Patch shutil.which to return None for tesseract
        with patch('shutil.which', return_value=None), \
             patch('loguru.logger.error') as mock_log:

            service = ScreenshotService()
            # _validate_decode_inputs doesn't check binary, it checks lang code
            # But _configure_tesseract_path (called in __init__) logs the error.
            args, _ = mock_log.call_args
            assert "Tesseract binary" in args[0]

    def test_language_manager_corrupted_download(self, lang_manager, tmp_path):
        """Test recovery when a download is interrupted/corrupted."""
        # The LanguageManager init_tessdata uses TESSDATA_DIR constant.
        # We need to ensure the test's lang_manager uses the tmp_path.
        import anura.language_manager as lm_mod
        with patch.object(lm_mod, 'TESSDATA_DIR', str(tmp_path)):
            # Create a partial/corrupted file
            corrupted = tmp_path / "fra.traineddata.tmp"
            corrupted.touch()

            with patch('shutil.which', return_value="/usr/bin/tesseract"), \
                 patch('os.access', return_value=True):
                # init_tessdata should clean up .tmp files
                lang_manager.init_tessdata()
                assert not corrupted.exists()

    def test_gsettings_schema_missing(self):
        """Test application behavior when GSettings schema is not installed."""
        from anura.services.settings import Settings

        with patch('gi.repository.Gio.SettingsSchemaSource.get_default') as mock_get:
            mock_source = MagicMock()
            mock_source.lookup.return_value = None
            mock_get.return_value = mock_source

            with pytest.raises(RuntimeError, match="GSettings schema .* not found"):
                Settings()
