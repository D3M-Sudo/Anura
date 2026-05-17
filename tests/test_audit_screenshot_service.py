import os
import pytest
from unittest.mock import MagicMock, patch
from PIL import Image
import io
from anura.services.screenshot_service import ScreenshotService

class TestAuditScreenshotService:
    @pytest.fixture
    def service(self):
        with patch('gi.repository.Xdp.Portal'), \
             patch('anura.services.screenshot_service._configure_tesseract_path'):
            return ScreenshotService()

    def test_decode_image_sync_0_byte_file(self, service, tmp_path):
        empty_file = tmp_path / "empty.png"
        empty_file.write_bytes(b"")

        success, text, error = service.decode_image_sync("eng", str(empty_file))
        assert success is False
        assert text == ""
        assert "empty" in error.lower()

    @patch('pytesseract.image_to_string')
    @patch('anura.services.screenshot_service.decode')
    def test_decode_image_sync_qr_priority(self, mock_decode, mock_ocr, service):
        mock_qr = MagicMock()
        mock_qr.data = b"https://qr-code.com"
        mock_decode.return_value = [mock_qr]

        img_byte_arr = io.BytesIO()
        Image.new('RGB', (100, 100)).save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        success, text, error = service.decode_image_sync("eng", img_byte_arr)

        assert success is True
        assert text == "https://qr-code.com"
        mock_ocr.assert_not_called()

    @patch('pytesseract.image_to_string')
    @patch('anura.services.screenshot_service.decode')
    def test_decode_image_sync_ocr_fallback(self, mock_decode, mock_ocr, service):
        mock_decode.return_value = []
        mock_ocr.return_value = "Extracted Text"

        img_byte_arr = io.BytesIO()
        Image.new('RGB', (100, 100)).save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)

        success, text, error = service.decode_image_sync("eng", img_byte_arr)

        assert success is True
        assert text == "Extracted Text"
        mock_decode.assert_called_once()
        mock_ocr.assert_called_once()

    def test_validate_decode_inputs_invalid(self, service):
        success, text, error = service.decode_image_sync("invalid;lang", "somefile.png")
        assert success is False
        assert "Invalid language code" in error
