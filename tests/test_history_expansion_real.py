# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""History V2 expandable rows against the real HistoryPage and real GTK widgets.

The headless tests in test_history_ui.py check the page against mocks. These build the
real page (real template, `Adw.ExpanderRow`, `Gtk.TextView`) so that what the user sees
is what is asserted: what exists before a row is opened, what is shown after, the single
open row, the bounded height and the cost of very long text.
"""

import pytest

pytest.importorskip("gi")

import time
from unittest.mock import MagicMock

from anura.services.history_service import HistoryService

LONG_TEXT = "first line of the extracted text\n" + ("a long wrapped sentence of text " * 40) + "\nlast line"


class _Settings:
    def get_boolean(self, key: str) -> bool:
        return key == "history-enabled"


def _find_all(widget, widget_type):
    found = []
    child = widget.get_first_child()
    while child is not None:
        if isinstance(child, widget_type):
            found.append(child)
        found.extend(_find_all(child, widget_type))
        child = child.get_next_sibling()
    return found


def _settle(scrolled, max_seconds: float = 5.0) -> int:
    """Pump the main loop until the area's height stops changing; return it.

    A text view lays its text out incrementally, so the height right after the row is
    opened is only an estimate.
    """
    from gi.repository import GLib

    context = GLib.MainContext.default()
    deadline = time.monotonic() + max_seconds
    last_height, stable_since = -1, time.monotonic()
    while time.monotonic() < deadline:
        context.iteration(False)
        height = scrolled.get_height()
        if height != last_height:
            last_height, stable_since = height, time.monotonic()
        elif height > 0 and time.monotonic() - stable_since > 0.4:
            break
        time.sleep(0.01)
    return last_height


@pytest.fixture
def real_history(tmp_path):
    """A real HistoryPage with three entries (newest first: 'short', LONG_TEXT, 'oldest')."""
    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gdk", "4.0")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, Gdk, Gtk

    from anura.core.resources import load_gresource_bundle

    if not Gtk.init_check() or Gdk.Display.get_default() is None:
        pytest.skip("no GDK display available")
    if not load_gresource_bundle():
        pytest.skip("GResource bundle not available")
    Adw.init()

    from anura.widgets.history_page import HistoryPage

    service = HistoryService(base_dir=tmp_path)
    service.record("oldest entry", "eng")
    service.record(LONG_TEXT, "eng")
    service.record("short", "eng")

    controller = MagicMock()
    controller.copy_entry_text.return_value = True
    page = HistoryPage()
    page.settings = _Settings()
    page.setup(service, controller)
    yield page, service, controller
    page.cleanup()


def test_rows_start_collapsed_and_have_no_text_area(real_history):
    from gi.repository import Adw, Gtk

    page, _service, _controller = real_history

    assert len(page._rows) == 3
    for row in page._rows:
        assert isinstance(row, Adw.ExpanderRow)
        assert row.get_expanded() is False
        assert _find_all(row, Gtk.TextView) == []


def test_expanding_a_row_shows_the_full_stored_text(real_history):
    from gi.repository import Gtk

    page, _service, _controller = real_history
    long_row = page._rows[1]

    long_row.set_expanded(True)

    (text_view,) = _find_all(long_row, Gtk.TextView)
    buffer = text_view.get_buffer()
    shown = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
    assert shown == LONG_TEXT
    assert text_view.get_editable() is False
    # The header keeps showing only the first line.
    assert long_row.get_title() == "first line of the extracted text"


def test_text_area_is_built_once_even_if_the_row_is_reopened(real_history):
    from gi.repository import Gtk

    page, _service, _controller = real_history
    row = page._rows[0]

    row.set_expanded(True)
    row.set_expanded(False)
    row.set_expanded(True)

    assert len(_find_all(row, Gtk.TextView)) == 1


def test_expanding_another_row_collapses_the_previous_one(real_history):
    page, _service, _controller = real_history
    first, second, third = page._rows

    first.set_expanded(True)
    second.set_expanded(True)

    assert first.get_expanded() is False
    assert second.get_expanded() is True
    third.set_expanded(True)
    assert [row.get_expanded() for row in (first, second, third)] == [False, False, True]
    third.set_expanded(False)
    assert [row.get_expanded() for row in (first, second, third)] == [False, False, False]


def test_refresh_rebuilds_the_list_with_every_row_collapsed(real_history):
    page, _service, _controller = real_history
    page._rows[1].set_expanded(True)
    old_rows = list(page._rows)

    page.refresh()

    assert len(page._rows) == 3
    assert all(row.get_expanded() is False for row in page._rows)
    assert all(new is not old for new, old in zip(page._rows, old_rows, strict=True))
    assert page._open_row is None


def test_text_area_height_is_capped_and_short_text_is_not_padded(real_history):
    """Rendered heights, measured once the layout has settled in a presented window."""
    from gi.repository import Gtk

    page, service, _controller = real_history
    service.record("long " * 4_000, "eng")  # 20 KB: far taller than the cap
    page.refresh()
    long_row, short_row = page._rows[0], page._rows[1]  # newest first: the 20 KB entry, then "short"
    window = Gtk.Window(default_width=560, default_height=700)
    window.set_child(page)
    window.present()

    long_row.set_expanded(True)
    (long_scrolled,) = _find_all(long_row, Gtk.ScrolledWindow)
    long_height = _settle(long_scrolled)
    long_row.set_expanded(False)
    short_row.set_expanded(True)
    (short_scrolled,) = _find_all(short_row, Gtk.ScrolledWindow)
    short_height = _settle(short_scrolled)
    window.destroy()

    assert long_scrolled.get_max_content_height() == 240
    assert 200 <= long_height <= 240  # filled and capped; the rest scrolls
    assert 0 < short_height < 100  # a one-word entry is not padded to the cap


def test_very_long_text_expands_without_blocking(real_history):
    """Regression guard for the widget choice: a Gtk.Label took 24 s with 300 KB of text."""
    from gi.repository import Gtk

    page, service, _controller = real_history
    huge = ("lorem ipsum dolor sit amet " * 12_000)[:300_000]
    service.record(huge, "eng")
    page.refresh()
    row = page._rows[0]

    started = time.monotonic()
    row.set_expanded(True)
    (scrolled,) = _find_all(row, Gtk.ScrolledWindow)
    scrolled.measure(Gtk.Orientation.VERTICAL, 500)

    assert time.monotonic() - started < 15


def test_copy_button_still_copies_the_full_text_with_the_row_expanded(real_history):
    from gi.repository import Gtk

    page, _service, controller = real_history
    long_row = page._rows[1]
    long_row.set_expanded(True)
    (copy_button,) = [
        w for w, _hid in page._row_handlers if isinstance(w, Gtk.Button) and w in _find_all(long_row, Gtk.Button)
    ]

    copy_button.emit("clicked")

    controller.copy_entry_text.assert_called_once_with(LONG_TEXT)
