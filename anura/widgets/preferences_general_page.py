# preferences_general_page.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _

from gi.repository import Adw, Gio, Gtk
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.language_manager import language_manager
from anura.services.settings import settings
from anura.services.tts import ttsservice
from anura.utils.signal_manager import SignalManagerMixin


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/preferences_general.ui")
class PreferencesGeneralPage(Adw.PreferencesPage, SignalManagerMixin):
    __gtype_name__ = "PreferencesGeneralPage"

    extra_language_combo: Adw.ComboRow = Gtk.Template.Child()
    autocopy_switch: Adw.SwitchRow = Gtk.Template.Child()
    autolinks_switch: Adw.SwitchRow = Gtk.Template.Child()
    volume_row: Adw.SpinRow = Gtk.Template.Child()
    tts_language_combo: Adw.ComboRow = Gtk.Template.Child()
    # FIX: telemetry_switch removed — it was declared as Template.Child() but the
    # widget no longer exists in preferences_general.blp (telemetry is fully
    # disabled in Anura). Keeping a Template.Child() for a non-existent widget
    # causes a Gtk.BuilderError at runtime.

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self.settings = settings

        self.settings.bind("autocopy", self.autocopy_switch, "active", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("autolinks", self.autolinks_switch, "active", Gio.SettingsBindFlags.DEFAULT)

        self._setup_extra_languages()

        # Update combo when languages are installed or removed (tracked for cleanup)
        self.connect_tracked(language_manager, "downloaded", self._on_language_changed)
        self.connect_tracked(language_manager, "removed", self._on_language_changed)

        self._setup_tts_volume()
        self._setup_tts_language()

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

        self.connect_tracked(self.extra_language_combo, "notify::selected-item", self._on_extra_language_changed)

    def _on_extra_language_changed(self, combo_row: Adw.ComboRow, _param):
        selected_item = combo_row.get_selected_item()
        if not selected_item:
            return
        lang_name = selected_item.get_string()
        lang_code = language_manager.get_language_code(lang_name)
        logger.debug(f"Anura: Extra language set to {lang_name} ({lang_code})")
        self.settings.set_string("extra-language", lang_code)

    def _on_language_changed(self, _sender, _code: str) -> None:
        """Refresh the extra-language combo when models are installed or removed."""
        # Disconnect old signal to avoid duplicate connections
        try:
            self.extra_language_combo.disconnect_by_func(self._on_extra_language_changed)
        except TypeError:
            pass  # Handler not connected yet (first call)
        self._setup_extra_languages()

    def _setup_tts_volume(self):
        """Setup TTS volume spin row with percentage display (0-100)."""
        # Load initial value from settings (0.0-1.0) and convert to percentage
        volume_normalized = self.settings.get_double("tts-volume")
        self.volume_row.set_value(volume_normalized * 100)

        # Update subtitle to show current value with %
        self._update_volume_subtitle(volume_normalized * 100)

        # Connect to changes and convert back to 0.0-1.0 for GSettings
        self.connect_tracked(self.volume_row, "notify::value", self._on_volume_changed)

    def _update_volume_subtitle(self, percentage: float):
        """Update the volume row subtitle to show the percentage."""
        self.volume_row.set_subtitle(_("TTS playback volume level: {percentage:.0f}%").format(percentage=percentage))

    def _on_volume_changed(self, spin_row, _param):
        """Convert percentage (0-100) to normalized value (0.0-1.0) for GSettings."""
        percentage = spin_row.get_value()
        normalized = percentage / 100.0
        self.settings.set_double("tts-volume", normalized)
        self._update_volume_subtitle(percentage)
        logger.debug(f"Anura: TTS volume set to {percentage:.0f}% ({normalized:.2f})")

    def _setup_tts_language(self):
        """Populate TTS language combo with gTTS supported languages."""
        supported = ttsservice.get_supported_gtts_languages()

        # Create list: "Auto (follow OCR)" + all supported languages
        lang_names = [_("Auto (follow OCR language)"), *list(supported.values())]
        self.tts_language_combo.set_model(Gtk.StringList.new(lang_names))

        # Select current setting
        current = self.settings.get_string("tts-language")
        if current:
            try:
                idx = list(supported.keys()).index(current) + 1  # +1 for "Auto"
                self.tts_language_combo.set_selected(idx)
            except ValueError:
                self.tts_language_combo.set_selected(0)  # Auto
        else:
            self.tts_language_combo.set_selected(0)  # Auto

        self.connect_tracked(self.tts_language_combo, "notify::selected", self._on_tts_language_changed)

    def _on_tts_language_changed(self, combo, _param):
        idx = combo.get_selected()
        if idx == 0:
            self.settings.set_string("tts-language", "")  # Auto
        else:
            supported = ttsservice.get_supported_gtts_languages()
            supported_keys = list(supported.keys())
            # Bounds check to prevent IndexError
            if idx - 1 < len(supported_keys):
                lang_code = supported_keys[idx - 1]  # -1 for "Auto"
                self.settings.set_string("tts-language", lang_code)
                logger.debug(f"Anura: TTS language set to {lang_code}")
            else:
                logger.warning(f"Anura: TTS language index {idx} out of bounds, falling back to Auto")
                self.settings.set_string("tts-language", "")

    def do_destroy(self):
        """Clean up all tracked signal handlers to prevent memory leaks."""
        self.disconnect_all_signals()
        super().do_destroy()
