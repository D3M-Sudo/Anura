# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from unittest.mock import MagicMock

import pytest

pytest.importorskip("gi")

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")

from gi.repository import Adw, Gio  # noqa: E402

Adw.init()


@pytest.mark.gtk
def test_preferences_dialog_uses_real_gsettings_for_voice_volume(monkeypatch):
    """Instantiate the real PreferencesDialog and verify bidirectional GSettings sync."""
    repo_root = Path(__file__).resolve().parents[1]
    resource_name = "io.github.d3m_sudo.anura.gresource"
    resource_file = next(
        (
            candidate
            for candidate in (
                repo_root / "builddir" / "data" / resource_name,
                repo_root / "data" / resource_name,
            )
            if candidate.is_file()
        ),
        None,
    )
    if resource_file is None:
        pytest.skip("Built GResource bundle is unavailable in builddir/data or data")
    Gio.Resource.load(str(resource_file))._register()

    schema_source = Gio.SettingsSchemaSource.get_default()
    schema = schema_source.lookup("io.github.d3m_sudo.anura", True) if schema_source else None
    if schema is None:
        pytest.skip("Compiled Anura GSettings schema is unavailable")
    backend = Gio.memory_settings_backend_new()
    real_settings = Gio.Settings.new_full(schema, backend, "/io/github/d3msudo/anura/")

    manager = MagicMock()
    manager.get_available_codes.return_value = []
    manager.get_downloaded_languages.return_value = []
    manager.get_cached_supported_languages.return_value = {"en": "English"}
    manager.get_language_item.return_value = None

    import anura.widgets.preferences_dialog as dialog_module
    import anura.widgets.preferences_editor_page as editor_module
    import anura.widgets.preferences_general_page as general_module
    import anura.widgets.preferences_languages_page as languages_module
    import anura.widgets.preferences_voice_page as voice_module

    for module in (general_module, editor_module, languages_module, voice_module):
        monkeypatch.setattr(module, "settings", real_settings)
    for module in (dialog_module, general_module, languages_module):
        monkeypatch.setattr(module, "get_language_manager", lambda: manager)
    monkeypatch.setattr(languages_module.PreferencesLanguagesPage, "check_connection", lambda _self: None)
    monkeypatch.setattr(voice_module, "get_tts_service", lambda: manager)

    real_settings.set_double("tts-volume", 1.0)
    dialog = dialog_module.PreferencesDialog()
    assert dialog.voice_page.volume_row.get_value() == pytest.approx(100.0)
    assert dialog.voice_page.tts_language_combo.get_model().get_n_items() == 2

    dialog.voice_page.volume_row.set_value(30.0)
    assert real_settings.get_double("tts-volume") == pytest.approx(0.3)

    real_settings.set_double("tts-volume", 0.65)
    assert dialog.voice_page.volume_row.get_value() == pytest.approx(65.0)

