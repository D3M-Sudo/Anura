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

from gi.repository import Gio, GLib, GObject, Xdp
from loguru import logger
from PIL import Image
import pytesseract
from pyzbar.pyzbar import decode

from anura.config import LANG_CODE_PATTERN, get_tesseract_config


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
        """Callback triggered when the portal finishes the screenshot request."""
        if res.had_error():
            logger.error("Anura Screenshot: Portal failed to provide a screenshot.")
            return GLib.idle_add(self.emit, "error", _("Can't take a screenshot."))

        lang, copy = user_data
        uri = self.portal.take_screenshot_finish(res)

        if not uri:
            logger.warning("Anura Screenshot: Portal returned empty URI.")
            return GLib.idle_add(self.emit, "error", _("Can't take a screenshot."))

        if uri.startswith("file://"):
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
        # Security: Validate language code before processing (same as decode_image)
        if not lang or not re.match(LANG_CODE_PATTERN, lang):
            logger.error(f"Anura: Invalid language code '{lang}' for OCR")
            return (False, None, _("Invalid language code specified."))

        # Rigor: Ensure source removal only for valid local file paths
        is_physical_file = isinstance(file, str) and os.path.exists(file)
        if not is_physical_file:
            remove_source = False

        logger.debug(f"Anura OCR: Starting OCR task with language: {lang}")
        start_time = time.time()
        extracted = None
        error_message = None
        image_size = None

        try:
            # Image.open is polymorphic: handles both paths and byte streams
            with Image.open(file) as img:
                image_size = img.size  # (width, height)
                logger.debug(f"Anura OCR: Processing image size: {image_size[0]}x{image_size[1]}")

                # Step 1: QR Code detection
                qr_data = decode(img)

                if len(qr_data) > 0:
                    extracted = qr_data[0].data.decode("utf-8")
                    duration = time.time() - start_time
                    logger.info(f"Anura OCR: QR code detected in {duration:.3f}s")

                # Step 2: Tesseract OCR
                else:
                    text = pytesseract.image_to_string(img, lang=lang, config=get_tesseract_config(lang))
                    extracted = text.strip()
                    duration = time.time() - start_time
                    logger.info(f"Anura OCR: Text extraction completed in {duration:.3f}s")

        except OSError as e:
            logger.exception(f"Anura OCR/QR File Error: {e}")
            error_message = _("Failed to read image file.")
        except (pytesseract.TesseractError, pytesseract.TesseractNotFoundError) as e:
            logger.exception(f"Anura OCR Error: Tesseract failed: {e}")
            error_message = _("OCR engine failed to process image.")
        except (Image.DecompressionBombError, Image.UnidentifiedImageError, Exception) as e:
            # Catch specific image/QR decoding errors (PIL, zbar) but NOT system exceptions
            # KeyboardInterrupt and SystemExit will propagate correctly
            if isinstance(e, (SystemExit, KeyboardInterrupt)):
                raise
            logger.exception(f"Anura OCR/QR Error: {type(e).__name__}: {e}")
            error_message = _("Failed to decode data.")

        finally:
            # Cleanup: Delete temporary portal files if requested
            if remove_source and is_physical_file:
                try:
                    os.unlink(file)
                    logger.debug(f"Anura OCR: Cleaned up temporary file: {file}")
                except (OSError, PermissionError) as e:
                    logger.warning(f"Anura OCR: Could not delete {file}: {e}")

        if extracted:
            return (True, extracted, None)
        elif error_message:
            return (False, None, error_message)
        else:
            return (False, None, _("No text found."))

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
