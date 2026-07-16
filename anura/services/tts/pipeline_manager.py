# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import threading

from gi.repository import GLib, GObject
from loguru import logger

from anura.services.settings import settings
from anura.services.tts.audio_player import AudioPlayer
from anura.services.tts.language_mapper import LanguageMapper
from anura.services.tts.speech_generator import SpeechGenerator


class PipelineManager(GObject.GObject):
    """
    Orchestrates the TTS pipeline: generation → playback.
    Coordinates SpeechGenerator and AudioPlayer.
    """

    __gtype_name__ = "PipelineManager"

    __gsignals__ = {
        "speak": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "stop": (GObject.SignalFlags.RUN_LAST, None, (bool,)),
        "paused": (GObject.SignalFlags.RUN_LAST, None, (bool,)),
        "error": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self) -> None:
        super().__init__()
        self._generator = SpeechGenerator()
        self._player = AudioPlayer()
        self._generation_id = 0

        # Connect player signals
        self._player.connect("eos", self._on_player_eos)
        self._player.connect("error", self._on_player_error)

        self._mapper = LanguageMapper()
        self._init_lock = threading.Lock()

        # Pre-cache supported languages in background
        self._init_thread = threading.Thread(target=self._mapper.get_supported_gtts_languages, daemon=True)
        self._init_thread.start()

    def generate_and_play(self, text: str, ocr_lang: str = "eng") -> None:
        """Generate speech and play it."""
        # Get effective language
        tts_lang = settings.get_string("tts-language")
        if not tts_lang:
            tts_lang = self._mapper.map_tesseract_to_gtts(ocr_lang)

        if not tts_lang:
            logger.warning(f"Anura TTS: No TTS language available for '{ocr_lang}'")
            self.emit("error", "No TTS language available")
            return

        # Increment generation to invalidate any previous generation
        self._generation_id += 1
        current_gen = self._generation_id

        # Generate speech file with generation_id
        filepath = self._generator.generate(text, tts_lang, generation_id=current_gen)
        if not filepath:
            logger.error("Anura TTS: Failed to generate speech file")
            self.emit("error", "Failed to generate speech")
            return

        # Emit speak signal with filepath
        GLib.idle_add(lambda: (self.emit("speak", filepath), GLib.SOURCE_REMOVE)[1])

        # Play the file with generation_id
        volume = max(0.0, min(1.0, settings.get_double("tts-volume")))
        self._player.play(filepath, volume, generation_id=current_gen)

    def _on_player_eos(self, _player: AudioPlayer, generation_id: int) -> None:
        """Handle player end-of-stream with staleness verification."""
        # Verify this callback is for the current generation
        if generation_id != self._generation_id:
            logger.debug(f"PipelineManager: Ignoring stale EOS callback (gen {generation_id} != current {self._generation_id})")
            return

        # Clean up the speech file
        filepath = self._generator.clear_current_file()
        self._generator.cleanup_file(filepath)

        # Emit stop signal
        GLib.idle_add(lambda: (self.emit("stop", True), GLib.SOURCE_REMOVE)[1])

    def _on_player_error(self, _player: AudioPlayer, generation_id: int, error_msg: str) -> None:
        """Handle player error with staleness verification."""
        # Verify this callback is for the current generation
        if generation_id != self._generation_id:
            logger.debug(f"PipelineManager: Ignoring stale error callback (gen {generation_id} != current {self._generation_id})")
            return

        # Clean up the speech file
        filepath = self._generator.clear_current_file()
        self._generator.cleanup_file(filepath)

        # Emit error and stop signals
        GLib.idle_add(lambda: (self.emit("error", error_msg), self.emit("stop", False), GLib.SOURCE_REMOVE)[1])

    def stop(self) -> None:
        """Stop playback and cleanup."""
        had_player = self._player.player is not None
        self._player.stop()

        # Clean up speech file
        filepath = self._generator.clear_current_file()
        self._generator.cleanup_file(filepath)

        # Only emit stop if there was an active player
        if had_player:
            GLib.idle_add(lambda: (self.emit("stop", False), GLib.SOURCE_REMOVE)[1])

    def pause(self) -> None:
        """Pause playback."""
        self._player.pause()
        GLib.idle_add(lambda: (self.emit("paused", True), GLib.SOURCE_REMOVE)[1])

    def resume(self) -> None:
        """Resume playback."""
        self._player.resume()
        GLib.idle_add(lambda: (self.emit("paused", False), GLib.SOURCE_REMOVE)[1])

    def toggle_pause(self) -> None:
        """Toggle pause state."""
        if self._player.is_playing():
            self.pause()
        elif self._player.is_paused():
            self.resume()

    def is_playing(self) -> bool:
        """Check if currently playing."""
        return self._player.is_playing()

    def is_paused(self) -> bool:
        """Check if currently paused."""
        return self._player.is_paused()

    def get_supported_languages(self) -> dict:
        """Get supported gTTS languages."""
        return self._mapper.get_supported_gtts_languages()

    def map_language(self, tess_code: str) -> str | None:
        """Map Tesseract code to gTTS code."""
        return self._mapper.map_tesseract_to_gtts(tess_code)

    def cleanup(self) -> None:
        """Complete cleanup for shutdown."""
        self._player.cleanup()
        self._generator.cleanup_directory()

    def generate_speech_file(self, text: str, lang: str = "en") -> str:
        """
        Generate a speech file without playing it.
        Public method for backward compatibility.
        """
        return self._generator.generate(text, lang, generation_id=0)

    def play_speech_file(self, speech_file: str, volume: float = 1.0) -> None:
        """
        Play a speech file with specified volume.
        Public method for backward compatibility.
        """
        self._player.play(speech_file, volume, generation_id=0)
