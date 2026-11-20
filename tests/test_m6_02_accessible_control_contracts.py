# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""P5 contracts for high-value accessible names, roles, states and announcements."""

import os
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


def test_language_selector_row_name_and_selected_state_follow_language(headless_gi_mocks):
    from gi.repository import Gtk

    from anura.widgets.language_popover_row import LanguagePopoverRow

    for selected, expected_label in (
        (False, "Select Italian"),
        (True, "Italian (active language)"),
    ):
        row = MagicMock()
        row.lang = SimpleNamespace(title="Italian", selected=selected)

        LanguagePopoverRow._update_accessibility_metadata(row)

        row.set_tooltip_text.assert_called_once_with(expected_label)
        row.update_property.assert_called_once_with([Gtk.AccessibleProperty.LABEL], [expected_label])
        row.update_state.assert_called_once_with([Gtk.AccessibleState.SELECTED], [selected])


def test_language_selector_selection_change_refreshes_accessible_metadata(headless_gi_mocks):
    from gi.repository import Gtk

    from anura.widgets.language_popover_row import LanguagePopoverRow

    row = MagicMock()
    row.lang = SimpleNamespace(title="English", selected=True)

    LanguagePopoverRow._on_selected_changed(row, MagicMock(), MagicMock())

    row.update_property.assert_called_once_with(
        [Gtk.AccessibleProperty.LABEL],
        ["English (active language)"],
    )
    row.update_state.assert_called_once_with([Gtk.AccessibleState.SELECTED], [True])


def test_welcome_drop_area_toggle_updates_expanded_state_and_accessible_name(headless_gi_mocks, monkeypatch):
    import anura.widgets.welcome_page as welcome_page
    from gi.repository import Gtk

    page = MagicMock()
    page.drop_revealer.get_reveal_child.side_effect = [False, True]
    monkeypatch.setattr(welcome_page.GLib, "idle_add", MagicMock())

    welcome_page.WelcomePage._on_drop_button_clicked(page, MagicMock())
    welcome_page.WelcomePage._on_drop_button_clicked(page, MagicMock())

    assert [call.args for call in page.drop_button.update_state.call_args_list] == [
        ([Gtk.AccessibleState.EXPANDED], [True]),
        ([Gtk.AccessibleState.EXPANDED], [False]),
    ]
    assert [call.args for call in page.drop_button.update_property.call_args_list] == [
        ([Gtk.AccessibleProperty.LABEL], ["Hide drop area"]),
        ([Gtk.AccessibleProperty.LABEL], ["Drop image here"]),
    ]


def test_extracted_tts_controls_expose_pressed_state_and_current_action_name(headless_gi_mocks):
    from gi.repository import Gtk

    from anura.widgets.extracted_page import ExtractedPage

    page = MagicMock()
    page.listen_stack = MagicMock()
    page.listen_spinner = MagicMock()
    page.listen_btn = MagicMock()
    page.listen_pause_btn = MagicMock()
    page.swap_controls = MagicMock()

    ExtractedPage.update_tts_state(page, "playing")
    ExtractedPage.update_tts_state(page, "paused")
    ExtractedPage.update_tts_state(page, "idle")

    assert [call.args for call in page.listen_pause_btn.update_state.call_args_list] == [
        ([Gtk.AccessibleState.PRESSED], [True]),
        ([Gtk.AccessibleState.PRESSED], [False]),
    ]
    assert [call.args for call in page.listen_pause_btn.update_property.call_args_list] == [
        ([Gtk.AccessibleProperty.LABEL], ["Pause listening"]),
        ([Gtk.AccessibleProperty.LABEL], ["Resume listening"]),
    ]
    assert page.listen_btn.update_state.call_args_list[-1].args == (
        [Gtk.AccessibleState.PRESSED],
        [False],
    )


def _spin_until(predicate, timeout: float = 2.0) -> bool:
    from gi.repository import GLib

    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        if predicate():
            return True
        time.sleep(0.01)
    return bool(predicate())


@pytest.mark.gtk
def test_primary_application_controls_keep_native_accessible_roles():
    pytest.importorskip("gi")

    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gio", "2.0")
    gi.require_version("Gtk", "4.0")

    from gi.repository import Adw, Gio, Gtk

    Adw.init()
    resource_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "io.github.d3msudo.anura.gresource",
    )
    if not os.path.exists(resource_path):
        pytest.skip("Anura GResource bundle is required for GTK template integration tests")
    Gio.Resource.load(resource_path)._register()

    from anura.models.history import HistoryEntry
    from anura.models.language_item import LanguageItem
    from anura.window import AnuraWindow

    app = Gtk.Application(
        application_id="io.github.d3msudo.anura.M602AccessibleControlContractsTest",
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )
    app.register(None)
    app.add_action(Gio.SimpleAction.new("get_screenshot", None))
    app.settings = MagicMock()
    app.settings.get_string.return_value = "eng"
    app.settings.get_int.return_value = 10

    language_manager = MagicMock()
    language_manager.get_language_item.return_value = LanguageItem(code="eng", title="English")
    history_service = MagicMock()
    history_service.get_entries.return_value = [
        HistoryEntry(text="Accessible history entry", language="eng"),
    ]
    page_settings = MagicMock()
    page_settings.get_boolean.return_value = True

    with (
        patch("gi.repository.Gtk.Application.get_default", return_value=app),
        patch("anura.window.get_language_manager", return_value=language_manager),
        patch("anura.window.get_share_service", return_value=MagicMock()),
        patch("anura.window.get_clipboard_service", side_effect=RuntimeError("clipboard unavailable")),
        patch("anura.window.HistoryService", return_value=history_service),
        patch("anura.widgets.history_page.settings", page_settings),
        patch("anura.window.HistoryController", return_value=MagicMock()),
        patch("anura.window.TtsController", return_value=MagicMock()),
        patch("anura.window.OcrController", return_value=MagicMock()),
        patch("anura.window.DndController", return_value=MagicMock()),
        patch.object(AnuraWindow, "_setup_geometry"),
        patch.object(AnuraWindow, "_apply_capability_constraints"),
    ):
        window = AnuraWindow(application=app, backend=MagicMock())

    try:
        assert _spin_until(lambda: window.history_page.clear_button is not None)
        assert window.welcome_page.screenshot_button.get_accessible_role() == Gtk.AccessibleRole.BUTTON
        assert window.extracted_page.search_entry.get_accessible_role() == Gtk.AccessibleRole.SEARCH_BOX
        assert window.history_page.clear_button.get_accessible_role() == Gtk.AccessibleRole.BUTTON
    finally:
        window.destroy()
