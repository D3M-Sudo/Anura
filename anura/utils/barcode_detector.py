# barcode_detector.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License
"""
Barcode and QR Code detection using zxing-cpp.
Provides high-performance and robust decoding for various code formats.
"""

from typing import NamedTuple

from loguru import logger
from PIL import Image
import zxingcpp


class BarcodeResult(NamedTuple):
    """Result of a barcode/QR code detection."""

    text: str
    format: str


def detect_barcodes(image: Image.Image) -> list[BarcodeResult]:
    """
    Detect and decode barcodes and QR codes from a PIL Image.

    Args:
        image: PIL Image object.

    Returns:
        List of BarcodeResult named tuples containing decoded text and format.
    """
    try:
        # zxingcpp can read directly from PIL images if they are in a supported format.
        # It's generally better to pass it a numpy array or a memoryview.
        # Pillow's Image.tobytes() or simply passing the image might work depending on version.

        # Ensure image is in a mode zxing-cpp likes (RGB or Grayscale)
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        results = zxingcpp.read_barcodes(image)

        barcode_results = []
        for res in results:
            if res.valid and res.text:
                barcode_results.append(BarcodeResult(text=res.text, format=str(res.format)))

        if barcode_results:
            logger.info(f"Anura ZXing: Detected {len(barcode_results)} codes")

        return barcode_results
    except (ImportError, RuntimeError, AttributeError, TypeError) as e:
        logger.debug(f"Anura ZXing: Detection failed or zxing-cpp not available: {e}")
        return []
