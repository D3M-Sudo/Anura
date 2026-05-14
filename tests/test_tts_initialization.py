# test_tts_initialization.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# Regression test for BUG-01: AttributeError when accessing TTSService.player before play()

from unittest.mock import patch

from anura.services.tts import TTSService


class TestTTSServiceInitialization:
    """Test TTSService initialization and safe method access before play()."""

    @patch("anura.services.tts.Gst")
    @patch("anura.services.tts.logger")
    def test_player_slot_initialized(self, mock_logger, mock_gst):
        """Test that self.player is properly initialized to None in __init__."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create TTSService instance
        tts_service = TTSService()

        # Verify player slot is initialized to None
        assert tts_service.player is None

    @patch("anura.services.tts.Gst")
    @patch("anura.services.tts.logger")
    def test_stop_speaking_before_play(self, mock_logger, mock_gst):
        """Test that stop_speaking() can be called before play() without AttributeError."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create TTSService instance
        tts_service = TTSService()

        # This should not raise AttributeError
        tts_service.stop_speaking()

        # Verify cleanup was attempted (player was None, so no cleanup occurred)
        assert tts_service.player is None

    @patch("anura.services.tts.Gst")
    @patch("anura.services.tts.logger")
    def test_cleanup_before_play(self, mock_logger, mock_gst):
        """Test that cleanup() can be called before play() without AttributeError."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create TTSService instance
        tts_service = TTSService()

        # This should not raise AttributeError
        tts_service.cleanup()

        # Verify cleanup was attempted (player was None, so no cleanup occurred)
        assert tts_service.player is None

    @patch("anura.services.tts.Gst")
    @patch("anura.services.tts.logger")
    def test_multiple_stop_calls_before_play(self, mock_logger, mock_gst):
        """Test that multiple stop_speaking() calls before play() are safe."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create TTSService instance
        tts_service = TTSService()

        # Multiple calls should not raise AttributeError
        tts_service.stop_speaking()
        tts_service.stop_speaking()
        tts_service.stop_speaking()

        # Verify player remains None
        assert tts_service.player is None

    @patch("anura.services.tts.Gst")
    @patch("anura.services.tts.logger")
    def test_multiple_cleanup_calls_before_play(self, mock_logger, mock_gst):
        """Test that multiple cleanup() calls before play() are safe."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create TTSService instance
        tts_service = TTSService()

        # Multiple calls should not raise AttributeError
        tts_service.cleanup()
        tts_service.cleanup()
        tts_service.cleanup()

        # Verify player remains None
        assert tts_service.player is None

    @patch("anura.services.tts.Gst")
    @patch("anura.services.tts.logger")
    def test_mixed_calls_before_play(self, mock_logger, mock_gst):
        """Test that mixed stop_speaking() and cleanup() calls before play() are safe."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create TTSService instance
        tts_service = TTSService()

        # Mixed calls should not raise AttributeError
        tts_service.stop_speaking()
        tts_service.cleanup()
        tts_service.stop_speaking()
        tts_service.cleanup()

        # Verify player remains None
        assert tts_service.player is None
