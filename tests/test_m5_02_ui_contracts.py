# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


ROOT = Path(__file__).resolve().parents[1]



gi = pytest.importorskip("gi")

gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gdk, Gio  # noqa: E402

Adw.init()

resource_path = ROOT / "data/io.github.d3m_sudo.anura.gresource"
if resource_path.exists():
    resource = Gio.Resource.load(str(resource_path))
    resource._register()


@pytest.mark.gtk
class TestM502ShortcutsSearch:
    @pytest.fixture
    def overlay(self):
        from anura.widgets.shortcuts_overlay import ShortcutsOverlay

        instance = ShortcutsOverlay()
        yield instance
        instance.destroy()

    def test_search_filters_matching_rows_and_categories(self, overlay):
        overlay.search_entry.set_text("open image file")
        overlay.search_entry.emit("search-changed")

        assert overlay.stack.get_visible_child_name() == "results"
        matching_rows = [
            row
            for group, rows in overlay._groups
            for row in rows
            if row.get_visible()
        ]
        assert len(matching_rows) == 1
        assert matching_rows[0].get_title() == "Open image file"
        assert sum(group.get_visible() for group, _rows in overlay._groups) == 1

    def test_search_empty_state_and_clearing_restore_all_groups(self, overlay):
        overlay.search_entry.set_text("no-shortcut-can-match-this")
        overlay.search_entry.emit("search-changed")

        assert overlay.stack.get_visible_child_name() == "no_results"
        assert not any(group.get_visible() for group, _rows in overlay._groups)

        overlay.search_entry.set_text("")
        overlay.search_entry.emit("search-changed")

        assert overlay.stack.get_visible_child_name() == "results"
        assert all(group.get_visible() for group, _rows in overlay._groups)
        assert all(row.get_visible() for _group, rows in overlay._groups for row in rows)

    def test_escape_clears_nonempty_search_without_closing_overlay(self, overlay):
        overlay.search_entry.set_text("clipboard")
        overlay.search_entry.emit("search-changed")
        close = MagicMock()
        overlay.close = close

        handled = overlay._on_key_pressed(None, Gdk.KEY_Escape, 0, Gdk.ModifierType(0))

        assert handled is True
        assert overlay.search_entry.get_text() == ""
        assert overlay.stack.get_visible_child_name() == "results"
        close.assert_not_called()

    def test_escape_with_empty_search_closes_overlay(self, overlay):
        close = MagicMock()
        overlay.close = close

        handled = overlay._on_key_pressed(None, Gdk.KEY_Escape, 0, Gdk.ModifierType(0))

        assert handled is True
        close.assert_called_once_with()


@pytest.mark.gtk
class TestM502ToastDelegation:
    def test_show_toast_delegates_title_and_priority_to_overlay(self):
        from anura.window import AnuraWindow

        overlay = MagicMock()
        window = SimpleNamespace(toast_overlay=overlay)

        AnuraWindow.show_toast(window, "M5-02 test toast", Adw.ToastPriority.HIGH)

        overlay.add_toast.assert_called_once()
        toast = overlay.add_toast.call_args.args[0]
        assert isinstance(toast, Adw.Toast)
        assert toast.get_title() == "M5-02 test toast"
        assert toast.get_priority() == Adw.ToastPriority.HIGH

    def test_toast_dismiss_signal_is_deterministic(self):
        toast = Adw.Toast.new("Dismiss lifecycle")
        dismissed = []
        toast.connect("dismissed", lambda _toast: dismissed.append(True))

        toast.dismiss()

        assert dismissed == [True]
