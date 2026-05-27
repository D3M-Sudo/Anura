# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import pytest

pytest.importorskip("gi")

from anura.services.host_screenshot_fallback import build_fallback_argv


def test_build_fallback_argv_scrot() -> None:
    """The tool must use scrot with -s and the output path."""
    argv = build_fallback_argv("scrot", "/tmp/out.png")
    assert argv == ["scrot", "-s", "/tmp/out.png"]


def test_build_fallback_argv_gnome_screenshot() -> None:
    """The tool must use gnome-screenshot with -a -f and the output path."""
    argv = build_fallback_argv("gnome-screenshot", "/tmp/out.png")
    assert argv == ["gnome-screenshot", "-a", "-f", "/tmp/out.png"]


def test_build_fallback_argv_invalid_tool() -> None:
    """The tool must raise ValueError for invalid or unauthorized tools."""
    with pytest.raises(ValueError, match="Unsupported or invalid screenshot tool"):
        build_fallback_argv("invalid-tool", "/tmp/out.png")


def test_build_fallback_argv_security_check() -> None:
    """The tool must reject potentially malicious tool names."""
    with pytest.raises(ValueError):
        build_fallback_argv("scrot; rm -rf /", "/tmp/out.png")
