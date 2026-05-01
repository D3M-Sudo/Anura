# notification_service.py
#
# Copyright 2026 D3M-Sudo (Anura improvements)
#
# Notification service with XDG Portal and libnotify fallback
# Provides maximum compatibility across desktop environments

from gettext import gettext as _
from loguru import logger

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
        self.use_portal = self._detect_portal_available()
        self.libnotify_initialized = False
        
        if not self.use_portal and HAS_LIBNOTIFY:
            try:
                Notify.init(app_id)
                self.libnotify_initialized = True
                logger.debug("NotificationService: Using libnotify backend")
            except Exception as e:
                logger.warning(f"NotificationService: Failed to initialize libnotify: {e}")
        
        if self.use_portal:
            logger.debug("NotificationService: Using XDG Portal backend")
        elif not self.libnotify_initialized:
            logger.warning("NotificationService: No notification backend available")
    
    def _detect_portal_available(self) -> bool:
        """Check if XDG notification portal is available."""
        if not HAS_PORTAL:
            return False
        
        try:
            portal = Xdp.Portal.new()
            # Check if notification portal is available
            # This is a basic check - in practice, we'll try to use it and fallback if needed
            return portal is not None
        except Exception as e:
            logger.debug(f"NotificationService: Portal detection failed: {e}")
            return False
    
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
        if self.use_portal:
            return self._show_portal_notification(title, body, priority)
        elif self.libnotify_initialized:
            return self._show_libnotify_notification(title, body)
        else:
            logger.warning("NotificationService: No backend available for notification")
            return False
    
    def _show_portal_notification(self, title: str, body: str, priority: str) -> bool:
        """Show notification via XDG Desktop Portal."""
        try:
            portal = Xdp.Portal.new()
            
            # Prepare notification according to XDG Portal specification
            notification = {
                "title": title,
                "body": body,
                "priority": priority,
                # Use app icon for better recognition
                "icon": {"themed": [self.app_id]}
            }
            
            # Generate unique ID for this notification
            import time
            notification_id = f"{self.app_id}-{int(time.time())}"
            
            # Show notification via portal
            portal.add_notification(notification_id, notification)
            logger.debug(f"NotificationService: Portal notification sent: {title}")
            return True
            
        except Exception as e:
            logger.warning(f"NotificationService: Portal notification failed: {e}")
            # Fallback to libnotify if available
            if self.libnotify_initialized:
                return self._show_libnotify_notification(title, body)
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
        return self.use_portal or self.libnotify_initialized
    
    def get_backend_info(self) -> str:
        """Get information about the active notification backend."""
        if self.use_portal:
            return "XDG Portal (preferred)"
        elif self.libnotify_initialized:
            return "libnotify (fallback)"
        else:
            return "None (notifications disabled)"
