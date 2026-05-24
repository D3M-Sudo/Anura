# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
import importlib
import os
import shutil

from loguru import logger


@dataclass(frozen=True, slots=True)
class ApplicationContext:
    """Immutable representation of application capabilities based on environment audit."""
    has_ocr: bool
    has_barcode: bool
    has_tts: bool
    has_libnotify: bool
    has_scrot: bool
    is_flatpak: bool

    @classmethod
    def perform_audit(cls) -> "ApplicationContext":
        """Execute a boot-time audit of system dependencies and binaries."""
        logger.info("Anura: Performing boot-time capability audit...")

        # 1. Environment Check
        is_flatpak = os.path.exists("/.flatpak-info") or "FLATPAK_ID" in os.environ

        # 2. OCR Audit (Tesseract binary + wrapper)
        has_pytesseract = importlib.util.find_spec("pytesseract") is not None
        # In Flatpak, we expect it at /app/bin/tesseract
        tess_bin = "/app/bin/tesseract" if is_flatpak else "tesseract"
        has_tesseract_bin = shutil.which(tess_bin) is not None
        has_ocr = has_pytesseract and has_tesseract_bin

        # 3. Barcode Audit (zxing-cpp)
        has_barcode = importlib.util.find_spec("zxingcpp") is not None

        # 4. TTS Audit (gtts + gst)
        has_gtts = importlib.util.find_spec("gtts") is not None
        has_gst = importlib.util.find_spec("gi.repository.Gst") is not None
        has_tts = has_gtts and has_gst

        # 5. UI Extras (libnotify)
        has_libnotify = importlib.util.find_spec("gi.repository.Notify") is not None

        # 6. Fallback Audit (scrot)
        has_scrot = shutil.which("scrot") is not None

        ctx = cls(
            has_ocr=has_ocr,
            has_barcode=has_barcode,
            has_tts=has_tts,
            has_libnotify=has_libnotify,
            has_scrot=has_scrot,
            is_flatpak=is_flatpak
        )

        logger.info(f"Anura Capabilities: OCR={ctx.has_ocr}, Barcode={ctx.has_barcode}, "
                    f"TTS={ctx.has_tts}, Scrot={ctx.has_scrot}, Flatpak={ctx.is_flatpak}")
        return ctx

# Global context instance (populated at boot)
_app_context: ApplicationContext | None = None

def get_app_context() -> ApplicationContext:
    """Get the global application context. Performs audit on first call if not initialized."""
    global _app_context
    if _app_context is None:
        _app_context = ApplicationContext.perform_audit()
    return _app_context
