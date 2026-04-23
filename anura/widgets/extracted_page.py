# extracted_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gi.repository import Gtk, GObject, Adw
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.gobject_worker import GObjectWorker
from anura.services.share_service import ShareService
from anura.services.tts import ttsservice, TTSService
from anura.services.settings import settings
from anura.widgets.share_row import ShareRow


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/ui/extracted_page.ui")
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
    text_view: Gtk.TextView = Gtk.Template.Child()
    buffer: Gtk.TextBuffer = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = settings

        for provider in ShareService.providers():
            self.share_list_box.append(ShareRow(provider))

        ttsservice.connect("stop", self._on_listen_end)

    def do_hiding(self) -> None:
        """
        Clears the buffer when the user navigates back to ensure system stability.
        """
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
        except Exception as e:
            logger.error(f"Error setting extracted text: {e}")

    def listen(self):
        """
        Starts Text-to-Speech (TTS) for the extracted text.
        """
        self.swap_controls(True)
        lang = self.settings.get_string("active-language")

        GObjectWorker.call(
            ttsservice.generate,
            (self.extracted_text, lang[:2]),
            callback=self._on_generated,
        )

    def listen_cancel(self):
        """
        Stops the audio playback.
        """
        ttsservice.stop_speaking()
        self.swap_controls(False)

    def _on_generated(self, filepath):
        if not filepath:
            self.swap_controls(False)
            return

        ttsservice.play(filepath)

    def _on_listen_end(self, service: TTSService, success: bool):
        self.emit("on-listen-stop")
        self.swap_controls(False)

    def swap_controls(self, state: bool = False):
        """
        Handles widget states during audio playback.
        Currently a placeholder for future UI integrations.
        """
        pass