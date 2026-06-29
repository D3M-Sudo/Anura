# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from itertools import count
import time
from typing import ClassVar

import gi

# Set GTK version requirements before imports
gi.require_version("GLib", "2.0")
gi.require_version("Notify", "0.7")
gi.require_version("Xdp", "1.0")

from loguru import logger  # noqa: E402

try:
    from gi.repository import GLib
except ImportError:
    GLib = None

try:
    from gi.repository import Gio

    HAS_GIO = True
except ImportError:
    HAS_GIO = False
    Gio = None

try:
    from gi.repository import Notify

    HAS_LIBNOTIFY = True
except ImportError:
    HAS_LIBNOTIFY = False
    Notify = None

try:
    from gi.repository import Xdp

    HAS_PORTAL = True
except ImportError:
    HAS_PORTAL = False
    Xdp = None


class NotificationService:
    """
    Unified notification service with automatic fallback.

    Primary: XDG Desktop Portal (preferred for Flatpak/Wayland)
    Fallback: libnotify (traditional, works on most systems)
    Gio.Notification: Used for action-capable notifications (Flatpak-safe)
    """

    def __init__(self, app_id: str | None = None) -> None:
        from anura.config import APP_ID as _APP_ID

        self.app_id = app_id if app_id is not None else _APP_ID
        self.libnotify_initialized = False
        self._portal = None
        self._notification_id_counter = count()  # Monotonic counter for unique IDs
        self._active_notifications: set[str] = set()  # Track active notification IDs

        # Initialize XDP portal once for reuse
        if HAS_PORTAL:
            try:
                self._portal = Xdp.Portal()
                logger.debug("NotificationService: XDG Portal initialized")
            except (ImportError, AttributeError, TypeError) as e:
                logger.warning(f"NotificationService: Failed to initialize XDG Portal: {e}")

        # Initialize libnotify as fallback
        if HAS_LIBNOTIFY:
            try:
                Notify.init(app_id)
                self.libnotify_initialized = True
                logger.debug("NotificationService: libnotify fallback ready")
            except (ImportError, AttributeError, TypeError) as e:
                logger.warning(f"NotificationService: Failed to initialize libnotify: {e}")

        # Start periodic cleanup timer for the notification tracking set
        self._cleanup_timeout_id = GLib.timeout_add_seconds(60, self._periodic_cleanup)

        if not HAS_PORTAL and not self.libnotify_initialized:
            logger.warning("NotificationService: No notification backend available")

    def cleanup(self) -> None:
        """Clean up the periodic timer to prevent resource leaks."""
        if hasattr(self, "_cleanup_timeout_id") and self._cleanup_timeout_id is not None:
            with contextlib.suppress(GLib.Error):
                GLib.source_remove(self._cleanup_timeout_id)
            self._cleanup_timeout_id = None
        self.cleanup_notifications()

    # Valid priority levels according to XDG Portal specification
    _VALID_PRIORITIES: ClassVar[set[str]] = {"low", "normal", "high", "urgent"}

    # Notification dismiss timeout in seconds (default: 8 seconds)
    _DISMISS_SECONDS = 8

    def _periodic_cleanup(self) -> bool:
        """Periodic safety net: clear the notification tracking set every 60 seconds."""
        self.cleanup_notifications()
        return GLib.SOURCE_CONTINUE  # Keep the timeout active

    def show_notification(self, title: str, body: str, priority: str = "normal") -> bool:
        """
        Show a notification with automatic backend selection.

        This is the public API method expected by tests.

        Args:
            title: Notification title
            body: Notification body text
            priority: Priority level ("low", "normal", "high", "urgent")

        Returns:
            True if notification was shown successfully, False otherwise
        """
        return self.show(title, body, priority)

    def show(self, title: str, body: str, priority: str = "normal") -> bool:
        """
        Show a notification with automatic backend selection.

        Args:
            title: Notification title
            body: Notification body text
            priority: Priority level ("low", "normal", "high", "urgent")

        Returns:
            True if notification was shown successfully, False otherwise
        """
        # Validate priority parameter
        if priority not in self._VALID_PRIORITIES:
            logger.warning(f"NotificationService: Invalid priority '{priority}', using 'normal'")
            priority = "normal"

        # Security: Escape Pango markup in title and body to prevent injection attacks
        # from OCR'd text (phishing, UI spoofing, etc).
        if GLib:
            title = GLib.markup_escape_text(title)
            body = GLib.markup_escape_text(body)

        # Try portal first, then fallback to libnotify
        if HAS_PORTAL:
            result = self._show_portal_notification(title, body, priority)
            if result:
                return True
            # Portal failed, try libnotify
        if self.libnotify_initialized:
            return self._show_libnotify_notification(title, body)
        logger.warning("NotificationService: No backend available for notification")
        return False

    def send_notification_with_action(
        self,
        notification_id: str,
        title: str,
        body: str,
        action_id: str,
        action_target: GLib.Variant,
        priority: str = "high",
    ) -> None:
        """
        Send a notification via Gio.Application's notification system.

        This is the Flatpak-safe approach — actions are handled in-process
        via Gio.SimpleAction, avoiding libnotify callback sandbox issues.

        Args:
            notification_id: Unique ID (replacing any existing notification with same ID)
            title: Notification title
            body: Notification body text
            action_id: Fully qualified action name, e.g. "app.open-qr-url"
            action_target: GLib.Variant with the action's target parameter
            priority: Notification priority ("low", "normal", "high", "urgent")
        """
        if not HAS_GIO:
            logger.warning("NotificationService: Gio not available for action notification")
            return

        # Security: Escape Pango markup in title and body to prevent injection attacks
        # from OCR'd text (phishing, UI spoofing, etc).
        if GLib:
            title = GLib.markup_escape_text(title) if title else ""
            body = GLib.markup_escape_text(body) if body else ""

        notification = Gio.Notification.new(title)
        notification.set_body(body)
        notification.set_default_action_and_target(action_id, action_target)

        # Set priority if valid
        if priority in self._VALID_PRIORITIES:
            if priority == "high":
                notification.set_priority(Gio.NotificationPriority.HIGH)
            elif priority == "urgent":
                notification.set_priority(Gio.NotificationPriority.URGENT)
            elif priority == "low":
                notification.set_priority(Gio.NotificationPriority.LOW)
            else:
                notification.set_priority(Gio.NotificationPriority.NORMAL)

        # Get the application instance and send
        app = Gio.Application.get_default()
        if app:
            app.send_notification(notification_id, notification)
            logger.debug(f"NotificationService: Gio action notification sent: {title} (id={notification_id})")
        else:
            logger.warning("NotificationService: No Gio.Application instance for action notification")

    def _show_portal_notification(self, title: str, body: str, priority: str) -> bool:
        """Show notification via XDG Desktop Portal."""
        if GLib is None:
            return False
        if self._portal is None:
            logger.warning("NotificationService: XDG Portal not available")
            return False
        try:
            # Prepare notification as GLib.Variant according to XDG Portal spec
            # Schema: a{sv} (dictionary of string -> variant)
            notification = GLib.Variant(
                "a{sv}",
                {
                    "title": GLib.Variant("s", title),
                    "body": GLib.Variant("s", body),
                    "priority": GLib.Variant("s", priority),
                    # Icon: (sv) tuple with themed icon name and string array
                    "icon": GLib.Variant("(sv)", ("themed", GLib.Variant("as", [self.app_id]))),
                },
            )

            # Generate unique ID for this notification (timestamp + monotonic counter)
            notification_id = f"{self.app_id}-{int(time.time())}-{next(self._notification_id_counter)}"

            # Track notification ID for potential cleanup
            self._active_notifications.add(notification_id)

            # Show notification via portal using correct XDG Portal API
            self._portal.add_notification(
                notification_id,
                notification,
                Xdp.NotificationFlags.NONE,
                None,  # cancellable
                None,  # callback
                None,  # data
            )
            # Schedule auto-dismiss after configured timeout
            GLib.timeout_add_seconds(self._DISMISS_SECONDS, self._dismiss_portal_notification, notification_id)

            logger.debug(f"NotificationService: Portal notification sent: {title}, dismiss in {self._DISMISS_SECONDS}s")
            return True

        except (AttributeError, RuntimeError, TypeError, GLib.Error) as e:
            logger.warning(f"NotificationService: Portal notification failed: {e}")
            return False

    def _dismiss_portal_notification(self, notification_id: str) -> bool:
        """Auto-dismiss a portal notification by removing it via the portal API."""
        try:
            if self._portal is not None:
                self._portal.remove_notification(notification_id)
                logger.debug(f"NotificationService: Dismissed portal notification: {notification_id}")
        except (AttributeError, RuntimeError, TypeError, GLib.Error) as e:
            logger.debug(f"NotificationService: Failed to dismiss portal notification: {e}")
        # Remove from tracking set regardless
        self._active_notifications.discard(notification_id)
        return GLib.SOURCE_REMOVE  # One-shot timer

    def _show_libnotify_notification(self, title: str, body: str) -> bool:
        """Show notification via traditional libnotify."""
        try:
            notification = Notify.Notification.new(title, body, self.app_id)
            notification.set_timeout(self._DISMISS_SECONDS * 1000)
            notification.show()
            logger.debug(f"NotificationService: libnotify notification sent: {title}")
            return True
        except (AttributeError, RuntimeError, TypeError, GLib.Error) as e:
            logger.warning(f"NotificationService: libnotify notification failed: {e}")
            return False

    def is_available(self) -> bool:
        """Check if any notification backend is available."""
        return HAS_PORTAL or self.libnotify_initialized

    def cleanup_notifications(self) -> None:
        """Clean up tracking of active notifications.

        Called periodically (every 60s) as a safety net, on app shutdown,
        and by _dismiss_portal_notification after the auto-dismiss timer.
        Actively withdraws any still-live portal notifications so they do not
        persist on the desktop after the application exits.
        """
        if self._active_notifications:
            logger.debug(f"NotificationService: Cleaning up {len(self._active_notifications)} tracked notifications")
            if self._portal is not None:
                for notification_id in list(self._active_notifications):
                    try:
                        self._portal.remove_notification(notification_id)
                    except (AttributeError, RuntimeError, TypeError, GLib.Error) as e:
                        logger.debug(f"NotificationService: Could not remove notification {notification_id}: {e}")
            self._active_notifications.clear()


def get_notification_service() -> NotificationService:
    """Get the thread-safe NotificationService singleton."""
    from anura.utils.singleton import get_instance

    return get_instance(NotificationService)
