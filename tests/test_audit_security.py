import pytest
import os
import re
import subprocess
from unittest.mock import patch, MagicMock
from anura.language_manager import LanguageManager
from anura.config import get_tesseract_config

class TestAuditSecurity:

    def test_tesseract_command_injection(self):
        malicious_code = "eng; rm -rf /"
        config = get_tesseract_config(malicious_code)
        assert ";" not in config
        assert "rm" not in config

    def test_language_manager_path_traversal(self, tmp_path):
        tessdata_dir = tmp_path / "tessdata"
        tessdata_dir.mkdir()
        secret_file = tmp_path / "secret.txt"
        secret_file.write_text("shhhh")

        with patch('anura.language_manager.TESSDATA_DIR', str(tessdata_dir)):
            manager = LanguageManager()
            manager.remove_language("../secret.txt")
            assert secret_file.exists()

            manager.remove_language("/etc/passwd")

    @patch('pytesseract.image_to_string')
    def test_screenshot_service_malicious_input(self, mock_ocr):
        from anura.services.screenshot_service import ScreenshotService
        with patch('gi.repository.Xdp.Portal'), \
             patch('anura.services.screenshot_service._configure_tesseract_path'):
            service = ScreenshotService()

            success, text, error = service.decode_image_sync("eng; $(whoami)", "test.png")
            assert success is False
            assert "Invalid language code" in error
            mock_ocr.assert_not_called()

    def test_secret_scan(self):
        """Scan for potential hardcoded secrets."""
        # Patterns for potential secrets
        patterns = [
            r'api_key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
            r'token\s*=\s*["\'][a-zA-Z0-9]{20,}["\']',
            r'secret\s*=\s*["\'][a-zA-Z0-9]{20,}["\']'
        ]

        found_secrets = []
        for root, _, files in os.walk("anura"):
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    with open(path) as f:
                        content = f.read()
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                found_secrets.append(f"{path}: matched {pattern}")

        # We expect no hardcoded secrets in the app source
        assert not found_secrets, f"Potential secrets found: {found_secrets}"
