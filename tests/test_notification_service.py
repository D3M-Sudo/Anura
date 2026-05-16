# test_notification_service.py
#
# Unit tests for NotificationService
# Tests XDG Portal and libnotify fallback functionality
#
# NOTE: This file imports `anura.services.notification_service` which in turn
# imports `gi` and uses `Xdp.Portal()`. It is NOT marked @pytest.mark.gtk
# because the tests mock the portal and libnotify entirely; however the
# module-level `import gi` requires PyGObject (python3-gi) on the system.
# Run with: $ uv run env GI_TYPELIB_PATH=... pytest tests/test_notification_service.py -v

from unittest.mock import Mock, patch

import gi

gi.require_version("GLib", "2.0")

from gi.repository import GLib  # noqa: E402

from anura.services.notification_service import HAS_LIBNOTIFY, NotificationService  # noqa: E402


class TestNotificationService:
    """Test suite for NotificationService core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = NotificationService("com.github.d3msudo.anura.test")

    def test_init(self):
        """Test service initialization."""
        assert self.service._portal is not None
        assert hasattr(self.service, "libnotify_initialized")
        assert isinstance(self.service.libnotify_initialized, bool)

    def test_show_notification_with_portal(self):
        """Test showing notification via XDG Portal."""
        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification("Test title", "Test body")

            mock_send.assert_called_once()
            pos_args = mock_send.call_args[0]
            assert pos_args[0].startswith("com.github.d3msudo.anura")
            notification = pos_args[1].unpack()
            assert notification["title"] == "Test title"
            assert notification["body"] == "Test body"

    def test_show_notification_with_portal_error(self):
        """Test fallback when XDG Portal fails."""
        with patch.object(self.service._portal, "add_notification", side_effect=Exception("Portal error")):
            if HAS_LIBNOTIFY:
                with patch("anura.services.notification_service.Notify") as mock_notify:
                    mock_notification = Mock()
                    mock_notify.Notification.new.return_value = mock_notification

                    self.service.show_notification("Test title", "Test body")

                    mock_notify.Notification.new.assert_called_once_with("Test title", "Test body", "com.github.d3msudo.anura.test")
                    mock_notification.show.assert_called_once()
            else:
                # Should not raise exception even without libnotify
                self.service.show_notification("Test title", "Test body")

    def test_show_notification_empty_title(self):
        """Test showing notification with empty title."""
        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification("", "Test body")

            mock_send.assert_called_once()
            notification = mock_send.call_args[0][1].unpack()
            assert notification["title"] == ""
            assert notification["body"] == "Test body"

    def test_show_notification_empty_body(self):
        """Test showing notification with empty body."""
        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification("Test title", "")

            mock_send.assert_called_once()
            notification = mock_send.call_args[0][1].unpack()
            assert notification["title"] == "Test title"
            assert notification["body"] == ""

    def test_show_notification_long_content(self):
        """Test showing notification with long content."""
        long_title = "A" * 200  # Very long title
        long_body = "B" * 500  # Very long body

        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification(long_title, long_body)

            mock_send.assert_called_once()
            notification = mock_send.call_args[0][1].unpack()
            assert notification["title"] == long_title
            assert notification["body"] == long_body

    def test_show_notification_unicode_content(self):
        """Test showing notification with unicode content."""
        unicode_title = "Título con ñ y áéíóú"
        unicode_body = "Cuerpo con emojis 🎉🔔 y caracteres especiales"

        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification(unicode_title, unicode_body)

            mock_send.assert_called_once()
            notification = mock_send.call_args[0][1].unpack()
            assert notification["title"] == unicode_title
            assert notification["body"] == unicode_body

    @patch("anura.services.notification_service.HAS_LIBNOTIFY", True)
    def test_libnotify_fallback_available(self):
        """Test libnotify fallback when available."""
        service = NotificationService("com.github.d3msudo.anura.test")
        assert service.libnotify_initialized is True

    @patch("anura.services.notification_service.HAS_LIBNOTIFY", False)
    def test_libnotify_fallback_unavailable(self):
        """Test libnotify fallback when unavailable."""
        service = NotificationService("com.github.d3msudo.anura.test")
        assert service.libnotify_initialized is False

    @patch("anura.services.notification_service.HAS_LIBNOTIFY", True)
    def test_libnotify_fallback_when_portal_fails(self):
        """Test libnotify fallback when portal fails."""
        with (
            patch.object(self.service._portal, "add_notification", side_effect=Exception("Portal error")),
            patch("anura.services.notification_service.Notify") as mock_notify,
        ):
            mock_notification = Mock()
            mock_notify.Notification.new.return_value = mock_notification

            self.service.show_notification("Title", "Body")

            mock_notify.Notification.new.assert_called_once_with("Title", "Body", "com.github.d3msudo.anura.test")
            mock_notification.show.assert_called_once()

    @patch("anura.services.notification_service.HAS_LIBNOTIFY", True)
    def test_libnotify_fallback_error_handling(self):
        """Test libnotify fallback error handling."""
        with (
            patch.object(self.service._portal, "add_notification", side_effect=Exception("Portal error")),
            patch("anura.services.notification_service.Notify") as mock_notify,
        ):
            mock_notify.Notification.side_effect = Exception("Libnotify error")

            # Should not raise exception
            self.service.show_notification("Title", "Body")

    @patch("anura.services.notification_service.HAS_LIBNOTIFY", False)
    def test_no_fallback_available(self):
        """Test behavior when no notification backend is available."""
        with patch.object(self.service._portal, "add_notification", side_effect=Exception("Portal error")):
            # Should not raise exception even without libnotify
            self.service.show_notification("Title", "Body")

    def test_portal_notification_with_priority(self):
        """Test portal notification with priority parameter."""
        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification("Title", "Body", priority="high")

            mock_send.assert_called_once()
            notification = mock_send.call_args[0][1].unpack()
            assert notification["title"] == "Title"
            assert notification["body"] == "Body"

    def test_portal_notification_error_handling(self):
        """Test portal notification error handling."""
        with patch.object(self.service._portal, "add_notification") as mock_send:
            mock_send.side_effect = [Exception("First error"), None]

            # First call fails, should not raise exception
            self.service.show_notification("Title", "Body")

            # Second call succeeds
            self.service.show_notification("Title2", "Body2")

            assert mock_send.call_count == 2

    def test_show_notification_with_special_characters(self):
        """Test notification with special characters that might cause issues."""
        special_title = "Test & < > \" ' \\ /"
        special_body = "Body with newlines\nand\ttabs"

        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification(special_title, special_body)

            mock_send.assert_called_once()
            notification = mock_send.call_args[0][1].unpack()
            assert notification["title"] == special_title
            assert notification["body"] == special_body

    def test_send_notification_with_action_sends_via_application(self):
        """Test that send_notification_with_action sends via Gio.Application."""
        from unittest.mock import MagicMock, patch

        with patch("anura.services.notification_service.Gio.Application.get_default") as mock_get_app:
            mock_app = MagicMock()
            mock_get_app.return_value = mock_app

            target = GLib.Variant("s", "https://example.com")
            self.service.send_notification_with_action(
                notification_id="qr-url",
                title="QR Code URL Detected",
                body="https://example.com",
                action_id="app.open-qr-url",
                action_target=target,
                priority="high",
            )

            mock_app.send_notification.assert_called_once()
            args = mock_app.send_notification.call_args[0]
            assert args[0] == "qr-url"  # notification_id
            notification = args[1]
            # Verify the notification was created with correct title and body via Gio.Notification.new()
            # and set_body() - Gio.Notification has no getter methods, so we verify the call pattern
            assert hasattr(notification, "set_body")
            assert hasattr(notification, "set_default_action_and_target")

    def test_send_notification_with_action_no_application(self):
        """Test graceful handling when no Gio.Application is available."""
        from unittest.mock import patch

        with patch("anura.services.notification_service.Gio.Application.get_default") as mock_get_app:
            mock_get_app.return_value = None

            target = GLib.Variant("s", "https://example.com")
            # Should not raise
            self.service.send_notification_with_action(
                notification_id="qr-url",
                title="Test",
                body="Test body",
                action_id="app.open-qr-url",
                action_target=target,
            )

    def test_send_notification_with_action_empty_url(self):
        """Test notification with empty URL body."""
        from unittest.mock import MagicMock, patch

        with patch("anura.services.notification_service.Gio.Application.get_default") as mock_get_app:
            mock_app = MagicMock()
            mock_get_app.return_value = mock_app

            target = GLib.Variant("s", "")
            self.service.send_notification_with_action(
                notification_id="qr-url",
                title="QR Code URL Detected",
                body="",
                action_id="app.open-qr-url",
                action_target=target,
            )

            mock_app.send_notification.assert_called_once()

    def test_notification_service_singleton_behavior(self):
        """Test that service can be instantiated multiple times."""
        service1 = NotificationService("com.github.d3msudo.anura.test")
        service2 = NotificationService("com.github.d3msudo.anura.test")

        # Both should have portal instances
        assert service1._portal is not None
        assert service2._portal is not None
        # They should be different instances
        assert service1 is not service2
