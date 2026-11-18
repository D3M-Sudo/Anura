# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""GTK integration coverage for Extracted and History responsive geometry."""

import os
import time
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("gi")

import gi

gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")

from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

Adw.init()

# Template-backed widgets require the compiled GResource bundle.
_resource_path = os.path.join(os.path.dirname(__file__), "..", "data", "io.github.d3msudo.anura.gresource")
if os.path.exists(_resource_path):
    _resource = Gio.Resource.load(_resource_path)
    _resource._register()
else:
    pytest.skip("Anura GResource bundle is required for GTK template integration tests", allow_module_level=True)

# These imports must follow GResource registration above.
# isort: off
from anura.services.history_service import HistoryService  # noqa: E402
from anura.widgets.extracted_page import ExtractedPage  # noqa: E402
from anura.widgets.history_page import HistoryPage  # noqa: E402
# isort: on


_VIEWPORTS = [(360, 600), (640, 480), (900, 600), (1280, 800)]
_LONG_OCR_TEXT = "\n".join(f"OCR line {index:04d}: " + ("recognized content " * 8) for index in range(500))
_LONG_HISTORY_TEXT = "Stored OCR content with enough words to wrap across the expanded text area. " * 900


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


def _present(widget: Gtk.Widget, width: int, height: int) -> Gtk.Window:
    window = Gtk.Window()
    window.set_default_size(width, height)
    window.set_child(widget)
    window.present()
    _wait_until(
        lambda: window.get_mapped() and window.get_width() > 0 and window.get_height() > 0 and widget.get_mapped(),
        f"allocate {width}x{height} test window",
    )
    _drain_main_context()
    return window


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


def _descendants(widget: Gtk.Widget):
    child = widget.get_first_child()
    while child is not None:
        yield child
        yield from _descendants(child)
        child = child.get_next_sibling()


@pytest.mark.gtk
@pytest.mark.parametrize(("width", "height"), _VIEWPORTS)
def test_extracted_long_ocr_text_scrolls_without_clipping_primary_actions(width: int, height: int) -> None:
    """Long OCR content belongs to its scroller while primary actions remain in-window."""
    with patch("anura.widgets.extracted_page.get_share_service") as get_share_service:
        get_share_service.return_value.providers.return_value = []
        page = ExtractedPage()

    # The application normally resolves these actions through AnuraApplication.
    # Remove the action dependency so this test measures widget geometry and reachability.
    for button in (page.grab_btn, page.text_copy_btn, page.listen_btn):
        button.set_action_name(None)
        button.set_sensitive(True)

    page.buffer.set_text(_LONG_OCR_TEXT)
    window = _present(page, width, height)
    try:
        scroller = page.text_view.get_ancestor(Gtk.ScrolledWindow)
        assert scroller is not None
        _wait_until(
            lambda: (
                scroller.get_vadjustment().get_page_size() > 0
                and scroller.get_vadjustment().get_upper() > scroller.get_vadjustment().get_page_size()
            ),
            "lay out long Extracted OCR content in its vertical scroller",
        )
        adjustment = scroller.get_vadjustment()
        assert adjustment.get_upper() > adjustment.get_page_size()
        assert scroller.get_width() > 0
        assert scroller.get_height() > 0
        assert page.text_view.get_mapped()

        for control in (page.grab_btn, page.text_copy_btn, page.share_button, page.listen_btn):
            _assert_inside_window(control, window)
            assert control.get_focusable(), f"{type(control).__name__} is not keyboard-focusable"
            assert control.is_sensitive(), f"{type(control).__name__} is not actionable"
        _assert_inside_window(page.stats_label, window)
    finally:
        window.destroy()


@pytest.mark.gtk
@pytest.mark.parametrize(("width", "height"), _VIEWPORTS)
def test_history_long_expanded_text_scrolls_and_row_actions_remain_reachable(width: int, height: int, tmp_path) -> None:
    """Expanded history text scrolls independently and keeps Copy/Editor/TTS actions in bounds."""
    service = HistoryService(base_dir=tmp_path)
    for index in range(40):
        service.record(f"History entry {index:02d}: {_LONG_HISTORY_TEXT}", "eng")

    page = HistoryPage()
    page.settings = MagicMock()
    page.settings.get_boolean.return_value = True
    tts_controller = MagicMock()
    tts_controller.can_listen_for_language.return_value = True
    page.setup(service, tts_controller=tts_controller)
    window = _present(page, width, height)

    try:
        list_scroller = page.history_list.get_ancestor(Gtk.ScrolledWindow)
        assert list_scroller is not None
        _wait_until(
            lambda: (
                list_scroller.get_vadjustment().get_page_size() > 0
                and list_scroller.get_vadjustment().get_upper() > list_scroller.get_vadjustment().get_page_size()
            ),
            "lay out overflowing History entries",
        )

        entry = service.get_entries()[0]
        row = page._row_entry_ids[entry.id]
        row.set_expanded(True)
        _wait_until(lambda: row.get_expanded() and row in page._content_built, "expand the selected History row")
        _drain_main_context()

        text_scrollers = [
            child
            for child in _descendants(row)
            if isinstance(child, Gtk.ScrolledWindow) and isinstance(child.get_child(), Gtk.TextView)
        ]
        assert len(text_scrollers) == 1, "expanded History row must contain one dedicated text scroller"
        text_scroller = text_scrollers[0]
        _wait_until(
            lambda: (
                text_scroller.get_vadjustment().get_page_size() > 0
                and text_scroller.get_vadjustment().get_upper() > text_scroller.get_vadjustment().get_page_size()
            ),
            "lay out overflowing expanded History text",
        )
        assert text_scroller.get_height() <= 241, "expanded text area exceeded its 240px height cap"

        action_buttons = [
            child for child in _descendants(row)
            if isinstance(child, Gtk.Button)
            and child.get_icon_name()
            in {"edit-copy-symbolic", "document-edit-symbolic", "media-playback-start-symbolic"}
        ]
        assert len(action_buttons) == 3, "History row must expose Copy, Editor and TTS action buttons"
        for button in action_buttons:
            _assert_inside_window(button, window)
            assert button.get_focusable(), f"{button.get_tooltip_text()} action is not keyboard-focusable"
            assert button.is_sensitive(), f"{button.get_tooltip_text()} action is not actionable"
    finally:
        window.destroy()
        page.cleanup()
