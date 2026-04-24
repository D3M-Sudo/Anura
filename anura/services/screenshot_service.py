# screenshot_service.py
#
# Copyright 2022-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import os
from gettext import gettext as _
from urllib.request import url2pathname
from gi.repository import GObject, Gio, GLib, Xdp
from loguru import logger

from anura.config import tessdata_config

try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
from pyzbar.pyzbar import decode


class ScreenshotService(GObject.GObject):
    """
    Service responsible for capturing screenshots via XDG Portals
    and processing them for OCR or QR code decoding.
    """

    __gtype_name__ = "ScreenshotService"

    __gsignals__ = {
        "error": (GObject.SIGNAL_RUN_LAST, None, (str,)),
        "decoded": (GObject.SIGNAL_RUN_FIRST, None, (str, bool)),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        self.cancelable: Gio.Cancellable = Gio.Cancellable.new()
        self.cancelable.connect(self.capture_cancelled)
        self.portal = Xdp.Portal()

    def capture(self, lang: str, copy: bool = False) -> None:
        """Requests a screenshot from the system portal."""
        self.portal.take_screenshot(
            None,
            Xdp.ScreenshotFlags.INTERACTIVE,
            self.cancelable,
            self.take_screenshot_finish,
            [lang, copy],
        )

    def take_screenshot_finish(self, source_object, res: Gio.Task, user_data):
        """Callback triggered when the portal finishes the screenshot request."""
        if res.had_error():
            logger.error("Anura Screenshot: Portal failed to provide a screenshot.")
            return self.emit("error", _("Can't take a screenshot."))

        lang, copy = user_data
        uri = self.portal.take_screenshot_finish(res)
        
        if uri.startswith("file://"):
            filename = url2pathname(uri[7:])
        else:
            filename = GLib.Uri.unescape_string(uri)
            
        self.decode_image(lang, filename, copy, True)

    def decode_image(self,
                     lang: str,
                     file: str | Image.Image | object,
                     copy: bool = False,
                     remove_source: bool = False,
                     ) -> None:
        """
        Decodes the image to find QR codes or extracts text using Tesseract OCR.
        Supports file paths (str) and binary streams (BytesIO).
        """
        # Rigor: Ensure source removal only for valid local file paths
        is_physical_file = isinstance(file, str) and os.path.exists(file)
        if not is_physical_file:
            remove_source = False

        logger.debug(f"Anura OCR: Decoding image with language: {lang}")
        extracted = None

        try:
            # Image.open is polymorphic: handles both paths and byte streams
            with Image.open(file) as img:
                # Step 1: QR Code detection
                qr_data = decode(img)
                
                if len(qr_data) > 0:
                    extracted = qr_data[0].data.decode("utf-8")
                    logger.info("Anura OCR: QR code detected.")

                # Step 2: Tesseract OCR
                else:
                    text = pytesseract.image_to_string(
                        img, lang=lang, config=tessdata_config
                    )
                    extracted = text.strip()

        except Exception as e:
            logger.error(f"Anura OCR/QR Error: {e}")
            return self.emit("error", _("Failed to decode data."))

        finally:
            # Cleanup: Delete temporary portal files if requested
            if remove_source and is_physical_file:
                try:
                    os.unlink(file)
                    logger.debug(f"Anura OCR: Cleaned up temporary file: {file}")
                except Exception as e:
                    logger.warning(f"Anura OCR: Could not delete {file}: {e}")

        if extracted:
            self.emit("decoded", extracted, copy)
        else:
            self.emit("error", _("No text found."))

    def capture_cancelled(self, cancellable: Gio.Cancellable) -> None:
        """Handles the cancellation of the screenshot request."""
        logger.info("Anura Screenshot: Capture cancelled by user.")
        self.emit("error", _("Cancelled"))