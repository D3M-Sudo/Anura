# test_notification_service.py
#
# Unit tests for NotificationService
# Tests XDG Portal and libnotify fallback functionality

from unittest.mock import Mock, patch

from anura.services.notification_service import HAS_LIBNOTIFY, NotificationService


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
            call_args = mock_send.call_args[1]
            assert call_args["title"] == "Test title"
            assert call_args["body"] == "Test body"

    def test_show_notification_with_portal_error(self):
        """Test fallback when XDG Portal fails."""
        with patch.object(self.service._portal, "add_notification", side_effect=Exception("Portal error")):
            if HAS_LIBNOTIFY:
                with patch("anura.services.notification_service.Notify") as mock_notify:
                    mock_notification = Mock()
                    mock_notify.Notification.return_value = mock_notification

                    self.service.show_notification("Test title", "Test body")

                    mock_notify.Notification.assert_called_once_with("Test title", "Test body")
                    mock_notification.show.assert_called_once()
            else:
                # Should not raise exception even without libnotify
                self.service.show_notification("Test title", "Test body")

    def test_show_notification_empty_title(self):
        """Test showing notification with empty title."""
        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification("", "Test body")

            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args["title"] == ""
            assert call_args["body"] == "Test body"

    def test_show_notification_empty_body(self):
        """Test showing notification with empty body."""
        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification("Test title", "")

            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args["title"] == "Test title"
            assert call_args["body"] == ""

    def test_show_notification_none_values(self):
        """Test showing notification with None values."""
        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification(None, None)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args["title"] == ""
            assert call_args["body"] == ""

    def test_show_notification_long_content(self):
        """Test showing notification with long content."""
        long_title = "A" * 200  # Very long title
        long_body = "B" * 500  # Very long body

        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification(long_title, long_body)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args["title"] == long_title
            assert call_args["body"] == long_body

    def test_show_notification_unicode_content(self):
        """Test showing notification with unicode content."""
        unicode_title = "Título con ñ y áéíóú"
        unicode_body = "Cuerpo con emojis 🎉🔔 y caracteres especiales"

        with patch.object(self.service._portal, "add_notification") as mock_send:
            self.service.show_notification(unicode_title, unicode_body)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]
            assert call_args["title"] == unicode_title
            assert call_args["body"] == unicode_body

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
        with patch.object(self.service._portal, "add_notification", side_effect=Exception("Portal error")), \
             patch("anura.services.notification_service.Notify") as mock_notify:
            mock_notification = Mock()
            mock_notify.Notification.return_value = mock_notification

            self.service.show_notification("Title", "Body")

            mock_notify.Notification.assert_called_once_with("Title", "Body")
            mock_notification.show.assert_called_once()

    @patch("anura.services.notification_service.HAS_LIBNOTIFY", True)
    def test_libnotify_fallback_error_handling(self):
        """Test libnotify fallback error handling."""
        with patch.object(self.service._portal, "add_notification", side_effect=Exception("Portal error")), \
             patch("anura.services.notification_service.Notify") as mock_notify:
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
            call_args = mock_send.call_args[1]
            assert call_args["title"] == "Title"
            assert call_args["body"] == "Body"

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
            call_args = mock_send.call_args[1]
            assert call_args["title"] == special_title
            assert call_args["body"] == special_body

    def test_notification_service_singleton_behavior(self):
        """Test that service can be instantiated multiple times."""
        service1 = NotificationService("com.github.d3msudo.anura.test")
        service2 = NotificationService("com.github.d3msudo.anura.test")

        # Both should have portal instances
        assert service1._portal is not None
        assert service2._portal is not None
        # They should be different instances
        assert service1 is not service2
