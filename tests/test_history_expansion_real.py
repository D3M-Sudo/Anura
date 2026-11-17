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

import os
import subprocess
import time

import pytest

pytest.importorskip("gi")

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
    controller.can_listen_for_language.return_value = True
    page = HistoryPage()
    page.settings = _Settings()
    page.setup(service, controller, controller)
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


def test_refresh_rebuilds_the_list_and_restores_the_expanded_row(real_history):
    from gi.repository import GLib

    page, _service, _controller = real_history
    expanded_row = page._rows[1]
    expanded_entry_id = next(entry_id for entry_id, row in page._row_entry_ids.items() if row is expanded_row)
    expanded_row.set_expanded(True)
    old_rows = list(page._rows)

    page.refresh()

    context = GLib.MainContext.default()
    while context.pending():
        context.iteration(False)

    assert len(page._rows) == 3
    assert all(new is not old for new, old in zip(page._rows, old_rows, strict=True))
    restored_row = page._row_entry_ids[expanded_entry_id]
    assert page._open_row is restored_row
    assert restored_row.get_expanded() is True
    assert sum(row.get_expanded() for row in page._rows) == 1


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


def test_editor_button_delegates_the_full_stored_text(real_history):
    from gi.repository import Gtk

    page, _service, controller = real_history
    row = page._rows[1]
    editor_buttons = [
        button for button in _find_all(row, Gtk.Button) if button.get_tooltip_text() == "Open in external editor"
    ]
    assert len(editor_buttons) == 1

    editor_buttons[0].emit("clicked")

    controller.open_entry_in_external_editor.assert_called_once_with(LONG_TEXT)


def test_copy_button_still_copies_the_full_text_with_the_row_expanded(real_history):
    from gi.repository import Gtk

    page, _service, controller = real_history
    long_row = page._rows[1]
    long_row.set_expanded(True)
    (copy_button,) = [
        button for button in _find_all(long_row, Gtk.Button) if button.get_tooltip_text() == "Copy text to clipboard"
    ]

    copy_button.emit("clicked")

    controller.copy_entry_text.assert_called_once_with(LONG_TEXT)


def _send_weston_key(key: str) -> None:
    """Inject a real XTest key event into Weston; GTK receives it through wl_keyboard."""
    display = os.environ.get("WESTON_HOST_DISPLAY")
    window_id = os.environ.get("WESTON_WINDOW_ID")
    if not display or not window_id:
        pytest.skip("real keyboard input requires the Weston X11 host display configured by CI")

    env = os.environ.copy()
    env["DISPLAY"] = display

    # Weston forwards X11 keyboard input to its currently focused Wayland
    # surface. Move the pointer into the center of the 1920x1080 Weston output
    # first, so the app surface under the pointer can acquire wl_pointer focus;
    # then focus the Weston host window before sending the XTest key event.
    subprocess.run(
        ["xdotool", "mousemove", "--sync", "--window", window_id, "960", "540"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    subprocess.run(
        ["xdotool", "windowfocus", "--sync", window_id],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )
    x11_focus = subprocess.run(
        ["xdotool", "getwindowfocus"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()
    pointer = subprocess.run(
        ["xdotool", "getmouselocation", "--shell"],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    ).stdout.strip()
    print(
        f"XTest preflight: Weston host={window_id}, X11 focus={x11_focus}, "
        f"pointer=({pointer.replace(chr(10), ', ')})"
    )
    subprocess.run(
        ["xdotool", "key", "--clearmodifiers", "--delay", "20", key],
        check=True,
        capture_output=True,
        text=True,
        env=env,
    )


def _install_keyboard_probe(window):
    """Record key events at the GTK toplevel before child event handling."""
    from gi.repository import Gtk

    received = []
    controller = Gtk.EventControllerKey()
    controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    controller.connect(
        "key-pressed",
        lambda _controller, keyval, keycode, state: received.append((keyval, state)) or False,
    )
    window.add_controller(controller)
    return received


def _wait_for_key_event(window, received, previous_count: int, key: str, timeout: float = 1.0):
    """Wait until GTK confirms receipt of the injected physical key event."""
    from gi.repository import GLib

    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        if len(received) > previous_count:
            return
        time.sleep(0.01)
    pytest.fail(
        f"Weston received the injected {key!r} request, but GTK's toplevel "
        "EventControllerKey did not observe the key event; "
        f"GTK window active={window.is_active()}, mapped={window.get_mapped()}, "
        f"focus={window.get_focus()!r}"
    )


def _wait_for_focus_change(
    window, previous_focus, key: str, timeout: float = 1.0, diagnostic_context=None
):
    """Pump GTK events until the observed key event changes focus."""
    from gi.repository import GLib

    context = GLib.MainContext.default()
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        focused = window.get_focus()
        if focused is not previous_focus:
            return focused
        time.sleep(0.01)
    pytest.fail(
        f"GTK received {key!r}, but focus remained on {previous_focus!r}; "
        f"GTK window active={window.is_active()}, mapped={window.get_mapped()}, "
        f"focus={window.get_focus()!r}, context={diagnostic_context!r}"
    )


def _tab_focus_cycle(window, starting_control, key: str, received, max_steps: int = 40):
    """Return the widgets reached by physical Tab/Shift+Tab input before wrapping."""
    assert starting_control.grab_focus()
    assert window.get_focus() is starting_control
    visited = {starting_control}
    focused = starting_control

    for _ in range(max_steps):
        previous_count = len(received)
        _send_weston_key(key)
        _wait_for_key_event(window, received, previous_count, key)
        focused = _wait_for_focus_change(window, focused, key)
        if focused is starting_control:
            return visited
        visited.add(focused)

    pytest.fail(f"{key} traversal did not wrap to its starting widget within {max_steps} events")


@pytest.fixture
def real_history_window(real_history):
    """Present the real HistoryPage so GTK can receive actual Wayland keyboard events."""
    from gi.repository import GLib, Gtk

    page, _service, _controller = real_history
    window = Gtk.Window(default_width=720, default_height=600)
    window.set_child(page)
    window.present()

    context = GLib.MainContext.default()
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        if window.get_mapped():
            break
        time.sleep(0.01)
    assert window.get_mapped(), "History test window was not mapped by Weston"

    received = _install_keyboard_probe(window)
    yield window, page, received

    window.destroy()


def _suffix_buttons(row):
    from gi.repository import Gtk

    buttons = _find_all(row, Gtk.Button)
    by_label = {button.get_tooltip_text(): button for button in buttons}
    return [
        by_label["Copy text to clipboard"],
        by_label["Open in external editor"],
        by_label["Listen to text"],
    ]


@pytest.mark.keyboard_traversal
def test_tab_and_shift_tab_reach_enabled_history_suffix_actions(real_history_window):
    """Actual Tab and Shift+Tab events traverse the enabled suffix actions."""
    window, page, received = real_history_window
    assert len(page._rows) == 3
    expected = [button for row in page._rows for button in _suffix_buttons(row)]
    assert all(button.get_sensitive() for button in expected)

    forward = _tab_focus_cycle(window, expected[0], "Tab", received)
    backward = _tab_focus_cycle(window, expected[0], "shift+Tab", received)
    assert set(expected) <= forward
    assert set(expected) <= backward


@pytest.mark.keyboard_traversal
def test_expanded_history_row_keeps_suffix_actions_in_keyboard_traversal(real_history_window):
    """Expanding a row preserves keyboard access to its suffix actions."""
    from gi.repository import Gtk

    window, page, received = real_history_window
    row = page._rows[1]
    buttons = _suffix_buttons(row)

    row.set_expanded(True)
    text_views = _find_all(row, Gtk.TextView)
    assert text_views
    assert buttons == _suffix_buttons(row)

    forward = _tab_focus_cycle(window, buttons[0], "Tab", received)
    backward = _tab_focus_cycle(window, buttons[0], "shift+Tab", received)
    assert set(buttons) <= forward
    assert set(buttons) <= backward


@pytest.mark.keyboard_traversal
def test_collapsing_focused_history_text_keeps_keyboard_navigation_usable(real_history_window):
    """After collapse, Tab must leave the expanded content if it still owns focus."""
    from gi.repository import GLib, Gtk

    window, page, received = real_history_window
    row = page._rows[1]
    row.set_expanded(True)
    (text_view,) = _find_all(row, Gtk.TextView)

    assert text_view.grab_focus()
    assert window.get_focus() is text_view

    row.set_expanded(False)
    assert row.get_expanded() is False

    # Let GTK process the collapse/layout before observing widget state.
    context = GLib.MainContext.default()
    deadline = time.monotonic() + 0.5
    while time.monotonic() < deadline:
        while context.pending():
            context.iteration(False)
        time.sleep(0.01)

    collapsed_state = {
        "visible": text_view.get_visible(),
        "effectively_visible": text_view.is_visible(),
        "mapped": text_view.get_mapped(),
        "has_focus": text_view.has_focus(),
        "window_focus_is_text_view": window.get_focus() is text_view,
    }

    if window.get_focus() is text_view:
        previous_count = len(received)
        _send_weston_key("Tab")
        _wait_for_key_event(window, received, previous_count, "Tab")
        focused = _wait_for_focus_change(
            window, text_view, "Tab", diagnostic_context=collapsed_state
        )

        assert focused is not text_view, (
            "Tab was delivered but focus remained on the collapsed TextView; "
            f"observed collapsed widget state: {collapsed_state}"
        )
    else:
        assert window.get_focus() is not text_view


@pytest.mark.keyboard_traversal
def test_expanding_another_history_row_preserves_keyboard_traversal(real_history_window):
    """Single-open-row behavior remains compatible with actual keyboard traversal."""
    window, page, received = real_history_window
    first, second, _third = page._rows
    first.set_expanded(True)
    second.set_expanded(True)

    assert first.get_expanded() is False
    assert second.get_expanded() is True

    expected = [button for row in page._rows for button in _suffix_buttons(row)]
    forward = _tab_focus_cycle(window, expected[0], "Tab", received)
    backward = _tab_focus_cycle(window, expected[0], "shift+Tab", received)
    assert set(expected) <= forward
    assert set(expected) <= backward
