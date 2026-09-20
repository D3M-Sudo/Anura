# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from typing import ClassVar
import weakref

from gi.repository import GLib, GObject
from loguru import logger
import requests

from anura.core.atomic_task_manager import get_atomic_manager
from anura.services.settings import settings
from anura.services.tts import get_tts_service
from anura.utils.signal_manager import SignalManagerMixin

# UX ceiling for TTS generation (independent of the underlying network cause).
# After _TTS_STILL_WAITING_DELAY_S the user gets a one-shot 'still waiting'
# toast so the spinner is never mute; after _TTS_GENERATION_TIMEOUT_S
# generation is treated as failed and the UI returns to idle even if the
# worker thread is still blocked. Superseded by real completion via a
# monotonic request id.
_TTS_STILL_WAITING_DELAY_S = 8
_TTS_GENERATION_TIMEOUT_S = 35


class TtsController(GObject.GObject, SignalManagerMixin):
    """
    Decoupled controller for Text-to-Speech operations.
    Detains absolute monopoly over TTS logic and state.
    """

    __gsignals__: ClassVar[dict[str, tuple]] = {
        # 'idle', 'generating', 'playing', 'paused'
        "state-changed": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "error-occurred": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        # One-shot notice fired while generation is still pending; carries
        # no payload. The window surfaces it as a toast — never as a state.
        "still-waiting": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self, window):
        GObject.GObject.__init__(self)
        SignalManagerMixin.__init__(self)

        self._window = weakref.proxy(window)
        self._tts_service = get_tts_service()
        self._current_text: str | None = None
        # Monotonic generation request id: only the newest request may drive
        # UI state; late completions from superseded requests are ignored.
        self._generation_seq = 0
        self._active_generation_seq: int | None = None
        self._waiting_source: int | None = None
        self._timeout_source: int | None = None

        # Register for automatic teardown
        if hasattr(window, "register_controller"):
            window.register_controller(self)

        self._setup_connections()
        logger.debug("TtsController: Initialized and connected to AnuraWindow")

    def _setup_connections(self):
        self.connect_tracked(self._tts_service, "speak", self._on_tts_speak)
        self.connect_tracked(self._tts_service, "stop", self._on_tts_stop)
        self.connect_tracked(self._tts_service, "paused", self._on_tts_paused)
        self.connect_tracked(self._tts_service, "error", self._on_tts_error)

    def request_listen(self, text: str):
        """Monopoly: initiate the TTS flow."""
        if not text or not text.strip():
            return

        # FIX BUG-NEW-001: Implement explicit GStreamer state check and text delta check.
        # If the player is PAUSED and the text matches what we're currently playing,
        # resume. If the text has changed, we MUST generate a new speech file
        # regardless of the player's current state.
        if self._tts_service.is_paused() and text == self._current_text:
            logger.debug("TtsController: Resuming paused playback for identical text")
            self.toggle_pause()
            return

        self._current_text = text
        self.emit("state-changed", "generating")

        ocr_lang = settings.get_string("active-language")
        tts_lang = self._tts_service.get_effective_language(ocr_lang)

        if not tts_lang:
            from gettext import gettext as _
            self.emit("error-occurred", _("Text-to-speech is not available for this language"))
            self.emit("state-changed", "idle")
            return

        try:
            self._generation_seq += 1
            seq = self._generation_seq
            self._active_generation_seq = seq
            self._cancel_generation_timers()
            try:
                self._waiting_source = GLib.timeout_add_seconds(
                    _TTS_STILL_WAITING_DELAY_S, self._on_still_waiting, seq
                )
            except (GLib.Error, RuntimeError, TypeError) as e:
                logger.debug(f"TtsController: cannot schedule still-waiting timer: {e}")
                self._waiting_source = None
            try:
                self._timeout_source = GLib.timeout_add_seconds(
                    _TTS_GENERATION_TIMEOUT_S, self._on_generation_timeout, seq
                )
            except (GLib.Error, RuntimeError, TypeError) as e:
                logger.debug(f"TtsController: cannot schedule generation-timeout timer: {e}")
                self._timeout_source = None
            get_atomic_manager().execute(
                self._tts_service.generate,
                (text, tts_lang),
                callback=self._on_generated,
                errorback=self._on_generate_error,
            )
        except (AttributeError, RuntimeError, TypeError) as e:
            logger.exception(f"TtsController: Failed to initiate speech generation: {e}")
            self._cancel_generation_timers()
            self._active_generation_seq = None
            self.emit("state-changed", "idle")

    def stop(self):
        """Stop TTS playback."""
        self._cancel_generation_timers()
        self._active_generation_seq = None
        self._tts_service.stop_speaking()

    def toggle_pause(self):
        """Toggle pause/resume."""
        self._tts_service.toggle_pause()

    def _on_still_waiting(self, seq: int) -> bool:
        """Inform the UI once that generation is taking longer than usual."""
        self._waiting_source = None
        if seq == self._active_generation_seq:
            logger.debug(f"TtsController: generation still pending after {_TTS_STILL_WAITING_DELAY_S}s")
            self.emit("still-waiting")
        return False

    def _on_generation_timeout(self, seq: int) -> bool:
        """Treat a hung generation as failed so the UI never wedges on the spinner."""
        from gettext import gettext as _

        self._timeout_source = None
        if seq != self._active_generation_seq:
            return False
        logger.warning(f"TtsController: generation timed out after {_TTS_GENERATION_TIMEOUT_S}s")
        self._cancel_generation_timers()
        self._active_generation_seq = None
        self.emit("error-occurred", _("Text-to-speech is taking too long. Please try again."))
        self.emit("state-changed", "idle")
        return False

    def _cancel_generation_timers(self) -> None:
        for attr in ("_waiting_source", "_timeout_source"):
            source = getattr(self, attr, None)
            if source is not None:
                with contextlib.suppress(GLib.Error, RuntimeError):
                    GLib.source_remove(source)
                setattr(self, attr, None)

    def _settle_generation(self) -> bool:
        """Drop timers for the active request; True only if it is still current."""
        if self._active_generation_seq is None:
            return False
        self._cancel_generation_timers()
        self._active_generation_seq = None
        return True

    def _on_generated(self, filepath: str | None):
        """Callback when generation succeeds."""
        if not self._settle_generation():
            return
        if not filepath:
            self.emit("state-changed", "idle")
            return
        logger.debug(f"TtsController: Generated {filepath} — queuing playback")
        self._tts_service.play(filepath)
        self.emit("state-changed", "playing")

    def _on_generate_error(self, error: Exception, traceback_str: str | None = None):
        """Callback when generation fails."""
        if not self._settle_generation():
            return
        from gettext import gettext as _
        if isinstance(error, TimeoutError):
            msg = _("Request timed out. Please try again.")
        elif isinstance(error, (requests.RequestException, OSError)):
            msg = _("Network error. Please check your internet connection.")
        else:
            msg = _("Text-to-speech failed. Please try again.")

        self.emit("error-occurred", msg)
        self.emit("state-changed", "idle")

    def _on_tts_speak(self, _service, filepath):
        if filepath:
            self._tts_service.play(filepath)
            self.emit("state-changed", "playing")

    def _on_tts_stop(self, _service, is_finished):
        self.emit("state-changed", "idle")
        if is_finished:
            logger.debug("TtsController: Playback finished normally")

    def _on_tts_paused(self, _service, is_paused):
        if is_paused:
            self.emit("state-changed", "paused")
        else:
            self.emit("state-changed", "playing")

    def _on_tts_error(self, _service, message):
        self.emit("error-occurred", message)
        self.emit("state-changed", "idle")

    def teardown(self) -> None:
        """Unified teardown called by SignalManagerMixin."""
        self.cleanup()

    def cleanup(self):
        """Explicit cleanup to prevent memory leaks."""
        self._cancel_generation_timers()
        self._active_generation_seq = None
        try:
            self.disconnect_all_signals()
        except (TypeError, RuntimeError) as e:
            logger.debug(f"Signal disconnection omitted or failed during cleanup: {e}")
        self._window = None
        logger.debug("TtsController: Cleaned up and disconnected")
