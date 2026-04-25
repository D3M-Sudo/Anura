# preferences_general_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gi.repository import Gtk, Adw, Gio
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.services.settings import settings


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/ui/preferences_general.ui")
class PreferencesGeneralPage(Adw.PreferencesPage):
    __gtype_name__ = "PreferencesGeneralPage"

    extra_language_combo: Adw.ComboRow = Gtk.Template.Child()
    autocopy_switch: Adw.SwitchRow = Gtk.Template.Child()
    autolinks_switch: Adw.SwitchRow = Gtk.Template.Child()
    # FIX: telemetry_switch removed — it was declared as Template.Child() but the
    # widget no longer exists in preferences_general.blp (telemetry is fully
    # disabled in Anura). Keeping a Template.Child() for a non-existent widget
    # causes a Gtk.BuilderError at runtime.

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.settings = settings

        self.settings.bind("autocopy", self.autocopy_switch, "active", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("autolinks", self.autolinks_switch, "active", Gio.SettingsBindFlags.DEFAULT)

        self._setup_extra_languages()

    def _setup_extra_languages(self):
        downloaded_langs = language_manager.get_downloaded_languages()
        if not downloaded_langs:
            return

        self.extra_language_combo.set_model(Gtk.StringList.new(downloaded_langs))

        current_extra = self.settings.get_string("extra-language")
        current_name = language_manager.get_language(current_extra)

        try:
            index = downloaded_langs.index(current_name)
            self.extra_language_combo.set_selected(index)
        except ValueError:
            logger.warning(f"Anura: Extra language '{current_name}' not found among installed models.")

        self.extra_language_combo.connect("notify::selected-item", self._on_extra_language_changed)

    def _on_extra_language_changed(self, combo_row: Adw.ComboRow, _param):
        selected_item = combo_row.get_selected_item()
        if not selected_item:
            return
        lang_name = selected_item.get_string()
        lang_code = language_manager.get_language_code(lang_name)
        logger.debug(f"Anura: Extra language set to {lang_name} ({lang_code})")
        self.settings.set_string("extra-language", lang_code)
