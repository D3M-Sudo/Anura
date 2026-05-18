import pytest

pytest.importorskip("gi")

# tests/test_unit_app_lifecycle_enterprise.py
from unittest.mock import MagicMock, patch

from gi.repository import GLib

from anura.main import AnuraApplication


class TestAppLifecycleEnterprise:
    """
    Enterprise-grade unit tests for AnuraApplication lifecycle and handlers.
    Safe for VM/headless.
    """

    @pytest.fixture
    def app(self):
        with (
            patch("anura.main._load_gresource_bundle", return_value=True),
            patch("anura.main.ScreenshotService"),
            patch("anura.main.NotificationService"),
            patch("anura.main.get_clipboard_service"),
        ):
            app = AnuraApplication()
            app.settings = MagicMock()
            app.backend = MagicMock()
            return app

    def test_on_error_handler(self, app):
        """Test on_error logic, ensuring 'Cancelled' is ignored."""
        with patch.object(app.notification_service, "show_notification") as mock_notif:
            # Case: Cancelled
            app.on_error(None, "Cancelled")
            mock_notif.assert_not_called()

            # Case: Real error
            app.on_error(None, "Fatal Crash")
            mock_notif.assert_called_with(title="Anura OCR", body="Fatal Crash")

    def test_decode_image_synchronously_success(self, app):
        """Test synchronous decoding used in silent mode."""
        app.backend.decode_image_sync.return_value = (True, "Extracted Text", None)
        app.settings.get_string.return_value = "eng"

        success, text, _ = app._decode_image_synchronously("/tmp/test.png")
        assert success is True
        assert text == "Extracted Text"
        app.backend.decode_image_sync.assert_called_with("eng", "/tmp/test.png", remove_source=False)

    def test_decode_image_synchronously_failures(self, app):
        """Test synchronous decoding error paths."""
        # File not found
        app.backend.decode_image_sync.side_effect = FileNotFoundError()
        s, _, e = app._decode_image_synchronously("missing.png")
        assert s is False
        assert "not found" in e

        # Permission denied
        app.backend.decode_image_sync.side_effect = PermissionError()
        s, _, e = app._decode_image_synchronously("secret.png")
        assert s is False
        assert "Permission denied" in e

    def test_open_qr_notification_validation(self, app):
        """Test validation of URLs from QR notifications."""
        # Case: Invalid URL
        param = GLib.Variant("s", "javascript:alert(1)")
        with patch("loguru.logger.warning") as mock_log:
            app._on_open_qr_notification(None, param)
            mock_log.assert_any_call("Anura: Blocked invalid URL from notification: javascript:alert(1)")

        # Case: Valid URL (calls launch)
        param = GLib.Variant("s", "https://google.com")
        with (
            patch.object(app, "get_active_window", return_value=None),
            patch("gi.repository.Gtk.UriLauncher.launch") as mock_launch,
        ):
            app._on_open_qr_notification(None, param)
            assert mock_launch.called

    def test_app_cleanup_handlers(self, app):
        """Test that shutdown cleans up various services."""
        with (
            patch("anura.main.get_clipboard_service") as mock_get_cb,
            patch("anura.services.tts.get_tts_service") as mock_get_tts,
        ):
            mock_cb = mock_get_cb.return_value
            mock_tts = mock_get_tts.return_value

            app.do_shutdown()

            mock_cb.cancel_pending_operations.assert_called()
            mock_tts.cleanup.assert_called()
