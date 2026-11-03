# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from anura.window import _initial_window_size


def test_first_run_uses_reasonable_default_size() -> None:
    assert _initial_window_size(-1, -1, 1920, 1080) == (1000, 700)


def test_first_run_size_is_clamped_for_small_screen() -> None:
    width, height = _initial_window_size(-1, -1, 800, 600)
    assert width <= 720
    assert height <= 540
    assert width >= 320
    assert height >= 240


def test_saved_dimensions_are_restored_with_monitor_clamping() -> None:
    assert _initial_window_size(1200, 900, 1920, 1080) == (1200, 900)
    assert _initial_window_size(1200, 900, 800, 600) == (720, 540)
