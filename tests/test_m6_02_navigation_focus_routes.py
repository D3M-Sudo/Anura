# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
import time
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("gi")

import gi

gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

Adw.init()

resource_path = os.path.join(os.path.dirname(__file__), "..", "data", "io.github.d3msudo.anura.gresource")
if os.path.exists(resource_path):
    resource = Gio.Resource.load(resource_path)
    resource._register()

from anura.models.history import HistoryEntry  # noqa: E402
from anura.models.language_item import LanguageItem  # noqa: E402


def _spin_until(predicate, timeout: float = 2.0) -> bool:
    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        if predicate():
            return True
        time.sleep(0.01)
    return bool(predicate())


def _build_window(history_entries: list[HistoryEntry] | None = None):
    from anura.window import AnuraWindow

    app = Gtk.Application(
        application_id="io.github.d3msudo.anura.M602NavigationFocusRoutesTest",
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )
    app.register(None)
    # Keep the Welcome primary action enabled in this isolated application.
    app.add_action(Gio.SimpleAction.new("get_screenshot", None))
    app.settings = MagicMock()
    app.settings.get_string.return_value = "eng"
    app.settings.get_int.return_value = 10

    language_manager = MagicMock()
    language_manager.get_language_item.return_value = LanguageItem(code="eng", title="English")

    history_service = MagicMock()
    history_service.get_entries.return_value = history_entries or []
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

    return window


@pytest.mark.gtk
def test_extracted_to_welcome_restores_primary_action_focus():
    """The Extracted page's go-back route returns to Welcome and restores its primary action."""
    window = _build_window()
    window.present()

    try:
        welcome_button = window.welcome_page.screenshot_button
        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.welcome_page)
        assert _spin_until(welcome_button.get_mapped)
        assert welcome_button.is_sensitive()
        assert welcome_button.grab_focus()
        assert _spin_until(welcome_button.has_focus)

        window.navigation_view.push_by_tag("extracted")
        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.extracted_page)

        # Adw.NavigationView invokes do_hiding() as the page is popped; that
        # signal is the production route wired to AnuraWindow.show_welcome_page.
        window.navigation_view.pop()

        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.welcome_page)
        assert _spin_until(welcome_button.has_focus), (
            "Extracted → Welcome left keyboard focus outside the Welcome primary action"
        )
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_to_history_focuses_first_history_row():
    """Entering a populated History page places focus on its first entry row."""
    entries = [
        HistoryEntry(text="First OCR entry", language="eng"),
        HistoryEntry(text="Second OCR entry", language="eng"),
    ]
    window = _build_window(entries)
    window.present()

    try:
        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.welcome_page)
        window.show_history_page()

        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.history_page)
        first_row = window.history_page._row_entry_ids[entries[0].id]
        assert _spin_until(first_row.get_mapped)
        assert _spin_until(first_row.has_focus), (
            "Welcome → History did not place keyboard focus on the first History entry row"
        )
    finally:
        window.destroy()


@pytest.mark.gtk
def test_welcome_to_empty_history_shows_empty_state_without_forcing_focus():
    """The empty History route is verified without targeting a disabled/destructive control."""
    window = _build_window()
    window.present()

    try:
        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.welcome_page)
        window.show_history_page()

        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.history_page)
        assert window.history_page.history_stack.get_visible_child_name() == "empty"
        assert not window.history_page.clear_button.is_sensitive()
    finally:
        window.destroy()
