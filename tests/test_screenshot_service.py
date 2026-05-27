# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")


from unittest.mock import patch

from anura.services.screenshot_service import ScreenshotService


class TestScreenshotServiceEnterprise:
    """
    Enterprise-grade unit tests for ScreenshotService.
    Focuses on logic paths and fallbacks safe for VM/headless.
    """

    @pytest.fixture
    def service(self):
        with patch("gi.repository.Xdp.Portal"), patch("anura.services.screenshot_service._configure_tesseract_path"):
            return ScreenshotService()

    def test_validate_decode_inputs(self, service):
        """Test language code validation."""
        valid, _, _, _ = service._validate_decode_inputs("eng")
        assert valid is True

        invalid, _, err, _ = service._validate_decode_inputs("invalid-code!!")
        assert invalid is False
        assert "Invalid language code" in err

    @patch("os.environ.get")
    def test_try_host_screenshot_fallback_trigger_x11(self, mock_env_get, service):
        """Test that host fallback is triggered on X11."""

        def side_effect(key, default=None):
            if key == "DISPLAY":
                return ":0"
            if key == "WAYLAND_DISPLAY":
                return None
            return default

        mock_env_get.side_effect = side_effect

        with patch("gi.repository.Gio.Subprocess.new") as mock_sub:
            service._try_host_screenshot_fallback("eng", False)
            assert mock_sub.called
            # Verify it's trying to call scrot
            args = mock_sub.call_args[0][0]
            assert "scrot" in args
            assert "-s" in args

    @patch("os.environ.get")
    def test_host_fallback_wayland_emits_portal_failure(self, mock_env_get, service):
        """Test that on Wayland, host fallback emits portal failure instead of spawning scrot."""

        def side_effect(key, default=None):
            if key == "WAYLAND_DISPLAY":
                return "wayland-0"
            return default

        mock_env_get.side_effect = side_effect

        with patch.object(service, "_emit_portal_failure") as mock_fail:
            service._try_host_screenshot_fallback("eng", False)
            mock_fail.assert_called_once()
            assert service._is_capturing is False

    def test_format_decode_result(self, service):
        """Test result formatting for various OCR outcomes."""
        # Success
        s, t, e, _r = service._format_decode_result("Extracted Text", None)
        assert s is True
        assert t == "Extracted Text"
        assert e is None

        # Explicit Error
        s, t, e, _r = service._format_decode_result(None, "Fatal Error")
        assert s is False
        assert t == ""
        assert e == "Fatal Error"

        # No Text Found
        s, t, e, _r = service._format_decode_result(None, None)
        assert s is False
        assert "No text found" in e

    def test_cleanup_temporary_file(self, service, tmp_path):
        """Test cleanup logic for source files."""
        temp_file = tmp_path / "shot.png"
        temp_file.touch()

        # Case: remove_source=True
        service._cleanup_temporary_file(str(temp_file), True, True)
        assert not temp_file.exists()

        # Case: remove_source=False
        temp_file.touch()
        service._cleanup_temporary_file(str(temp_file), True, False)
        assert temp_file.exists()
