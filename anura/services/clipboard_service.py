# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from gettext import gettext as _
from io import BytesIO
from pathlib import Path
import threading
from typing import ClassVar

import gi

# Set GTK version requirements before imports
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")

from gi.repository import Gdk, Gio, GLib, GObject  # noqa: E402
from loguru import logger  # noqa: E402
from PIL import Image  # noqa: E402

from anura.utils import mask_url, validate_image_resource  # noqa: E402
from anura.utils.singleton import get_instance  # noqa: E402

# When the clipboard advertises a file URI list (e.g. user copied a PNG from
# Nautilus), reading the URI list and loading the file via PIL is much more
# reliable than ``read_texture_async`` — the latter happily picks unsupported
# MIME types like ``image/x-xpixmap`` and then fails the entire paste.
_CLIPBOARD_TEXT_URI_LIST = "text/uri-list"

# Stream chunk size when slurping clipboard streams.
_CLIPBOARD_STREAM_CHUNK = 16 * 1024


class ClipboardService(GObject.GObject):
    """
    Service responsible for interacting with the system clipboard.
    Optimized for Anura OCR to handle text and image textures.
    """

    __gtype_name__ = "ClipboardService"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "paste_from_clipboard": (GObject.SignalFlags.RUN_FIRST, None, (Gdk.Texture,)),
        "error": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    # Timeout for clipboard read operations (seconds)
    CLIPBOARD_TIMEOUT_SECONDS = 10

    @property
    def clipboard(self) -> Gdk.Clipboard:
        """Thread-safe lazy initialization of clipboard to avoid crash on headless/CI."""
        with self._state_lock:
            if self._clipboard is None:
                display = Gdk.Display.get_default()
                if display is None:
                    raise RuntimeError("No GTK display available.")
                self._clipboard = display.get_clipboard()
                logger.debug("Anura Clipboard: Initialized with thread safety.")
            return self._clipboard

    def __init__(self) -> None:
        super().__init__()
        logger.debug("Anura ClipboardService: Initializing clipboard service singleton")
        self._cancellable = None
        self._clipboard = None
        self._clipboard_timeout_id = None
        self._state_lock = threading.Lock()
        self._fallback_attempted = False
        logger.debug("Anura ClipboardService: Clipboard service initialization complete")

    def init(self) -> None:
        """
        Initialize the clipboard on the main thread.

        This method should be called during AnuraApplication.do_startup to ensure
        Gdk.Clipboard is created on the main thread, avoiding race conditions that
        can occur with lazy initialization from background threads.
        """
        with self._state_lock:
            if self._clipboard is None:
                display = Gdk.Display.get_default()
                if display is None:
                    logger.warning("Anura Clipboard: No GDK display available during init.")
                    return
                self._clipboard = display.get_clipboard()
                logger.debug("Anura Clipboard: Initialized on main thread.")

    def set(self, value: str) -> None:
        """
        Sets text to the system clipboard with robust timeout handling.
        """
        if not value:
            logger.warning("Anura Clipboard: Attempted to copy empty string.")
            return

        # Capture IDs under lock, then cancel/remove outside to avoid deadlock
        # with GLib's internal main-loop lock (see _clear_active_timeout).
        # For set() operations, which are synchronous/one-shot, we can safely
        # cancel any pending read.
        self._clear_active_timeout()

        # Gdk.Clipboard.set_text() was removed in GTK4.
        # The correct GTK4 API is set_content() with a ContentProvider wrapping
        # a GLib.Variant string, which is supported across all GTK4 backends
        # (X11, Wayland, Broadway).
        content = Gdk.ContentProvider.new_for_value(GLib.Variant("s", value))
        self.clipboard.set_content(content)

        # Set timeout as expected by tests and for robustness
        with self._state_lock:
            self._clipboard_timeout_id = GLib.timeout_add_seconds(
                self.CLIPBOARD_TIMEOUT_SECONDS,
                self._on_clipboard_timeout,
                None,
            )

        logger.debug(f"Anura Clipboard: Text successfully copied: {value[:50]}...")

    def copy_text(self, text: str) -> None:
        """Legacy alias for set(text)."""
        self.set(text)

    def _on_read_texture(self, _sender: GObject.GObject, result: Gio.AsyncResult) -> None:
        """
        Thread-safe callback for texture reading from clipboard.

        If the direct texture read fails (e.g. GDK cannot decode the advertised
        MIME type), falls back to reading the clipboard as a ``text/uri-list``
        and loading the image file via PIL.  Some clipboard managers update their
        MIME type list between the initial ``_available_clipboard_mimes()`` check
        and the actual read, so this fallback increases robustness.
        """
        # Capture timeout ID under lock, remove the source outside the lock.
        # BUG-043: We must NOT call _clear_active_timeout() here because it
        # also cancels the cancellable. Since this callback is part of the
        # async operation, cancelling it now would prevent read_texture_finish()
        # from succeeding. We only stop the watchdog timer.
        self._stop_timeout()

        try:
            # Marshal GTK operations to main thread
            def process_result() -> None:
                try:
                    texture = self.clipboard.read_texture_finish(result)
                    if not texture:
                        raise ValueError("No valid texture found in result.")

                    logger.info("Anura Clipboard: Image texture retrieved.")
                    self.emit("paste_from_clipboard", texture)
                except GLib.Error as e:
                    # Check if operation was cancelled
                    if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                        logger.debug("Anura Clipboard: Read operation cancelled.")
                        return
                    # Guard: if we already attempted the fallback chain once,
                    # emit an error instead of looping indefinitely.
                    with self._state_lock:
                        if self._fallback_attempted:
                            logger.warning(
                                f"Anura Clipboard: Texture read failed ({e.message}); "
                                "fallback already attempted, giving up.",
                            )
                            self._emit_clipboard_error(_("No image in clipboard"))
                            return
                        self._fallback_attempted = True
                    # Fallback: attempt to read as URI list (some clipboard managers
                    # expose file paths as text/uri-list but don't advertise them
                    # via get_formats() at the time of the initial check).
                    logger.warning(
                        f"Anura Clipboard: Texture read failed ({e.message}); falling back to URI list read.",
                    )
                    self._fallback_to_uri_list_read()
                    return
                except (ValueError, RuntimeError) as e:
                    # Technical rigor: log error for X11/Wayland clipboard synchronization issues
                    with self._state_lock:
                        if self._fallback_attempted:
                            logger.error(f"Anura Clipboard Error: {e}; fallback already attempted.")
                            self._emit_clipboard_error(_("No image in clipboard"))
                            return
                        self._fallback_attempted = True
                    logger.error(f"Anura Clipboard Error: {e}")
                    self._fallback_to_uri_list_read()
                    return
                finally:
                    # Clean up cancellable regardless of outcome
                    with self._state_lock:
                        self._cancellable = None

            GLib.idle_add(process_result)

        except (AttributeError, RuntimeError, TypeError) as e:
            # Handle unexpected errors in the callback setup itself
            logger.error(f"Anura Clipboard: Unexpected error in callback setup: {e}")

            def _on_error_idle():
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)

    def read_texture(self) -> None:
        """
        Thread-safe asynchronous texture reading with 10-second timeout.
        Strategy (in priority order):
        1. In-memory texture (read_texture_async) — bypasses filesystem entirely,
           works for clipboard sources that put pixel data directly on the clipboard
           (GIMP, screenshot tools, browsers, etc.).
        2. text/uri-list (read_async) — for file manager copies (e.g. user copied
           a PNG in PCManFM). Gdk.FileList is intentionally skipped: it invokes
           application/vnd.portal.filetransfer which hangs silently when
           xdg-desktop-portal is unavailable (VirtualBox/non-GNOME guests).
        3. Final fallback: read_texture_async again for sources with no MIME info.
        """
        with self._state_lock:
            # Reset fallback flag for this fresh read attempt
            self._fallback_attempted = False
            # Capture old timeout ID and cancellable to release outside the lock
            old_timeout_id = self._clipboard_timeout_id
            self._clipboard_timeout_id = None
            if self._cancellable is not None:
                self._cancellable.cancel()
                self._cancellable = None
            # Create new cancellable for this operation
            self._cancellable = Gio.Cancellable()
            cancellable = self._cancellable
            # Register the new timeout inside the lock so _clipboard_timeout_id
            # is always consistent with the active cancellable.
            self._clipboard_timeout_id = GLib.timeout_add_seconds(
                self.CLIPBOARD_TIMEOUT_SECONDS,
                self._on_clipboard_timeout,
                cancellable,
            )
        # Remove the old source outside the lock to avoid potential deadlock
        # with GLib's internal main-loop lock (see _clear_active_timeout).
        self._remove_source(old_timeout_id)

        mimes = self._available_clipboard_mimes()

        # Strategy: Prefer direct in-memory textures first (bypass filesystem entirely).
        texture_available = any(m.startswith("image/") for m in mimes)
        if texture_available:
            self.clipboard.read_texture_async(cancellable=cancellable, callback=self._on_read_texture)
            return

        # Direct URI list read — bypasses portal entirely (same rationale as DnD fix).
        # Gdk.FileList is intentionally skipped: on VirtualBox/non-GNOME guests,
        # read_value_async(Gdk.FileList) invokes application/vnd.portal.filetransfer
        # which hangs silently when xdg-desktop-portal is unavailable.
        if _CLIPBOARD_TEXT_URI_LIST in mimes:
            self.clipboard.read_async(
                [_CLIPBOARD_TEXT_URI_LIST],
                GLib.PRIORITY_DEFAULT,
                cancellable,
                self._on_read_uri_list,
            )
            return

        # Final fallback: try texture anyway (handles cases with no MIME info)
        self.clipboard.read_texture_async(cancellable=cancellable, callback=self._on_read_texture)

    def _available_clipboard_mimes(self) -> list[str]:
        """Return MIME types currently advertised by the clipboard (best effort)."""
        try:
            formats = self.clipboard.get_formats()
        except (AttributeError, RuntimeError, TypeError, GLib.Error) as e:
            logger.debug(f"Anura Clipboard: get_formats() failed: {e}")
            return []
        if formats is None:
            return []
        try:
            return list(formats.get_mime_types() or [])
        except (AttributeError, RuntimeError, TypeError, GLib.Error) as e:
            logger.debug(f"Anura Clipboard: get_mime_types() failed: {e}")
            return []

    def _emit_clipboard_error(self, message: str) -> None:
        """Emit the ``error`` signal from the main thread via idle_add."""

        def _on_error_idle():
            self.emit("error", message)
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_on_error_idle)

    def _stop_timeout(self) -> None:
        """Stop the watchdog timer without cancelling the underlying operation."""
        with self._state_lock:
            timeout_id = self._clipboard_timeout_id
            self._clipboard_timeout_id = None

        self._remove_source(timeout_id)

    def _remove_source(self, timeout_id: int | None) -> None:
        """Safely remove a GLib source ID if it still exists."""
        if timeout_id is not None and timeout_id > 0:
            # BUG-032: Check if source exists before removing to prevent C-level warnings
            # on stderr when a one-shot source has already fired and auto-removed.
            ctx = GLib.MainContext.default()
            if ctx and ctx.find_source_by_id(timeout_id):
                try:
                    GLib.source_remove(timeout_id)
                except (AttributeError, RuntimeError, TypeError, GLib.Error):
                    # Source might have fired between check and removal.
                    pass

    def _clear_active_timeout(self) -> None:
        """Atomically remove the in-flight read timeout and cancel the operation.

        GLib.source_remove() must be called OUTSIDE threading.Lock because it
        may need to acquire GLib's internal main-loop lock.  If the GTK main
        thread is simultaneously executing a timeout callback that tries to
        acquire self._state_lock, both threads would deadlock waiting for each
        other's lock.  The safe pattern: capture + clear the ID under the
        Python lock, then call source_remove after releasing it.
        """
        with self._state_lock:
            timeout_id = self._clipboard_timeout_id
            self._clipboard_timeout_id = None
            if self._cancellable is not None:
                self._cancellable.cancel()
                self._cancellable = None

        # source_remove called outside the lock to prevent deadlock.
        self._remove_source(timeout_id)

    def _on_read_uri_list(self, _sender: GObject.GObject, result: Gio.AsyncResult) -> None:
        """Callback for ``text/uri-list`` clipboard reads (file paths)."""
        # BUG-043: Stop the timer but DON'T cancel the operation we're currently finishing.
        self._stop_timeout()

        try:
            stream, _mime = self.clipboard.read_finish(result)
            if stream is None:
                raise ValueError("No URI list stream from clipboard.")
        except GLib.Error as e:
            if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                logger.debug("Anura Clipboard: URI list read cancelled.")
                return
            logger.warning(
                f"Anura Clipboard: URI list read failed ({e.message}); falling back to texture.",
            )
            self._fallback_to_texture_read()
            return
        except (ValueError, RuntimeError) as e:
            logger.warning(f"Anura Clipboard: URI list read returned no stream ({e}); falling back.")
            self._fallback_to_texture_read()
            return

        # FIX BUG-H-005: capture _cancellable under _state_lock so a concurrent call to
        # cancel_pending_operations() (which holds _state_lock and sets _cancellable=None)
        # cannot race with this read.  _stop_timeout() above deliberately does NOT cancel
        # _cancellable (BUG-043), so the lock just guards the snapshot.
        with self._state_lock:
            cancellable = self._cancellable
        self._read_stream_to_bytes(
            stream,
            cancellable,
            lambda data: self._on_uri_list_bytes(data),
        )

    def _fallback_to_texture_read(self) -> None:
        """Rearm the read state and ask GDK for a texture directly.

        Called from _on_read_uri_list when the URI-list path also fails.
        Does NOT reset _fallback_attempted: that flag was set True by the
        original texture-read failure and must remain True so that if this
        second texture attempt also fails, _on_read_texture will stop the
        cycle and emit an error instead of looping again.
        """
        # BUG-032: Clear previous timeout before assigning new one to avoid leaks.
        # Here we use _clear_active_timeout() because we ARE starting a fresh attempt.
        self._clear_active_timeout()

        with self._state_lock:
            # Both fallback paths have now been tried — bail out if so.
            if self._fallback_attempted:
                logger.warning(
                    "Anura Clipboard: Both texture and URI-list reads failed; giving up.",
                )
            if self._cancellable is None or self._cancellable.is_cancelled():
                self._cancellable = Gio.Cancellable()
            cancellable = self._cancellable
            # NOTE: _fallback_attempted intentionally NOT reset here.
            # Resetting it would allow read_texture_async → fail →
            # _fallback_to_uri_list_read → fail → _fallback_to_texture_read
            # to loop infinitely.  The guard stays True so the next
            # texture failure terminates the chain with an error signal.
            self._clipboard_timeout_id = GLib.timeout_add_seconds(
                self.CLIPBOARD_TIMEOUT_SECONDS,
                self._on_clipboard_timeout,
                cancellable,
            )
        self.clipboard.read_texture_async(cancellable=cancellable, callback=self._on_read_texture)

    def _fallback_to_uri_list_read(self) -> None:
        """Rearm the read state and read the clipboard as a ``text/uri-list``."""
        # BUG-032: Clear previous timeout before assigning new one to avoid leaks.
        # Here we use _clear_active_timeout() because we ARE starting a fresh attempt.
        self._clear_active_timeout()

        with self._state_lock:
            if self._cancellable is None or self._cancellable.is_cancelled():
                self._cancellable = Gio.Cancellable()
            cancellable = self._cancellable
            self._clipboard_timeout_id = GLib.timeout_add_seconds(
                self.CLIPBOARD_TIMEOUT_SECONDS,
                self._on_clipboard_timeout,
                cancellable,
            )
        self.clipboard.read_async(
            [_CLIPBOARD_TEXT_URI_LIST],
            GLib.PRIORITY_DEFAULT,
            cancellable,
            self._on_read_uri_list,
        )

    def _read_stream_to_bytes(
        self,
        stream: Gio.InputStream,
        cancellable: Gio.Cancellable | None,
        on_done: Callable[[bytes], None],
    ) -> None:
        """Read a Gio.InputStream fully and invoke ``on_done(bytes)``."""
        chunks: list[bytes] = []

        def _on_chunk(_stream: Gio.InputStream, res: Gio.AsyncResult) -> None:
            try:
                gbytes = stream.read_bytes_finish(res)
            except GLib.Error as e:
                if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                    logger.debug("Anura Clipboard: stream read cancelled.")
                    return
                logger.error(f"Anura Clipboard: stream read failed: {e.message}")

                def _on_error_idle():
                    self.emit("error", _("No image in clipboard"))
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_error_idle)
                return
            data = gbytes.get_data() if gbytes is not None else b""
            if not data:
                on_done(b"".join(chunks))
                return
            chunks.append(bytes(data))
            stream.read_bytes_async(
                _CLIPBOARD_STREAM_CHUNK,
                GLib.PRIORITY_DEFAULT,
                cancellable,
                _on_chunk,
            )

        stream.read_bytes_async(
            _CLIPBOARD_STREAM_CHUNK,
            GLib.PRIORITY_DEFAULT,
            cancellable,
            _on_chunk,
        )

    def _on_uri_list_bytes(self, data: bytes) -> None:
        """Decode a text/uri-list payload and load the first image file URI."""
        if not data:
            logger.debug("Anura Clipboard: URI list payload is empty.")

            def _on_error_idle():
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return

        text = data.decode("utf-8", errors="replace")
        # RFC 2483: lines are CRLF separated; lines starting with '#' are comments.
        uris = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
        file_uri = next((u for u in uris if u.startswith("file://")), None)
        if not file_uri:
            # Mask entries for safety
            masked_entries = [mask_url(u) for u in uris[:3]]
            logger.debug(f"Anura Clipboard: no file:// URI in list (entries={masked_entries!r}).")

            def _on_error_idle():
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return

        try:
            path, _hostname = GLib.filename_from_uri(file_uri)
        except GLib.Error as e:
            logger.warning(f"Anura Clipboard: bad file URI {mask_url(file_uri)}: {e.message}")

            def _on_error_idle():
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return

        if not path or not Path(path).exists():
            logger.warning(f"Anura Clipboard: file does not exist or inaccessible: {path!r}")
            self._emit_clipboard_error(_("No image in clipboard"))
            return

        self._emit_texture_from_file(path)

    def _emit_texture_from_file(self, path: str) -> None:
        """Decode an image file with PIL → re-encode to PNG → Gdk.Texture."""
        # Security Hardening: Validate file size before opening (DoS prevention)
        is_valid, _size, error = validate_image_resource(path)
        if not is_valid:
            logger.error(f"Anura Clipboard: {error}")
            self._emit_clipboard_error(_(error) if error else _("No image in clipboard"))
            return

        try:
            with Image.open(path) as img:
                img.load()
                out = img if img.mode in ("RGB", "RGBA", "L") else img.convert("RGBA")
                buf = BytesIO()
                out.save(buf, format="PNG")
                png_bytes = buf.getvalue()
        except (OSError, ValueError, Image.UnidentifiedImageError) as e:
            logger.warning(f"Anura Clipboard: PIL failed to decode {path!r}: {e}")

            def _on_error_idle():
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return

        try:
            texture = Gdk.Texture.new_from_bytes(GLib.Bytes.new(png_bytes))
        except GLib.Error as e:
            logger.warning(f"Anura Clipboard: Gdk.Texture.new_from_bytes failed: {e.message}")

            def _on_error_idle():
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return

        logger.debug(f"Anura Clipboard: loaded image from clipboard file URI ({path}).")

        def _on_success_idle(tex):
            self.emit("paste_from_clipboard", tex)
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_on_success_idle, texture)

    # Note: read_text() and _on_text_read() have been removed as they were dead code.
    # The method read clipboard text but never emitted a signal or called a callback,
    # making it a no-op for consumers. If text reading from clipboard is needed in
    # the future, implement it following the pattern used by paste_from_clipboard()
    # which correctly emits the "paste_from_clipboard" signal.

    def _on_clipboard_timeout(self, cancellable: Gio.Cancellable) -> bool:
        """Thread-safe timeout handler with atomic state management."""
        with self._state_lock:
            # Enhanced null check for cancellable object
            if cancellable is None:
                logger.debug("Anura Clipboard: Timeout called with null cancellable")
                return False

            # Check if this cancellable is still the active one (not replaced by new operation)
            if cancellable is not self._cancellable:
                # Stale timeout from previous operation - ignore
                logger.debug("Anura Clipboard: Stale timeout detected, ignoring")
                return False

            # This is the active timeout, handle cancellation
            active_cancellable = self._cancellable
            self._clipboard_timeout_id = None

        if active_cancellable and not active_cancellable.is_cancelled():
            logger.warning("Anura Clipboard: Read operation timed out after 10s, cancelling.")
            active_cancellable.cancel()

            # Emit error signal so UI can show user feedback
            def _on_error_idle():
                self.emit("error", _("Clipboard read operation timed out."))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)

        return False  # Don't repeat timeout

    def cancel_pending_operations(self) -> None:
        """Thread-safe cancellation of pending clipboard read operations."""
        self._clear_active_timeout()

    def cleanup(self) -> None:
        """Clean up resources and cancel pending operations."""
        self.cancel_pending_operations()
        logger.debug("Anura Clipboard: Cleanup completed.")


# Thread-safe singleton instance for global app access
def get_clipboard_service() -> ClipboardService:
    """Get the thread-safe clipboard service singleton."""
    return get_instance(ClipboardService)
