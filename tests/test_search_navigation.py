#!/usr/bin/env python3
# tests/test_search_navigation.py
"""GTK-marked tests for ExtractedPage search navigation (audit items F6+F7).

These require GtkSource-5 typelibs and a display; they are skipped by the
headless suite (``-m 'not gtk'``) and run in CI / on developer machines
with the full stack installed.
"""

import pytest

gtk = pytest.importorskip("gi")

gtk.require_version("GtkSource", "5")
from gi.repository import GtkSource  # noqa: E402

from anura.widgets.extracted_page import ExtractedPage  # noqa: E402

pytestmark = pytest.mark.gtk


@pytest.fixture
def page():
    widget = ExtractedPage()
    widget.buffer.set_text("alpha beta gamma beta delta\n")
    yield widget


def _selected_text(page) -> str:
    start, end = page.buffer.get_selection_bounds()
    return page.buffer.get_text(start, end, False)


def test_search_finds_first_match(page):
    page.search_entry.set_text("beta")
    page._on_search_text_changed(page.search_entry)
    assert _selected_text(page) == "beta"


def test_next_navigates_forward(page):
    page.search_entry.set_text("beta")
    page._on_search_text_changed(page.search_entry)
    page._on_search_next()
    assert _selected_text(page) == "beta"


def test_prev_navigates_backward(page):
    page.search_entry.set_text("beta")
    page._on_search_text_changed(page.search_entry)
    page._on_search_next()
    page._on_search_prev()
    # after prev from the 2nd occurrence we are back on the 1st
    sel_start = page.buffer.get_selection_bounds()[0].get_offset()
    assert sel_start == 6


def test_wrap_around_defaults_enabled(page):
    assert page.search_settings.get_wrap_around() is True


def test_next_wraps_around_past_last_match(page):
    page.search_entry.set_text("beta")
    page._on_search_text_changed(page.search_entry)  # 1st occurrence
    page._on_search_next()  # 2nd occurrence
    page._on_search_next()  # must wrap back to 1st occurrence
    sel_start = page.buffer.get_selection_bounds()[0].get_offset()
    assert sel_start == 6


def test_search_context_methods_exist(page):
    """Regression guard: forward/backward (not forward2/backward2)."""
    ctx = page.search_context
    assert isinstance(ctx, GtkSource.SearchContext)
    assert callable(getattr(ctx, "forward", None))
    assert callable(getattr(ctx, "backward", None))
