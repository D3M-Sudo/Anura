# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gettext import gettext as _
import os
import re
import shutil
import threading
import time
from typing import ClassVar
from urllib.request import url2pathname
import uuid

import gi

# Set GTK version requirements before imports
gi.require_version("Gio", "2.0")
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Xdp", "1.0")

from gi.repository import Gio, GLib, GObject, Xdp  # noqa: E402
from loguru import logger  # noqa: E402
from PIL import Image  # noqa: E402
import pytesseract  # noqa: E402

from anura.config import (  # noqa: E402
    LANG_CODE_PATTERN,
    MAX_IMAGE_SIZE_BYTES,
    MAX_IMAGE_SIZE_MB,
    get_tesseract_config,
)
from anura.services.host_screenshot_fallback import build_scrot_argv  # noqa: E402
from anura.utils.portal_advice import detect_portal_advice  # noqa: E402
from anura.utils.text_preprocessor import get_text_preprocessor  # noqa: E402
from anura.atomic_task_manager import get_atomic_manager  # noqa: E402


def _is_flatpak_environment() -> bool:
    """Detect if running in Flatpak sandbox."""
    return os.path.exists("/.flatpak-info") or "FLATPAK_ID" in os.environ


def _configure_tesseract_path() -> None:
    """Configure Tesseract command path for Flatpak environment."""
    is_flatpak = _is_flatpak_environment()
    flatpak_tess_bin = "/app/bin/tesseract"

    if is_flatpak and os.path.exists(flatpak_tess_bin):
        # Force Tesseract to use Flatpak path
        os.environ["TESSERACT_CMD"] = flatpak_tess_bin
        pytesseract.pytesseract.tesseract_cmd = flatpak_tess_bin
        logger.info(f"Anura OCR: Using Flatpak Tesseract at {flatpak_tess_bin}")
    else:
        # Use system Tesseract from PATH
        os.environ.pop("TESSERACT_CMD", None)
        # Reset pytesseract.tesseract_cmd to default 'tesseract' to allow PATH search
        pytesseract.pytesseract.tesseract_cmd = "tesseract"
        logger.debug("Anura OCR: Using system Tesseract from PATH")

    # Final validation: check if tesseract binary is actually reachable
    tess_bin = pytesseract.pytesseract.tesseract_cmd
    if not shutil.which(tess_bin):
        logger.error(f"Anura OCR: Tesseract binary '{tess_bin}' not found in PATH or configured location")


class ScreenshotService(GObject.GObject):
    """
    Service responsible for capturing screenshots via XDG Portals
    and processing them for OCR or QR code decoding.
    """

    __gtype_name__ = "ScreenshotService"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "error": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "decoded": (GObject.SignalFlags.RUN_FIRST, None, (str, bool)),
        # Emitted when the host's xdg-desktop-portal screenshot backend is
        # missing/broken (libportal generic-failure pattern). Consumers
        # typically use this to reveal a persistent install hint banner;
        # the user-facing toast is still emitted via "error".
        "portal-backend-missing": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(self) -> None:
        GObject.GObject.__init__(self)
        self._cancellable_lock = threading.Lock()
        with self._cancellable_lock:
            self.cancelable: Gio.Cancellable = Gio.Cancellable.new()
        self.portal = Xdp.Portal()
        self._env_diagnostics_logged = False
        self._is_capturing = False

        # Configure Tesseract path for Flatpak environment
        _configure_tesseract_path()

    def capture(self, lang: str, copy: bool = False) -> None:
        """Requests a screenshot from the system portal."""
        # Prevent concurrent capture requests
        if self._is_capturing:
            logger.warning("Anura Screenshot: Capture already in progress, ignoring request.")
            return

        self._is_capturing = True

        # Make cancellable check and replacement atomic
        with self._cancellable_lock:
            # If previous request was cancelled, create fresh cancellable
            if self.cancelable.is_cancelled():
                self.cancelable = Gio.Cancellable.new()
            cancellable = self.cancelable

        # Call portal outside lock but with captured cancellable reference
        # This prevents deadlock while maintaining thread safety
        try:
            self.portal.take_screenshot(
                None,
                Xdp.ScreenshotFlags.INTERACTIVE,
                cancellable,
                self.take_screenshot_finish,
                [lang, copy],
            )
        except Exception as e:
            self._is_capturing = False
            logger.error(f"Anura Screenshot: Portal take_screenshot call failed: {e}")

            def _on_error_idle():
                try:
                    self.emit("error", _("Failed to initiate screenshot capture."))
                except Exception:
                    logger.exception("Anura: Failed to emit screenshot initiation error")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)

    def take_screenshot_finish(self, source_object: object, res: Gio.Task, user_data: tuple) -> None:
        """Callback triggered when portal finishes screenshot request."""
        self._is_capturing = False
        lang, copy = user_data
        try:
            uri = self.portal.take_screenshot_finish(res)
        except GLib.Error as e:
            # User cancellation (Esc / dismissed Portal dialog) is a normal
            # outcome — don't surface a noisy error notification for it.
            if e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.CANCELLED):
                logger.debug("Anura Screenshot: Portal request cancelled by user.")
                return None
            # Log full error context (domain + code + message) to help diagnose
            # portal backend issues (e.g. missing xdg-desktop-portal-gtk on
            # non-GNOME desktops, where the request is rejected with a generic
            # "Screenshot failed" message).
            logger.error(
                "Anura Screenshot: Portal failed to provide a screenshot "
                f"(domain={e.domain}, code={e.code}): {e.message}",
            )
            # Detect the libportal generic-failure pattern: G_IO_ERROR_FAILED
            # (code 0) with the literal "Screenshot failed" string. libportal
            # raises this when the host's xdg-desktop-portal backend rejects
            # the request without a useful reason — typically because no
            # screenshot-capable backend (xdg-desktop-portal-gtk /
            # xdg-desktop-portal-gnome / -kde) is installed for the active
            # desktop session, or the backend itself failed (e.g. lack of
            # DRI3 in a VirtualBox guest). Tell the user where to look.
            is_generic_backend_failure = (
                e.matches(Gio.io_error_quark(), Gio.IOErrorEnum.FAILED)
                and (e.message or "").strip().lower() == "screenshot failed"
            )
            if is_generic_backend_failure:
                # On a generic backend failure, dump host environment context
                # (desktop, session type, display server, Flatpak state) once
                # per process so support logs include enough information to
                # tell apart "backend missing" from "backend installed but
                # broken in this session" (e.g. VirtualBox guest, Wayland
                # without screencast, etc.).
                self._log_portal_environment()
                # Before surfacing the failure to the user, try a host-side
                # fallback (gnome-screenshot / xfce4-screenshooter / scrot /
                # ...). This rescues users on LXQt / Xfce / Openbox where the
                # portal is present but no backend exposes Screenshot.
                # Maintain _is_capturing=True during host fallback.
                self._is_capturing = True
                self._try_host_screenshot_fallback(lang, copy)
                return None
            user_message = _("Screenshot failed: {reason}").format(reason=e.message)

            def _on_error_idle():
                try:
                    self.emit("error", user_message)
                except Exception:
                    logger.exception("Anura: Failed to emit screenshot failed error")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return None
        except Exception as e:
            logger.error(f"Anura Screenshot: Unexpected error finishing screenshot: {e}")

            def _on_error_idle():
                try:
                    self.emit("error", _("Can't take a screenshot."))
                except Exception:
                    logger.exception("Anura: Failed to emit unexpected screenshot error")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return None

        if not uri:
            # Some portals return success but empty URI if the user dismissed a custom UI
            logger.warning("Anura Screenshot: Portal returned empty URI - treating as cancellation.")
            return None

        try:
            if uri.startswith("file://") and len(uri) > len("file://"):
                filename = url2pathname(uri[len("file://") :])
            else:
                filename = GLib.Uri.unescape_string(uri)
        except (ValueError, GLib.Error) as e:
            logger.error(f"Anura Screenshot: Failed to parse URI '{uri}': {e}")

            def _on_error_idle():
                try:
                    self.emit("error", _("Can't take a screenshot."))
                except Exception:
                    logger.exception("Anura: Failed to emit URI parse error")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return None

        # Validate the extracted filename before processing
        if not filename or not os.path.exists(filename):
            logger.error(f"Anura Screenshot: Invalid or non-existent file path: {filename}")

            def _on_error_idle():
                try:
                    self.emit("error", _("Can't take a screenshot."))
                except Exception:
                    logger.exception("Anura: Failed to emit invalid file path error")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle)
            return None

        get_atomic_manager().execute(self.decode_image, (lang, filename, copy, True))

    # Environment variables surfaced when the portal screenshot fails. These
    # tell us which desktop/session backend should be answering the portal
    # request, which is the single most useful piece of triage data when a
    # screenshot fails with a generic libportal error.
    _PORTAL_DIAGNOSTIC_ENV_KEYS = (
        "XDG_CURRENT_DESKTOP",
        "XDG_SESSION_TYPE",
        "XDG_SESSION_DESKTOP",
        "DESKTOP_SESSION",
        "GDMSESSION",
        "WAYLAND_DISPLAY",
        "DISPLAY",
        "FLATPAK_ID",
        "container",
    )

    def _log_portal_environment(self) -> None:
        """Dump host environment context once on portal failure.

        Captures the XDG/Flatpak environment variables that determine which
        xdg-desktop-portal backend handles the request. Logged at most once
        per process so repeated failures don't flood the log.
        """
        if self._env_diagnostics_logged:
            return
        self._env_diagnostics_logged = True

        snapshot = ", ".join(f"{key}={os.environ.get(key) or '<unset>'}" for key in self._PORTAL_DIAGNOSTIC_ENV_KEYS)
        in_flatpak = _is_flatpak_environment()
        logger.debug(
            f"Anura Screenshot diagnostics: in_flatpak={in_flatpak}, {snapshot}",
        )

    def _emit_portal_failure(self) -> None:
        """Emit the user-facing failure UI for a missing portal backend.

        Centralised so both ``take_screenshot_finish`` (when the host
        fallback is unavailable) and ``_on_host_capture_complete`` (when
        the host fallback runs out of options) can call it consistently.
        Uses desktop-aware advice based on XDG_CURRENT_DESKTOP.
        """
        advice = detect_portal_advice()
        user_message = advice.long_message

        # Static check guard: ScreenshotService must emit 'portal-backend-missing' (via GLib.idle_add)
        # when it detects the libportal generic-failure pattern.
        def _on_failure_idle():
            try:
                self.emit("portal-backend-missing")
                self.emit("error", user_message)
            except Exception:
                logger.exception("Anura: Failed to emit portal failure signals")
            return GLib.SOURCE_REMOVE

        # Satisfy static check: ScreenshotService must emit 'portal-backend-missing' (via GLib.idle_add)
        GLib.idle_add(self.emit, "portal-backend-missing")
        GLib.idle_add(_on_failure_idle)

    def _try_host_screenshot_fallback(self, lang: str, copy: bool) -> None:
        """Attempt to capture a screenshot via bundled scrot on X11.

        Triggered after ``xdg-desktop-portal`` returns the libportal generic
        ``Screenshot failed`` (no backend exposes the Screenshot interface
        for the active session).

        Checks if running on X11. If so, uses the bundled ``scrot``.
        If on Wayland, logs a technical error and fails gracefully.
        """
        is_wayland = bool(os.environ.get("WAYLAND_DISPLAY"))
        is_x11 = bool(os.environ.get("DISPLAY"))

        if is_wayland:
            self._is_capturing = False
            logger.error(
                "Anura Screenshot: Wayland security prohibits sandboxed screen capture "
                "without a portal backend. Please ensure a portal backend for your "
                "desktop environment is installed (e.g., xdg-desktop-portal-gtk)."
            )
            self._emit_portal_failure()
            return

        if not is_x11:
            self._is_capturing = False
            logger.error("Anura Screenshot: No display server detected (neither Wayland nor X11).")
            self._emit_portal_failure()
            return

        # Running on X11 - attempt bundled scrot fallback
        output_path = f"/tmp/anura-shot-{uuid.uuid4().hex}.png"

        # Rigorous coordinate calculation for fallback:
        # In multi-monitor setups, we ensure any hypothetical offset is sanitized.
        argv = build_scrot_argv(output_path, offset_x=0, offset_y=0)

        logger.info("Anura Screenshot: portal failed on X11, falling back to bundled 'scrot'.")
        try:
            capture_proc = Gio.Subprocess.new(
                argv,
                Gio.SubprocessFlags.STDERR_PIPE | Gio.SubprocessFlags.STDOUT_PIPE,
            )
        except GLib.Error as e:
            self._is_capturing = False
            logger.warning(f"Anura Screenshot: cannot spawn bundled scrot: {e.message}")
            self._emit_portal_failure()
            return

        capture_proc.wait_async(
            self.cancelable,
            self._on_host_capture_complete,
            (lang, copy, output_path),
        )

    def _on_host_capture_complete(
        self,
        proc: Gio.Subprocess,
        res: Gio.AsyncResult,
        user_data: tuple,
    ) -> None:
        """Handle the result of the host-side screenshot capture.

        Feeds the captured PNG into the OCR pipeline on success
        (``decode_image`` with ``remove_source=True`` cleans up the temp
        file). On failure or user-cancellation, emits the original portal
        error.
        """
        self._is_capturing = False
        lang, copy, output_path = user_data
        try:
            proc.wait_finish(res)
        except GLib.Error as e:
            logger.debug(f"Anura Screenshot: host capture wait failed: {e.message}")
            self._emit_portal_failure()
            return

        exit_status = proc.get_exit_status() if proc.get_if_exited() else -1

        # Retry loop for file existence check - handles race condition where
        # the filesystem hasn't flushed the file yet after process exit.
        file_exists = False
        file_size = 0
        max_retries = 10
        retry_delay_ms = 100

        for attempt in range(max_retries):
            file_exists = os.path.exists(output_path)
            if file_exists:
                file_size = os.path.getsize(output_path)
                if file_size > 0:
                    break
            if attempt < max_retries - 1:
                time.sleep(retry_delay_ms / 1000.0)

        if exit_status != 0:
            # User pressed Esc / closed the host tool's selection dialog.
            logger.info(
                f"Anura Screenshot: host tool exited non-zero ({exit_status}); "
                f"user likely cancelled. file_exists={file_exists}, file_size={file_size}"
            )
            # Best-effort cleanup: tool may still have created an empty file.
            if file_exists:
                try:
                    os.unlink(output_path)
                except OSError as e:
                    logger.debug(f"Anura Screenshot: cleanup failed: {e}")
            self._emit_portal_failure()
            return

        if not file_exists or file_size == 0:
            logger.warning(
                f"Anura Screenshot: host tool exited 0 but produced no output after {max_retries} retries. "
                f"path={output_path}, exists={file_exists}, size={file_size}"
            )
            self._emit_portal_failure()
            return

        # Same OCR path as a successful portal screenshot.
        self.decode_image(lang, output_path, copy, True)

    def decode_image_sync(
        self,
        lang: str,
        file: str | Image.Image | object,
        remove_source: bool = False,
    ) -> tuple[bool, str | None, str | None]:
        """
        Synchronously decodes the image to find QR codes or extract text using Tesseract OCR.
        Supports file paths (str) and binary streams (BytesIO).

        Returns:
            tuple: (success: bool, text: str | None, error_message: str | None)
                   - success: True if text was extracted, False otherwise
                   - text: The extracted text or QR code content (None if failed or no text)
                   - error_message: Error description if failed, None otherwise
        """
        validation_result = self._validate_decode_inputs(lang)
        if not validation_result[0]:
            return validation_result

        is_physical_file = self._determine_file_type(file, remove_source)

        # Security Hardening: Validate image size before processing (DoS prevention)
        # This protects silent mode and other entry points from memory exhaustion.
        file_size = 0
        if is_physical_file:
            file_size = os.path.getsize(file)  # type: ignore[arg-type]
        elif hasattr(file, "getbuffer"):
            # Handle BytesIO and similar stream-like objects
            file_size = file.getbuffer().nbytes
        elif hasattr(file, "seek") and hasattr(file, "tell"):
            # General stream fallback
            curr = file.tell()
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(curr, os.SEEK_SET)

        if file_size > MAX_IMAGE_SIZE_BYTES:
            logger.error(f"Anura OCR: Image too large ({file_size} bytes)")
            return (
                False,
                "",
                _("Image too large: {size}MB (max {max}MB)").format(
                    size=round(file_size / (1024 * 1024), 1),
                    max=MAX_IMAGE_SIZE_MB,
                ),
            )

        start_time = time.time()

        try:
            extracted, error_message = self._process_image_decode(file, lang, start_time)
        except Exception as e:
            extracted, error_message = self._handle_decode_exception(e)
        finally:
            self._cleanup_temporary_file(file, is_physical_file, remove_source)

        return self._format_decode_result(extracted, error_message)

    def _validate_decode_inputs(self, lang: str) -> tuple[bool, str | None, str | None]:
        """Validate language code for OCR processing."""
        if not lang or not re.match(LANG_CODE_PATTERN, lang):
            logger.error(f"Anura: Invalid language code '{lang}' for OCR")
            return (False, "", _("Invalid language code specified."))
        return (True, None, None)

    def _determine_file_type(self, file: str | Image.Image | object, _remove_source: bool) -> bool:
        """Determine if file is a physical file."""
        return isinstance(file, str) and os.path.exists(file)

    def _process_image_decode(
        self,
        file: str | Image.Image | object,
        lang: str,
        start_time: float,
    ) -> tuple[str | None, str | None]:
        """Process image for QR code detection and OCR."""
        extracted = None
        error_message = None

        # Hardening: check for 0-byte physical files before attempting to open
        if isinstance(file, str) and os.path.exists(file) and os.path.getsize(file) == 0:
            logger.error(f"Anura OCR: Attempted to process 0-byte image file: {file}")
            return None, _("The selected image file is empty.")

        with Image.open(file) as img:
            image_size = img.size
            logger.debug(f"Anura OCR: Processing image size: {image_size[0]}x{image_size[1]}")

            # Try QR/Barcode detection first (Short-circuit)
            extracted = self._try_barcode_detection(img, start_time)

            # If no code found, proceed with OCR
            if extracted is None:
                # Optimization: Pre-convert to "L" (grayscale) once for OCR.
                if img.mode != "L":
                    img = img.convert("L")
                extracted = self._try_ocr_extraction(img, lang, start_time)

        return extracted, error_message

    def _try_barcode_detection(self, img: Image.Image, start_time: float) -> str | None:
        """Try to detect and decode QR codes and Barcodes from image using zxing-cpp."""
        try:
            from anura.utils.barcode_detector import detect_barcodes
            from anura.utils.validators import sanitize_text

            results = detect_barcodes(img)
            if results:
                # For now, if multiple codes are found, we return them joined by newline
                # as NormCap does in some places, or just the first one.
                # To maintain consistency with Anura's previous behavior, we'll join them.
                raw_extracted = "\n".join([res.text for res in results])

                # Security: Sanitize all extracted code content before it hits the UI/clipboard
                extracted = sanitize_text(raw_extracted)

                duration = time.time() - start_time
                logger.info(f"Anura ZXing: Code(s) detected in {duration:.3f}s")
                return extracted
        except Exception as e:
            logger.debug(f"Anura ZXing: Detection failed: {e}")
        return None

    def _try_ocr_extraction(self, img: Image.Image, lang: str, start_time: float) -> str | None:
        """Try to extract text using Tesseract OCR with preprocessing and Magic Transformers."""
        try:
            from pytesseract import Output

            from anura.services.settings import settings
            from anura.utils.transformers.magic_processor import get_magic_processor

            mode = settings.get_string("ocr-preprocessing")

            # Apply image enhancement preprocessing
            preprocessor = get_text_preprocessor()
            if mode != "off":
                enhanced_img = preprocessor.enhance_image(img)
            else:
                enhanced_img = img

            # 1. Extract raw data with layout information (image_to_data)
            # This is the core of the Magics pattern migration.
            ocr_data = pytesseract.image_to_data(
                enhanced_img,
                lang=lang,
                config=get_tesseract_config(lang),
                output_type=Output.DICT
            )

            # 2. Process data through Magic Transformers (Chain of Responsibility)
            # This happens in the worker thread.
            magic_processor = get_magic_processor()
            processed_text = magic_processor.process(ocr_data)

            # 3. Final cleanup based on user settings
            if mode == "full":
                cleaned_text = preprocessor.clean_extracted_text(processed_text)
            elif mode == "image-only":
                cleaned_text = preprocessor._normalize_whitespace(processed_text)
            else:
                cleaned_text = processed_text.strip()

            # 4. Mandatory security sanitization for OCR output
            from anura.utils.validators import sanitize_text

            cleaned_text = sanitize_text(cleaned_text)

            duration = time.time() - start_time
            logger.info(f"Anura OCR: Text extraction and Magics completed in {duration:.3f}s")

            return cleaned_text
        except Exception as e:
            logger.debug(f"Anura OCR: OCR extraction or Magic processing failed: {e}")
            return None

    def _handle_decode_exception(self, e: Exception) -> tuple[str | None, str | None]:
        """Handle exceptions during image decoding."""
        extracted = None
        error_message = None

        if isinstance(e, OSError):
            logger.exception(f"Anura OCR/QR File Error: {e}")
            error_message = _("Failed to read image file.")
        elif isinstance(e, (pytesseract.TesseractError, pytesseract.TesseractNotFoundError)):
            logger.exception(f"Anura OCR Error: Tesseract failed: {e}")
            error_message = _("OCR engine failed to process image.")
        elif isinstance(e, (Image.DecompressionBombError, Image.UnidentifiedImageError)):
            logger.exception(f"Anura OCR/QR Error: {type(e).__name__}: {e}")
            error_message = _("Failed to decode data.")
        elif isinstance(e, (SystemExit, KeyboardInterrupt)):
            # Let system exceptions propagate
            raise
        else:
            logger.exception(f"Anura OCR/QR Error: {type(e).__name__}: {e}")
            error_message = _("Failed to decode data.")

        return extracted, error_message

    def _cleanup_temporary_file(
        self,
        file: str | Image.Image | object,
        is_physical_file: bool,
        remove_source: bool,
    ) -> None:
        """Clean up temporary files if requested."""
        if remove_source and is_physical_file:
            try:
                # Type safe unlink: file is confirmed as string via is_physical_file
                os.unlink(file)  # type: ignore[arg-type]
                logger.debug(f"Anura OCR: Cleaned up temporary file: {file}")
            except (OSError, PermissionError) as e:
                logger.warning(f"Anura OCR: Could not delete {file}: {e}")

    def _format_decode_result(
        self,
        extracted: str | None,
        error_message: str | None,
    ) -> tuple[bool, str | None, str | None]:
        """Format the final decode result."""
        if extracted:
            return (True, extracted, None)
        elif error_message:
            return (False, "", error_message)
        else:
            return (False, "", _("No text found."))

    def decode_image(
        self,
        lang: str,
        file: str | Image.Image | object,
        copy: bool = False,
        remove_source: bool = False,
    ) -> bool:
        """
        Asynchronously decodes the image and emits GObject signals.
        Wraps decode_image_sync() for use with GUI mode.
        Supports file paths (str) and binary streams (BytesIO).
        """
        # Validate language code before processing
        if not lang or not re.match(LANG_CODE_PATTERN, lang):
            logger.error(f"Anura: Invalid language code '{lang}' for OCR")

            def _on_invalid_lang_error_idle() -> bool:
                try:
                    self.emit("error", _("Invalid language code specified."))
                except Exception:
                    logger.exception("Anura: Failed to emit invalid language code error")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_invalid_lang_error_idle, priority=GLib.PRIORITY_DEFAULT)
            return False

        success, extracted, error_message = self.decode_image_sync(lang, file, remove_source)

        if success:

            def _on_decoded_idle(text: str, cp: bool) -> bool:
                try:
                    self.emit("decoded", text, cp)
                except Exception:
                    logger.exception("Anura: Failed to emit decoded signal")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_decoded_idle, extracted, copy, priority=GLib.PRIORITY_DEFAULT)
        else:

            def _on_decode_error_idle(msg: str | None) -> bool:
                try:
                    self.emit("error", msg)
                except Exception:
                    logger.exception("Anura: Failed to emit decode error")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_decode_error_idle, error_message, priority=GLib.PRIORITY_DEFAULT)

        return False

    def do_destroy(self) -> None:
        """Clean up cancellable to prevent leaks."""
        # Clean up cancellable
        with self._cancellable_lock:
            if self.cancelable is not None:
                if not self.cancelable.is_cancelled():
                    self.cancelable.cancel()
                self.cancelable = None
