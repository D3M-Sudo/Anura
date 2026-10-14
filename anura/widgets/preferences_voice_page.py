# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from gettext import gettext as _

from gi.repository import Adw, Gtk
from loguru import logger

from anura.config import RESOURCE_PREFIX
from anura.services.settings import settings
from anura.services.tts import get_tts_service
from anura.utils.signal_manager import SignalManagerMixin


@Gtk.Template(resource_path=f"{RESOURCE_PREFIX}/preferences_voice.ui")
class PreferencesVoicePage(Adw.PreferencesPage, SignalManagerMixin):
    __gtype_name__ = "PreferencesVoicePage"

    volume_row: Adw.SpinRow = Gtk.Template.Child()
    tts_language_combo: Adw.ComboRow = Gtk.Template.Child()

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self.settings = settings

        self._setup_tts_volume()
        # TTS language setup depends on the (possibly network-backed) TTS
        # service; a failure there must not abort __init__ or the volume
        # binding above.
        with contextlib.suppress(Exception):
            self._setup_tts_language()

    def _setup_tts_volume(self) -> None:
        """Setup TTS volume spin row with percentage display (0-100)."""
        volume_normalized = self.settings.get_double("tts-volume")
        self.volume_row.set_value(volume_normalized * 100)

        # Update subtitle to show current value with %
        self._update_volume_subtitle(volume_normalized * 100)

        # Connect to changes and convert back to 0.0-1.0 for GSettings
        self.connect_tracked(self.volume_row, "notify::value", self._on_volume_changed)

    def _update_volume_subtitle(self, percentage: float) -> None:
        """Update the volume row subtitle to show the percentage."""
        self.volume_row.set_subtitle(_("TTS playback volume level: {percentage:.0f}%").format(percentage=percentage))

    def _on_volume_changed(self, spin_row: Adw.SpinRow, _param: object) -> None:
        """Convert percentage (0-100) to normalized value (0.0-1.0) for GSettings."""
        percentage = spin_row.get_value()
        normalized = percentage / 100.0
        self.settings.set_double("tts-volume", normalized)
        self._update_volume_subtitle(percentage)
        logger.debug(f"Anura: TTS volume set to {percentage:.0f}% ({normalized:.2f})")

    def _setup_tts_language(self) -> None:
        """Populate TTS language combo with gTTS supported languages."""
        supported = get_tts_service().get_supported_languages()

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

    def _on_tts_language_changed(self, combo: Adw.ComboRow, _param: object) -> None:
        idx = combo.get_selected()
        if idx == 0:
            self.settings.set_string("tts-language", "")  # Auto
        else:
            supported = get_tts_service().get_supported_languages()
            supported_keys = list(supported.keys())
            # Bounds check to prevent IndexError
            if idx - 1 < len(supported_keys):
                lang_code = supported_keys[idx - 1]  # -1 for "Auto"
                self.settings.set_string("tts-language", lang_code)
                logger.debug(f"Anura: TTS language set to {lang_code}")
            else:
                logger.warning(f"Anura: TTS language index {idx} out of bounds, falling back to Auto")
                self.settings.set_string("tts-language", "")

    def do_destroy(self) -> None:
        """Clean up all tracked signal handlers to prevent memory leaks."""
        self.teardown_all()
        super().do_destroy()
