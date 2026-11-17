# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Real-window focus restoration across History → Welcome navigation."""

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

from anura.models.language_item import LanguageItem  # noqa: E402
from anura.widgets.history_page import HistoryPage  # noqa: E402


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


def _build_window():
    from anura.window import AnuraWindow

    app = Gtk.Application(
        application_id="io.github.d3msudo.anura.M2G01FocusTest",
        flags=Gio.ApplicationFlags.NON_UNIQUE,
    )
    app.register(None)
    # The Blueprint button uses app.get_screenshot. Install the action so GTK
    # does not mark the primary control insensitive in this isolated fixture.
    app.add_action(Gio.SimpleAction.new("get_screenshot", None))
    app.settings = MagicMock()
    app.settings.get_string.return_value = "eng"
    app.settings.get_int.return_value = 10

    language_manager = MagicMock()
    language_manager.get_language_item.return_value = LanguageItem(code="eng", title="English")

    with (
        patch("gi.repository.Gtk.Application.get_default", return_value=app),
        patch("anura.window.get_language_manager", return_value=language_manager),
        patch("anura.window.get_share_service", return_value=MagicMock()),
        patch("anura.window.get_clipboard_service", side_effect=RuntimeError("clipboard unavailable")),
        patch("anura.window.HistoryService", return_value=MagicMock()),
        patch("anura.window.HistoryController", return_value=MagicMock()),
        patch("anura.window.TtsController", return_value=MagicMock()),
        patch("anura.window.OcrController", return_value=MagicMock()),
        patch("anura.window.DndController", return_value=MagicMock()),
        patch.object(AnuraWindow, "_setup_geometry"),
        patch.object(AnuraWindow, "_apply_capability_constraints"),
        patch.object(HistoryPage, "setup"),
    ):
        window = AnuraWindow(application=app, backend=MagicMock())

    window.history_page.refresh = MagicMock()
    return window


@pytest.mark.gtk
@pytest.mark.parametrize("navigation_route", ["window-method", "native-back"])
def test_history_to_welcome_restores_primary_action_focus(navigation_route):
    """Returning to Welcome restores focus to its visible primary action."""
    window = _build_window()
    window.present()

    try:
        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.welcome_page)
        assert _spin_until(window.welcome_page.screenshot_button.get_mapped)
        assert window.welcome_page.screenshot_button.is_sensitive()
        assert window.welcome_page.screenshot_button.grab_focus()
        assert _spin_until(window.welcome_page.screenshot_button.has_focus)

        window.show_history_page()
        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.history_page)

        if navigation_route == "window-method":
            window.show_welcome_page()
        else:
            window.navigation_view.pop_to_tag("welcome")

        assert _spin_until(lambda: window.navigation_view.get_visible_page() is window.welcome_page)
        assert _spin_until(window.welcome_page.screenshot_button.has_focus), (
            "History → Welcome left keyboard focus outside the Welcome primary action"
        )
    finally:
        window.destroy()
