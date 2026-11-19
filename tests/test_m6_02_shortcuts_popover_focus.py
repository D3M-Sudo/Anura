# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""GTK integration coverage for compact Shortcuts and language-selector popovers."""

import os
import time
from typing import ClassVar
from unittest.mock import MagicMock

import pytest

pytest.importorskip("gi")

import gi

gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gio, GLib, GObject, Gtk  # noqa: E402

Adw.init()

_resource_path = os.path.join(os.path.dirname(__file__), "..", "data", "io.github.d3m_sudo.anura.gresource")
if not os.path.exists(_resource_path):
    pytest.skip("Anura GResource bundle is required for GTK template integration tests", allow_module_level=True)
Gio.Resource.load(_resource_path)._register()

# Template-backed widgets must be imported after registering the resource.
# isort: off
from anura.models.language_item import LanguageItem  # noqa: E402
from anura.widgets.language_popover import LanguagePopover  # noqa: E402
from anura.widgets.shortcuts_overlay import ShortcutsOverlay  # noqa: E402
# isort: on


_VIEWPORTS = [(360, 600), (640, 480)]


def _drain_main_context() -> None:
    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)


def _wait_until(condition, description: str, timeout_seconds: float = 5.0) -> None:
    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout_seconds
    while not condition():
        while context.pending():
            context.iteration(False)
        if time.monotonic() >= deadline:
            pytest.fail(f"GTK did not {description} within {timeout_seconds:.1f}s")
        time.sleep(0.01)


def _is_descendant(widget: Gtk.Widget | None, ancestor: Gtk.Widget) -> bool:
    current = widget
    while current is not None:
        if current == ancestor:
            return True
        current = current.get_parent()
    return False


def _assert_inside_window(widget: Gtk.Widget, window: Gtk.Window) -> None:
    assert widget.get_visible(), f"{type(widget).__name__} is not visible"
    assert widget.get_mapped(), f"{type(widget).__name__} is not mapped"
    available, bounds = widget.compute_bounds(window)
    assert available, f"could not calculate {type(widget).__name__} bounds"
    assert bounds.origin.x >= -1, f"{type(widget).__name__} starts outside the left window edge"
    assert bounds.origin.y >= -1, f"{type(widget).__name__} starts outside the top window edge"
    assert bounds.origin.x + bounds.size.width <= window.get_width() + 1, (
        f"{type(widget).__name__} extends beyond the right window edge"
    )
    assert bounds.origin.y + bounds.size.height <= window.get_height() + 1, (
        f"{type(widget).__name__} extends beyond the bottom window edge"
    )


@pytest.mark.gtk
@pytest.mark.parametrize(("width", "height"), _VIEWPORTS)
def test_shortcuts_overlay_keeps_search_and_scrolled_results_reachable(width: int, height: int) -> None:
    overlay = ShortcutsOverlay()
    overlay.set_default_size(width, height)
    overlay.present()
    try:
        _wait_until(
            lambda: overlay.get_mapped() and overlay.get_width() > 0 and overlay.get_height() > 0,
            f"present Shortcuts overlay at {width}x{height}",
        )
        _drain_main_context()
        scroller = overlay.shortcuts_list.get_ancestor(Gtk.ScrolledWindow)
        assert scroller is not None, "Shortcuts results must be hosted by a scroll container"
        _wait_until(
            lambda: scroller.get_vadjustment().get_page_size() > 0,
            "allocate the Shortcuts results viewport",
        )

        assert overlay.search_entry.get_visible() and overlay.search_entry.get_mapped()
        _assert_inside_window(overlay.search_entry, overlay)
        _assert_inside_window(scroller, overlay)

        adjustment = scroller.get_vadjustment()
        assert adjustment.get_upper() > adjustment.get_page_size(), (
            "Shortcuts list should overflow the compact viewport"
        )
        adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
        _wait_until(
            lambda: abs(adjustment.get_value() - (adjustment.get_upper() - adjustment.get_page_size())) <= 1,
            "scroll Shortcuts results to the end",
        )
        last_group, last_rows = overlay._groups[-1]
        last_row = last_rows[-1]
        _wait_until(lambda: last_row.get_mapped() and last_group.get_mapped(), "map the final Shortcuts row")
        available, bounds = last_row.compute_bounds(scroller)
        assert available and bounds.size.height > 0
        page_size = adjustment.get_page_size()
        visible_center = bounds.origin.y + bounds.size.height / 2 - adjustment.get_value()
        assert -1 <= visible_center <= page_size + 1, "final Shortcuts row is not reachable in the scroller viewport"
    finally:
        overlay.destroy()


@pytest.mark.gtk
def test_shortcuts_filtering_does_not_leave_focus_on_a_hidden_result() -> None:
    parent = Gtk.Window()
    parent.present()
    overlay = ShortcutsOverlay(transient_for=parent)
    overlay.present()
    try:
        _wait_until(lambda: parent.get_mapped() and parent.is_active(), "activate Shortcuts parent window")
        _wait_until(lambda: overlay.get_mapped() and overlay.is_active(), "activate Shortcuts overlay")
        assert overlay.search_entry.grab_focus(), "Shortcuts search should accept focus"
        _wait_until(lambda: overlay.search_entry.has_focus(), "focus Shortcuts search")

        # Gtk.SearchEntry debounces search-changed. Observe the signal rather
        # than assuming set_text() synchronously ran the filtering callback.
        search_events: list[str] = []
        search_handler = overlay.search_entry.connect(
            "search-changed",
            lambda entry: search_events.append(entry.get_text()),
        )
        try:
            overlay.search_entry.set_text("open image file")
            target_row = next(
                row for _group, rows in overlay._groups for row in rows if row.get_title() == "Take screenshot"
            )
            _wait_until(lambda: bool(search_events), "emit the debounced Shortcuts search-changed signal")
            _wait_until(lambda: not target_row.get_visible(), "filter out the non-matching Shortcuts result")

            assert search_events[-1] == "open image file"
            assert overlay.stack.get_visible_child_name() == "results"
            visible_rows = [row for _group, rows in overlay._groups for row in rows if row.get_visible()]
            assert len(visible_rows) == 1
            assert visible_rows[0].get_title() == "Open image file"
            assert overlay.get_focus() is overlay.search_entry, "focus should remain in the visible search control"
        finally:
            overlay.search_entry.disconnect(search_handler)
    finally:
        overlay.destroy()
        parent.destroy()


class _LanguageManager(GObject.Object):
    __gsignals__: ClassVar[dict] = {
        "downloaded": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "removed": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

    def __init__(self) -> None:
        super().__init__()
        self.languages = [
            ("eng", "English"),
            ("ita", "Italian"),
            ("fra", "French"),
            ("deu", "German"),
            ("spa", "Spanish"),
        ] + [(f"x{index:02d}", f"Test language {index:02d}") for index in range(35)]
        self.active_language = LanguageItem("eng", "English", selected=True)

    def get_downloaded_codes(self, force: bool = False) -> list[str]:
        del force
        return [code for code, _title in self.languages]

    def get_language(self, code: str) -> str:
        return dict(self.languages)[code]

    def get_language_item(self, code: str) -> LanguageItem | None:
        return next(
            (
                LanguageItem(item_code, title, selected=(item_code == code))
                for item_code, title in self.languages
                if item_code == code
            ),
            None,
        )


def _make_language_popover(monkeypatch):
    import anura.widgets.language_popover as language_popover_module

    manager = _LanguageManager()
    settings = MagicMock()
    settings.get_string.return_value = "eng"
    monkeypatch.setattr(language_popover_module, "get_language_manager", lambda: manager)
    monkeypatch.setattr(language_popover_module, "settings", settings)
    popover = LanguagePopover()
    return popover, manager, settings


def _open_language_popover(popover: LanguagePopover, width: int, height: int):
    window = Gtk.Window()
    window.set_default_size(width, height)
    anchor = Gtk.MenuButton()
    anchor.set_label("Language")
    anchor.set_popover(popover)
    window.set_child(anchor)
    window.present()
    try:
        _wait_until(lambda: window.get_mapped() and anchor.get_mapped(), "map language selector anchor")
        _wait_until(lambda: window.is_active(), "activate Language selector parent window")
        # Activate the MenuButton through its widget activation path rather than
        # forcing its active property; this lets GTK establish the popover grab.
        assert anchor.activate(), "Language selector MenuButton should activate"
        _wait_until(
            lambda: popover.get_mapped() and popover.get_width() > 0 and popover.get_height() > 0,
            "open Language selector popover",
        )
        return window, anchor
    except BaseException:
        # The caller cannot enter its try/finally until this helper returns.
        # Tear down partially opened GTK objects here on every setup failure.
        popover.popdown()
        window.destroy()
        raise


@pytest.mark.gtk
@pytest.mark.parametrize(("width", "height"), _VIEWPORTS)
def test_language_selector_is_compact_scrollable_and_focuses_search(monkeypatch, width: int, height: int) -> None:
    popover, _manager, _settings = _make_language_popover(monkeypatch)
    window, _anchor = _open_language_popover(popover, width, height)
    try:
        _wait_until(lambda: popover.entry.has_focus(), "focus Language selector search")
        assert popover.entry.get_visible() and popover.entry.get_mapped()
        assert popover.get_width() <= width + 1
        assert popover.get_height() <= 360, "language selector exceeded its 300px list cap plus controls"

        scroller = popover.list_view.get_ancestor(Gtk.ScrolledWindow)
        assert scroller is not None
        _wait_until(
            lambda: scroller.get_vadjustment().get_page_size() > 0,
            "allocate Language selector list viewport",
        )
        adjustment = scroller.get_vadjustment()
        assert adjustment.get_upper() > adjustment.get_page_size(), (
            "language list should scroll when many models are installed"
        )
        adjustment.set_value(adjustment.get_upper() - adjustment.get_page_size())
        _wait_until(
            lambda: abs(adjustment.get_value() - (adjustment.get_upper() - adjustment.get_page_size())) <= 1,
            "scroll Language selector to the final model",
        )
        final_row = popover.list_view.get_row_at_index(popover.filter_list.get_n_items() - 1)
        assert final_row is not None and final_row.get_mapped()
        available, bounds = final_row.compute_bounds(scroller)
        assert available and bounds.size.height > 0
        visible_center = bounds.origin.y + bounds.size.height / 2 - adjustment.get_value()
        assert -1 <= visible_center <= adjustment.get_page_size() + 1
    finally:
        popover.popdown()
        window.destroy()


@pytest.mark.gtk
def test_language_selector_filter_selection_metadata_and_close_focus(monkeypatch) -> None:
    popover, _manager, settings = _make_language_popover(monkeypatch)
    window, anchor = _open_language_popover(popover, 900, 600)
    try:
        _wait_until(lambda: popover.entry.has_focus(), "focus Language selector search before filtering")
        popover.entry.set_text("ital")
        _wait_until(lambda: popover.filter_list.get_n_items() == 1, "filter Language selector to Italian")
        row = popover.list_view.get_row_at_index(0)
        assert row is not None
        assert row.lang.code == "ita"
        assert row.get_tooltip_text() == "Select Italian"

        row.lang.selected = True
        _drain_main_context()
        assert row.get_tooltip_text() == "Italian (active language)"

        popover.entry.set_text("no-language-matches-this")
        _wait_until(lambda: popover.filter_list.get_n_items() == 0, "show empty Language selector results")
        assert popover.views.get_visible_child_name() == "empty_page"

        popover.popdown()
        _drain_main_context()
        assert popover.entry.get_text() == ""
        assert (
            popover.views.get_visible_child_name() == "empty_page"
            or popover.views.get_visible_child_name() == "languages_page"
        )
        focus = window.get_focus()
        assert focus is None or not _is_descendant(focus, popover), "focus remains inside the closed language selector"
        assert anchor.get_mapped()
        settings.set_string.assert_not_called()
    finally:
        popover.popdown()
        window.destroy()
