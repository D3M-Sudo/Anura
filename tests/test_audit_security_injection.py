# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import re
from unittest.mock import patch

import pytest

pytest.importorskip("gi")

from anura.config import LANG_CODE_PATTERN
from anura.utils.validators import uri_validator


class TestSecurityAudit:
    def test_lang_code_injection_prevention(self):
        # The regex should prevent injection into tesseract command line
        # Tesseract command: --tessdata-dir "{TESSDATA_DIR}" --psm 3 --oem 1
        # If we can inject something like 'eng" ; rm -rf / ; "'

        malicious_codes = ['eng" ; rm -rf /', "eng --param value", "eng$(whoami)", "../../etc/passwd", "eng\n\r"]

        for code in malicious_codes:
            assert not re.match(LANG_CODE_PATTERN, code), f"Malicious code '{code}' bypassed pattern!"

    def test_uri_validation_security(self):
        # Ensure sensitive schemes and local files are blocked
        assert uri_validator("file:///etc/shadow") is False
        assert uri_validator("gopher://evil.com") is False
        assert uri_validator("javascript:alert('XSS')") is False
        assert uri_validator("data:text/html,<html>") is False

        # Ensure userinfo spoofing is blocked
        assert uri_validator("https://user:password@legit.com") is False

        # Ensure control characters are blocked
        assert uri_validator("https://google.com\r\n/evil") is False
        assert uri_validator("https://google.com\0/evil") is False


    def test_absolute_path_injection_in_language_manager(self, tmp_path):
        # Test that LanguageManager.remove_language validates input
        from anura.services.language_manager import LanguageManager

        # Mock TESSDATA_DIR to a safe temp path
        tessdata = tmp_path / "tessdata"
        tessdata.mkdir()

        with patch("anura.services.language_manager.TESSDATA_DIR", str(tessdata)), \
             patch("gi.repository.GLib.idle_add"), \
             patch("gi.repository.GObject.GObject.__init__"):
            lm = LanguageManager()

            # Try to remove a file outside the directory
            outside_file = tmp_path / "outside.txt"
            outside_file.touch()

            # This code should be blocked by LANG_CODE_PATTERN
            lm.remove_language("../../../" + str(outside_file))

            assert outside_file.exists()
