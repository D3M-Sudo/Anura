# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
import time
from types import SimpleNamespace
from typing import ClassVar

import pytest

pytest.importorskip("gi")

import gi

gi.require_version("Adw", "1")
gi.require_version("Gio", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Adw, Gio, GLib, GObject, Gtk  # noqa: E402

Adw.init()

_resource_name = "io.github.d3m_sudo.anura.gresource"
_repo_root = os.path.dirname(os.path.dirname(__file__))
_resource_file = next(
    (
        candidate
        for candidate in (
            os.path.join(_repo_root, "builddir", "data", _resource_name),
            os.path.join(_repo_root, "data", _resource_name),
        )
        if os.path.isfile(candidate)
    ),
    None,
)
if _resource_file is None:
    pytest.skip("Anura GResource bundle is required for Preferences GTK integration tests", allow_module_level=True)
Gio.Resource.load(_resource_file)._register()

# Imports must follow GResource registration.
# isort: off
from anura.widgets.preferences_dialog import PreferencesDialog  # noqa: E402
# isort: on


_VIEWPORTS = [(360, 600), (640, 480), (900, 600), (1280, 800)]


class _LanguageManager(GObject.Object):
    __gsignals__: ClassVar[dict] = {
        "added": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "downloaded": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "download-failed": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "removed": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "downloading": (GObject.SignalFlags.RUN_LAST, None, (str, float)),
    }

    def __init__(self) -> None:
        super().__init__()
        from anura.models.language_item import LanguageItem

        self.items = {"eng": LanguageItem("eng", "English")}
        self.loading_languages: set[str] = set()

    def get_available_codes(self) -> list[str]:
        return list(self.items)

    def get_downloaded_codes(self) -> list[str]:
        return ["eng"]

    def get_downloaded_languages(self) -> list[str]:
        return ["English"]

    def get_language_item(self, code: str):
        return self.items.get(code)


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


def _make_dialog(monkeypatch) -> PreferencesDialog:
    manager = _LanguageManager()
    import anura.widgets.language_row as language_row_module
    import anura.widgets.preferences_dialog as dialog_module
    import anura.widgets.preferences_general_page as general_module
    import anura.widgets.preferences_languages_page as languages_module
    import anura.widgets.preferences_voice_page as voice_module

    monkeypatch.setattr(dialog_module, "get_language_manager", lambda: manager)
    monkeypatch.setattr(general_module, "get_language_manager", lambda: manager)
    monkeypatch.setattr(languages_module, "get_language_manager", lambda: manager)
    monkeypatch.setattr(language_row_module, "get_language_manager", lambda: manager)
    monkeypatch.setattr(languages_module.PreferencesLanguagesPage, "check_connection", lambda _self: None)
    monkeypatch.setattr(
        voice_module,
        "get_tts_service",
        lambda: SimpleNamespace(get_cached_supported_languages=lambda: {}),
    )
    return PreferencesDialog()


def _present_dialog(dialog: PreferencesDialog, width: int, height: int) -> Adw.Window:
    parent = Adw.Window()
    parent.set_default_size(width, height)
    parent.present()
    _wait_until(
        lambda: parent.get_mapped() and parent.get_width() > 0 and parent.get_height() > 0,
        f"map {width}x{height} parent window",
    )
    dialog.present(parent)
    _wait_until(
        lambda: dialog.get_mapped() and dialog.get_width() > 0 and dialog.get_height() > 0,
        f"present Preferences dialog at {width}x{height}",
    )
    _drain_main_context()
    return parent


def _assert_inside(widget: Gtk.Widget, ancestor: Gtk.Widget) -> None:
    assert widget.get_visible(), f"{type(widget).__name__} is not visible"
    assert widget.get_mapped(), f"{type(widget).__name__} is not mapped"
    available, bounds = widget.compute_bounds(ancestor)
    assert available, f"could not calculate {type(widget).__name__} bounds"
    assert bounds.origin.x >= -1, f"{type(widget).__name__} starts outside the left edge"
    assert bounds.origin.y >= -1, f"{type(widget).__name__} starts outside the top edge"
    assert bounds.origin.x + bounds.size.width <= ancestor.get_width() + 1, (
        f"{type(widget).__name__} extends beyond the right edge"
    )
    assert bounds.origin.y + bounds.size.height <= ancestor.get_height() + 1, (
        f"{type(widget).__name__} extends beyond the bottom edge"
    )


def _scroll_to(widget: Gtk.Widget, end: bool) -> None:
    scroller = widget.get_ancestor(Gtk.ScrolledWindow)
    if scroller is None:
        return
    adjustment = scroller.get_vadjustment()
    value = adjustment.get_upper() - adjustment.get_page_size() if end else adjustment.get_lower()
    adjustment.set_value(max(adjustment.get_lower(), value))
    _drain_main_context()


def _focus_target(widget: Gtk.Widget) -> Gtk.Widget:
    if widget.get_focusable():
        return widget
    child = widget.get_first_child()
    while child is not None:
        try:
            return _focus_target(child)
        except AssertionError:
            child = child.get_next_sibling()
    raise AssertionError(f"{type(widget).__name__} has no focusable widget or descendant")


def _is_descendant(widget: Gtk.Widget, ancestor: Gtk.Widget) -> bool:
    current = widget
    while current is not None:
        if current == ancestor:
            return True
        current = current.get_parent()
    return False


def _page_controls(dialog: PreferencesDialog):
    return [
        (dialog.general_page, dialog.general_page.color_scheme_combo, dialog.general_page.history_limit_row),
        (dialog.languages_page, dialog.languages_page.model_quality_combo, dialog.languages_page.list_view),
        (dialog.editor_page, dialog.editor_page.editor_line_numbers_switch, dialog.editor_page.editor_wrap_mode_combo),
        (dialog.voice_page, dialog.voice_page.volume_row, dialog.voice_page.tts_language_combo),
    ]


@pytest.mark.gtk
@pytest.mark.parametrize(("width", "height"), _VIEWPORTS)
def test_preferences_pages_keep_primary_controls_reachable_at_reference_viewports(
    monkeypatch, width: int, height: int
) -> None:
    """Each Preferences page and its first/last primary controls remain reachable in the viewport."""
    dialog = _make_dialog(monkeypatch)
    parent = _present_dialog(dialog, width, height)
    try:
        assert dialog.get_width() <= parent.get_width() + 1
        assert dialog.get_height() <= parent.get_height() + 1

        for page, first_control, last_control in _page_controls(dialog):
            dialog.set_visible_page(page)
            _wait_until(
                lambda page=page: dialog.get_visible_page() == page and page.get_mapped(),
                f"show {page.get_title()} Preferences page",
            )
            _scroll_to(first_control, end=False)
            _assert_inside(first_control, dialog)
            _scroll_to(last_control, end=True)
            _assert_inside(last_control, dialog)
    finally:
        dialog.force_close()
        parent.destroy()


@pytest.mark.gtk
def test_preferences_page_switching_does_not_retain_focus_on_hidden_controls(monkeypatch) -> None:
    """Programmatic focus entry works and page changes do not leave focus in a hidden page."""
    dialog = _make_dialog(monkeypatch)
    parent = _present_dialog(dialog, 900, 600)
    try:
        transitions = [
            (dialog.general_page, dialog.general_page.color_scheme_combo, dialog.languages_page),
            (dialog.languages_page, dialog.languages_page.model_quality_combo, dialog.editor_page),
            (dialog.editor_page, dialog.editor_page.editor_line_numbers_switch, dialog.voice_page),
            (dialog.voice_page, dialog.voice_page.volume_row, dialog.general_page),
        ]

        for current_page, control, next_page in transitions:
            dialog.set_visible_page(current_page)
            _wait_until(
                lambda current_page=current_page: dialog.get_visible_page() == current_page and current_page.get_mapped(),
                f"show {current_page.get_title()} before focus entry",
            )
            target = _focus_target(control)
            assert target.get_mapped()
            dialog.set_focus(target)
            _wait_until(
                lambda target=target: dialog.get_focus() == target,
                f"focus {type(target).__name__} on {current_page.get_title()}",
            )

            dialog.set_visible_page(next_page)
            _wait_until(
                lambda next_page=next_page: dialog.get_visible_page() == next_page and next_page.get_mapped(),
                f"switch to {next_page.get_title()}",
            )
            _drain_main_context()
            focus = dialog.get_focus()
            assert focus is None or focus.get_mapped(), "focus remains on an unmapped Preferences control"
            assert focus is None or not _is_descendant(focus, current_page), (
                f"focus remained inside hidden {current_page.get_title()} page after switching"
            )
    finally:
        dialog.force_close()
        parent.destroy()
