# tests/test_reliability_chaos.py
from unittest.mock import patch

import pytest
import requests

pytest.importorskip("gi")

from anura.services.tts import TTSService


class TestReliabilityChaos:
    @pytest.mark.gtk
    def test_ocr_missing_binary(self, monkeypatch):
        # Simulate tesseract missing from PATH
        monkeypatch.setenv("PATH", "")

        # This shouldn't crash the app, but should log/emit error
        # We check the behavior of _configure_tesseract_path indirectly
        from anura.services.screenshot_service import _configure_tesseract_path

        with patch("shutil.which", return_value=None):
            _configure_tesseract_path()
            # Should have logged error

    @pytest.mark.gtk
    def test_tts_network_failure(self):
        service = TTSService()
        # Simulate network error during gTTS generation
        with patch("gtts.gTTS.save", side_effect=requests.RequestException("Connection timed out")):
            result = service.generate("Some text", lang="en")
            assert result == ""  # Should handle gracefully and return empty path

    @pytest.mark.gtk
    def test_idempotency_share_service(self):
        from anura.services.share_service import ShareService

        service = ShareService()
        # Sharing same text multiple times should not cause issues
        with patch.object(service.launcher, "launch") as mock_launch:
            service.share("email", "Test text")
            service.share("email", "Test text")
            assert mock_launch.call_count == 2

    def test_gsettings_missing_schema(self, monkeypatch):
        # Simulate missing GSettings schema
        monkeypatch.setenv("GSETTINGS_SCHEMA_DIR", "/tmp/nonexistent")
        # Need to patch Gio.SettingsSchemaSource.get_default to return something that returns None on lookup
        with patch("gi.repository.Gio.SettingsSchemaSource.get_default") as mock_get:
            mock_get.return_value.lookup.return_value = None
            from anura.services.settings import Settings

            with pytest.raises(RuntimeError, match=r"GSettings schema .* not found"):
                Settings()
