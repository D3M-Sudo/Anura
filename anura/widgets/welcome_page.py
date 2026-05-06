# welcome_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib

from gi.repository import Adw, Gtk

from anura.config import RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.services.settings import settings
from anura.types.language_item import LanguageItem
from anura.widgets.language_popover import LanguagePopover


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/welcome_page.ui")
class WelcomePage(Adw.NavigationPage):
    __gtype_name__ = "WelcomePage"

    spinner: Adw.Spinner = Gtk.Template.Child()
    welcome: Adw.StatusPage = Gtk.Template.Child()
    lang_combo: Gtk.MenuButton = Gtk.Template.Child()
    language_popover: LanguagePopover = Gtk.Template.Child()

    _language_changed_handler_id: int | None = None

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)

        self.settings = settings

        self._language_changed_handler_id = self.language_popover.connect('language-changed', self._on_language_changed)

        current_lang_code = self.settings.get_string("active-language")
        self.lang_combo.set_label(
            language_manager.get_language(current_lang_code)
        )

    def _on_language_changed(self, _: LanguagePopover, language: LanguageItem) -> None:
        self.lang_combo.set_label(language.title)
        self.settings.set_string("active-language", language.code)

    def do_destroy(self) -> None:
        """Clean up signal handlers to prevent memory leaks."""
        if self._language_changed_handler_id is not None:
            with contextlib.suppress(Exception):
                self.language_popover.disconnect(self._language_changed_handler_id)
            self._language_changed_handler_id = None
        super().do_destroy()
