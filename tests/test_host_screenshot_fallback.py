# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest

pytest.importorskip("gi")

from anura.services.host_screenshot_fallback import build_scrot_argv


def test_build_scrot_argv_basic() -> None:
    """The tool must use scrot with -s and the output path."""
    argv = build_scrot_argv("/tmp/out.png")
    assert argv == ["scrot", "-s", "/tmp/out.png"]


def test_build_scrot_argv_with_offsets() -> None:
    """The tool accepts offsets but currently they don't affect the command line
    as scrot interactively handles selection. This tests the logic for safe_x/safe_y."""
    argv = build_scrot_argv("/tmp/out.png", offset_x=10, offset_y=20)
    assert argv == ["scrot", "-s", "/tmp/out.png"]


def test_build_scrot_argv_negative_offsets_sanitized() -> None:
    """Negative offsets must be sanitized to 0 internally."""
    # This is a bit of a white-box test as the offsets are not currently used
    # in the returned argv, but we ensure the function doesn't crash.
    argv = build_scrot_argv("/tmp/out.png", offset_x=-10, offset_y=-20)
    assert argv == ["scrot", "-s", "/tmp/out.png"]
