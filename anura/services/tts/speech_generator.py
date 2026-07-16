# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
import os
from pathlib import Path
import threading
import uuid

import gtts
from loguru import logger
import requests

from anura.config import MAX_TTS_TEXT_LENGTH, REQUEST_TIMEOUT


class SpeechGenerator:
    """
    Handles MP3 speech generation using gTTS.
    Manages temporary file creation and cleanup.
    """

    _tld: str = "com"
    _cache_home: str = os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))
    _speech_dir: Path = Path(_cache_home) / "anura"

    def __init__(self) -> None:
        super().__init__()
        logger.debug("Anura SpeechGenerator: Initializing")

        # Security: Ensure speech cache directory has restrictive permissions (0700)
        # to protect potentially sensitive audio artifacts of OCR text.
        self._speech_dir.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            self._speech_dir.chmod(0o700)

        self._current_speech_file: str | None = None
        self._state_lock = threading.Lock()

        logger.debug("Anura SpeechGenerator: Initialization complete")

    def generate(self, text: str, lang: str = "en", generation_id: int = 0) -> str:
        """Thread-safe MP3 generation with proper state management.
        
        Args:
            text: Text to convert to speech
            lang: Language code for gTTS
            generation_id: Generation ID from PipelineManager (for reporting only)
        """
        # Input validation: avoid unnecessary gTTS calls for empty/whitespace text
        if not text or not text.strip():
            logger.debug("Anura TTS: Empty text provided, returning empty path")
            return ""

        # Security: Enforce hard length limit for TTS requests to prevent resource
        # exhaustion (DoS).
        if len(text) > MAX_TTS_TEXT_LENGTH:
            logger.warning(
                f"Anura TTS: Text exceeds maximum length ({len(text)} > {MAX_TTS_TEXT_LENGTH}). "
                "Truncating for safety."
            )
            text = text[:MAX_TTS_TEXT_LENGTH]

        # Use uuid to ensure zero filename collisions during high-frequency requests
        filename = f"speech_{uuid.uuid4().hex}.mp3"
        filepath = str(self._speech_dir / filename)

        tts = gtts.gTTS(text, lang=lang, tld=self._tld, timeout=REQUEST_TIMEOUT)
        logger.info(f"Anura TTS: Generating speech for language: {lang} (timeout={REQUEST_TIMEOUT}s)")

        try:
            # Perform blocking I/O without holding the state lock
            tts.save(filepath)
        except (SystemExit, KeyboardInterrupt):
            # Re-raise system exceptions that should terminate the application
            raise
        except (requests.RequestException, OSError) as e:
            logger.error(f"Anura TTS: Failed to save speech file: {e}")
            path = Path(filepath)
            if path.exists():
                with contextlib.suppress(OSError):
                    path.unlink()
            return ""

        logger.debug(f"Anura TTS: Speech file saved: {filename}")

        # Update current speech file state under lock only after successful save
        with self._state_lock:
            # Clean up previous file if any
            if self._current_speech_file:
                old_path = Path(self._current_speech_file)
                if old_path.exists():
                    with contextlib.suppress(OSError):
                        old_path.unlink()

            self._current_speech_file = filepath

        return filepath

    def get_current_file(self) -> str | None:
        """Get the current speech file path."""
        with self._state_lock:
            return self._current_speech_file

    def clear_current_file(self) -> str | None:
        """Clear and return the current speech file path."""
        with self._state_lock:
            filepath = self._current_speech_file
            self._current_speech_file = None
            return filepath


    def cleanup_file(self, filepath: str | None) -> None:
        """Clean up a speech file."""
        if filepath:
            path = Path(filepath)
            if path.exists():
                try:
                    path.unlink()
                    logger.debug("Anura TTS: Cleaned up temporary speech file")
                except OSError:
                    logger.warning("Anura TTS: Failed to cleanup temporary speech file")

    def cleanup_directory(self) -> None:
        """Clean up old speech files from the directory."""
        import time

        try:
            if self._speech_dir.exists():
                for file_path in self._speech_dir.iterdir():
                    if (
                        file_path.name.startswith("speech_")
                        and file_path.name.endswith(".mp3")
                        and time.time() - file_path.stat().st_mtime > 3600
                    ):
                        # Only delete files older than 1 hour to avoid deleting active files from other instances
                        with contextlib.suppress(OSError):
                            file_path.unlink()
        except (OSError, RuntimeError) as e:
            logger.debug(f"Anura TTS: Error during directory cleanup: {e}")
