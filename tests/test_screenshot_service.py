# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

import os
from unittest.mock import Mock, patch

from PIL import Image
import pytesseract

from anura.services.screenshot_service import ScreenshotService


@pytest.mark.gtk
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
        assert self.service.portal is not None

    def test_decode_image_sync_ocr_success(self, tmp_path):
        """Test successful OCR text extraction."""
        # Create a test image with text
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        # Mock pytesseract raw data output
        with patch("pytesseract.image_to_data") as mock_ocr_data:
            mock_ocr_data.return_value = {
                "level": [5],
                "page_num": [1],
                "block_num": [1],
                "par_num": [1],
                "line_num": [1],
                "word_num": [1],
                "left": [0],
                "top": [0],
                "width": [100],
                "height": [30],
                "conf": [95],
                "text": ["Sample extracted text"]
            }

            success, result, error = self.service.decode_image_sync("eng", str(test_file), False)

            assert success is True
            assert "Sample extracted text" in result
            assert error is None
            mock_ocr_data.assert_called_once()

    def test_decode_image_sync_qr_success(self, tmp_path):
        """Test successful QR code decoding."""
        # Create a test image
        img = Image.new("RGB", (100, 100), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        # Mock zxing-cpp barcode detection
        with patch("anura.utils.barcode_detector.detect_barcodes") as mock_detect:
            from anura.utils.barcode_detector import BarcodeResult
            mock_detect.return_value = [BarcodeResult(text="https://example.com", format="QRCode")]

            success, result, error = self.service.decode_image_sync("eng", str(test_file), False)

            assert success is True
            assert result == "https://example.com"
            assert error is None

    def test_decode_image_sync_invalid_language(self, tmp_path):
        """Test handling of invalid language codes."""
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        success, result, error = self.service.decode_image_sync("invalid@lang", str(test_file), False)

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

        with patch("pytesseract.image_to_data") as mock_ocr:
            mock_ocr.side_effect = pytesseract.TesseractError("Test error", "Test error")

            success, result, error = self.service.decode_image_sync("eng", str(test_file), False)

            assert success is False
            assert result == ""
            assert "OCR engine failed to process image" in error

    def test_decode_image_sync_cleanup_temp_file(self, tmp_path):
        """Test that temporary files are cleaned up when requested."""
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        # Mock successful OCR
        with patch("pytesseract.image_to_data") as mock_ocr:
            mock_ocr.return_value = {"text": ["test"], "conf": [90], "level": [5]}

            success, _, _ = self.service.decode_image_sync(
                "eng",
                str(test_file),
                remove_source=True
            )

            assert success is True
            # Verification: physical file is removed when remove_source=True
            assert not test_file.exists()

    def test_decode_image_with_portal_file(self, tmp_path):
        """Test decoding with portal-generated temporary files."""
        # Create a test image
        img = Image.new("RGB", (100, 30), color="white")
        portal_file = tmp_path / f".portal-{os.getpid()}-test.png"
        img.save(portal_file)

        with patch("pytesseract.image_to_data") as mock_ocr:
            mock_ocr.return_value = {"text": ["portal"], "conf": [90], "level": [5]}

            success, result, _ = self.service.decode_image_sync(
                "eng",
                str(portal_file),
                remove_source=True
            )

            assert success is True
            assert "portal" in result
            # Portal temp file should be removed
            assert not portal_file.exists()

    def test_decode_image_empty_result(self, tmp_path):
        """Test handling of empty OCR/QR results."""
        img = Image.new("RGB", (100, 30), color="white")
        test_file = tmp_path / "test.png"
        img.save(test_file)

        with patch("pytesseract.image_to_data") as mock_ocr:
            mock_ocr.return_value = {"text": [""], "conf": [-1], "level": [5]}

            success, result, error = self.service.decode_image_sync("eng", str(test_file), False)

            assert success is False
            assert result == ""
            assert error == "No text found."
