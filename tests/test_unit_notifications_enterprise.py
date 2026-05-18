# tests/test_unit_notifications_enterprise.py
from unittest.mock import MagicMock, patch

import pytest

from anura.services.notification_service import NotificationService


class TestNotificationServiceEnterprise:
    """
    Enterprise-grade unit tests for NotificationService.
    Can run in VM/headless environment via mocks.
    """

    @pytest.fixture
    def service(self):
        with patch("gi.repository.Xdp.Portal"), patch("gi.repository.Notify.init"):
            return NotificationService("test.app.id")

    def test_show_notification_portal_success(self, service):
        """Test notification via XDG Portal."""
        service._portal = MagicMock()

        with patch.object(service, "_show_portal_notification", return_value=True) as mock_portal:
            res = service.show("Title", "Body")
            assert res is True
            mock_portal.assert_called_once_with("Title", "Body", "normal")

    def test_show_notification_libnotify_fallback(self, service):
        """Test fallback to libnotify when portal is unavailable."""
        service._portal = None
        service.libnotify_initialized = True

        with patch.object(service, "_show_libnotify_notification", return_value=True) as mock_libnotify:
            res = service.show("Title", "Body")
            assert res is True
            mock_libnotify.assert_called_once_with("Title", "Body")

    def test_invalid_priority_fallback(self, service):
        """Test that invalid priorities are clamped to 'normal'."""
        service._portal = MagicMock()
        with patch.object(service, "_show_portal_notification", return_value=True) as mock_portal:
            service.show("Title", "Body", priority="urgent-extremely")
            mock_portal.assert_called_with("Title", "Body", "normal")

    def test_send_notification_with_action(self, service):
        """Test sending a notification with a Gio action (Flatpak-safe)."""
        from gi.repository import GLib

        with (
            patch("gi.repository.Gio.Notification.new") as mock_new,
            patch("gi.repository.Gio.Application.get_default") as mock_app_get,
        ):
            mock_notif = MagicMock()
            mock_new.return_value = mock_notif
            mock_app = MagicMock()
            mock_app_get.return_value = mock_app

            variant = GLib.Variant("s", "https://example.com")
            service.send_notification_with_action("id1", "Title", "Body", "app.action", variant)

            mock_notif.set_body.assert_called_with("Body")
            mock_notif.set_default_action_and_target.assert_called_with("app.action", variant)
            mock_app.send_notification.assert_called_with("id1", mock_notif)
