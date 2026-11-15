# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from anura.window import _initial_window_size

pytestmark = pytest.mark.gtk


def test_first_run_uses_reasonable_default_size() -> None:
    assert _initial_window_size(-1, -1, 1920, 1080) == (900, 600)


def test_first_run_size_is_clamped_for_small_screen() -> None:
    width, height = _initial_window_size(-1, -1, 800, 600)
    assert width <= 720
    assert height <= 540
    assert width >= 320
    assert height >= 240


def test_saved_dimensions_are_restored_with_monitor_clamping() -> None:
    assert _initial_window_size(1200, 900, 1920, 1080) == (1200, 900)
    assert _initial_window_size(1200, 900, 800, 600) == (720, 540)


def test_initial_size_stays_within_available_bounds_on_very_small_monitor() -> None:
    assert _initial_window_size(-1, -1, 300, 250) == (270, 225)


def test_window_blueprint_does_not_force_minimums_above_geometry_clamp() -> None:
    from pathlib import Path

    blueprint = Path("data/ui/window.blp").read_text(encoding="utf-8")
    assert "width-request: 360;" not in blueprint
    assert "height-request: 360;" not in blueprint


@pytest.mark.parametrize(
    ("screen_width", "screen_height"),
    [(360, 600), (640, 480), (900, 600), (1280, 800)],
)
def test_initial_window_size_respects_m1_viewport_bounds(screen_width: int, screen_height: int) -> None:
    width, height = _initial_window_size(-1, -1, screen_width, screen_height)
    assert width <= int(screen_width * 0.9)
    assert height <= int(screen_height * 0.9)


def _window_helper(name: str):
    from anura import window

    helper = getattr(window, name, None)
    assert callable(helper), f"anura.window.{name} must be implemented"
    return helper


class _FakeMonitor:
    def __init__(self, width: int, height: int) -> None:
        from types import SimpleNamespace

        self._geometry = SimpleNamespace(width=width, height=height)

    def get_geometry(self):
        return self._geometry


class _FakeMonitorModel:
    def __init__(self, monitors: list[_FakeMonitor]) -> None:
        self._monitors = monitors

    def get_n_items(self) -> int:
        return len(self._monitors)

    def get_item(self, index: int) -> _FakeMonitor:
        return self._monitors[index]


class _FakeDisplay:
    def __init__(self, monitors: list[_FakeMonitor], surface_monitor: _FakeMonitor | None = None) -> None:
        self._monitors = _FakeMonitorModel(monitors)
        self._surface_monitor = surface_monitor

    def get_monitors(self):
        return self._monitors

    def get_monitor_at_surface(self, _surface):
        return self._surface_monitor


def test_monitor_selection_prefers_the_monitor_containing_the_window_surface() -> None:
    first = _FakeMonitor(1920, 1080)
    second = _FakeMonitor(1280, 1024)
    display = _FakeDisplay([first, second], surface_monitor=second)

    assert _window_helper("_select_monitor_for_surface")(display, object()) is second


def test_monitor_selection_falls_back_to_largest_monitor_geometry() -> None:
    first = _FakeMonitor(1280, 720)
    second = _FakeMonitor(1920, 1080)
    display = _FakeDisplay([first, second])

    assert _window_helper("_select_monitor_for_surface")(display) is second


def test_monitor_size_uses_gdk_monitor_geometry() -> None:
    monitor = _FakeMonitor(1440, 900)
    assert _window_helper("_monitor_size")(monitor) == (1440, 900)
    assert _window_helper("_monitor_size")(None) == (0, 0)


def test_window_size_is_persisted_only_for_normal_window_state() -> None:
    should_persist = _window_helper("_should_persist_window_size")

    assert should_persist(False, False) is True
    assert should_persist(True, False) is False
    assert should_persist(False, True) is False
    assert should_persist(True, True) is False


def test_shortcuts_overlay_is_resizable_and_keeps_its_content_scrollable() -> None:
    from pathlib import Path

    blueprint = Path("data/ui/shortcuts_overlay.blp").read_text(encoding="utf-8")
    assert "resizable: true;" in blueprint
    assert "Gtk.ScrolledWindow" in blueprint
    assert "vscrollbar-policy: automatic;" in blueprint


def test_preferences_dialog_does_not_force_a_fixed_minimum_window_size() -> None:
    from pathlib import Path

    blueprint = Path("data/ui/preferences_dialog.blp").read_text(encoding="utf-8")
    assert "width-request:" not in blueprint
    assert "height-request:" not in blueprint


def test_extracted_headerbar_keeps_the_compact_action_hierarchy() -> None:
    from pathlib import Path

    blueprint = Path("data/ui/extracted_page.blp").read_text(encoding="utf-8")
    headerbar = blueprint.split("Adw.HeaderBar headerbar {", maxsplit=1)[1].split("\n    }", maxsplit=1)[0]
    assert headerbar.count("[start]") <= 2
    assert headerbar.count("[end]") <= 1
