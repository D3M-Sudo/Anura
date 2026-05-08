# screenshot_service.py
#
# Copyright 2022-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gettext import gettext as _
import os
import re
import threading
import time
from typing import ClassVar
from urllib.request import url2pathname

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
from pyzbar.pyzbar import decode  # noqa: E402

from anura.config import LANG_CODE_PATTERN, get_tesseract_config  # noqa: E402


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


class ScreenshotService(GObject.GObject):
    """
    Service responsible for capturing screenshots via XDG Portals
    and processing them for OCR or QR code decoding.
    """

    __gtype_name__ = "ScreenshotService"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "error": (GObject.SIGNAL_RUN_LAST, None, (str,)),
        "decoded": (GObject.SIGNAL_RUN_FIRST, None, (str, bool)),
    }

    __slots__ = ("_cancellable_lock", "cancelable", "portal")

    def __init__(self) -> None:
        GObject.GObject.__init__(self)
        self._cancellable_lock = threading.Lock()
        with self._cancellable_lock:
            self.cancelable: Gio.Cancellable = Gio.Cancellable.new()
        self.portal = Xdp.Portal()

        # Configure Tesseract path for Flatpak environment
        _configure_tesseract_path()

    def capture(self, lang: str, copy: bool = False) -> None:
        """Requests a screenshot from the system portal."""
        with self._cancellable_lock:
            # If previous request was cancelled, create fresh cancellable
            if self.cancelable.is_cancelled():
                self.cancelable = Gio.Cancellable.new()
            cancellable = self.cancelable
        # Release lock before async D-Bus call to prevent deadlock
        self.portal.take_screenshot(
            None,
            Xdp.ScreenshotFlags.INTERACTIVE,
            cancellable,
            self.take_screenshot_finish,
            [lang, copy],
        )

    def take_screenshot_finish(self, source_object: object, res: Gio.Task, user_data: tuple) -> None:
        """Callback triggered when portal finishes screenshot request."""
        if res.had_error():
            logger.error("Anura Screenshot: Portal failed to provide a screenshot.")
            # Try to get more detailed error information
            try:
                # Gio.Task doesn't expose propagate_error() in Python bindings
                # Check if error details are available through get_error()
                error = res.get_error()
                if error:
                    logger.error(f"Anura Screenshot: Portal error details: {error.message}")
                else:
                    logger.error("Anura Screenshot: Portal failed without specific error details")
            except GLib.Error as e:
                logger.warning(
                    f"Anura Screenshot: Failed to get Portal error details (Flatpak/D-Bus): {e}",
                )
            except Exception as e:
                logger.error(f"Anura Screenshot: Unexpected error handling Portal error: {e}")
            return GLib.idle_add(self.emit, "error", _("Can't take a screenshot."))

        lang, copy = user_data
        try:
            uri = self.portal.take_screenshot_finish(res)
        except Exception as e:
            logger.error(f"Anura Screenshot: Exception getting screenshot URI: {e}")
            return GLib.idle_add(self.emit, "error", _("Can't take a screenshot."))

        if not uri:
            logger.warning("Anura Screenshot: Portal returned empty URI.")
            return GLib.idle_add(self.emit, "error", _("Can't take a screenshot."))

        if uri.startswith("file://") and len(uri) > len("file://"):
            filename = url2pathname(uri[len("file://") :])
        else:
            filename = GLib.Uri.unescape_string(uri)

        self.decode_image(lang, filename, copy, True)

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

        with Image.open(file) as img:
            image_size = img.size
            logger.debug(f"Anura OCR: Processing image size: {image_size[0]}x{image_size[1]}")

            # Try QR code detection first
            extracted = self._try_qr_detection(img, start_time)

            # If no QR code found, try OCR
            if extracted is None:
                extracted = self._try_ocr_extraction(img, lang, start_time)

        return extracted, error_message

    def _try_qr_detection(self, img: Image.Image, start_time: float) -> str | None:
        """Try to detect and decode QR codes from image."""
        try:
            qr_data = decode(img)
            if len(qr_data) > 0:
                extracted = qr_data[0].data.decode("utf-8")
                duration = time.time() - start_time
                logger.info(f"Anura OCR: QR code detected in {duration:.3f}s")
                return extracted
        except Exception as e:
            logger.debug(f"Anura OCR: QR detection failed: {e}")
        return None

    def _try_ocr_extraction(self, img: Image.Image, lang: str, start_time: float) -> str | None:
        """Try to extract text using Tesseract OCR."""
        try:
            text = pytesseract.image_to_string(img, lang=lang, config=get_tesseract_config(lang))
            extracted = text.strip()
            duration = time.time() - start_time
            logger.info(f"Anura OCR: Text extraction completed in {duration:.3f}s")
            return extracted
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
                os.unlink(file)
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
    ) -> None:
        """
        Asynchronously decodes the image and emits GObject signals.
        Wraps decode_image_sync() for use with GUI mode.
        Supports file paths (str) and binary streams (BytesIO).
        """
        # Validate language code before processing
        if not lang or not re.match(LANG_CODE_PATTERN, lang):
            logger.error(f"Anura: Invalid language code '{lang}' for OCR")
            GLib.idle_add(self.emit, "error", _("Invalid language code specified."))
            return

        success, extracted, error_message = self.decode_image_sync(lang, file, remove_source)

        if success:
            GLib.idle_add(self.emit, "decoded", extracted, copy)
        else:
            GLib.idle_add(self.emit, "error", error_message)

    def do_destroy(self) -> None:
        """Clean up cancellable to prevent leaks."""
        with self._cancellable_lock:
            if not self.cancelable.is_cancelled():
                self.cancelable.cancel()
            self.cancelable = Gio.Cancellable.new()
