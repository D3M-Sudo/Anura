import asyncio
import datetime
import sys
from gettext import gettext as _

from gi.events import GLibEventLoopPolicy
from gi.repository import Gtk, Gio, GLib, Notify, Adw, GdkPixbuf, Gdk, GObject
from loguru import logger

from anura.config import RESOURCE_PREFIX, APP_ID
from anura.language_manager import language_manager
from anura.services.clipboard_service import clipboard_service
from anura.services.screenshot_service import ScreenshotService
from anura.services.settings import settings
from anura.window import AnuraWindow


class AnuraApplication(Adw.Application):
    __gtype_name__ = 'AnuraApplication'

    def __init__(self, version=None):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.backend = None
        self.version = version
        self.settings = settings

        self.add_main_option(
            'extract_to_clipboard',
            ord('e'),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            _("Extract directly into the clipboard"),
            None
        )

        language_manager.init_tessdata()
        Notify.init(APP_ID)

    def do_startup(self, *args, **kwargs):
        Adw.Application.do_startup(self)

        self.backend = ScreenshotService()
        self.backend.connect('decoded', self.on_decoded)

        self._setup_actions()

        GLib.set_application_name("Anura OCR")
        GLib.set_prgname(APP_ID)

    def _setup_actions(self):
        self.create_action('get_screenshot', self.get_screenshot, ['<primary>g'])
        self.create_action('get_screenshot_and_copy', self.get_screenshot_and_copy, ['<primary><shift>g'])
        self.create_action('copy_to_clipboard', self.on_copy_to_clipboard, ['<primary>c'])
        self.create_action('open_image', self.open_image, ['<primary>o'])
        self.create_action('paste_from_clipboard', self.on_paste_from_clipboard, ['<primary>v'])
        self.create_action('listen', self.on_listen, ['<primary>l'])
        self.create_action('listen_cancel', self.on_listen_cancel, ['<primary><shift>l'])
        self.create_action('shortcuts', self.on_shortcuts, ['<primary>question'])
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q', '<primary>w'])
        self.create_action('preferences', self.on_preferences, ['<primary>comma'])
        self.create_action('about', self.on_about)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = AnuraWindow(application=self, backend=self.backend)
        win.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict().end().unpack()

        if "extract_to_clipboard" in options:
            logger.info("Anura: CLI Extraction triggered.")
            self.backend.capture(self.settings.get_string("active-language"), copy=True)
            return 1

        self.activate()
        return 0

    def on_preferences(self, _action, _param) -> None:
        self.get_active_window().show_preferences()

    def on_about(self, _action, _param):
        about_window = Adw.AboutDialog(
            application_name="Anura",
            application_icon=APP_ID,
            version=self.version,
            copyright=f'© {datetime.date.today().year} D3M-Sudo & Anura Contributors',
            website="https://github.com/d3msudo/anura",
            license_type=Gtk.License.MIT,
            developers=["Andrey Maksimov", "D3M-Sudo"],
            designers=["Andrey Maksimov"],
            release_notes=_("Technical and rigorous OCR tool optimized for Linux.")
        )
        about_window.present(self.props.active_window)

    def on_shortcuts(self, _action, _param):
        window = self.get_active_window()
        if window:
            window.show_shortcuts()

    def on_copy_to_clipboard(self, _action, _param) -> None:
        self.get_active_window().on_copy_to_clipboard(self)

    def get_screenshot(self, _action, _param) -> None:
        self.get_active_window().get_screenshot()

    def get_screenshot_and_copy(self, _action, _param) -> None:
        self.get_active_window().get_screenshot(copy=True)

    def open_image(self, _action, _param) -> None:
        self.get_active_window().open_image()

    def on_paste_from_clipboard(self, _action, _param) -> None:
        self.get_active_window().on_paste_from_clipboard(self)

    def on_decoded(self, _sender, text: str, copy: bool) -> None:
        if not text:
            notification = Notify.Notification.new(
                summary='Anura OCR',
                body=_("No text found. Try to grab another region.")
            )
            notification.show()
            return

        if copy:
            clipboard_service.set(text)
            notification = Notify.Notification.new(
                summary='Anura OCR',
                body=_("Text extracted and copied to clipboard.")
            )
            notification.show()
        else:
            logger.debug(f'Extracted: {text}')

    def on_listen(self, _sender, _event):
        self.get_active_window().on_listen()

    def on_listen_cancel(self, _sender, _event):
        self.get_active_window().on_listen_cancel()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    asyncio.set_event_loop_policy(GLibEventLoopPolicy())
    app = AnuraApplication(version)
    return app.run(sys.argv)