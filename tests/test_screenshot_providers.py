# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("gi")

# Mock only what is missing
import gi

try:
    from gi.repository import Gio  # noqa: F401
except ImportError:
    mock_gio = MagicMock()
    sys.modules["gi.repository.Gio"] = mock_gio
    gi.repository.Gio = mock_gio

try:
    from gi.repository import GLib  # noqa: F401
except ImportError:
    mock_glib = MagicMock()
    sys.modules["gi.repository.GLib"] = mock_glib
    gi.repository.GLib = mock_glib

try:
    from gi.repository import Xdp  # noqa: F401
except ImportError:
    mock_xdp = MagicMock()
    sys.modules["gi.repository.Xdp"] = mock_xdp
    gi.repository.Xdp = mock_xdp

from anura.services.screenshot.factory import ScreenshotProviderFactory
from anura.services.screenshot.legacy_provider import LegacyX11Provider
from anura.services.screenshot.portal_provider import PortalProvider


class TestLegacyX11Provider:
    @pytest.fixture
    def provider(self):
        return LegacyX11Provider()

    def test_availability_no_display(self, provider):
        with patch.dict(os.environ, {}, clear=True):
            assert provider.is_available() is False

    def test_availability_wayland(self, provider):
        with patch.dict(os.environ, {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"}):
            assert provider.is_available() is False

    @patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary")
    def test_availability_x11_with_scrot(self, mock_resolve, provider):
        mock_resolve.return_value = "/usr/bin/scrot"
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            assert provider.is_available() is True

    @patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary")
    def test_availability_x11_no_scrot(self, mock_resolve, provider):
        mock_resolve.return_value = None
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            assert provider.is_available() is False

    @patch("anura.services.screenshot.legacy_provider.Gio")
    @patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary")
    def test_capture_spawns_process(self, mock_resolve, mock_gio, provider):
        mock_resolve.return_value = "/usr/bin/scrot"
        mock_proc = MagicMock()
        mock_launcher = MagicMock()
        mock_launcher.spawnv.return_value = mock_proc
        mock_gio.SubprocessLauncher.new.return_value = mock_launcher

        callback = MagicMock()
        provider.capture("eng", False, callback)

        # The provider now uses SubprocessLauncher (not Subprocess.new) so that
        # X11-critical env vars (DISPLAY, XAUTHORITY) are explicitly forwarded.
        assert mock_gio.SubprocessLauncher.new.called
        args = mock_launcher.spawnv.call_args[0][0]
        assert args[0] == "/usr/bin/scrot"
        assert "-s" in args


class TestScreenshotProviderFactory:
    def test_get_provider_returns_portal(self):
        provider = ScreenshotProviderFactory.get_provider()
        assert isinstance(provider, PortalProvider)

    def test_get_fallback_provider_available(self):
        with patch.object(LegacyX11Provider, "is_available", return_value=True):
            provider = ScreenshotProviderFactory.get_fallback_provider()
            assert isinstance(provider, LegacyX11Provider)

    def test_get_fallback_provider_unavailable(self):
        with patch.object(LegacyX11Provider, "is_available", return_value=False):
            provider = ScreenshotProviderFactory.get_fallback_provider()
            assert provider is None
