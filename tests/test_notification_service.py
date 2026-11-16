# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")


from unittest.mock import MagicMock, patch

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

    def test_markup_escaping(self, service):
        """Security: Verify that markup in title and body is escaped."""
        from gi.repository import GLib

        service._portal = MagicMock()

        # In mock environment (CI), ensure predictable behavior if GLib is mocked
        if isinstance(GLib.markup_escape_text, MagicMock):
            GLib.markup_escape_text.side_effect = lambda x: f"ESCAPED({x})"

        unsafe_title = "<b>Bold Title</b>"
        unsafe_body = "Click <a href='http://evil.com'>here</a> & win!"
        expected_title = GLib.markup_escape_text(unsafe_title)
        expected_body = GLib.markup_escape_text(unsafe_body)

        # 1. Test show() -> _show_portal_notification
        with patch.object(service, "_show_portal_notification", return_value=True) as mock_portal:
            service.show(unsafe_title, unsafe_body)
            mock_portal.assert_called_once_with(expected_title, expected_body, "normal")

        # 2. Test send_notification_with_action()
        with (
            patch("gi.repository.Gio.Notification.new") as mock_new,
            patch("gi.repository.Gio.Application.get_default") as mock_app_get,
        ):
            mock_notif = MagicMock()
            mock_new.return_value = mock_notif
            mock_app = MagicMock()
            mock_app_get.return_value = mock_app

            variant = GLib.Variant("s", "target")
            service.send_notification_with_action("id1", unsafe_title, unsafe_body, "app.action", variant)

            mock_new.assert_called_with(expected_title)
            mock_notif.set_body.assert_called_with(expected_body)
