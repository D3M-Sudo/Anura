# extracted_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib
from gettext import gettext as _
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
        # X11 Constraint: Ensure TTS service is properly initialized before any signal connections
        self._tts_service = get_tts_service()
        self._tts_stop_handler_id = None
        self._tts_paused_handler_id = None

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
        except (TypeError, RuntimeError, AttributeError) as e:
            logger.warning(f"Failed to connect TTS services: {e}")

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
        """Handle widget disposal - clean up TTS resources."""
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
            except Exception as e:
                logger.warning(f"Failed to cleanup TTS during dispose: {e}")
        super().do_dispose()

    @GObject.Property(type=str)
    def extracted_text(self) -> str:
        """Get the extracted text from the buffer."""
        return self.buffer.get_text(
            start=self.buffer.get_start_iter(),
            end=self.buffer.get_end_iter(),
            include_hidden_chars=False,
        )

    @extracted_text.setter
    def extracted_text(self, text: str) -> None:
        try:
            self.buffer.set_text(text)
        except (GLib.Error, ValueError) as e:
            logger.error(f"Error setting extracted text: {e}")

    def listen(self) -> None:
        """Start TTS playback for the extracted text."""
        tts_service_instance = get_tts_service()

        # Defensive check: ensure critical template components are loaded
        if not self.listen_stack:
            logger.error("ExtractedPage: listen_stack not found in template")
            return

        # If already paused, resume instead of starting over
        if self._tts_service and self.listen_stack.get_visible_child_name() == "pause":
            self.listen_pause()
            return

        # X11 Constraint: Set UI to generating state (Spinner) immediately and keep it active
        # during entire generate phase until GStreamer reaches PLAYING state
        self.swap_controls(False)  # Disable other controls
        self._set_spinner_active(True)

        # Store reference for cleanup if not already stored
        if self._tts_service is None:
            self._tts_service = tts_service_instance
            try:
                self._tts_stop_handler_id = self._tts_service.connect("stop", self._on_listen_end)
                self._tts_paused_handler_id = self._tts_service.connect("paused", self._on_paused)
            except (TypeError, RuntimeError, AttributeError) as e:
                logger.warning(f"Failed to connect TTS signals during listen: {e}")

        # Resolve TTS language: explicit user preference (tts-language) wins,
        # otherwise map the OCR language (Tesseract 3-letter, e.g. "ita") to
        # the gTTS code (ISO 639-1, e.g. "it"). Fetch the OCR language from
        # GSettings directly so this widget doesn't depend on an accessor on
        # its parent window.
        ocr_lang = self.settings.get_string("active-language")
        tts_lang = tts_service_instance.get_effective_language(ocr_lang)

        GObjectWorker.call(
            tts_service_instance.generate,
            (self.extracted_text, tts_lang),
            callback=self._on_generated,
            errorback=self._on_generate_error,
        )

    def _set_spinner_active(self, active: bool) -> None:
        """X11 Constraint: Switch Stack between button and spinner with fixed dimensions."""
        if active:
            # Ensure spinner has fixed dimensions to prevent UI shifting
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

    def _on_share(self, service: object, provider: str) -> None:
        """Share extracted text via external service."""
        share_service_instance = get_share_service()
        share_service_instance.share(provider, self.extracted_text)

    def _on_share_finished(self, _service: object, _success: bool) -> None:
        """Handle share completion - close the popover."""
        popover = self.share_button.get_popover()
        if popover:
            popover.popdown()

    def _on_generate_error(self, error: Exception, traceback_str: str | None = None) -> None:
        """Handle generation errors (called on main thread by GObjectWorker)."""
        # X11 Constraint: Ensure spinner is properly deactivated on error
        self._set_spinner_active(False)
        self.swap_controls(False)

        # Determine error message by type - check specific exceptions first
        if isinstance(error, TimeoutError):
            msg = _("Request timed out. Please try again.")
        elif isinstance(error, (requests.RequestException, OSError)):
            msg = _("Network error. Please check your internet connection.")
        else:
            msg = _("Text-to-speech failed. Please try again.")
        self.show_toast(msg)

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

    def _on_generated(self, filepath: str | None) -> None:
        if not filepath:
            self._set_spinner_active(False)
            self.swap_controls(False)
            return

        # X11 Constraint: Keep spinner active until GStreamer reaches PLAYING state
        # The spinner will be deactivated when we receive the "speak" signal
        # indicating the pipeline is ready
        tts_service_instance = get_tts_service()

        # Connect temporarily to the "speak" signal to know when GStreamer is ready
        def on_pipeline_ready(service, audio_file):
            # Deactivate spinner only when GStreamer pipeline reaches PLAYING state
            self._set_spinner_active(False)
            # Transition to playing controls
            self.swap_controls(True)
            # Disconnect this temporary handler
            service.disconnect(temp_handler_id)

        temp_handler_id = tts_service_instance.connect("speak", on_pipeline_ready)

        # Start playback - this will trigger the "speak" signal when ready
        tts_service_instance.play(filepath)

    def _on_listen(self, service: object, filepath: str) -> None:
        """Play TTS audio file."""
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
        # Disconnect share signal handler
        if hasattr(self, "_share_handler_id") and self._share_handler_id is not None:
            if hasattr(self, "_share_service") and self._share_service is not None:
                with contextlib.suppress(TypeError, RuntimeError, AttributeError):
                    self._share_service.disconnect(self._share_handler_id)
            self._share_handler_id = None

        # Check handler is not None AND service is valid before disconnecting
        if self._tts_service is not None:
            if self._tts_stop_handler_id is not None:
                with contextlib.suppress(TypeError, RuntimeError, AttributeError):
                    self._tts_service.disconnect(self._tts_stop_handler_id)
                self._tts_stop_handler_id = None
            if self._tts_paused_handler_id is not None:
                with contextlib.suppress(TypeError, RuntimeError, AttributeError):
                    self._tts_service.disconnect(self._tts_paused_handler_id)
                self._tts_paused_handler_id = None
        super().do_destroy()
