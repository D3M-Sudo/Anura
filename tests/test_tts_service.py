# test_tts_service.py
#
# Unit tests for TTSService
# Tests language mapping, audio generation, and GStreamer integration

import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from anura.services.tts import TTSService


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

    @patch("anura.services.tts.gTTS")
    @patch("anura.services.tts.os.path.exists")
    @patch("anura.services.tts.os.makedirs")
    def test_speak_text_cache_hit(self, mock_makedirs, mock_exists, mock_gtts):
        """Test speaking text when cached file exists."""
        # Mock cache hit
        mock_exists.return_value = True
        cache_path = "/cache/test.mp3"

        with patch("anura.services.tts.GLib") as mock_glib:
            result = self.service.speak_text("test text", "en", cache_path)

            assert result == cache_path
            mock_gtts.assert_not_called()  # Should not generate new audio
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "speak"
            assert args[2] == cache_path

    @patch("anura.services.tts.gTTS")
    @patch("anura.services.tts.os.path.exists")
    @patch("anura.services.tts.os.makedirs")
    def test_speak_text_cache_miss(self, mock_makedirs, mock_exists, mock_gtts):
        """Test speaking text when cached file doesn't exist."""
        # Mock cache miss
        mock_exists.return_value = False
        cache_path = "/cache/test.mp3"

        # Mock gTTS
        mock_tts = Mock()
        mock_gtts.return_value = mock_tts

        with patch("anura.services.tts.GLib") as mock_glib:
            result = self.service.speak_text("test text", "en", cache_path)

            assert result == cache_path
            mock_gtts.assert_called_once_with(text="test text", lang="en", tld="com")
            mock_tts.save.assert_called_once_with(cache_path)
            mock_glib.idle_add.assert_called_once()

    @patch("anura.services.tts.gTTS")
    @patch("anura.services.tts.os.path.exists")
    @patch("anura.services.tts.os.makedirs")
    def test_speak_text_gtts_error(self, mock_makedirs, mock_exists, mock_gtts):
        """Test handling of gTTS generation errors."""
        mock_exists.return_value = False
        mock_gtts.side_effect = Exception("TTS error")
        cache_path = "/cache/test.mp3"

        with patch("anura.services.tts.GLib") as mock_glib:
            result = self.service.speak_text("test text", "en", cache_path)

            assert result is None
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "stop"
            assert args[2] is False

    @patch("anura.services.tts.gTTS")
    @patch("anura.services.tts.os.path.exists")
    @patch("anura.services.tts.os.makedirs")
    def test_speak_text_save_error(self, mock_makedirs, mock_exists, mock_gtts):
        """Test handling of file save errors."""
        mock_exists.return_value = False
        mock_tts = Mock()
        mock_tts.save.side_effect = IOError("Save error")
        mock_gtts.return_value = mock_tts
        cache_path = "/cache/test.mp3"

        with patch("anura.services.tts.GLib") as mock_glib:
            result = self.service.speak_text("test text", "en", cache_path)

            assert result is None
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "stop"
            assert args[2] is False

    def test_speak_text_empty_text(self):
        """Test speaking empty text."""
        cache_path = "/cache/test.mp3"

        result = self.service.speak_text("", "en", cache_path)
        assert result is None

    def test_speak_text_none_text(self):
        """Test speaking None text."""
        cache_path = "/cache/test.mp3"

        result = self.service.speak_text(None, "en", cache_path)
        assert result is None

    @patch("anura.services.tts.Gst")
    def test_play_audio_success(self, mock_gst):
        """Test successful audio playback."""
        # Mock GStreamer elements
        mock_playbin = Mock()
        mock_gst.ElementFactory.make.return_value = mock_playbin
        mock_bus = Mock()
        mock_playbin.get_bus.return_value = mock_bus

        with patch("anura.services.tts.GLib") as mock_glib:
            self.service.play_audio("/test/audio.mp3")

            mock_gst.ElementFactory.make.assert_called_once_with("playbin3", "player")
            mock_playbin.set_property.assert_called_once_with("uri", "file:///test/audio.mp3")
            mock_playbin.set_state.assert_called_once()
            mock_glib.idle_add.assert_called_once()

    @patch("anura.services.tts.Gst")
    def test_play_audio_gst_error(self, mock_gst):
        """Test handling of GStreamer errors."""
        mock_gst.ElementFactory.make.side_effect = Exception("GStreamer error")

        with patch("anura.services.tts.GLib") as mock_glib:
            self.service.play_audio("/test/audio.mp3")

            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "stop"
            assert args[2] is False

    def test_stop_audio(self):
        """Test stopping audio playback."""
        with patch("anura.services.tts.GLib") as mock_glib:
            self.service.stop_audio()

            self.service.player.set_state.assert_called_once()
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "stop"
            assert args[2] is True

    def test_setup_bus_watch(self):
        """Test GStreamer bus watch setup."""
        mock_bus = Mock()

        with patch("anura.services.tts.Gst") as mock_gst:
            self.service._setup_bus_watch(mock_bus)

            mock_gst.Bus.TIMESTAMP_FLAG = Mock()
            mock_bus.add_signal_watch.assert_called_once()
            mock_bus.connect.assert_called_once()

    def test_on_bus_message_error(self):
        """Test handling of GStreamer error messages."""
        mock_bus = Mock()
        mock_message = Mock()
        mock_message.parse_error.return_value = (Mock(), "Test error")

        with patch("anura.services.tts.GLib") as mock_glib:
            result = self.service._on_bus_message(mock_bus, mock_message)

            assert result is True
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "stop"
            assert args[2] is False

    def test_on_bus_message_eos(self):
        """Test handling of GStreamer end-of-stream messages."""
        mock_bus = Mock()
        mock_message = Mock()
        mock_message.type = Mock()
        mock_message.type.return_value = Mock()
        mock_message.type.EOS = Mock()

        with patch("anura.services.tts.GLib") as mock_glib:
            # Mock the message type comparison
            mock_message.type.__eq__ = Mock(return_value=True)

            result = self.service._on_bus_message(mock_bus, mock_message)

            assert result is True
            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "stop"
            assert args[2] is True

    def test_on_bus_message_other(self):
        """Test handling of other GStreamer messages."""
        mock_bus = Mock()
        mock_message = Mock()
        mock_message.type = Mock()

        result = self.service._on_bus_message(mock_bus, mock_message)

        assert result is True
        # Should not emit any signals for other messages

    def test_get_cache_dir(self):
        """Test cache directory path generation."""
        with patch("anura.services.tts.os.path.exists", return_value=True):
            cache_dir = self.service._get_cache_dir()
            assert cache_dir.endswith("/anura/tts")

    def test_get_cache_dir_creation(self):
        """Test cache directory creation when it doesn't exist."""
        with patch("anura.services.tts.os.path.exists", return_value=False):
            with patch("anura.services.tts.os.makedirs") as mock_makedirs:
                cache_dir = self.service._get_cache_dir()
                mock_makedirs.assert_called_once()
                assert cache_dir.endswith("/anura/tts")

    def test_get_cache_path(self):
        """Test cache file path generation."""
        with patch.object(self.service, "_get_cache_dir", return_value="/cache"):
            cache_path = self.service._get_cache_path("test text", "en")

            # Should generate a hash-based filename
            assert cache_path.startswith("/cache/")
            assert cache_path.endswith(".mp3")

    def test_get_cache_path_consistent(self):
        """Test that same text generates same cache path."""
        with patch.object(self.service, "_get_cache_dir", return_value="/cache"):
            path1 = self.service._get_cache_path("test text", "en")
            path2 = self.service._get_cache_path("test text", "en")

            assert path1 == path2

    def test_get_cache_path_different_text(self):
        """Test that different text generates different cache paths."""
        with patch.object(self.service, "_get_cache_dir", return_value="/cache"):
            path1 = self.service._get_cache_path("text1", "en")
            path2 = self.service._get_cache_path("text2", "en")

            assert path1 != path2

    def test_get_cache_path_different_language(self):
        """Test that different languages generate different cache paths."""
        with patch.object(self.service, "_get_cache_dir", return_value="/cache"):
            path1 = self.service._get_cache_path("test text", "en")
            path2 = self.service._get_cache_path("test text", "it")

            assert path1 != path2
