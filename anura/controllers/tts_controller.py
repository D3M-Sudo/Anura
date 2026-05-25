# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gi.repository import GObject
from loguru import logger

from anura.services.tts import get_tts_service


class TtsController(GObject.GObject):
    """
    Decoupled controller for Text-to-Speech operations.
    """

    def __init__(self, window):
        GObject.GObject.__init__(self)
        self._window = window
        self._tts_service = get_tts_service()
        self._signal_connections = {}

        # Register for automatic teardown
        if hasattr(window, "register_controller"):
            window.register_controller(self)

        self._setup_connections()
        logger.debug("TtsController: Initialized and connected to AnuraWindow")

    def connect_tracked(self, emitter, signal_name, callback):
        handler_id = emitter.connect(signal_name, callback)
        if emitter not in self._signal_connections:
            self._signal_connections[emitter] = []
        self._signal_connections[emitter].append(handler_id)
        return handler_id

    def _setup_connections(self):
        self.connect_tracked(self._tts_service, "speak", self._on_tts_speak)
        self.connect_tracked(self._tts_service, "stop", self._on_tts_stop)
        self.connect_tracked(self._tts_service, "paused", self._on_tts_paused)
        self.connect_tracked(self._tts_service, "error", self._on_tts_error)

    def _on_tts_speak(self, _service, filepath):
        if filepath:
            self._tts_service.play(filepath)
            self._window.extracted_page.update_tts_state(playing=True)

    def _on_tts_stop(self, _service, is_finished):
        self._window.extracted_page.update_tts_state(playing=False)
        if is_finished:
            logger.debug("TtsController: Playback finished normally")

    def _on_tts_paused(self, _service, is_paused):
        self._window.extracted_page.update_tts_state(paused=is_paused)

    def _on_tts_error(self, _service, message):
        self._window.show_toast(message)
        self._window.extracted_page.update_tts_state(playing=False)

    def teardown(self) -> None:
        """Unified teardown called by SignalManagerMixin."""
        self.cleanup()

    def cleanup(self):
        for emitter, handler_ids in self._signal_connections.items():
            for handler_id in handler_ids:
                try:
                    emitter.disconnect(handler_id)
                except Exception:
                    pass
        self._signal_connections.clear()
        self._window = None
        logger.debug("TtsController: Cleaned up and disconnected")
