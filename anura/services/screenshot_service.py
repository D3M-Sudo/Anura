# screenshot_service.py
#
# Copyright 2022-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _
import os
from pathlib import Path
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
from pyzbar.pyzbar import ZBarSymbol, decode  # noqa: E402

from anura.config import LANG_CODE_PATTERN, get_tesseract_config  # noqa: E402
from anura.services.host_screenshot_fallback import (  # noqa: E402
    build_detection_argv,
    build_screenshot_argv,
    find_tool_by_name,
    parse_detection_output,
)
from anura.utils.portal_advice import detect_portal_advice  # noqa: E402
from anura.utils.text_preprocessor import get_text_preprocessor  # noqa: E402


def _is_flatpak_environment() -> bool:
    """Detect if running in Flatpak sandbox."""
    return os.path.exists("/.flatpak-info")


def _configure_tesseract_path() -> None:
    """Configure Tesseract command path for Flatpak environment."""
    if _is_flatpak_environment() and os.path.exists("/app/bin/tesseract"):
        # Force Tesseract to use Flatpak path
        os.environ["TESSERACT_CMD"] = "/app/bin/tesseract"
        logger.info("Anura OCR: Using Flatpak Tesseract at /app/bin/tesseract")
    else:
        # Use system Tesseract from PATH
        os.environ.pop("TESSERACT_CMD", None)
        logger.debug("Anura OCR: Using system Tesseract from PATH")

    # Final validation: check if tesseract binary is actually reachable
    tess_bin = os.environ.get("TESSERACT_CMD", "tesseract")
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

    __slots__ = (
        "_cancellable_lock",
        "_env_diagnostics_logged",
        "_is_capturing",
        "cancelable",
        "portal",
    )

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

        from anura.gobject_worker import GObjectWorker

        GObjectWorker.call(self.decode_image, (lang, filename, copy, True))

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
        """Attempt to capture a screenshot via a host-side CLI tool.

        Triggered after ``xdg-desktop-portal`` returns the libportal generic
        ``Screenshot failed`` (no backend exposes the Screenshot interface
        for the active session). Tries ``flatpak-spawn --host`` to invoke
        a host-installed screenshot tool (gnome-screenshot, xfce4-screenshooter,
        scrot, …). On success the captured PNG is fed into the same OCR
        pipeline as portal screenshots; on failure ``_emit_portal_failure``
        surfaces the original error.

        Only runs in a Flatpak sandbox — outside Flatpak there is no
        ``flatpak-spawn`` and the portal failure is genuinely terminal.
        """
        if not _is_flatpak_environment():
            self._is_capturing = False
            self._emit_portal_failure()
            return
        try:
            argv = build_detection_argv()
            proc = Gio.Subprocess.new(
                argv,
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE,
            )
        except GLib.Error as e:
            self._is_capturing = False
            logger.warning(f"Anura Screenshot: cannot spawn flatpak-spawn for host fallback: {e.message}")
            self._emit_portal_failure()
            return
        proc.communicate_utf8_async(
            None,
            self.cancelable,
            self._on_host_detection_complete,
            (lang, copy),
        )

    def _on_host_detection_complete(
        self,
        proc: Gio.Subprocess,
        res: Gio.AsyncResult,
        user_data: tuple,
    ) -> None:
        """Handle the result of the host-tool detection probe.

        On success, picks a tool from the probe's stdout and proceeds to
        the capture step. On failure, falls back to the original portal
        error UI.
        """
        lang, copy = user_data
        try:
            success, stdout, _stderr = proc.communicate_utf8_finish(res)
        except GLib.Error as e:
            self._is_capturing = False
            logger.debug(f"Anura Screenshot: host fallback detection failed: {e.message}")
            self._emit_portal_failure()
            return

        exit_status = proc.get_exit_status() if proc.get_if_exited() else -1
        if not success or exit_status != 0:
            self._is_capturing = False
            logger.debug(
                f"Anura Screenshot: no host-side screenshot tool found (exit={exit_status}). "
                "Surface the original portal error.",
            )
            self._emit_portal_failure()
            return

        tool_name = parse_detection_output(stdout or "")
        if tool_name is None:
            self._is_capturing = False
            self._emit_portal_failure()
            return
        tool = find_tool_by_name(tool_name)
        if tool is None:
            self._is_capturing = False
            self._emit_portal_failure()
            return

        # Pick a host-addressable temp path inside ~/Anura screenshots.
        # This directory is created on the host via flatpak-spawn --host.
        output_dir = Path.home() / "Anura screenshots"
        output_path = str(output_dir / f"anura-shot-{uuid.uuid4().hex}.png")

        logger.info(f"Anura Screenshot: portal failed, falling back to host '{tool_name}'.")
        # Log environment for debugging display issues
        env_vars = ["DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE", "XDG_CURRENT_DESKTOP"]
        env_snapshot = ", ".join(f"{k}={os.environ.get(k) or '<unset>'}" for k in env_vars)
        logger.debug(f"Anura Screenshot: host fallback env: {env_snapshot}")

        # Create the directory on the host asynchronously to avoid blocking main thread
        mkdir_argv = ["flatpak-spawn", "--host", "mkdir", "-p", str(output_dir)]
        try:
            mkdir_proc = Gio.Subprocess.new(mkdir_argv, Gio.SubprocessFlags.STDERR_SILENCE)
            mkdir_proc.wait_async(
                self.cancelable,
                self._on_mkdir_complete,
                (lang, copy, output_path, tool),
            )
        except GLib.Error as e:
            self._is_capturing = False
            logger.warning(f"Anura Screenshot: cannot spawn host mkdir: {e.message}")
            self._emit_portal_failure()
            return

    def _on_mkdir_complete(
        self,
        proc: Gio.Subprocess,
        res: Gio.AsyncResult,
        user_data: tuple,
    ) -> None:
        """Handle mkdir completion and proceed with screenshot capture."""
        lang, copy, output_path, tool = user_data
        try:
            proc.wait_finish(res)
        except GLib.Error as e:
            self._is_capturing = False
            logger.warning(f"Anura Screenshot: mkdir failed: {e.message}")
            self._emit_portal_failure()
            return

        exit_status = proc.get_exit_status() if proc.get_if_exited() else -1
        if exit_status != 0:
            self._is_capturing = False
            logger.warning(f"Anura Screenshot: mkdir failed with exit code {exit_status}")
            self._emit_portal_failure()
            return

        # Now proceed with screenshot capture
        try:
            argv = build_screenshot_argv(tool, output_path)
            logger.debug(f"Anura Screenshot: host fallback argv: {argv}")
            capture_proc = Gio.Subprocess.new(
                argv,
                Gio.SubprocessFlags.STDERR_PIPE | Gio.SubprocessFlags.STDOUT_PIPE,
            )
        except GLib.Error as e:
            self._is_capturing = False
            logger.warning(f"Anura Screenshot: cannot spawn host screenshot tool: {e.message}")
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

            # Optimization: Pre-convert to "L" (grayscale) once.
            # Benchmarks show that pyzbar's internal conversion is ~2x slower than Pillow's
            # on 4K images. Additionally, OCR preprocessing starts with grayscale conversion.
            if img.mode != "L":
                img = img.convert("L")

            # Try QR code detection first
            extracted = self._try_qr_detection(img, start_time)

            # If no QR code found, try OCR
            if extracted is None:
                extracted = self._try_ocr_extraction(img, lang, start_time)

        return extracted, error_message

    def _try_qr_detection(self, img: Image.Image, start_time: float) -> str | None:
        """Try to detect and decode QR codes from image."""
        try:
            # Optimization: Fast path for high-res images.
            # Attempt QR detection on a downscaled version first (~1024px).
            # This is significantly faster for 4K+ images and usually sufficient for QR.
            width, height = img.size
            max_side = max(width, height)
            if max_side > 1024:
                scale = 1024 / max_side
                small_img = img.resize(
                    (int(width * scale), int(height * scale)),
                    Image.Resampling.BILINEAR
                )
                qr_data = decode(small_img, symbols=[ZBarSymbol.QRCODE])
                if len(qr_data) > 0:
                    extracted = qr_data[0].data.decode("utf-8").strip()
                    duration = time.time() - start_time
                    logger.info(f"Anura OCR: QR code detected (fast path) in {duration:.3f}s")
                    return extracted

            # Optimization: Restrict decoding to QR codes only.
            # By default, pyzbar tries to decode all supported barcode formats
            # (EAN13, Code128, etc.), which adds unnecessary overhead.
            qr_data = decode(img, symbols=[ZBarSymbol.QRCODE])
            if len(qr_data) > 0:
                # Security/Robustness: Strip leading/trailing whitespace and control characters
                extracted = qr_data[0].data.decode("utf-8").strip()
                duration = time.time() - start_time
                logger.info(f"Anura OCR: QR code detected in {duration:.3f}s")
                return extracted
        except Exception as e:
            logger.debug(f"Anura OCR: QR detection failed: {e}")
        return None

    def _try_ocr_extraction(self, img: Image.Image, lang: str, start_time: float) -> str | None:
        """Try to extract text using Tesseract OCR with preprocessing."""
        try:
            # Apply image enhancement preprocessing
            preprocessor = get_text_preprocessor()
            enhanced_img = preprocessor.enhance_image(img)

            # Extract text with Tesseract
            raw_text = pytesseract.image_to_string(enhanced_img, lang=lang, config=get_tesseract_config(lang))

            # Clean and normalize the extracted text
            cleaned_text = preprocessor.clean_extracted_text(raw_text.strip())

            duration = time.time() - start_time
            logger.info(f"Anura OCR: Text extraction completed in {duration:.3f}s")

            # Log if preprocessing improved results
            if cleaned_text != raw_text.strip():
                logger.debug("Anura OCR: Text preprocessing improved OCR results")

            return cleaned_text
        except Exception as e:
            logger.debug(f"Anura OCR: OCR extraction failed: {e}")
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
