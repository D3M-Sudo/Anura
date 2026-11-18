# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from pathlib import Path

import pytest

pytest.importorskip("gi")

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
gi.require_version("GObject", "2.0")

from gi.repository import Adw, Gio, GObject  # noqa: E402

from anura.models.language_item import LanguageItem  # noqa: E402

Adw.init()


class _LanguageManager(GObject.Object):
    __gsignals__ = {
        "added": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "downloaded": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "removed": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self):
        super().__init__()
        self.items = {
            "eng": LanguageItem("eng", "English"),
            "ita": LanguageItem("ita", "Italian"),
        }
        self.downloaded_codes = {"eng"}

    def get_available_codes(self):
        return list(self.items)

    def get_downloaded_codes(self):
        return list(self.downloaded_codes)

    def get_language_item(self, code):
        return self.items.get(code)


@pytest.mark.gtk
def test_languages_page_search_empty_reset_and_model_lifecycle(monkeypatch):
    """Real GTK filtering, stack state, search reset and language signals stay coherent."""
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
    manager = _LanguageManager()

    import anura.widgets.preferences_languages_page as languages_module

    monkeypatch.setattr(languages_module, "settings", real_settings)
    monkeypatch.setattr(languages_module, "get_language_manager", lambda: manager)
    monkeypatch.setattr(languages_module.PreferencesLanguagesPage, "check_connection", lambda _self: None)

    page = languages_module.PreferencesLanguagesPage()

    # The normal filter shows downloaded models only.
    assert page.model.get_n_items() == 1
    assert page.model.get_item(0).code == "eng"

    # Search is case-insensitive and can find a model that is not downloaded.
    page.language_search_entry.set_text("iTaLiAn")
    page.on_language_search(page.language_search_entry)
    assert page.model.get_n_items() == 1
    assert page.model.get_item(0).code == "ita"
    assert page.views.get_visible_child_name() == "languages_state"

    # An unmatched query selects the explicit empty state.
    page.language_search_entry.set_text("no-such-language")
    page.on_language_search(page.language_search_entry)
    assert page.model.get_n_items() == 0
    assert page.views.get_visible_child_name() == "empty_state"

    # Stopping search restores the downloaded-only view and clears the query.
    page.on_language_search_stop(page.language_search_entry)
    assert page.language_search_entry.get_text() == ""
    assert page.model.get_n_items() == 1
    assert page.model.get_item(0).code == "eng"
    assert page.views.get_visible_child_name() == "languages_state"

    # Added events append a new row once, even if the event is delivered twice.
    manager.items["fra"] = LanguageItem("fra", "French")
    manager.downloaded_codes.add("fra")
    manager.emit("added", "fra")
    manager.emit("added", "fra")
    assert page.list_store.get_n_items() == 3
    assert page.model.get_n_items() == 2

    # Removal refreshes the active downloaded-only filter.
    manager.downloaded_codes.remove("eng")
    manager.emit("removed", "eng")
    assert page.model.get_n_items() == 1
    assert page.model.get_item(0).code == "fra"
