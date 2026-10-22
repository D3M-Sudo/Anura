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
import time
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

from anura.utils import mask_url, validate_image_dimensions, validate_image_resource  # noqa: E402
from anura.utils.singleton import get_instance  # noqa: E402

# When the clipboard advertises a file URI list (e.g. user copied a PNG from
# Nautilus), reading the URI list and loading the file via PIL is much more
# reliable than ``read_texture_async`` — the latter happily picks unsupported
# MIME types like ``image/x-xpixmap`` and then fails the entire paste.
_CLIPBOARD_TEXT_URI_LIST = "text/uri-list"

# Stream chunk size when slurping clipboard streams.
_CLIPBOARD_STREAM_CHUNK = 16 * 1024

# Hard cap on the text/uri-list payload buffered in memory. The clipboard source
# controls the stream length, and CLIPBOARD_TIMEOUT_SECONDS only bounds elapsed
# time: without a byte cap a paste can allocate an unbounded amount of memory.
_CLIPBOARD_URI_LIST_MAX_BYTES = 1024 * 1024


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

    _clipboard: Gdk.Clipboard | None = None
    _state_lock: threading.Lock

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

        # Gdk.Clipboard.set_text() is not exposed to PyGObject in GTK4, so the text is
        # published through set_content() with a ContentProvider.
        #
        # The provider must wrap a plain string (G_TYPE_STRING): GTK then advertises
        # text/plain;charset=utf-8 and text/plain (plus UTF8_STRING and friends on X11)
        # and every other application can paste it. Wrapping the string in a
        # GLib.Variant would publish only the "GVariant" format, which nothing else
        # can read, so the copy would silently never reach the other apps.
        content = Gdk.ContentProvider.new_for_value(GObject.Value(GObject.TYPE_STRING, value))
        # Gdk.Clipboard.set_content() returns True if the content was set.
        # We don't need a watchdog for a one-shot synchronous set operation
        # that doesn't involve any async callback or stream read.
        # Removing the leaked timeout (BUG-NEW-CS-001).
        self.clipboard.set_content(content)

        logger.debug(f"Anura Clipboard: Text successfully copied: {value[:50]}...")

    def copy_text(self, text: str) -> None:
        """Legacy alias for set(text)."""
        self.set(text)

    def _default_context_in_use(self) -> bool:
        """Return True when iterating the default context would re-enter its loop.

        Silent/CLI mode iterates a private context, so the default one is free
        there; an active GTK main loop owns it instead. Checking the depth as
        well covers a call made from another thread while the loop runs.
        """
        context = GLib.MainContext.default()
        if context.is_owner():
            return True
        depth = getattr(context, "depth", 0)
        return isinstance(depth, int) and depth > 0

    def hand_off_to_manager(self, timeout_seconds: float = 3.0) -> bool:
        """Ask the desktop clipboard manager to keep the current content after exit.

        The clipboard belongs to the process that set it: when a short-lived process
        (headless/silent mode) exits, the text disappears unless a clipboard manager
        took it over first. This asks GTK to do that and waits for the answer.

        Blocking: it runs the default main context itself, so call it only when no UI
        main loop is running. Returns False without iterating when the default context
        is already running (for example when called from a GTK callback). Never raises;
        returns True only if a manager took the content. Returns False when there is no
        manager (X11: "No clipboard manager is active") or the backend cannot store at
        all (Wayland: "cannot store data").
        """
        if self._default_context_in_use():
            logger.warning("Anura Clipboard: refusing to iterate the default main context while it is running.")
            return False

        try:
            clipboard = self.clipboard
        except RuntimeError as e:
            logger.warning(f"Anura Clipboard: Cannot hand off clipboard content: {e}")
            return False

        outcome: dict[str, bool] = {}
        cancellable = Gio.Cancellable()

        def on_stored(source: Gdk.Clipboard, result: Gio.AsyncResult) -> None:
            try:
                source.store_finish(result)
                outcome["stored"] = True
            except GLib.Error as e:
                logger.debug(f"Anura Clipboard: Clipboard manager hand-off unavailable: {e.message}")
                outcome["stored"] = False

        clipboard.store_async(GLib.PRIORITY_DEFAULT, cancellable, on_stored)
        context = GLib.MainContext.default()
        deadline = time.monotonic() + timeout_seconds
        while "stored" not in outcome and time.monotonic() < deadline:
            context.iteration(False)
            time.sleep(0.005)

        if "stored" not in outcome:
            cancellable.cancel()
            logger.warning("Anura Clipboard: Clipboard manager hand-off timed out.")
            return False
        return outcome["stored"]

    def wait_until_replaced(self, timeout_seconds: float, should_stop: Callable[[], bool] | None = None) -> bool:
        """Keep serving our clipboard content until another application replaces it.

        Fallback for short-lived processes when no clipboard manager took the content
        over (see hand_off_to_manager): the text stays pasteable only while this process
        is alive and its main context keeps answering paste requests.

        Blocking, same caveat as hand_off_to_manager. Returns True when another
        application took the clipboard, False on timeout, on should_stop() or when no
        display is available. Returns False without iterating when the default context
        is already running.
        """
        if self._default_context_in_use():
            logger.warning("Anura Clipboard: refusing to iterate the default main context while it is running.")
            return False

        try:
            clipboard = self.clipboard
        except RuntimeError as e:
            logger.warning(f"Anura Clipboard: Cannot wait for clipboard replacement: {e}")
            return False

        context = GLib.MainContext.default()
        deadline = time.monotonic() + timeout_seconds
        while clipboard.is_local():
            if (should_stop is not None and should_stop()) or time.monotonic() >= deadline:
                return False
            context.iteration(False)
            time.sleep(0.02)
        return True

    def _on_read_texture(self, _sender: GObject.GObject, result: Gio.AsyncResult) -> None:
        """
        Primary callback for texture reading from clipboard.

        Triggered by clipboard.read_texture_async() initiated from read_texture()
        or _fallback_to_texture_read(). Handles successful texture reads and
        coordinates fallback to URI-list reading on failure.

        State reads:
            - _state_lock: Guards access to _fallback_attempted and _cancellable
            - _cancellable: Shared cancellable for the async operation
            - _fallback_attempted: Guard flag preventing infinite fallback loops

        State mutates:
            - Sets _fallback_attempted = True on first failure before delegating
            - Clears _cancellable in finally block regardless of outcome

        Hand-off:
            - Calls _fallback_to_uri_list_read() on texture read failure
            - Emits "paste_from_clipboard" signal on success
            - Emits "error" signal when fallback already attempted

        References:
            - BUG-043: Timeout handling (uses _stop_timeout(), not _clear_active_timeout())
            - BUG-H-005: Cancellable race condition protection via _state_lock
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

            def _on_error_idle() -> bool:
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

        def _on_error_idle() -> bool:
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
        """
        Fallback callback for text/uri-list clipboard reads.

        Triggered by clipboard.read_async() initiated from _fallback_to_uri_list_read()
        when direct texture reading fails. Handles file URI extraction and delegates
        to texture loading from file.

        State reads:
            - _state_lock: Guards cancellable snapshot (BUG-H-005)
            - _cancellable: Snapshotted under lock to prevent race with cancel_pending_operations()

        State mutates:
            - Stops the watchdog timer via _stop_timeout()
            - Cancellable is read-only, snapshotted under lock only

        Hand-off:
            - Calls _fallback_to_texture_read() on URI-list read failure
            - Calls _read_stream_to_bytes() on successful stream read
            - Eventually calls _emit_texture_from_file() via _on_uri_list_bytes()

        References:
            - BUG-043: Timeout handling (uses _stop_timeout(), not _clear_active_timeout())
            - BUG-H-005: Cancellable race condition protection via _state_lock snapshot
        """
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
        """
        Rearm read state and retry texture read when URI-list path fails.

        Called from _on_read_uri_list when the URI-list fallback also fails.
        Reuses the existing cancellable if still valid, otherwise creates a new one,
        and initiates a second texture read attempt. Does NOT reset _fallback_attempted:
        that flag was set True by the original texture-read failure and must remain
        True so that if this second texture attempt also fails, _on_read_texture will
        stop the cycle and emit an error instead of looping again.

        State reads:
            - _state_lock: Guards access to _fallback_attempted, _cancellable, _clipboard_timeout_id
            - _fallback_attempted: Guard flag preventing infinite fallback loops
            - _cancellable: Reused if valid, otherwise recreated
            - _clipboard_timeout_id: Previous timeout cleared before creating new one

        State mutates:
            - Reuses existing _cancellable if not cancelled, otherwise creates new Gio.Cancellable()
            - Sets new _clipboard_timeout_id via GLib.timeout_add_seconds()
            - Does NOT modify _fallback_attempted (preserves guard state)

        Hand-off:
            - Calls clipboard.read_texture_async() with _on_read_texture callback
            - If this second texture attempt fails, _on_read_texture checks _fallback_attempted
              and emits "error" instead of looping again

        References:
            - BUG-032: Timeout leak prevention (uses _clear_active_timeout())
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
        """
        Rearm read state and attempt URI-list read when texture path fails.

        Called from _on_read_texture when direct texture reading fails. Creates a new
        cancellable if needed, sets up a fresh timeout, and initiates a text/uri-list
        read to handle file manager copies (e.g., user copied a PNG in Nautilus).

        State reads:
            - _state_lock: Guards access to _cancellable and _clipboard_timeout_id
            - _cancellable: Reused if valid, otherwise recreated
            - _clipboard_timeout_id: Previous timeout cleared before creating new one

        State mutates:
            - Creates new Gio.Cancellable() if existing one is None or cancelled
            - Sets new _clipboard_timeout_id via GLib.timeout_add_seconds()
            - Sets _fallback_attempted = True in _on_read_texture before calling this method

        Hand-off:
            - Calls clipboard.read_async() with _on_read_uri_list callback
            - If URI-list read fails, _on_read_uri_list calls _fallback_to_texture_read()

        References:
            - BUG-032: Timeout leak prevention (uses _clear_active_timeout())
        """
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
        max_bytes: int = _CLIPBOARD_URI_LIST_MAX_BYTES,
    ) -> None:
        """Read a Gio.InputStream fully and invoke ``on_done(bytes)``.

        At most ``max_bytes`` are buffered: past the limit the read is stopped,
        the chunks are dropped and a clipboard error is emitted, so an oversized
        payload never reaches the join/decode/split stage. The existing timeout
        bounds elapsed time, not memory.
        """
        chunks: list[bytes] = []
        total = 0
        rejected = False

        def _reject(reason: str) -> None:
            nonlocal rejected
            if rejected:
                return
            rejected = True
            chunks.clear()
            logger.warning(f"Anura Clipboard: {reason}")
            # Stop the pending read and release the stream; both are best-effort
            # because the source may already be gone.
            if cancellable is not None:
                cancellable.cancel()
            stream.close_async(GLib.PRIORITY_DEFAULT, None, None)

            def _on_error_idle() -> bool:
                # Reuses the existing translated string: the payload is treated
                # as unusable content, while the precise reason stays in the log.
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)

        def _on_chunk(_stream: Gio.InputStream, res: Gio.AsyncResult) -> None:
            nonlocal total
            if rejected:
                return
            try:
                gbytes = stream.read_bytes_finish(res)
            except GLib.Error as e:
                if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                    logger.debug("Anura Clipboard: stream read cancelled.")
                    return
                logger.error(f"Anura Clipboard: stream read failed: {e.message}")

                def _on_error_idle() -> bool:
                    self.emit("error", _("No image in clipboard"))
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_error_idle)
                return
            data = gbytes.get_data() if gbytes is not None else b""
            if not data:
                on_done(b"".join(chunks))
                return
            if total + len(data) > max_bytes:
                _reject(f"URI list exceeds the {max_bytes}-byte limit; discarding")
                return
            total += len(data)
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

            def _on_error_idle() -> bool:
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

            def _on_error_idle() -> bool:
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return

        try:
            path, _hostname = GLib.filename_from_uri(file_uri)
        except GLib.Error as e:
            logger.warning(f"Anura Clipboard: bad file URI {mask_url(file_uri)}: {e.message}")

            def _on_error_idle() -> bool:
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
                # #522: reject a decompression bomb from the header before
                # load()/convert() allocate the decoded bitmap.
                dims_ok, dims_error = validate_image_dimensions(*img.size)
                if not dims_ok:
                    logger.error(f"Anura Clipboard: {dims_error}")
                    self._emit_clipboard_error(_("No image in clipboard"))
                    return

                img.load()
                out = img if img.mode in ("RGB", "RGBA", "L") else img.convert("RGBA")
                buf = BytesIO()
                out.save(buf, format="PNG")
                png_bytes = buf.getvalue()
        except (OSError, ValueError, Image.UnidentifiedImageError) as e:
            logger.warning(f"Anura Clipboard: PIL failed to decode {path!r}: {e}")

            def _on_error_idle() -> bool:
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return

        try:
            texture = Gdk.Texture.new_from_bytes(GLib.Bytes.new(png_bytes))
        except GLib.Error as e:
            logger.warning(f"Anura Clipboard: Gdk.Texture.new_from_bytes failed: {e.message}")

            def _on_error_idle() -> bool:
                self.emit("error", _("No image in clipboard"))
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return

        logger.debug(f"Anura Clipboard: loaded image from clipboard file URI ({path}).")

        def _on_success_idle(tex: Gdk.Texture) -> bool:
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
            def _on_error_idle() -> bool:
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
