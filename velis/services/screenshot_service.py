# velis/services/screenshot_service.py
try:
    import gi
    gi.require_version("Xdp", "1.0")
    from gi.repository import GLib, GObject, Xdp
    HAS_GI = True
except (ImportError, ValueError):
    HAS_GI = False
    class GObject:
        class Object: pass
        SignalFlags = type('SignalFlags', (), {'RUN_LAST': 1})

from loguru import logger

from velis.utils.singleton import get_instance


class ScreenshotService(GObject.Object if HAS_GI else object):
    if HAS_GI:
        __gsignals__ = {
            'screenshot-captured': (GObject.SignalFlags.RUN_LAST, None, (str,)),
            'error': (GObject.SignalFlags.RUN_LAST, None, (str,)),
        }

    def __init__(self):
        if HAS_GI:
            super().__init__()
            self.portal = Xdp.Portal.new()

    def capture(self, parent_window=None):
        if not HAS_GI:
            return
        # Use XDG Desktop Portal for Wayland/X11 compatibility
        self.portal.take_screenshot(
            None, # parent
            Xdp.ScreenshotFlags.NONE,
            None, # cancellable
            self._on_screenshot_ready
        )

    def _on_screenshot_ready(self, portal, result):
        if HAS_GI:
            try:
                uri = portal.take_screenshot_finish(result)
                if uri:
                    path = uri.replace("file://", "")
                    self.emit('screenshot-captured', path)
            except Exception as e:
                logger.error(f"Screenshot error: {e}")
                self.emit('error', str(e))

def get_screenshot_service():
    return get_instance(ScreenshotService)
