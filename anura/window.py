from gettext import gettext as _
from io import BytesIO
from mimetypes import guess_type
from typing import List
from urllib.parse import urlparse

from gi.repository import Gtk, Adw, Gio, GLib, Gdk, GObject
from loguru import logger

from anura.config import APP_ID, RESOURCE_PREFIX
from anura.gobject_worker import GObjectWorker
from anura.language_manager import language_manager
from anura.services.clipboard_service import clipboard_service, ClipboardService
from anura.services.screenshot_service import ScreenshotService
from anura.services.share_service import ShareService
from anura.widgets.extracted_page import ExtractedPage
from anura.widgets.preferences_dialog import PreferencesDialog
from anura.widgets.welcome_page import WelcomePage


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/ui/window.ui")
class AnuraWindow(Adw.ApplicationWindow):
    __gtype_name__ = "AnuraWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    split_view: Adw.NavigationSplitView = Gtk.Template.Child()
    welcome_page: WelcomePage = Gtk.Template.Child()
    extracted_page: ExtractedPage = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gtk.Application.get_default().props.settings
        
        language_manager.active_language = language_manager.get_language_item(
            self.settings.get_string("active-language")
        )

        self._setup_geometry()
        self._setup_controllers()
        self.set_icon_name(APP_ID)

        self.backend = ScreenshotService()
        self.backend.connect("decoded", self.on_shot_done)
        self.backend.connect("error", self.on_shot_error)

        self.extracted_page.connect("go-back", self.show_welcome_page)
        clipboard_service.connect("paste_from_clipboard", self._on_paste_from_clipboard)

    def _setup_geometry(self):
        width = self.settings.get_int("window-width")
        height = self.settings.get_int("window-height")
        self.set_default_size(width, height)

    def _setup_controllers(self):
        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_dnd_drop)
        self.split_view.add_controller(drop_target)

    def get_language(self) -> str:
        active = self.settings.get_string("active-language")
        extra = self.settings.get_string("extra-language")
        return f"{active}+{extra}" if extra else active

    def get_screenshot(self, copy: bool = False) -> None:
        self.extracted_page.listen_cancel()
        lang = self.get_language()
        self.hide() 
        self.backend.capture(lang, copy)

    def on_shot_done(self, _sender, text: str, copy: bool) -> None:
        self.present()
        self.welcome_page.spinner.set_visible(False)
        
        if not text:
            return

        try:
            self.extracted_page.extracted_text = text

            if self.settings.get_boolean("autocopy") or copy:
                clipboard_service.set(text)
                self.show_toast(_("Text copied to clipboard"))

            if self.uri_validator(text):
                if self.settings.get_boolean("autolinks"):
                    launcher = Gtk.UriLauncher.new(text)
                    launcher.launch(self, None, None)
                    self.show_toast(_("URL opened automatically"))
                else:
                    self._show_url_toast(text)

            self.split_view.set_show_content(True)

        except Exception as e:
            logger.error(f"Anura UI Error: {e}")

    def on_shot_error(self, _sender, message: str) -> None:
        self.present()
        self.welcome_page.spinner.set_visible(False)
        if message:
            self.show_toast(message)

    def open_image(self):
        dialog = Gtk.FileDialog()
        dialog.set_title(_("Choose an image for extraction"))
        
        img_filter = Gtk.FileFilter()
        img_filter.set_name(_("Images"))
        img_filter.add_pixbuf_formats()
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(img_filter)
        dialog.set_filters(filters)

        dialog.open(self, None, self._on_open_image_result)

    def _on_open_image_result(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.welcome_page.spinner.set_visible(True)
                GObjectWorker.call(self.backend.decode_image, (self.get_language(), file.get_path()))
        except Exception as e:
            logger.debug(f"File selection cancelled or failed: {e}")

    def on_dnd_drop(self, _target, value: Gdk.FileList, _x, _y) -> bool:
        files = value.get_files()
        if not files:
            return False

        item = files[0]
        mimetype, _ = guess_type(item.get_path())
        
        if mimetype and mimetype.startswith("image"):
            self.welcome_page.spinner.set_visible(True)
            GObjectWorker.call(self.backend.decode_image, (self.get_language(), item.get_path()))
            return True
        
        self.show_toast(_("Unsupported file format."))
        return False

    def _on_paste_from_clipboard(self, _service, texture: Gdk.Texture):
        self.welcome_page.spinner.set_visible(True)
        png_bytes = BytesIO(texture.save_to_png_bytes().get_data())
        GObjectWorker.call(self.backend.decode_image, (self.get_language(), png_bytes))

    def do_close_request(self) -> bool:
        width, height = self.get_default_size()
        self.settings.set_int("window-width", width)
        self.settings.set_int("window-height", height)
        return False

    def show_preferences(self):
        dialog = PreferencesDialog()
        dialog.present(self)

    def show_shortcuts(self):
        try:
            builder = Gtk.Builder.new_from_resource(f"{RESOURCE_PREFIX}/ui/shortcuts.ui")
            shortcuts_window = builder.get_object("shortcuts")
            
            if shortcuts_window:
                shortcuts_window.set_transient_for(self)
                shortcuts_window.present()
            else:
                logger.error("Failed to locate 'shortcuts' object in the UI resource.")
        except Exception as e:
            logger.error(f"An error occurred while loading shortcuts: {e}")

    def show_welcome_page(self, *_):
        self.split_view.set_show_content(False)
        self.extracted_page.listen_cancel()

    def show_toast(self, title: str, priority=Adw.ToastPriority.NORMAL):
        self.toast_overlay.add_toast(Adw.Toast(title=title, priority=priority))

    def _show_url_toast(self, url: str):
        toast = Adw.Toast(title=_("Text contains a link"), button_label=_("Open"))
        toast.set_detailed_action_name(f'app.show_uri("{url}")')
        self.toast_overlay.add_toast(toast)

    def uri_validator(self, text: str) -> bool:
        try:
            res = urlparse(text.strip())
            return all([res.scheme, res.netloc])
        except Exception:
            return False