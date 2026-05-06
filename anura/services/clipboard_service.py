# clipboard_service.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _
from typing import ClassVar

from gi.repository import Gdk, Gio, GLib, GObject
from loguru import logger


class ClipboardService(GObject.GObject):
    """
    Service responsible for interacting with the system clipboard.
    Optimized for Anura OCR to handle text and image textures.
    """

    __gtype_name__ = "ClipboardService"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "paste_from_clipboard": (GObject.SIGNAL_RUN_FIRST, None, (Gdk.Texture,)),
        "error": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    __slots__ = ("_cancellable", "_clipboard", "_clipboard_timeout_id")

    # Timeout for clipboard read operations (seconds)
    CLIPBOARD_TIMEOUT_SECONDS = 10

    @property
    def clipboard(self) -> Gdk.Clipboard:
        """Lazy initialization of clipboard to avoid crash on headless/CI."""
        if self._clipboard is None:
            display = Gdk.Display.get_default()
            if display is None:
                raise RuntimeError("No GTK display available.")
            self._clipboard = display.get_clipboard()
        return self._clipboard

    def __init__(self) -> None:
        super().__init__()
        self._cancellable = None
        self._clipboard = None
        self._clipboard_timeout_id = None

    def init(self) -> None:
        """
        Initialize the clipboard on the main thread.

        This method should be called during AnuraApplication.do_startup to ensure
        Gdk.Clipboard is created on the main thread, avoiding race conditions that
        can occur with lazy initialization from background threads.
        """
        if self._clipboard is None:
            display = Gdk.Display.get_default()
            if display is not None:
                self._clipboard = display.get_clipboard()
                logger.debug("Anura Clipboard: Initialized on main thread.")

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
        # Cancel the timeout since operation completed (success or failure)
        if self._clipboard_timeout_id and self._clipboard_timeout_id > 0:
            GLib.source_remove(self._clipboard_timeout_id)
            self._clipboard_timeout_id = None

        try:
            texture = self.clipboard.read_texture_finish(result)
            if not texture:
                raise ValueError("No valid texture found in result.")

            logger.info("Anura Clipboard: Image texture retrieved.")
            GLib.idle_add(self.emit, "paste_from_clipboard", texture)

        except GLib.Error as e:
            # Check if operation was cancelled
            if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                logger.debug("Anura Clipboard: Read operation cancelled.")
                return
            # Other errors - log and emit error signal
            logger.error(f"Anura Clipboard Error: {e}")
            GLib.idle_add(self.emit, "error", _("No image in clipboard"))
        except (ValueError, RuntimeError) as e:
            # Technical rigor: log error for X11/Wayland clipboard synchronization issues
            logger.error(f"Anura Clipboard Error: {e}")
            GLib.idle_add(self.emit, "error", _("No image in clipboard"))
        finally:
            # Clean up cancellable regardless of outcome
            self._cancellable = None

    def read_texture(self) -> None:
        """
        Asynchronously reads a texture from the clipboard with a 10-second timeout.
        """
        # Cancel any previous timeout to prevent accumulation
        if self._clipboard_timeout_id and self._clipboard_timeout_id > 0:
            GLib.source_remove(self._clipboard_timeout_id)
            self._clipboard_timeout_id = None

        # Cancel any previous pending operation to prevent race conditions
        if self._cancellable is not None:
            self._cancellable.cancel()
            self._cancellable = None

        # Create new cancellable for this operation
        self._cancellable = Gio.Cancellable()
        self._clipboard_timeout_id = GLib.timeout_add_seconds(
            self.CLIPBOARD_TIMEOUT_SECONDS,
            self._on_clipboard_timeout,
            self._cancellable
        )

        self.clipboard.read_texture_async(cancellable=self._cancellable, callback=self._on_read_texture)

    def _on_clipboard_timeout(self, cancellable: Gio.Cancellable) -> bool:
        """Cancel clipboard operation if it takes too long."""
        # Enhanced null check for cancellable object
        if cancellable is None:
            logger.debug("Anura Clipboard: Timeout called with null cancellable")
            return False

        # Check if this cancellable is still the active one (not replaced by new operation)
        if cancellable is not self._cancellable:
            # Stale timeout from previous operation - ignore
            logger.debug("Anura Clipboard: Stale timeout detected, ignoring")
            # Only clear timeout ID if this is still the active timeout context
            if self._clipboard_timeout_id is not None:
                self._clipboard_timeout_id = None
            return False

        if not cancellable.is_cancelled():
            logger.warning("Anura Clipboard: Read operation timed out after 10s, cancelling.")
            cancellable.cancel()
            # Emit error signal so UI can show user feedback
            GLib.idle_add(self.emit, "error", _("Clipboard read operation timed out."))

        # Clear timeout ID only in the active context to prevent race conditions
        self._clipboard_timeout_id = None
        return False  # Don't repeat timeout

    def cancel_pending_operations(self) -> None:
        """Cancel any pending clipboard read operations. Called during window cleanup."""
        if self._cancellable is not None and not self._cancellable.is_cancelled():
            logger.debug("Anura Clipboard: Cancelling pending clipboard operation.")
            self._cancellable.cancel()
        if self._clipboard_timeout_id and self._clipboard_timeout_id > 0:
            GLib.source_remove(self._clipboard_timeout_id)
            self._clipboard_timeout_id = None
        self._cancellable = None


# Singleton instance for global app access
clipboard_service = ClipboardService()
