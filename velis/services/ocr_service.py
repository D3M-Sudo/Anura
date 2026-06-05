# velis/services/ocr_service.py
from loguru import logger
from PIL import Image
import pytesseract
import zxingcpp

from velis.utils.singleton import get_instance


class OcrService:
    def __init__(self):
        pass

    def extract_text(self, image_path, lang='eng'):
        try:
            with Image.open(image_path) as img:
                # 1. Try barcode detection first
                barcodes = zxingcpp.read_barcodes(img)
                if barcodes:
                    return "\n".join([b.text for b in barcodes])

                # 2. Fallback to Tesseract OCR
                if img.mode != 'L':
                    img = img.convert('L')
                text = pytesseract.image_to_string(img, lang=lang)
                return text.strip()
        except Exception as e:
            logger.error(f"OCR/Barcode Error: {e}")
            return ""

def get_ocr_service():
    return get_instance(OcrService)
