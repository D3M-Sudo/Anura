# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import sys
from unittest.mock import MagicMock, patch

import pytest

pytest.importorskip("gi")

# Mock missing components
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

try:
    from gi.repository import GObject  # noqa: F401
except ImportError:
    mock_gobject = MagicMock()

    class MockGObject:
        def __init__(self, *args, **kwargs):
            pass

        @staticmethod
        def emit(*args, **kwargs):
            pass

    mock_gobject.GObject = MockGObject
    sys.modules["gi.repository.GObject"] = mock_gobject
    gi.repository.GObject = mock_gobject

# Now import the service
from anura.services.screenshot_service import ScreenshotService


class TestScreenshotServiceEnterprise:
    """
    Enterprise-grade unit tests for ScreenshotService.
    Focuses on logic paths and fallbacks safe for VM/headless.
    """

    @pytest.fixture
    def service(self):
        with patch("anura.services.screenshot_service._configure_tesseract_path"):
            # Minimal init to satisfy the tests
            # We want to use the real class logic but avoid GObject issues
            class PseudoService:
                @property
                def is_capturing(self):
                    return self._is_capturing

                @is_capturing.setter
                def is_capturing(self, value):
                    self._is_capturing = value

            s = PseudoService()
            s.provider = MagicMock()
            s.fallback_provider = MagicMock()
            s._is_capturing = False
            return s

    def test_validate_decode_inputs(self, service):
        """Test language code validation."""
        valid, _, _, _ = ScreenshotService._validate_decode_inputs(service, "eng")
        assert valid is True

        invalid, _, err, _ = ScreenshotService._validate_decode_inputs(service, "invalid-code!!")
        assert invalid is False
        assert "Invalid language code" in err

    def test_screenshot_fallback_logic(self, service):
        """Test that fallback provider is used when portal fails with a generic error."""
        # Simulate portal failure
        def _mock_capture(lang, copy, callback):
            callback(False, None, "screenshot failed")

        service.provider.capture = MagicMock(side_effect=_mock_capture)

        service._is_capturing = False
        ScreenshotService.capture(service, "eng", False)

        assert service.fallback_provider.capture.called

    def test_format_decode_result(self, service):
        """Test result formatting for various OCR outcomes."""
        # Success
        s, t, e, _ = ScreenshotService._format_decode_result(service, "Extracted Text", None)
        assert s is True
        assert t == "Extracted Text"
        assert e is None

        # Explicit Error
        s, t, e, _ = ScreenshotService._format_decode_result(service, None, "Fatal Error")
        assert s is False
        assert t == ""
        assert e == "Fatal Error"

        # No Text Found
        s, t, e, _ = ScreenshotService._format_decode_result(service, None, None)
        assert s is False
        assert "No text found" in e

    def test_cleanup_temporary_file(self, service, tmp_path):
        """Test cleanup logic for source files."""
        temp_file = tmp_path / "shot.png"
        temp_file.touch()

        # Case: remove_source=True
        ScreenshotService._cleanup_temporary_file(service, str(temp_file), True, True)
        assert not temp_file.exists()

        # Case: remove_source=False
        temp_file.touch()
        ScreenshotService._cleanup_temporary_file(service, str(temp_file), True, False)
        assert temp_file.exists()
