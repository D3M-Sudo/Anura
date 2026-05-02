# notification_service.py
#
# Copyright 2026 D3M-Sudo (Anura improvements)
#
# Notification service with XDG Portal and libnotify fallback
# Provides maximum compatibility across desktop environments

from loguru import logger

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

    def __init__(self, app_id: str):
        self.app_id = app_id
        self.libnotify_initialized = False
        self._portal = None

        # Initialize XDP portal once for reuse
        if HAS_PORTAL:
            try:
                self._portal = Xdp.Portal()
                logger.debug("NotificationService: XDG Portal initialized")
            except Exception as e:
                logger.warning(f"NotificationService: Failed to initialize XDG Portal: {e}")

        # Initialize libnotify as fallback
        if HAS_LIBNOTIFY:
            try:
                Notify.init(app_id)
                self.libnotify_initialized = True
                logger.debug("NotificationService: libnotify fallback ready")
            except Exception as e:
                logger.warning(f"NotificationService: Failed to initialize libnotify: {e}")

        if not HAS_PORTAL and not self.libnotify_initialized:
            logger.warning("NotificationService: No notification backend available")

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
        import time
        if GLib is None:
            return False
        if self._portal is None:
            logger.warning("NotificationService: XDG Portal not available")
            return False
        try:

            # Prepare notification as GLib.Variant according to XDG Portal spec
            # Schema: a{sv} (dictionary of string -> variant)
            notification = GLib.Variant("a{sv}", {
                "title": GLib.Variant("s", title),
                "body": GLib.Variant("s", body),
                "priority": GLib.Variant("s", priority),
                # Icon: (sv) tuple with themed icon name and string array
                "icon": GLib.Variant("(sv)", ("themed", GLib.Variant("as", [self.app_id])))
            })

            # Generate unique ID for this notification
            notification_id = f"{self.app_id}-{int(time.time())}"

            # Show notification via portal
            # Full signature: add_notification(id, notification, flags, cancellable, callback, data)
            self._portal.add_notification(
                notification_id,
                notification,
                Xdp.NotificationFlags.NONE,
                None,  # cancellable
                None,  # callback
                None   # data
            )
            logger.debug(f"NotificationService: Portal notification sent: {title}")
            return True

        except Exception as e:
            logger.warning(f"NotificationService: Portal notification failed: {e}")
            return False

    def _show_libnotify_notification(self, title: str, body: str) -> bool:
        """Show notification via traditional libnotify."""
        try:
            notification = Notify.Notification.new(title, body)
            notification.show()
            logger.debug(f"NotificationService: libnotify notification sent: {title}")
            return True
        except Exception as e:
            logger.warning(f"NotificationService: libnotify notification failed: {e}")
            return False

    def is_available(self) -> bool:
        """Check if any notification backend is available."""
        return HAS_PORTAL or self.libnotify_initialized

    def get_backend_info(self) -> str:
        """Get information about the active notification backend."""
        if HAS_PORTAL and self.libnotify_initialized:
            return "XDG Portal (primary) + libnotify (fallback)"
        elif HAS_PORTAL:
            return "XDG Portal (available, untested)"
        elif self.libnotify_initialized:
            return "libnotify (fallback)"
        else:
            return "None (notifications disabled)"
