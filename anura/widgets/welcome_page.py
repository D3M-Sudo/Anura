# welcome_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gi.repository import Adw, Gtk, Gdk
from loguru import logger

from anura.config import APP_ID, RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.services.settings import settings
from anura.types.language_item import LanguageItem
from anura.widgets.language_popover import LanguagePopover


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/ui/welcome_page.ui")
class WelcomePage(Adw.NavigationPage):
    __gtype_name__ = "WelcomePage"

    spinner: Adw.Spinner = Gtk.Template.Child()
    welcome: Adw.StatusPage = Gtk.Template.Child()
    lang_combo: Gtk.MenuButton = Gtk.Template.Child()
    language_popover: LanguagePopover = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = settings

        try:
            logo_path = f"{RESOURCE_PREFIX}/icons/{APP_ID}.svg"
            logo = Gdk.Texture.new_from_resource(logo_path)
            self.welcome.set_paintable(logo)
        except Exception as e:
            logger.error(f"Could not load welcome logo from {logo_path}: {e}")

        self.language_popover.connect('language-changed', self._on_language_changed)

        current_lang_code = self.settings.get_string("active-language")
        self.lang_combo.set_label(
            language_manager.get_language(current_lang_code)
        )

    def _on_language_changed(self, _: LanguagePopover, language: LanguageItem):
        self.lang_combo.set_label(language.title)
        self.settings.set_string("active-language", language.code)