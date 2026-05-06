# test_tts_service.py
#
# Unit tests for TTSService
# Tests language mapping, audio generation, and GStreamer integration

import pytest
from unittest.mock import Mock, patch

from anura.services.tts import TTSService
# Import Gst for message types
try:
    from gi.repository import Gst
except ImportError:
    Gst = Mock()
    Gst.MessageType = Mock()
    Gst.MessageType.ERROR = "error"
    Gst.MessageType.EOS = "eos"
    Gst.MessageType.TAG = "tag"


@pytest.mark.gtk
class TestTTSService:
    """Test suite for TTSService core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = TTSService()
        # Mock player to avoid GStreamer dependency
        self.service.player = Mock()

    def test_init(self):
        """Test service initialization."""
        assert self.service.player is not None
        assert hasattr(self.service, "_tld")
        assert self.service._tld == "com"

    def test_get_effective_language_english(self):
        """Test language mapping for English."""
        result = self.service.get_effective_language("eng")
        assert result == "en"

    def test_get_effective_language_italian(self):
        """Test language mapping for Italian."""
        result = self.service.get_effective_language("ita")
        assert result == "it"

    def test_get_effective_language_spanish(self):
        """Test language mapping for Spanish."""
        result = self.service.get_effective_language("spa")
        assert result == "es"

    def test_get_effective_language_french(self):
        """Test language mapping for French."""
        result = self.service.get_effective_language("fra")
        assert result == "fr"

    def test_get_effective_language_german(self):
        """Test language mapping for German."""
        result = self.service.get_effective_language("deu")
        assert result == "de"

    def test_get_effective_language_unknown(self):
        """Test language mapping for unknown language."""
        result = self.service.get_effective_language("xyz")
        assert result == "en"  # Should default to English

    def test_get_effective_language_multilingual(self):
        """Test language mapping for multilingual OCR codes."""
        result = self.service.get_effective_language("eng+ita")
        assert result == "en"  # Should use first language

    def test_get_effective_language_empty(self):
        """Test language mapping for empty input."""
        result = self.service.get_effective_language("")
        assert result == "en"  # Should default to English

    def test_get_effective_language_none(self):
        """Test language mapping for None input."""
        result = self.service.get_effective_language(None)
        assert result == "en"  # Should default to English

    @patch("anura.services.tts.gtts")
    def test_speak_text_cache_hit(self, mock_gtts):
        """Test speaking text when cached file exists."""
        # This test concept doesn't apply to current API - generate() always creates new files
        # Test generate() method instead
        with patch("anura.services.tts.gtts.gTTS") as mock_gtts:
            mock_tts = Mock()
            mock_tts.save.return_value = None
            mock_gtts.return_value = mock_tts

            result = self.service.generate("test text", "en")

            assert result.endswith(".mp3")
            mock_gtts.assert_called_once_with("test text", lang="en", tld="com")

    @patch("anura.services.tts.gtts")
    def test_generate_cache_miss(self, mock_gtts):
        """Test speaking text generation."""
        with patch("anura.services.tts.gtts.gTTS") as mock_gtts:
            mock_tts = Mock()
            mock_tts.save.return_value = None
            mock_gtts.return_value = mock_tts

            result = self.service.generate("test text", "en")

            assert result.endswith(".mp3")
            mock_gtts.assert_called_once_with("test text", lang="en", tld="com")

    @patch("anura.services.tts.gtts")
    def test_generate_gtts_error(self, mock_gtts):
        """Test handling of gTTS generation errors."""
        with patch("anura.services.tts.gtts.gTTS") as mock_gtts:
            mock_gtts.side_effect = Exception("TTS error")

            # generate() should raise the exception
            with pytest.raises(Exception, match="TTS error"):
                self.service.generate("test text", "en")

    @patch("anura.services.tts.gtts")
    def test_generate_save_error(self, mock_gtts):
        """Test handling of file save errors."""
        with patch("anura.services.tts.gtts.gTTS") as mock_gtts:
            mock_tts = Mock()
            mock_tts.save.side_effect = OSError("Save error")
            mock_gtts.return_value = mock_tts

            # generate() should raise the exception
            with pytest.raises(Exception, match="Save error"):
                self.service.generate("test text", "en")

    def test_generate_empty_text(self):
        """Test speaking empty text."""
        result = self.service.generate("", "en")
        assert result == ""

    def test_generate_none_text(self):
        """Test speaking None text."""
        result = self.service.generate(None, "en")
        assert result == ""

    @patch("anura.services.tts.Gst")
    def test_play_audio_success(self, mock_gst):
        """Test successful audio playback."""
        # Mock GStreamer elements
        mock_playbin = Mock()
        mock_gst.ElementFactory.make.return_value = mock_playbin
        mock_bus = Mock()
        mock_playbin.get_bus.return_value = mock_bus

        # Test play() method
        with patch("anura.services.tts.GLib"):
            self.service.play("/test/audio.mp3")

            mock_gst.ElementFactory.make.assert_called_once_with("playbin3", "player")
            mock_playbin.set_property.assert_any_call("uri", "file:///test/audio.mp3")
            mock_playbin.set_state.assert_called_once()

    @patch("anura.services.tts.Gst")
    def test_play_audio_gst_error(self, mock_gst):
        """Test handling of GStreamer errors."""
        mock_gst.ElementFactory.make.side_effect = Exception("GStreamer error")

        # play() should raise the exception
        with pytest.raises(Exception, match="GStreamer error"):
            self.service.play("/test/audio.mp3")

    def test_stop_audio(self):
        """Test stopping audio playback."""
        # Mock the player
        mock_player = Mock()
        self.service.player = mock_player
        
        self.service.stop_speaking()

        mock_player.set_state.assert_called_once()
        # Verify cleanup resources are called

    def test_setup_bus_watch(self):
        """Test GStreamer bus watch setup."""
        # Mock the bus and related objects
        with patch.object(self.service, '_bus', Mock()) as mock_bus:
            with patch.object(self.service, '_bus_message_handler_id', None):
                result = self.service._setup_bus_watch()
                
                # Should return False (don't repeat)
                assert result is False

    def test_on_bus_message_error(self):
        """Test handling of GStreamer error messages."""
        mock_message = Mock()
        mock_message.type = Gst.MessageType.ERROR
        mock_message.parse_error.return_value = (Mock(), "Test error")

        # Test on_gst_message method
        self.service.on_gst_message(Mock(), mock_message)

        # Should handle error gracefully
        mock_message.parse_error.assert_called_once()

    def test_on_bus_message_eos(self):
        """Test handling of GStreamer end-of-stream messages."""
        mock_message = Mock()
        mock_message.type = Gst.MessageType.EOS

        # Test on_gst_message method
        with patch.object(self.service, '_current_speech_file', '/test/file.mp3'):
            self.service.on_gst_message(Mock(), mock_message)

        # Should handle EOS gracefully
        # Verify cleanup was called

    def test_on_bus_message_other(self):
        """Test handling of other GStreamer messages."""
        mock_message = Mock()
        mock_message.type = Gst.MessageType.TAG  # Some other message type
        # Test on_gst_message method - should not crash
        self.service.on_gst_message(Mock(), mock_message)

        # Should handle other messages gracefully (no action needed)

    
