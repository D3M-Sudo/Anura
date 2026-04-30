# extracted_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _

import requests.exceptions
from gi.repository import Adw, GObject, Gtk
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.gobject_worker import GObjectWorker
from anura.services.settings import settings
from anura.services.share_service import ShareService
from anura.services.tts import TTSService, ttsservice
from anura.widgets.share_row import ShareRow


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/extracted_page.ui")
class ExtractedPage(Adw.NavigationPage):
    __gtype_name__ = "ExtractedPage"

    __gsignals__ = {
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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = settings

        for provider in ShareService.providers():
            self.share_list_box.append(ShareRow(provider))

        ttsservice.connect("stop", self._on_listen_end)

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
    def extracted_text(self, text: str):
        try:
            self.buffer.set_text(text)
        except (GLib.Error, ValueError) as e:
            logger.error(f"Error setting extracted text: {e}")

    def listen(self):
        self.swap_controls(True)
        self._set_spinner_active(True)

        ocr_lang = self.settings.get_string("active-language")
        lang = ttsservice.get_effective_language(ocr_lang)

        GObjectWorker.call(
            ttsservice.generate,
            (self.extracted_text, lang),
            callback=self._on_generated,
            errorback=self._on_generate_error,
        )

    def _set_spinner_active(self, active: bool) -> None:
        """Switch Stack between button and spinner."""
        self.listen_stack.set_visible_child_name("spinner" if active else "button")

    def _on_generate_error(self, error: Exception, traceback_str: str = None) -> None:
        """Handle generation errors (called on main thread by GObjectWorker)."""
        self._set_spinner_active(False)
        self.swap_controls(False)

        # Determine error message by type
        if isinstance(error, requests.exceptions.ConnectionError):
            msg = _("Network error. Please check your internet connection.")
        elif isinstance(error, requests.exceptions.Timeout):
            msg = _("Request timed out. Please try again.")
        else:
            msg = _("Failed to generate speech.")

        # Show toast via parent window
        window = self.get_root()
        if window and hasattr(window, "show_toast"):
            window.show_toast(msg)

    def listen_cancel(self):
        ttsservice.stop_speaking()
        self.swap_controls(False)

    def _on_generated(self, filepath):
        self._set_spinner_active(False)
        if not filepath:
            self.swap_controls(False)
            return
        ttsservice.play(filepath)

    def _on_listen_end(self, service: TTSService, success: bool):
        self.emit("on-listen-stop")
        self._set_spinner_active(False)
        self.swap_controls(False)

    def swap_controls(self, state: bool = False) -> None:
        """Enable or disable interactive controls during TTS playback."""
        self.grab_btn.set_sensitive(not state)
        self.text_copy_btn.set_sensitive(not state)
        self.listen_btn.set_visible(not state)
        self.listen_cancel_btn.set_visible(state)
