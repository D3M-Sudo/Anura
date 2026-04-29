# clipboard_service.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _

from gi.repository import Gdk, Gio, GLib, GObject
from loguru import logger


class ClipboardService(GObject.GObject):
    """
    Service responsible for interacting with the system clipboard.
    Optimized for Anura OCR to handle text and image textures.
    """
    __gtype_name__ = 'ClipboardService'

    __gsignals__ = {
        'paste_from_clipboard': (GObject.SIGNAL_RUN_FIRST, None, (Gdk.Texture,)),
        'error': (GObject.SIGNAL_RUN_FIRST, None, (str,))
    }

    _clipboard: Gdk.Clipboard | None = None

    @property
    def clipboard(self) -> Gdk.Clipboard:
        """Lazy initialization of clipboard to avoid crash on headless/CI."""
        if self._clipboard is None:
            display = Gdk.Display.get_default()
            if display is None:
                raise RuntimeError("No GTK display available.")
            self._clipboard = display.get_clipboard()
        return self._clipboard

    def __init__(self):
        super().__init__()

    def set(self, value: str) -> None:
        """
        Sets text to the system clipboard.
        """
        if value:
            self.clipboard.set(value)
            logger.debug("Anura Clipboard: Text successfully copied.")
        else:
            logger.warning("Anura Clipboard: Attempted to copy empty string.")

    def _on_read_texture(self, _sender: GObject.GObject, result: Gio.AsyncResult) -> None:
        """
        Callback for texture reading from clipboard.
        """
        try:
            texture = self.clipboard.read_texture_finish(result)
            if not texture:
                raise ValueError("No valid texture found in result.")

            logger.info("Anura Clipboard: Image texture retrieved.")
            self.emit('paste_from_clipboard', texture)

        except Exception as e:
            # Technical rigor: log error for X11/Wayland clipboard synchronization issues
            logger.error(f"Anura Clipboard Error: {e}")
            self.emit('error', _("No image in clipboard"))

    def read_texture(self) -> None:
        """
        Asynchronously reads a texture from the clipboard with a 10-second timeout.
        """
        # Create cancellable with timeout to prevent hanging on clipboard issues
        cancellable = Gio.Cancellable()
        GLib.timeout_add_seconds(10, self._on_clipboard_timeout, cancellable)

        self.clipboard.read_texture_async(
            cancellable=cancellable,
            callback=self._on_read_texture
        )

    def _on_clipboard_timeout(self, cancellable: Gio.Cancellable) -> bool:
        """Cancel clipboard operation if it takes too long."""
        if not cancellable.is_cancelled():
            logger.warning("Anura Clipboard: Read operation timed out after 10s, cancelling.")
            cancellable.cancel()
        return False  # Don't repeat timeout


# Singleton instance for global app access
clipboard_service = ClipboardService()
