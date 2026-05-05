# test_screenshot_service.py
#
# Unit tests for ScreenshotService
# Tests image validation, OCR processing, and QR decoding logic

import os
from unittest.mock import Mock, patch
from PIL import Image
import pytesseract

from anura.services.screenshot_service import ScreenshotService


class TestScreenshotService:
    """Test suite for ScreenshotService core functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ScreenshotService()
        # Mock the portal to avoid XDP dependency
        self.service.portal = Mock()

    def test_init(self):
        """Test service initialization."""
        assert self.service.cancelable is not None
        assert self.service._cancelable_handler_id is not None
        assert self.service.portal is not None

    def test_decode_image_sync_ocr_success(self, tmp_path):
        """Test successful OCR text extraction."""
        # Create a test image with text
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        # Mock pytesseract to return known text
        with patch("pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = "Sample extracted text"

            success, result, error = self.service.decode_image_sync("eng", str(test_file), False)

            assert success is True
            assert result == "Sample extracted text"
            assert error is None
            mock_ocr.assert_called_once()

    def test_decode_image_sync_qr_success(self, tmp_path):
        """Test successful QR code decoding."""
        # Create a test image
        img = Image.new("RGB", (100, 100), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        # Mock pyzbar decode to return QR data
        with patch("anura.services.screenshot_service.decode") as mock_decode:
            mock_qr = Mock()
            mock_qr.data = b"https://example.com"
            mock_qr.type = "QRCODE"
            mock_decode.return_value = [mock_qr]

            success, result, error = self.service.decode_image_sync("eng", str(test_file), False)

            assert success is True
            assert result == "https://example.com"
            assert error is None

    def test_decode_image_sync_invalid_language(self, tmp_path):
        """Test handling of invalid language codes."""
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        with patch("pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = ""

            success, result, error = self.service.decode_image_sync("invalid_lang", str(test_file), False)

            assert success is False
            assert result == ""
            assert "Invalid language code" in error

    def test_decode_image_sync_file_not_found(self):
        """Test handling of non-existent image files."""
        success, result, error = self.service.decode_image_sync("eng", "/nonexistent/file.png", False)

        assert success is False
        assert result == ""
        assert "Failed to read image file" in error

    def test_decode_image_sync_corrupted_image(self, tmp_path):
        """Test handling of corrupted image files."""
        # Create a file with invalid image data
        corrupted_file = tmp_path / "corrupted.png"
        corrupted_file.write_bytes(b"not an image")

        success, result, error = self.service.decode_image_sync("eng", str(corrupted_file), False)

        assert success is False
        assert result == ""
        assert "Failed to decode data" in error

    def test_decode_image_sync_tesseract_error(self, tmp_path):
        """Test handling of Tesseract OCR errors."""
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        with patch("pytesseract.image_to_string") as mock_ocr:
            mock_ocr.side_effect = pytesseract.TesseractError("Test error")

            success, result, error = self.service.decode_image_sync("eng", str(test_file), False)

            assert success is False
            assert result == ""
            assert "OCR engine failed to process image" in error

    def test_decode_image_sync_cleanup_temp_file(self, tmp_path):
        """Test that temporary files are cleaned up when requested."""
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        with patch("pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = "test text"

            success, result, error = self.service.decode_image_sync(
                "eng",
                str(test_file),
                True,  # remove_source=True
            )

            assert success is True
            # File should still exist since it's not a portal temp file
            assert test_file.exists()

    def test_capture_cancelled(self):
        """Test screenshot cancellation handling."""
        mock_cancellable = Mock()

        with patch("anura.services.screenshot_service.GLib") as mock_glib:
            self.service.capture_cancelled(mock_cancellable)

            mock_glib.idle_add.assert_called_once()
            args = mock_glib.idle_add.call_args[0]
            assert args[0] == self.service.emit
            assert args[1] == "error"

    def test_decode_image_with_portal_file(self, tmp_path):
        """Test decoding with portal-generated temporary files."""
        # Create a test image
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        with patch("pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = "portal text"

            # Simulate portal file path
            portal_file = f"/tmp/.portal-{os.getpid()}-test.png"
            with patch("os.path.exists", return_value=True):
                with patch("os.remove") as mock_remove:
                    success, result, error = self.service.decode_image_sync(
                        "eng",
                        portal_file,
                        True,  # remove_source=True
                    )

                    assert success is True
                    assert result == "portal text"
                    # Portal temp file should be removed
                    mock_remove.assert_called_once_with(portal_file)

    def test_decode_image_empty_result(self, tmp_path):
        """Test handling of empty OCR/QR results."""
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        with patch("pytesseract.image_to_string") as mock_ocr:
            mock_ocr.return_value = ""  # Empty result

            success, result, error = self.service.decode_image_sync("eng", str(test_file), False)

            assert success is True
            assert result == ""
            assert error is None
