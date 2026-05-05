# test_services_simple.py
#
# Simple unit tests for core services without GTK dependencies
# Tests business logic and utility functions

import pytest
from unittest.mock import Mock, patch


class TestShareServiceLogic:
    """Test ShareService logic without GTK dependencies."""

    def test_validate_share_url_valid_http(self):
        """Test validation of valid HTTP URLs."""
        # Import the validation function directly
        from anura.services.share_service import ShareService

        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://mastodon.social",
            "https://example.com/path?query=value",
        ]

        for url in valid_urls:
            assert ShareService._validate_share_url(url) is True

    def test_validate_share_url_valid_special_schemes(self):
        """Test validation of special scheme URLs."""
        from anura.services.share_service import ShareService

        special_urls = [
            "mailto:test@example.com",
            "web+mastodon://share?text=hello",
        ]

        for url in special_urls:
            assert ShareService._validate_share_url(url) is True

    def test_validate_share_url_invalid(self):
        """Test validation of invalid URLs."""
        from anura.services.share_service import ShareService

        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "javascript:alert('xss')",
            "",
            "   ",
        ]

        for url in invalid_urls:
            assert ShareService._validate_share_url(url) is False

    def test_get_link_email(self):
        """Test email link generation."""
        from anura.services.share_service import ShareService

        text = "Hello world"
        link = ShareService.get_link_email(text)
        expected = "mailto:?subject=Extracted%20Text&body=Hello%20world"
        assert link == expected

    def test_get_link_reddit(self):
        """Test Reddit link generation."""
        from anura.services.share_service import ShareService

        text = "Hello world"
        link = ShareService.get_link_reddit(text)
        expected = "https://www.reddit.com/submit?selftext=Hello%20world"
        assert link == expected

    def test_get_link_telegram(self):
        """Test Telegram link generation."""
        from anura.services.share_service import ShareService

        text = "Hello world"
        link = ShareService.get_link_telegram(text)
        expected = "https://t.me/share/url?text=Hello%20world"
        assert link == expected

    def test_get_link_x(self):
        """Test X (Twitter) link generation."""
        from anura.services.share_service import ShareService

        text = "Hello world"
        link = ShareService.get_link_x(text)
        expected = "https://twitter.com/intent/tweet?text=Hello%20world"
        assert link == expected

    def test_get_link_mastodon(self):
        """Test Mastodon link generation."""
        from anura.services.share_service import ShareService

        text = "Hello world"
        link = ShareService.get_link_mastodon(text)
        expected = "web+mastodon://share?text=Hello%20world"
        assert link == expected

    def test_providers(self):
        """Test provider list."""
        from anura.services.share_service import ShareService

        providers = ShareService.providers()
        expected = ["email", "mastodon", "reddit", "telegram", "x"]
        assert providers == expected


class TestTTSLogic:
    """Test TTSService logic without GStreamer dependencies."""

    def test_get_effective_language_english(self):
        """Test language mapping for English."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language("eng")
        assert result == "en"

    def test_get_effective_language_italian(self):
        """Test language mapping for Italian."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language("ita")
        assert result == "it"

    def test_get_effective_language_spanish(self):
        """Test language mapping for Spanish."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language("spa")
        assert result == "es"

    def test_get_effective_language_french(self):
        """Test language mapping for French."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language("fra")
        assert result == "fr"

    def test_get_effective_language_german(self):
        """Test language mapping for German."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language("deu")
        assert result == "de"

    def test_get_effective_language_unknown(self):
        """Test language mapping for unknown language."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language("xyz")
        assert result == "en"  # Should default to English

    def test_get_effective_language_multilingual(self):
        """Test language mapping for multilingual OCR codes."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language("eng+ita")
        assert result == "en"  # Should use first language

    def test_get_effective_language_empty(self):
        """Test language mapping for empty input."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language("")
        assert result == "en"  # Should default to English

    def test_get_effective_language_none(self):
        """Test language mapping for None input."""
        from anura.services.tts import TTSService

        service = TTSService()
        result = service.get_effective_language(None)
        assert result == "en"  # Should default to English


class TestConfigLogic:
    """Test configuration logic without system dependencies."""

    def test_get_tesseract_config_valid_english(self):
        """Test Tesseract config generation for valid English."""
        from anura.config import get_tesseract_config
        import os

        # Mock file exists
        with patch("os.path.exists", return_value=True):
            config = get_tesseract_config("eng")
            assert "--tessdata-dir" in config
            assert "--psm 3" in config
            assert "--oem 1" in config

    def test_get_tesseract_config_invalid_language(self):
        """Test Tesseract config generation for invalid language."""
        from anura.config import get_tesseract_config

        with patch("os.path.exists", return_value=False):
            config = get_tesseract_config("invalid")
            # Should default to 'eng' and return valid config
            assert "--tessdata-dir" in config
            assert "--psm 3" in config
            assert "--oem 1" in config

    def test_lang_code_pattern_valid(self):
        """Test language code validation pattern."""
        from anura.config import LANG_CODE_PATTERN
        import re

        valid_codes = ["eng", "ita", "spa", "fra", "deu", "eng+ita", "chi_sim"]

        for code in valid_codes:
            assert re.match(LANG_CODE_PATTERN, code) is not None

    def test_lang_code_pattern_invalid(self):
        """Test language code validation pattern for invalid codes."""
        from anura.config import LANG_CODE_PATTERN
        import re

        invalid_codes = ["", "a", "toolongcode123456789", "invalid!@#", "a b"]

        for code in invalid_codes:
            assert re.match(LANG_CODE_PATTERN, code) is None


class TestValidators:
    """Test utility validators."""

    def test_uri_validator_valid_urls(self):
        """Test URI validator with valid URLs."""
        from anura.utils.validators import uri_validator

        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://mastodon.social/share",
            "https://example.com/path?query=value",
            "http://127.0.0.1:3000",
            "https://192.168.1.1",
        ]

        for url in valid_urls:
            assert uri_validator(url) is True

    def test_uri_validator_invalid_urls(self):
        """Test URI validator with invalid URLs."""
        from anura.utils.validators import uri_validator

        invalid_urls = [
            "not-a-url",
            "ftp://example.com",
            "javascript:alert('xss')",
            "",
            "   ",
            "http://evil",  # Single word without dots
            "https://example.com\x00null",  # Control character
        ]

        for url in invalid_urls:
            assert uri_validator(url) is False

    def test_uri_validator_special_schemes(self):
        """Test URI validator with special schemes (should return False)."""
        from anura.utils.validators import uri_validator

        special_schemes = [
            "mailto:test@example.com",
            "web+mastodon://share?text=hello",
        ]

        for url in special_schemes:
            # These should return False for HTTP/HTTPS validation
            # but are handled separately in share service
            assert uri_validator(url) is False
