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
from anura.services.screenshot.mss_provider import MssScreenshotProvider
from anura.services.screenshot.portal_provider import PortalProvider


class TestMssScreenshotProvider:
    @pytest.fixture
    def provider(self):
        return MssScreenshotProvider()

    def test_availability_no_display(self, provider):
        with patch.dict(os.environ, {}, clear=True):
            assert provider.is_available() is False

    def test_availability_wayland(self, provider):
        with patch.dict(os.environ, {"DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0"}):
            assert provider.is_available() is False

    def test_availability_x11(self, provider):
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            assert provider.is_available() is True

    @patch("anura.services.screenshot.mss_provider.mss.mss")
    def test_capture_starts_thread(self, mock_mss, provider):
        callback = MagicMock()
        with patch("anura.services.screenshot.mss_provider.threading.Thread") as mock_thread:
            provider.capture("eng", False, callback)
            assert mock_thread.called


class TestScreenshotProviderFactory:
    def test_get_provider_returns_portal(self):
        provider = ScreenshotProviderFactory.get_provider()
        assert isinstance(provider, PortalProvider)

    def test_get_fallback_provider_available(self):
        with patch.object(MssScreenshotProvider, "is_available", return_value=True):
            provider = ScreenshotProviderFactory.get_fallback_provider()
            assert isinstance(provider, MssScreenshotProvider)

    def test_get_fallback_provider_unavailable(self):
        with patch.object(MssScreenshotProvider, "is_available", return_value=False):
            provider = ScreenshotProviderFactory.get_fallback_provider()
            assert provider is None
