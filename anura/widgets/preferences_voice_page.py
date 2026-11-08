# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
import threading

from gi.repository import Adw, Gio, GLib, Gtk
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

        self._setup_tts_volume()
        # TTS language setup depends on the (possibly network-backed) TTS
        # service; a failure there must not abort __init__ or any later
        # settings binding.
        try:
            self._setup_tts_language()
        except Exception:
            logger.exception("Anura: could not initialize the TTS language selector")

    # --- Volume (GSettings stores 0.0-1.0, UI shows 0-100) ---

    def _setup_tts_volume(self) -> None:
        """Initialize and synchronize the TTS volume percentage with GSettings."""
        self.volume_row.set_value(self.settings.get_double("tts-volume") * 100.0)
        self.connect_tracked(self.volume_row, "notify::value", self._on_volume_changed)
        self.connect_tracked(self.settings, "changed::tts-volume", self._on_tts_volume_setting_changed)

    def _on_volume_changed(self, spin_row: Adw.SpinRow, _param: object) -> None:
        """Persist the UI percentage as a normalized GSettings double."""
        percentage = spin_row.get_value()
        normalized = percentage / 100.0
        if abs(self.settings.get_double("tts-volume") - normalized) > 1e-9:
            self.settings.set_double("tts-volume", normalized)
        logger.debug(f"Anura: TTS volume set to {percentage:.0f}%")

    def _on_tts_volume_setting_changed(self, _settings: Gio.Settings, _key: str) -> None:
        """Reflect external GSettings changes in the volume row without signal loops."""
        percentage = self.settings.get_double("tts-volume") * 100.0
        if abs(self.volume_row.get_value() - percentage) > 1e-6:
            self.volume_row.set_value(percentage)

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
