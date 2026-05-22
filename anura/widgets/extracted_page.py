# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from gettext import gettext as _
from gettext import ngettext
from typing import ClassVar

import gi

# Set GTK version requirements before imports
gi.require_version("Adw", "1")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, GLib, GObject, Gtk  # noqa: E402
from loguru import logger  # noqa: E402
import requests  # noqa: E402

from anura.config import RESOURCE_PREFIX  # noqa: E402
from anura.gobject_worker import GObjectWorker  # noqa: E402
from anura.services.settings import settings  # noqa: E402
from anura.services.share_service import get_share_service  # noqa: E402
from anura.services.tts import get_tts_service  # noqa: E402
from anura.widgets.share_row import ShareRow  # noqa: E402


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/extracted_page.ui")
class ExtractedPage(Adw.NavigationPage):
    __gtype_name__ = "ExtractedPage"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "go-back": (GObject.SignalFlags.RUN_LAST, None, (int,)),
        "on-listen-start": (GObject.SignalFlags.RUN_LAST, None, ()),
        "on-listen-stop": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    stats_label: Gtk.Label = Gtk.Template.Child()
    share_list_box: Gtk.ListBox = Gtk.Template.Child()
    grab_btn: Gtk.Button = Gtk.Template.Child()
    text_copy_btn: Gtk.Button = Gtk.Template.Child()
    listen_stack: Gtk.Stack = Gtk.Template.Child()
    listen_btn: Gtk.Button = Gtk.Template.Child()
    listen_cancel_btn: Gtk.Button = Gtk.Template.Child()
    listen_pause_btn: Gtk.Button = Gtk.Template.Child()
    listen_spinner: Gtk.Spinner = Gtk.Template.Child()
    share_button: Gtk.MenuButton = Gtk.Template.Child()
    text_view: Gtk.TextView = Gtk.Template.Child()
    buffer: Gtk.TextBuffer = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        # Pre-initialize attributes to avoid AttributeError during failed template init
        self.settings = settings
        self._share_service = None
        self._share_handler_id = None
        # TTS service reference — initialized post-super() to avoid pre-template access
        self._tts_service = None
        self._tts_stop_handler_id = None
        self._tts_paused_handler_id = None
        self._tts_error_handler_id = None
        self._buffer_handler_id = None
        self._is_generating_tts = False

        super().__init__(**kwargs)

        # Defensive check: ensure critical template components are loaded
        if not self.share_list_box:
            logger.error("ExtractedPage: share_list_box not found in template")
        else:
            self._share_service = get_share_service()
            for provider in self._share_service.providers():
                self.share_list_box.append(ShareRow(provider))
            # Connect to share signal to automatically popdown the menu
            self._share_handler_id = self._share_service.connect("share", self._on_share_finished)

        try:
            self._tts_service = get_tts_service()
            self._tts_stop_handler_id = self._tts_service.connect("stop", self._on_listen_end)
            self._tts_paused_handler_id = self._tts_service.connect("paused", self._on_paused)
            self._tts_error_handler_id = self._tts_service.connect("error", self._on_tts_error)
        except (TypeError, RuntimeError, AttributeError) as e:
            logger.warning(f"Failed to connect TTS services: {e}")

        self._buffer_handler_id = self.buffer.connect("changed", self._on_buffer_changed)
        # GTK4 Layout Fix: Force reflow when widget is mapped to ensure correct Pango layout
        self.text_view.connect("map", lambda _: self._force_reflow())

    def _force_reflow(self) -> None:
        """Force the TextView to recalculate its layout and reflow text.

        This addresses a GTK4/Pango issue where programmatic text injection
        doesn't always trigger a re-layout until manual interaction occurs.
        """
        if not self.text_view:
            return

        # Strategy: Toggle wrap-mode to invalidate Pango cache and force re-layout.
        # This is more reliable in GTK4 than queue_resize() alone for programmatic text injection.
        current_wrap = self.text_view.get_wrap_mode()
        self.text_view.set_wrap_mode(Gtk.WrapMode.NONE)
        self.text_view.set_wrap_mode(current_wrap)
        self.text_view.queue_resize()

    def _on_buffer_changed(self, buffer: Gtk.TextBuffer) -> None:
        """Update character and word count in the status bar label."""
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        has_text = bool(text.strip()) if text else False

        # Update action sensitivity based on text presence
        if self.text_copy_btn:
            self.text_copy_btn.set_sensitive(has_text)
        if self.share_button:
            self.share_button.set_sensitive(has_text)
        if self.listen_btn:
            self.listen_btn.set_sensitive(has_text)

        char_count = len(text) if text else 0
        word_count = len(text.split()) if text else 0

        words_text = ngettext("{n} word", "{n} words", word_count).format(n=word_count)
        chars_text = ngettext("{n} character", "{n} characters", char_count).format(n=char_count)

        # Construct the stats label using a single translatable string to ensure
        # translators can adjust the ordering and separator if necessary.
        self.stats_label.set_text(_("{words} | {chars}").format(words=words_text, chars=chars_text))

    def show_copy_feedback(self) -> None:
        """Temporarily change the copy button icon to a checkmark for UX feedback."""
        if not self.text_copy_btn:
            return

        # Defensive: if already showing feedback, don't nested-capture the checkmark
        if self.text_copy_btn.get_icon_name() == "emblem-ok-symbolic":
            return

        # Store original icon and switch to checkmark
        original_icon = self.text_copy_btn.get_icon_name()
        self.text_copy_btn.set_icon_name("emblem-ok-symbolic")

        # Revert icon after 2 seconds
        GLib.timeout_add_seconds(2, self._reset_copy_icon, original_icon)

    def _reset_copy_icon(self, icon_name: str) -> bool:
        """Helper to reset copy button icon."""
        try:
            if self.text_copy_btn and self.text_copy_btn.get_icon_name() == "emblem-ok-symbolic":
                # Only reset if it's still showing the checkmark (don't overwrite newer state)
                self.text_copy_btn.set_icon_name(icon_name)
        except Exception:
            logger.exception("Anura: Failed to reset copy icon")
        return GLib.SOURCE_REMOVE

    def do_hiding(self) -> None:
        """Handle widget hiding event."""
        self.buffer.set_text("")
        self.emit("go-back", 1)

    def do_unmap(self) -> None:
        """Handle widget unmapping - stop TTS playback when widget is no longer visible."""
        # X11 Constraint: Stop TTS immediately when widget is unmapped to prevent zombie audio
        if self._tts_service:
            try:
                self._tts_service.stop_speaking()
            except Exception as e:
                logger.warning(f"Failed to stop TTS during unmap: {e}")
        Gtk.Widget.do_unmap(self)

    def do_dispose(self) -> None:
        """Handle widget disposal - clean up TTS and share resources."""
        # X11 Constraint: Ensure TTS is stopped and resources are cleaned up
        if self._tts_service:
            try:
                self._tts_service.stop_speaking()
                # Disconnect signal handlers
                if self._tts_stop_handler_id:
                    self._tts_service.disconnect(self._tts_stop_handler_id)
                    self._tts_stop_handler_id = None
                if self._tts_paused_handler_id:
                    self._tts_service.disconnect(self._tts_paused_handler_id)
                    self._tts_paused_handler_id = None
                if self._tts_error_handler_id:
                    self._tts_service.disconnect(self._tts_error_handler_id)
                    self._tts_error_handler_id = None
            except Exception as e:
                logger.warning(f"Failed to cleanup TTS during dispose: {e}")

        # Disconnect share service signal handler
        if self._share_service and self._share_handler_id:
            try:
                self._share_service.disconnect(self._share_handler_id)
                self._share_handler_id = None
            except (TypeError, RuntimeError) as e:
                logger.warning(f"Failed to cleanup share service during dispose: {e}")

        # Disconnect internal buffer handler
        if self._buffer_handler_id:
            with contextlib.suppress(TypeError, RuntimeError):
                self.buffer.disconnect(self._buffer_handler_id)
            self._buffer_handler_id = None

        super().do_dispose()

    @GObject.Property(type=str)
    def extracted_text(self) -> str:
        """Get the extracted text from the buffer."""
        return self.buffer.get_text(
            start=self.buffer.get_start_iter(),
            end=self.buffer.get_end_iter(),
            include_hidden_chars=False,
        )

    @extracted_text.setter  # type: ignore[no-redef]
    def extracted_text(self, text: str) -> None:
        try:
            self.buffer.set_text(text)
            self._force_reflow()
        except (GLib.Error, ValueError) as e:
            logger.error(f"Error setting extracted text: {e}")

    def listen(self) -> None:
        """Start TTS playback for the extracted text."""
        # Prevent concurrent TTS generation requests
        if self._is_generating_tts:
            logger.warning("Anura TTS: Generation already in progress, ignoring request.")
            return

        tts_service_instance = get_tts_service()

        # Defensive check: ensure critical template components are loaded
        if not self.listen_stack:
            logger.error("ExtractedPage: listen_stack not found in template")
            return

        # If already paused, resume instead of starting over
        if self._tts_service and self.listen_stack.get_visible_child_name() == "pause":
            self.listen_pause()
            return

        self._is_generating_tts = True

        # X11 Constraint: Set UI to generating state (Spinner) immediately and keep it active
        # during entire generate phase until GStreamer reaches PLAYING state
        self.swap_controls(False)  # Disable other controls
        self._set_spinner_active(True)

        # Store reference for cleanup if not already stored
        if self._tts_service is None:
            self._tts_service = tts_service_instance
            # Only connect handlers if they are not already connected from __init__
            try:
                if self._tts_stop_handler_id is None:
                    self._tts_stop_handler_id = self._tts_service.connect("stop", self._on_listen_end)
                if self._tts_paused_handler_id is None:
                    self._tts_paused_handler_id = self._tts_service.connect("paused", self._on_paused)
                if self._tts_error_handler_id is None:
                    self._tts_error_handler_id = self._tts_service.connect("error", self._on_tts_error)
            except (TypeError, RuntimeError, AttributeError) as e:
                logger.warning(f"Failed to connect TTS signals during listen: {e}")

        # Resolve TTS language: explicit user preference (tts-language) wins,
        # otherwise map the OCR language (Tesseract 3-letter, e.g. "ita") to
        # the gTTS code (ISO 639-1, e.g. "it"). Fetch the OCR language from
        # GSettings directly so this widget doesn't depend on an accessor on
        # its parent window.
        ocr_lang = self.settings.get_string("active-language")
        tts_lang = tts_service_instance.get_effective_language(ocr_lang)

        if not tts_lang:
            self._is_generating_tts = False
            self._set_spinner_active(False)
            self.swap_controls(False)
            msg = _("Text-to-speech is not available for this language")
            window = self.get_root()
            if window and hasattr(window, "show_toast"):
                window.show_toast(msg)
            return

        try:
            GObjectWorker.call(
                tts_service_instance.generate,
                (self.extracted_text, tts_lang),
                callback=self._on_generated,
                errorback=self._on_generate_error,
            )
        except Exception:
            self._is_generating_tts = False
            self._set_spinner_active(False)
            self.swap_controls(False)
            logger.exception("Anura TTS: Failed to initiate speech generation")

    def _set_spinner_active(self, active: bool) -> None:
        """X11 Constraint: Switch Stack between button and spinner."""
        if active:
            # Ensure spinner is properly aligned to prevent UI shifting
            if self.listen_stack:
                self.listen_stack.set_visible_child_name("spinner")
            # Explicitly start the spinner animation
            if self.listen_spinner:
                self.listen_spinner.start()
        else:
            # Stop spinner animation before switching
            if self.listen_spinner:
                self.listen_spinner.stop()
            # Note: Don't set stack here - let swap_controls handle it to avoid conflicts

    def _on_share_finished(self, _service: object, _success: bool) -> None:
        """Handle share completion - close the popover."""
        popover = self.share_button.get_popover()
        if popover:
            popover.popdown()

    def _on_generate_error(self, error: Exception, traceback_str: str | None = None) -> None:
        """Handle generation errors (called on main thread by GObjectWorker)."""
        self._is_generating_tts = False
        # Force stack back to button state on error — the spinner must not persist.
        # We bypass _set_spinner_active + swap_controls here because swap_controls
        # intentionally refuses to switch away from "spinner" (to avoid conflicts
        # during normal flow). On error, we need an unconditional reset.
        if self.listen_spinner:
            self.listen_spinner.stop()
        if self.listen_stack:
            self.listen_stack.set_visible_child_name("button")
        self.swap_controls(False)

        # Determine error message by type - check specific exceptions first
        if isinstance(error, TimeoutError):
            msg = _("Request timed out. Please try again.")
        elif isinstance(error, (requests.RequestException, OSError)):
            msg = _("Network error. Please check your internet connection.")
        else:
            msg = _("Text-to-speech failed. Please try again.")

        # Get the root window and call its show_toast method
        window = self.get_root()
        if window and hasattr(window, "show_toast"):
            window.show_toast(msg)

    def listen_cancel(self) -> None:
        """Stop TTS playback (public method)."""
        self._on_listen_stop()

    def _on_listen_stop(self) -> None:
        """Stop TTS playback."""
        tts_service_instance = get_tts_service()
        tts_service_instance.stop_speaking()
        self.swap_controls(False)

    def listen_pause(self) -> None:
        """Pause/Resume TTS playback."""
        tts_service_instance = get_tts_service()
        tts_service_instance.toggle_pause()

    def _on_paused(self, _service: object, is_paused: bool) -> None:
        """Handle TTS pause/resume signal."""
        if self.listen_pause_btn:
            icon = "media-playback-start-symbolic" if is_paused else "media-playback-pause-symbolic"
            self.listen_pause_btn.set_icon_name(icon)

    def _on_tts_error(self, _service: object, message: str) -> None:
        """Handle TTS error signal."""
        self._on_listen_end(_service, False)
        window = self.get_root()
        if window and hasattr(window, "show_toast"):
            window.show_toast(message)

    def _on_generated(self, filepath: str | None) -> None:
        self._is_generating_tts = False
        if not filepath:
            self._set_spinner_active(False)
            self.swap_controls(False)
            return

        # Deactivate spinner immediately when generation is complete
        self._set_spinner_active(False)
        # Show pause/stop controls
        self.swap_controls(True)
        # Start playback
        tts_service_instance = get_tts_service()
        tts_service_instance.play(filepath)

    def _on_listen_end(self, service: object, success: bool) -> None:
        """Handle TTS playback completion."""
        # Don't disconnect the signal handler - it should persist for multiple TTS operations
        self.emit("on-listen-stop")
        self._set_spinner_active(False)
        self.swap_controls(False)

        # Reset pause button icon
        if self.listen_pause_btn:
            self.listen_pause_btn.set_icon_name("media-playback-pause-symbolic")

    def swap_controls(self, state: bool = False) -> None:
        """Enable or disable interactive controls during TTS playback."""
        if self.grab_btn:
            self.grab_btn.set_sensitive(not state)
        if self.text_copy_btn:
            self.text_copy_btn.set_sensitive(not state)
        if self.listen_stack:
            # Unified stack management: handle both pause/play and spinner states
            if state:
                self.listen_stack.set_visible_child_name("pause")
            else:
                # Check if spinner is active before switching to button
                current_child = self.listen_stack.get_visible_child_name()
                if current_child != "spinner":
                    self.listen_stack.set_visible_child_name("button")

    def do_destroy(self) -> None:
        """Clean up signal handlers to prevent memory leaks."""
        # do_dispose() already handles TTS and share service cleanup
        super().do_destroy()
