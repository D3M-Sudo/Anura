# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from unittest.mock import patch

from anura.services.tts.audio_player import AudioPlayer


class TestTTSServiceInitialization:
    """Test AudioPlayer initialization and safe method access before play()."""

    @patch("anura.services.tts.audio_player.Gst")
    @patch("anura.services.tts.audio_player.logger")
    def test_player_slot_initialized(self, mock_logger, mock_gst):
        """Test that self.player is properly initialized to None in __init__."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create AudioPlayer instance
        player = AudioPlayer()

        # Verify player slot is initialized to None
        assert player.player is None

    @patch("anura.services.tts.audio_player.Gst")
    @patch("anura.services.tts.audio_player.logger")
    def test_stop_speaking_before_play(self, mock_logger, mock_gst):
        """Test that stop() can be called before play() without AttributeError."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create AudioPlayer instance
        player = AudioPlayer()

        # This should not raise AttributeError
        player.stop()

        # Verify cleanup was attempted (player was None, so no cleanup occurred)
        assert player.player is None

    @patch("anura.services.tts.audio_player.Gst")
    @patch("anura.services.tts.audio_player.logger")
    def test_cleanup_before_play(self, mock_logger, mock_gst):
        """Test that cleanup() can be called before play() without AttributeError."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create AudioPlayer instance
        player = AudioPlayer()

        # This should not raise AttributeError
        player.cleanup()

        # Verify cleanup was attempted (player was None, so no cleanup occurred)
        assert player.player is None

    @patch("anura.services.tts.audio_player.Gst")
    @patch("anura.services.tts.audio_player.logger")
    def test_multiple_stop_calls_before_play(self, mock_logger, mock_gst):
        """Test that multiple stop() calls before play() are safe."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create AudioPlayer instance
        player = AudioPlayer()

        # Multiple calls should not raise AttributeError
        player.stop()
        player.stop()
        player.stop()

        # Verify player remains None
        assert player.player is None

    @patch("anura.services.tts.audio_player.Gst")
    @patch("anura.services.tts.audio_player.logger")
    def test_multiple_cleanup_calls_before_play(self, mock_logger, mock_gst):
        """Test that multiple cleanup() calls before play() are safe."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create AudioPlayer instance
        player = AudioPlayer()

        # Multiple calls should not raise AttributeError
        player.cleanup()
        player.cleanup()
        player.cleanup()

        # Verify player remains None
        assert player.player is None

    @patch("anura.services.tts.audio_player.Gst")
    @patch("anura.services.tts.audio_player.logger")
    def test_mixed_calls_before_play(self, mock_logger, mock_gst):
        """Test that mixed stop() and cleanup() calls before play() are safe."""
        # Mock GStreamer to avoid actual initialization
        mock_gst.is_initialized.return_value = True

        # Create AudioPlayer instance
        player = AudioPlayer()

        # Mixed calls should not raise AttributeError
        player.stop()
        player.cleanup()
        player.stop()
        player.cleanup()

        # Verify player remains None
        assert player.player is None
