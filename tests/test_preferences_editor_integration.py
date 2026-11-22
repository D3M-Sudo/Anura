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

from gi.repository import Adw, Gio  # noqa: E402

Adw.init()


@pytest.mark.gtk
@pytest.mark.parametrize(
    ("stored_mode", "expected_index", "selected_index", "expected_mode"),
    [
        ("word", 0, 1, "char"),
        ("char", 1, 2, "none"),
        ("none", 2, 0, "word"),
    ],
)
def test_editor_page_uses_real_gsettings_for_wrap_mode(
    monkeypatch, stored_mode, expected_index, selected_index, expected_mode
):
    """The real Editor combo reflects and persists wrap-mode GSettings values."""
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
    real_settings.set_string("editor-wrap-mode", stored_mode)

    import anura.widgets.preferences_editor_page as editor_module

    monkeypatch.setattr(editor_module, "settings", real_settings)
    page = editor_module.PreferencesEditorPage()

    assert page.editor_wrap_mode_combo.get_selected() == expected_index

    page.editor_wrap_mode_combo.set_selected(selected_index)

    assert real_settings.get_string("editor-wrap-mode") == expected_mode
