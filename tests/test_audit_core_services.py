# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from unittest.mock import patch

from anura.services.clipboard_service import ClipboardService
from anura.services.screenshot_service import ScreenshotService
from anura.services.settings import Settings
from anura.services.share_service import ShareService
from anura.services.tts import TTSService


class TestShareService:
    def setup_method(self):
        self.service = ShareService()

    @pytest.mark.gtk
    def test_providers_list(self):
        providers = self.service.providers()
        assert "email" in providers
        assert "x" in providers
        assert "mastodon" in providers

    def test_validate_share_url(self):
        assert ShareService._validate_share_url("mailto:test@example.com") is True
        assert ShareService._validate_share_url("web+mastodon://share?text=foo") is True
        assert ShareService._validate_share_url("https://google.com") is True
        assert ShareService._validate_share_url("file:///etc/passwd") is False

    def test_get_link_telegram(self):
        assert "t.me/share" in self.service.get_link_telegram("hello")
        assert self.service.get_link_telegram("") == ""

    def test_get_link_email(self):
        link = self.service.get_link_email("hello world")
        assert "mailto:" in link
        assert "subject=Extracted%20Text" in link
        assert "body=hello%20world" in link


class TestTTSService:
    @pytest.mark.gtk
    def test_map_tesseract_to_gtts(self):
        assert TTSService.map_tesseract_to_gtts("eng") == "en"
        assert TTSService.map_tesseract_to_gtts("ita") == "it"
        assert TTSService.map_tesseract_to_gtts("jpn_vert") == "ja"
        assert TTSService.map_tesseract_to_gtts("unknown") == "en"

    @pytest.mark.gtk
    def test_get_effective_language(self):
        with patch("anura.services.tts.settings.get_string", return_value=""):
            service = TTSService()
            assert service.get_effective_language("eng") == "en"

        with patch("anura.services.tts.settings.get_string", return_value="fr"):
            service = TTSService()
            assert service.get_effective_language("eng") == "fr"

    @pytest.mark.gtk
    def test_generate_empty_text(self):
        service = TTSService()
        assert service.generate("") == ""
        assert service.generate("   ") == ""


class TestSettings:
    @pytest.mark.gtk
    def test_settings_initialization(self):
        try:
            s = Settings()
            assert s is not None
        except RuntimeError as e:
            pytest.skip(f"GSettings schema not found: {e}")


class TestScreenshotService:
    @pytest.mark.gtk
    def test_validate_decode_inputs(self):
        service = ScreenshotService()
        valid, _, _ = service._validate_decode_inputs("eng")
        assert valid is True

        invalid, _, _ = service._validate_decode_inputs("invalid!")
        assert invalid is False

    @pytest.mark.gtk
    def test_format_decode_result(self):
        service = ScreenshotService()
        success, text, err = service._format_decode_result("Extracted", None)
        assert success is True
        assert text == "Extracted"

        success, text, err = service._format_decode_result(None, "Error")
        assert success is False
        assert err == "Error"

        success, text, err = service._format_decode_result(None, None)
        assert success is False
        assert "No text found" in err


class TestClipboardService:
    @pytest.mark.gtk
    def test_init_and_cleanup(self):
        service = ClipboardService()
        assert service._cancellable is None
        service.cleanup()
