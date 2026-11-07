# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
import threading
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, GObject, Gtk
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

        # #532: TTS catalog state. The combo is filled from the cache and a
        # cold cache is refreshed off the GTK main thread. A TTS setup failure
        # must not prevent the volume row from being set up.
        self._tts_catalog_loading = False
        self._updating_tts_combo = False
        self._disposed = False

        self.settings.bind_with_mapping(
            "tts-volume",
            self.volume_row,
            "value",
            Gio.SettingsBindFlags.DEFAULT,
            self._tts_volume_transform_in,
            self._tts_volume_transform_out,
        )

        self._setup_tts_volume()
        # TTS language setup depends on the (possibly network-backed) TTS
        # service; a failure there must not abort __init__ or any later
        # settings binding.
        with contextlib.suppress(Exception):
            self._setup_tts_language()

    # --- Volume transform functions: GSettings stores 0.0-1.0, UI shows 0-100 ---

    @staticmethod
    def _tts_volume_transform_in(value: GObject.Value, variant: GLib.Variant) -> bool:
        """Map normalized GSettings volume (0.0-1.0) to the UI percentage (0-100)."""
        value.set_double(variant.get_double() * 100.0)
        return True

    @staticmethod
    def _tts_volume_transform_out(value: GObject.Value, _expected_type: GLib.VariantType) -> GLib.Variant:
        """Map the UI percentage (0-100) to normalized GSettings volume (0.0-1.0)."""
        return GLib.Variant.new_double(value.get_double() / 100.0)

    def _setup_tts_volume(self) -> None:
        """Setup TTS volume spin row with percentage display (0-100)."""
        volume_normalized = self.settings.get_double("tts-volume")
        self.volume_row.set_value(volume_normalized * 100)
        self.connect_tracked(self.volume_row, "notify::value", self._on_volume_changed)

    def _on_volume_changed(self, spin_row: Adw.SpinRow, _param: object) -> None:
        """Persist volume changes to GSettings (via transform_out binding)."""
        percentage = spin_row.get_value()
        logger.debug(f"Anura: TTS volume set to {percentage:.0f}%")

    # --- TTS language (async catalog loading, never blocks UI) ---

    def _setup_tts_language(self) -> None:
        """Populate the TTS combo from the cached catalog, refreshing in background."""
        supported = get_tts_service().get_cached_supported_languages()
        self._set_tts_languages(supported or {})

        self.connect_tracked(self.tts_language_combo, "notify::selected", self._on_tts_language_changed)

        if supported is None:
            self._refresh_tts_catalog_async()

    def _set_tts_languages(self, supported: dict) -> None:
        """Rebuild the combo model without writing the setting back."""
        self._updating_tts_combo = True
        try:
            lang_names = [_("Auto (follow OCR language)"), *list(supported.values())]
            self.tts_language_combo.set_model(Gtk.StringList.new(lang_names))

            current = self.settings.get_string("tts-language")
            idx = 0
            if current:
                try:
                    idx = list(supported.keys()).index(current) + 1  # +1 for "Auto"
                except ValueError:
                    idx = 0
            self.tts_language_combo.set_selected(idx)
        finally:
            self._updating_tts_combo = False

    def _refresh_tts_catalog_async(self) -> None:
        """Fetch the gTTS catalog on a worker thread and apply it via idle."""
        if self._tts_catalog_loading or self._disposed:
            return
        self._tts_catalog_loading = True

        def _worker() -> None:
            try:
                supported = get_tts_service().get_supported_languages()
            except Exception:
                logger.exception("Anura: failed to refresh the TTS language catalog")
                supported = None

            try:
                GLib.idle_add(self._on_tts_catalog_ready, supported)
            except Exception:
                # The main loop may already be shutting down. Do not leave the
                # page's loading state stuck if the callback cannot be queued.
                logger.exception("Anura: could not schedule the TTS catalog result")
                self._tts_catalog_loading = False

        worker = threading.Thread(target=_worker, daemon=True, name="AnuraTtsCatalogRefresh")
        try:
            worker.start()
        except RuntimeError:
            self._tts_catalog_loading = False
            logger.exception("Anura: could not start the TTS catalog worker")

    def _on_tts_catalog_ready(self, supported: dict | None) -> bool:
        """Apply a freshly fetched catalog to the combo (main thread)."""
        self._tts_catalog_loading = False
        if supported and not self._disposed:
            self._set_tts_languages(supported)
        return GLib.SOURCE_REMOVE

    def _on_tts_language_changed(self, combo: Adw.ComboRow, _param: object) -> None:
        """Persist the selected TTS language to settings."""
        if self._updating_tts_combo:
            return

        idx = combo.get_selected()
        if idx == 0:
            self.settings.set_string("tts-language", "")  # Auto
        else:
            # Cached-only: a UI callback must never trigger a network fetch.
            try:
                supported = get_tts_service().get_cached_supported_languages() or {}
            except Exception:
                logger.exception("Anura: could not read the cached TTS language catalog")
                return

            supported_keys = list(supported.keys())
            if idx - 1 < len(supported_keys):
                lang_code = supported_keys[idx - 1]  # -1 for "Auto"
                self.settings.set_string("tts-language", lang_code)
                logger.debug(f"Anura: TTS language set to {lang_code}")
            else:
                logger.warning(f"Anura: TTS language index {idx} out of bounds, falling back to Auto")
                self.settings.set_string("tts-language", "")

    def do_destroy(self) -> None:
        """Clean up all tracked signal handlers to prevent memory leaks."""
        self._disposed = True
        self.teardown_all()
        super().do_destroy()