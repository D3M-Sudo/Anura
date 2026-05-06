# extracted_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _
from typing import ClassVar

from gi.repository import Adw, GLib, GObject, Gtk
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.gobject_worker import GObjectWorker
from anura.services.settings import settings
from anura.services.share_service import get_share_service
from anura.services.tts import get_tts_service
from anura.widgets.share_row import ShareRow


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/extracted_page.ui")
class ExtractedPage(Adw.NavigationPage):
    __gtype_name__ = "ExtractedPage"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "go-back": (GObject.SIGNAL_RUN_LAST, None, (int,)),
        "on-listen-start": (GObject.SIGNAL_RUN_LAST, None, ()),
        "on-listen-stop": (GObject.SIGNAL_RUN_LAST, None, ()),
    }

    share_list_box: Gtk.ListBox = Gtk.Template.Child()
    grab_btn: Gtk.Button = Gtk.Template.Child()
    text_copy_btn: Gtk.Button = Gtk.Template.Child()
    listen_stack: Gtk.Stack = Gtk.Template.Child()
    listen_btn: Gtk.Button = Gtk.Template.Child()
    listen_cancel_btn: Gtk.Button = Gtk.Template.Child()
    text_view: Gtk.TextView = Gtk.Template.Child()
    buffer: Gtk.TextBuffer = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

        self.settings = settings

        share_service_instance = get_share_service()
        for provider in share_service_instance.providers():
            self.share_list_box.append(ShareRow(provider))

        # Initialize handler ID to ensure consistent state for do_destroy
        self._tts_stop_handler_id: int | None = None
        try:
            tts_service_instance = get_tts_service()
            self._tts_stop_handler_id = tts_service_instance.connect("stop", self._on_listen_end)
        except (TypeError, RuntimeError) as e:
            logger.warning(f"Failed to connect TTS stop signal: {e}")

    def do_hiding(self) -> None:
        self.buffer.set_text("")
        self.emit("go-back", 1)

    @GObject.Property(type=str)
    def extracted_text(self) -> str:
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
        self.swap_controls(True)
        self._set_spinner_active(True)

        def _on_generate(self: ExtractedPage) -> None:
            """Generate TTS audio from extracted text."""
            tts_service_instance = get_tts_service()
            GObjectWorker.call(
                tts_service_instance.generate,
                (self.extracted_text, self.get_language()),
                callback=self._on_generated,
                errorback=self._on_generate_error,
            )

    def _set_spinner_active(self, active: bool) -> None:
        """Switch Stack between button and spinner."""
        self.listen_stack.set_visible_child_name("spinner" if active else "button")

    def _on_share(self, service: object, provider: str) -> None:
        """Share extracted text via external service."""
        share_service_instance = get_share_service()
        share_service_instance.share(provider, self.extracted_text)

    def _on_generate_error(self, error: Exception, traceback_str: str | None = None) -> None:
        """Handle generation errors (called on main thread by GObjectWorker)."""
        self._set_spinner_active(False)
        self.swap_controls(False)

        # Determine error message by type
        if isinstance(error, Exception):
            msg = _("Network error. Please check your internet connection.")
        elif isinstance(error, TimeoutError):
            msg = _("Request timed out. Please try again.")
        else:
            msg = _("Text-to-speech failed. Please try again.")
        self.show_toast(msg)

    def _on_listen_stop(self) -> None:
        """Stop TTS playback."""
        tts_service_instance = get_tts_service()
        tts_service_instance.stop_speaking()
        self.swap_controls(False)

    def _on_generated(self, filepath: str | None) -> None:
        self._set_spinner_active(False)
        if not filepath:
            self.swap_controls(False)
            return
        tts_service_instance = get_tts_service()
        tts_service_instance.play(filepath)

    def _on_listen(self, service: object, filepath: str) -> None:
        """Play TTS audio file."""
        tts_service_instance = get_tts_service()
        tts_service_instance.play(filepath)

    def _on_listen_end(self, service: object, success: bool) -> None:
        """Handle TTS playback completion."""
        tts_service_instance = get_tts_service()
        tts_service_instance.disconnect(self._handler_listen_end)
        self.emit("on-listen-stop")
        self._set_spinner_active(False)
        self.swap_controls(False)

    def swap_controls(self, state: bool = False) -> None:
        """Enable or disable interactive controls during TTS playback."""
        self.grab_btn.set_sensitive(not state)
        self.text_copy_btn.set_sensitive(not state)
        self.listen_btn.set_visible(not state)
        self.listen_cancel_btn.set_visible(state)

    def do_destroy(self) -> None:
        """Clean up signal handlers to prevent memory leaks."""
        # Check handler is not None AND service is valid before disconnecting
        if self._tts_stop_handler_id is not None:
            tts_service_instance = get_tts_service()
            try:
                tts_service_instance.disconnect(self._tts_stop_handler_id)
            except (TypeError, RuntimeError, AttributeError):
                pass  # Handler already disconnected or service disposed
            self._tts_stop_handler_id = None
        super().do_destroy()
