# velis/core/boot.py
import shutil

from loguru import logger

from velis.utils.singleton import get_instance


class CapabilityAudit:
    def __init__(self):
        self.has_tesseract = shutil.which("tesseract") is not None
        self.has_scrot = shutil.which("scrot") is not None

        logger.info(f"Capability Audit: Tesseract={self.has_tesseract}, Scrot={self.has_scrot}")

def get_capability_audit():
    return get_instance(CapabilityAudit)
