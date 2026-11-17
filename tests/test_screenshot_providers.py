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
    from gi.repository import GLib
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
import anura.services.screenshot.legacy_provider
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

        # The provider uses SubprocessLauncher (not Subprocess.new) so that
        # X11-critical env vars (DISPLAY, XAUTHORITY) are explicitly forwarded
        # into the scrot subprocess inside the Flatpak sandbox.
        assert mock_gio.SubprocessLauncher.new.called
        args = mock_launcher.spawnv.call_args[0][0]
        assert args[0] == "/usr/bin/scrot"
        assert "-s" in args

    @patch("anura.services.screenshot.legacy_provider.Gio")
    @patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary")
    def test_capture_spawn_failure_removes_temp_file(self, mock_resolve, mock_gio, provider, tmp_path):
        """F4: a failed spawn must not leak the pre-created temp file."""
        mock_resolve.return_value = "/usr/bin/scrot"
        leaked_path = tmp_path / "anura-shot-x.png"

        def failing_mkstemp(*_a, **_k):
            fd = os.open(str(leaked_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            return fd, str(leaked_path)

        with patch(
            "anura.services.screenshot.legacy_provider.tempfile.mkstemp",
            side_effect=failing_mkstemp,
        ):
            mock_gio.SubprocessLauncher.new.side_effect = GLib.Error("spawn failed")  # type: ignore[attr-defined]

            callback = MagicMock()
            provider.capture("eng", False, callback)

        assert callback.called
        assert callback.call_args[0][0] is False
        assert not leaked_path.exists(), "temp file leaked after failed spawn"

    @patch("anura.services.screenshot.legacy_provider.Gio")
    @patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary")
    def test_capture_runtime_spawn_error_removes_temp_file(self, mock_resolve, mock_gio, provider, tmp_path):
        """F4: RuntimeError path must also clean up the temp file."""
        mock_resolve.return_value = "/usr/bin/scrot"
        leaked_path = tmp_path / "anura-shot-y.png"

        def failing_mkstemp(*_a, **_k):
            fd = os.open(str(leaked_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            return fd, str(leaked_path)

        with patch(
            "anura.services.screenshot.legacy_provider.tempfile.mkstemp",
            side_effect=failing_mkstemp,
        ):
            mock_gio.SubprocessLauncher.new.side_effect = RuntimeError("no launcher")

            callback = MagicMock()
            provider.capture("eng", False, callback)

        assert callback.called
        assert callback.call_args[0][0] is False
        assert not leaked_path.exists(), "temp file leaked after RuntimeError"

    def test_discard_failed_output_is_tolerant(self, tmp_path):
        """The helper must not raise for missing files or unreadable paths."""
        missing = str(tmp_path / "never-created.png")
        LegacyX11Provider._discard_failed_output(missing)  # no raise

        victim = tmp_path / "victim.png"
        victim.touch()
        LegacyX11Provider._discard_failed_output(str(victim))
        assert not victim.exists()


class TestScrotBinarySafety:
    """F5: reject group/world-writable scrot binaries."""

    @staticmethod
    def _make_scrot(tmp_path, mode: int) -> tuple[str, str]:
        binary = tmp_path / "scrot"
        binary.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        binary.chmod(mode)
        return str(binary), str(tmp_path)

    def test_rejects_world_writable(self, tmp_path, monkeypatch):
        _scrot, scrot_dir = self._make_scrot(tmp_path, 0o757)
        monkeypatch.setattr("anura.services.screenshot.legacy_provider._FLATPAK_SCROT_BIN", str(tmp_path / "none"))
        monkeypatch.setenv("PATH", scrot_dir)
        assert anura.services.screenshot.legacy_provider._resolve_scrot_binary() is None

    def test_rejects_group_writable(self, tmp_path, monkeypatch):
        _scrot, scrot_dir = self._make_scrot(tmp_path, 0o775)
        monkeypatch.setattr("anura.services.screenshot.legacy_provider._FLATPAK_SCROT_BIN", str(tmp_path / "none"))
        monkeypatch.setenv("PATH", scrot_dir)
        assert anura.services.screenshot.legacy_provider._resolve_scrot_binary() is None

    def test_accepts_owner_only_executable(self, tmp_path, monkeypatch):
        scrot, scrot_dir = self._make_scrot(tmp_path, 0o755)
        monkeypatch.setattr("anura.services.screenshot.legacy_provider._FLATPAK_SCROT_BIN", str(tmp_path / "none"))
        monkeypatch.setenv("PATH", scrot_dir)
        result = anura.services.screenshot.legacy_provider._resolve_scrot_binary()
        assert result == scrot

    def test_rejects_flatpak_path_writable(self, tmp_path, monkeypatch):
        binary = tmp_path / "scrot"
        binary.write_text("#!/bin/sh\n", encoding="utf-8")
        binary.chmod(0o757)
        monkeypatch.setattr("anura.services.screenshot.legacy_provider._FLATPAK_SCROT_BIN", str(binary))
        monkeypatch.setenv("PATH", str(tmp_path / "empty"))
        assert anura.services.screenshot.legacy_provider._resolve_scrot_binary() is None

    def test_non_executable_rejected(self, tmp_path, monkeypatch):
        _scrot, scrot_dir = self._make_scrot(tmp_path, 0o644)
        monkeypatch.setattr("anura.services.screenshot.legacy_provider._FLATPAK_SCROT_BIN", str(tmp_path / "none"))
        monkeypatch.setenv("PATH", scrot_dir)
        assert anura.services.screenshot.legacy_provider._resolve_scrot_binary() is None

    def test_helper_tolerates_missing_file(self, tmp_path):
        from anura.services.screenshot.legacy_provider import _is_safe_executable

        assert _is_safe_executable(tmp_path / "missing") is False


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
