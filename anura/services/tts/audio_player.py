# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
import functools
import threading
from typing import ClassVar

import gi

gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import GLib, GObject, Gst  # noqa: E402
from loguru import logger  # noqa: E402


class AudioPlayer(GObject.GObject):
    """
    Manages GStreamer audio playback.
    Handles playbin3 creation, state management, and bus message handling.
    """

    __gtype_name__ = "AudioPlayer"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "eos": (GObject.SignalFlags.RUN_LAST, None, (int,)),
        "error": (GObject.SignalFlags.RUN_LAST, None, (int, str)),
    }

    def __init__(self) -> None:
        super().__init__()
        self.player: Gst.Element | None = None
        self._bus: Gst.Bus | None = None
        self._eos_handler_id: int | None = None
        self._error_handler_id: int | None = None
        self._bus_watch_active: bool = False
        self._cleanup_lock = threading.Lock()

        # Initialize GStreamer only once
        if not Gst.is_initialized():
            logger.info("Anura AudioPlayer: Initializing GStreamer")
            Gst.init(None)
        else:
            logger.debug("Anura AudioPlayer: GStreamer already initialized")

    def play(self, filepath: str, volume: float = 1.0, generation_id: int = 0) -> None:
        """Play an audio file using GStreamer playbin3.

        Args:
            filepath: Path to audio file
            volume: Volume level (0.0 to 1.0)
            generation_id: Generation ID from PipelineManager (included in signals)
        """
        # Cleanup previous playback completely
        self.cleanup()

        self.player = Gst.ElementFactory.make("playbin3", "player")
        if not self.player:
            logger.error("Anura AudioPlayer: Failed to create GStreamer playbin.")
            self.emit("error", generation_id, "Failed to create GStreamer playbin")
            return

        self.player.set_property("uri", f"file://{filepath}")
        self.player.set_property("volume", max(0.0, min(1.0, volume)))

        # Setup bus before starting playback
        self._bus = self.player.get_bus()
        self._setup_bus_watch(generation_id)

        logger.info("Anura AudioPlayer: Setting state to PLAYING")
        self.player.set_state(Gst.State.PLAYING)

    def _setup_bus_watch(self, generation_id: int) -> bool:
        """Setup GStreamer bus signal watch with generation_id captured in closure."""
        if self._bus is None:
            return False

        self._bus.add_signal_watch()
        self._bus_watch_active = True

        # Register handlers with generation_id captured via functools.partial
        eos_callback = functools.partial(self._on_gst_eos, generation_id=generation_id)
        error_callback = functools.partial(self._on_gst_error, generation_id=generation_id)

        self._eos_handler_id = self._bus.connect("message::eos", eos_callback)
        self._error_handler_id = self._bus.connect("message::error", error_callback)

        logger.debug("Anura AudioPlayer: Bus watch setup completed")
        return True

    def _on_gst_eos(self, generation_id: int, _bus: Gst.Bus, _message: Gst.Message) -> None:
        """Handle EOS message with generation_id captured in closure."""
        logger.info("Anura AudioPlayer: End of Stream")
        self.cleanup()
        GLib.idle_add(lambda: (self.emit("eos", generation_id), GLib.SOURCE_REMOVE)[1])

    def _on_gst_error(self, generation_id: int, _bus: Gst.Bus, message: Gst.Message) -> None:
        """Handle error message with generation_id captured in closure."""
        err, _debug = message.parse_error()
        error_msg = f"{err}"
        logger.error(f"Anura AudioPlayer: GStreamer error: {error_msg}")
        self.cleanup()
        GLib.idle_add(lambda: (self.emit("error", generation_id, error_msg), GLib.SOURCE_REMOVE)[1])

    def _cleanup_resources(self) -> None:
        """Clean up GStreamer resources."""
        if self._bus_watch_active and self._bus:
            with contextlib.suppress(GLib.Error, RuntimeError):
                # Disconnect handlers before removing watch
                if self._eos_handler_id is not None:
                    self._bus.disconnect(self._eos_handler_id)
                    self._eos_handler_id = None
                if self._error_handler_id is not None:
                    self._bus.disconnect(self._error_handler_id)
                    self._error_handler_id = None
                self._bus.set_flushing(True)
                self._bus.remove_signal_watch()
                logger.debug("Anura AudioPlayer: Bus flushed and signal watch removed")
            self._bus_watch_active = False
            self._bus = None

        if self.player:
            logger.info("Anura AudioPlayer: Setting state to NULL")
            try:
                self.player.set_state(Gst.State.NULL)
                self.player.get_state(Gst.CLOCK_TIME_NONE)
            except (GLib.Error, RuntimeError) as e:
                logger.debug(f"Anura AudioPlayer: Suppressed NULL state error: {e}")
            self.player = None
            logger.debug("Anura AudioPlayer: Resource cleanup complete")

    def stop(self) -> None:
        """Stop playback."""
        if self.player:
            logger.info("Anura AudioPlayer: Stopping playback")
            self.cleanup()

    def pause(self) -> None:
        """Pause playback."""
        if not self.player:
            return
        logger.info("Anura AudioPlayer: Setting state to PAUSED")
        ret = self.player.set_state(Gst.State.PAUSED)
        if ret == Gst.StateChangeReturn.ASYNC:
            self.player.get_state(500 * Gst.MSECOND)

    def resume(self) -> None:
        """Resume playback."""
        if not self.player:
            return
        logger.info("Anura AudioPlayer: Setting state to PLAYING (resume)")
        ret = self.player.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.ASYNC:
            self.player.get_state(500 * Gst.MSECOND)

    def is_playing(self) -> bool:
        """Check if player is in PLAYING state."""
        if not self.player:
            return False
        _, state, _ = self.player.get_state(0)
        return state == Gst.State.PLAYING

    def is_paused(self) -> bool:
        """Check if player is in PAUSED state."""
        if not self.player:
            return False
        _, state, _ = self.player.get_state(0)
        return state == Gst.State.PAUSED

    def toggle_pause(self) -> None:
        """Toggle between paused and playing states."""
        if not self.player:
            return

        _, state, _ = self.player.get_state(100 * Gst.MSECOND)
        if state == Gst.State.PLAYING:
            self.pause()
        elif state == Gst.State.PAUSED:
            self.resume()
        else:
            logger.debug(f"Anura AudioPlayer: toggle_pause in unexpected state {state.value_nick}")

    def cleanup(self) -> None:
        """Complete cleanup for shutdown."""
        with self._cleanup_lock:
            if self.player:
                logger.debug("Anura AudioPlayer: Performing shutdown cleanup")
                self._cleanup_resources()
