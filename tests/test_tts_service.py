# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest
import sys
from unittest.mock import MagicMock, patch

pytest.importorskip("gi")

# Mock Gst before imports
sys.modules['gi.repository.Gst'] = MagicMock()

from anura.services.tts import TTSService


class TestTTSServiceEnterprise:
    """
    Enterprise-grade unit tests for TTSService.
    """

    @pytest.fixture
    def service(self):
        with patch("gi.repository.Gst.init"):
            return TTSService()

    def test_map_tesseract_to_gtts_happy_path(self):
        """Test mapping of Tesseract codes to gTTS codes."""
        assert TTSService.map_tesseract_to_gtts("eng") == "en"
        assert TTSService.map_tesseract_to_gtts("ita") == "it"
        assert TTSService.map_tesseract_to_gtts("jpn_vert") == "ja"
        assert TTSService.map_tesseract_to_gtts("chi_sim") == "zh-CN"

    def test_map_tesseract_to_gtts_fallbacks(self):
        """Test fallback behavior for unknown or invalid codes."""
        assert TTSService.map_tesseract_to_gtts(None) == "en"
        # Unknown codes now return None (no fallback to "en")
        assert TTSService.map_tesseract_to_gtts("unknown") is None

        # Test 2-char prefix matching
        with patch.object(TTSService, "get_supported_gtts_languages", return_value={"fr": "French"}):
            assert TTSService.map_tesseract_to_gtts("fra-new") == "fr"

    def test_generate_empty_text(self, service):
        """Test generate with empty or whitespace text."""
        assert service.generate("") == ""
        assert service.generate("   ") == ""
        assert service.generate(None) == ""

    @patch("gtts.gTTS")
    @patch("os.makedirs")
    def test_generate_save_error(self, mock_makedirs, mock_gtts, service):
        """Test error handling during speech file generation."""
        mock_tts_instance = mock_gtts.return_value
        mock_tts_instance.save.side_effect = OSError("Disk full")

        with patch("loguru.logger.error") as mock_log:
            result = service.generate("hello", "en")
            assert result == ""
            mock_log.assert_called()

    def test_get_effective_language(self, service):
        """Test determination of the effective TTS language."""
        # Case 1: User has set a specific TTS language
        with patch("anura.services.tts.settings.get_string", return_value="de"):
            assert service.get_effective_language("eng") == "de"

        # Case 2: No user preference, fallback to OCR mapping
        with patch("anura.services.tts.settings.get_string", return_value=""):
            assert service.get_effective_language("ita") == "it"

    def test_is_playing_states(self, service):
        """Test is_playing reporting based on GStreamer state."""
        assert service.is_playing() is False

        service.player = MagicMock()
        from gi.repository import Gst

        # Mock State.PLAYING
        service.player.get_state.return_value = (None, Gst.State.PLAYING, None)
        assert service.is_playing() is True

        # Mock State.NULL
        service.player.get_state.return_value = (None, Gst.State.NULL, None)
        assert service.is_playing() is False

    def test_stop_speaking_cleanup(self, service):
        """Test that stop_speaking cleans up resources and files."""
        service.player = MagicMock()
        service._current_speech_file = "/tmp/test.mp3"

        with patch("pathlib.Path.exists", return_value=True):
            service.stop_speaking()
            assert service.player is None
            assert service._current_speech_file is None

    def test_referential_transparency_mapping(self):
        """Test that language mapping is pure."""
        code = "eng"
        assert TTSService.map_tesseract_to_gtts(code) == TTSService.map_tesseract_to_gtts(code)
