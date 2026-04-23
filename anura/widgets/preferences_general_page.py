# preferences_general_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gi.repository import Gtk, Adw, Gio
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.services.settings import settings

@Gtk.Template(resource_path=f'{RESOURCE_PREFIX}/ui/preferences_general.ui')
class PreferencesGeneralPage(Adw.PreferencesPage):
    __gtype_name__ = 'PreferencesGeneralPage'

    extra_language_combo: Adw.ComboRow = Gtk.Template.Child()
    autocopy_switch: Adw.SwitchRow = Gtk.Template.Child()
    autolinks_switch: Adw.SwitchRow = Gtk.Template.Child()
    # Nota: Il widget telemetry_switch deve essere rimosso o nascosto nel file .blp/.ui 
    # per evitare errori di template, o lasciato scollegato se non rimosso dal file UI.
    telemetry_switch: Adw.SwitchRow = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Utilizzo dell'istanza globale dei settings di Anura
        self.settings = settings

        # Binding dei settaggi funzionali
        self.settings.bind('autocopy', self.autocopy_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind('autolinks', self.autolinks_switch, 'active', Gio.SettingsBindFlags.DEFAULT)
        
        # La telemetria è stata disabilitata a livello logico. 
        # Se il widget esiste ancora nel file UI, lo rendiamo insensibile.
        self.telemetry_switch.set_active(False)
        self.telemetry_switch.set_sensitive(False)
        self.telemetry_switch.set_visible(False)

        # Inizializzazione della lista lingue extra
        self._setup_extra_languages()

    def _setup_extra_languages(self):
        downloaded_langs = language_manager.get_downloaded_languages()
        if not downloaded_langs:
            return

        self.extra_language_combo.set_model(Gtk.StringList.new(downloaded_langs))
        
        current_extra = self.settings.get_string('extra-language')
        current_name = language_manager.get_language(current_extra)
        
        try:
            extra_language_index = downloaded_langs.index(current_name)
            self.extra_language_combo.set_selected(extra_language_index)
        except ValueError:
            logger.warning(f"Lingua extra '{current_name}' non trovata tra i modelli installati.")
            
        self.extra_language_combo.connect('notify::selected-item', self._on_extra_language_changed)

    def _on_extra_language_changed(self, combo_row: Adw.ComboRow, _param):
        selected_item = combo_row.get_selected_item()
        if not selected_item:
            return
            
        lang_name = selected_item.get_string()
        lang_code = language_manager.get_language_code(lang_name)
        logger.debug(f'Anura: Lingua extra impostata su {lang_name} ({lang_code})')
        self.settings.set_string('extra-language', lang_code)