# notification_service.py
#
# Copyright 2026 D3M-Sudo (Anura improvements)
#
# Notification service with XDG Portal and libnotify fallback
# Provides maximum compatibility across desktop environments

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
    """

    def __init__(self, app_id: str) -> None:
        self.app_id = app_id
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

        except Exception as e:
            logger.warning(f"NotificationService: Portal notification failed: {e}")
            return False

    def _dismiss_portal_notification(self, notification_id: str) -> bool:
        """Auto-dismiss a portal notification by removing it via the portal API."""
        try:
            if self._portal is not None:
                self._portal.remove_notification(notification_id, None, None, None)
                logger.debug(f"NotificationService: Dismissed portal notification: {notification_id}")
        except Exception as e:
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
        except Exception as e:
            logger.warning(f"NotificationService: libnotify notification failed: {e}")
            return False

    def is_available(self) -> bool:
        """Check if any notification backend is available."""
        return HAS_PORTAL or self.libnotify_initialized

    def cleanup_notifications(self) -> None:
        """Clean up tracking of active notifications.

        Called periodically (every 60s) as a safety net and by
        _dismiss_portal_notification after the auto-dismiss timer.
        """
        if self._active_notifications:
            logger.debug(f"NotificationService: Cleaning up {len(self._active_notifications)} tracked notifications")
            self._active_notifications.clear()
