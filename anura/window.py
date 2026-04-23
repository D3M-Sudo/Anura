# window.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

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
    """
    Finestra principale di Anura OCR.
    Gestisce l'integrazione tra l'input utente (DND, Clipboard, Screenshot)
    e il motore OCR in background.
    """
    __gtype_name__ = "AnuraWindow"

    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()
    split_view: Adw.NavigationSplitView = Gtk.Template.Child()
    welcome_page: WelcomePage = Gtk.Template.Child()
    extracted_page: ExtractedPage = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = Gtk.Application.get_default().props.settings
        
        # Sincronizzazione lingua attiva
        language_manager.active_language = language_manager.get_language_item(
            self.settings.get_string("active-language")
        )

        # Inizializzazione controlli finestra
        self._setup_geometry()
        self._setup_controllers()
        self.set_icon_name(APP_ID)

        # Inizializzazione Backend OCR
        self.backend = ScreenshotService()
        self.backend.connect("decoded", self.on_shot_done)
        self.backend.connect("error", self.on_shot_error)

        # Connessione segnali UI
        self.extracted_page.connect("go-back", self.show_welcome_page)
        clipboard_service.connect("paste_from_clipboard", self._on_paste_from_clipboard)

    def _setup_geometry(self):
        """Ripristina le dimensioni della finestra salvate."""
        width = self.settings.get_int("window-width")
        height = self.settings.get_int("window-height")
        self.set_default_size(width, height)

    def _setup_controllers(self):
        """Configura il controller per il Drag-and-Drop."""
        drop_target = Gtk.DropTarget.new(type=Gdk.FileList, actions=Gdk.DragAction.COPY)
        drop_target.connect("drop", self.on_dnd_drop)
        self.split_view.add_controller(drop_target)

    def get_language(self) -> str:
        """Costruisce la stringa delle lingue per Tesseract (es. 'ita+eng')."""
        active = self.settings.get_string("active-language")
        extra = self.settings.get_string("extra-language")
        return f"{active}+{extra}" if extra else active

    def get_screenshot(self, copy: bool = False) -> None:
        """Avvia la cattura schermo tramite portali XDG."""
        self.extracted_page.listen_cancel()
        lang = self.get_language()
        self.hide() # Nasconde la finestra per non ostruire lo screenshot
        self.backend.capture(lang, copy)

    def on_shot_done(self, _sender, text: str, copy: bool) -> None:
        """Gestisce il successo dell'OCR."""
        self.present()
        self.welcome_page.spinner.set_visible(False)
        
        if not text:
            return

        try:
            self.extracted_page.extracted_text = text

            # Logica Auto-Copy
            if self.settings.get_boolean("autocopy") or copy:
                clipboard_service.set(text)
                self.show_toast(_("Testo copiato negli appunti"))

            # Logica Auto-Links
            if self.uri_validator(text):
                if self.settings.get_boolean("autolinks"):
                    launcher = Gtk.UriLauncher.new(text)
                    launcher.launch(self, None, None)
                    self.show_toast(_("URL aperto automaticamente"))
                else:
                    self._show_url_toast(text)

            self.split_view.set_show_content(True)

        except Exception as e:
            logger.error(f"Anura UI Error: {e}")

    def on_shot_error(self, _sender, message: str) -> None:
        """Gestisce errori del backend o cancellazione utente."""
        self.present()
        self.welcome_page.spinner.set_visible(False)
        if message:
            self.show_toast(message)

    def open_image(self):
        """Apre il selettore file nativo."""
        dialog = Gtk.FileDialog()
        dialog.set_title(_("Scegli un'immagine per l'estrazione"))
        
        # Filtri immagini
        img_filter = Gtk.FileFilter()
        img_filter.set_name(_("Immagini"))
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
            logger.debug(f"Apertura file annullata: {e}")

    def on_dnd_drop(self, _target, value: Gdk.FileList, _x, _y) -> bool:
        files = value.get_files()
        if not files: return False

        item = files[0]
        mimetype, _ = guess_type(item.get_path())
        
        if mimetype and mimetype.startswith("image"):
            self.welcome_page.spinner.set_visible(True)
            GObjectWorker.call(self.backend.decode_image, (self.get_language(), item.get_path()))
            return True
        
        self.show_toast(_("Formato file non supportato."))
        return False

    def _on_paste_from_clipboard(self, _service, texture: Gdk.Texture):
        """Gestisce l'estrazione da immagini incollate (Ctrl+V)."""
        self.welcome_page.spinner.set_visible(True)
        # Convertiamo la texture in bytes per il backend OCR
        png_bytes = BytesIO(texture.save_to_png_bytes().get_data())
        GObjectWorker.call(self.backend.decode_image, (self.get_language(), png_bytes))

    def do_close_request(self) -> bool:
        """Salva lo stato della finestra prima di chiudere."""
        width, height = self.get_default_size()
        self.settings.set_int("window-width", width)
        self.settings.set_int("window-height", height)
        return False

    def show_preferences(self):
        dialog = PreferencesDialog()
        dialog.present(self)

    def show_welcome_page(self, *_):
        self.split_view.set_show_content(False)
        self.extracted_page.listen_cancel()

    def show_toast(self, title: str, priority=Adw.ToastPriority.NORMAL):
        self.toast_overlay.add_toast(Adw.Toast(title=title, priority=priority))

    def _show_url_toast(self, url: str):
        toast = Adw.Toast(title=_("Il testo contiene un link"), button_label=_("Apri"))
        toast.set_detailed_action_name(f'app.show_uri("{url}")')
        self.toast_overlay.add_toast(toast)

    def uri_validator(self, text: str) -> bool:
        try:
            res = urlparse(text.strip())
            return all([res.scheme, res.netloc])
        except:
            return False