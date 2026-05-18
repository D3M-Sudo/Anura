import pytest

pytest.importorskip("gi")


# tests/test_unit_screenshot_service_enterprise.py
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
        valid, _, _ = service._validate_decode_inputs("eng")
        assert valid is True

        invalid, _, err = service._validate_decode_inputs("invalid-code!!")
        assert invalid is False
        assert "Invalid language code" in err

    @patch("anura.services.screenshot_service._is_flatpak_environment", return_value=True)
    def test_try_host_screenshot_fallback_trigger(self, mock_flatpak, service):
        """Test that host fallback is triggered in Flatpak environment."""
        with patch("gi.repository.Gio.Subprocess.new") as mock_sub:
            service._try_host_screenshot_fallback("eng", False)
            assert mock_sub.called
            # Verify it's trying to build detection argv
            args = mock_sub.call_args[0][0]
            assert "flatpak-spawn" in args
            assert "--host" in args

    @patch("anura.services.screenshot_service._is_flatpak_environment", return_value=False)
    def test_host_fallback_skipped_outside_flatpak(self, mock_flatpak, service):
        """Test that host fallback is not used outside Flatpak."""
        with patch.object(service, "_emit_portal_failure") as mock_fail:
            service._try_host_screenshot_fallback("eng", False)
            mock_fail.assert_called_once()
            assert service._is_capturing is False

    def test_format_decode_result(self, service):
        """Test result formatting for various OCR outcomes."""
        # Success
        s, t, e = service._format_decode_result("Extracted Text", None)
        assert s is True
        assert t == "Extracted Text"
        assert e is None

        # Explicit Error
        s, t, e = service._format_decode_result(None, "Fatal Error")
        assert s is False
        assert t == ""
        assert e == "Fatal Error"

        # No Text Found
        s, t, e = service._format_decode_result(None, None)
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
