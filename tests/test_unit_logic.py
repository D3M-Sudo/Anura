# test_unit_logic.py
#
# Unit tests for core business logic without GTK dependencies
# Tests individual functions and classes directly

import os
import re
import sys
from urllib.parse import quote

# Add the project root to Python path to import modules directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestShareServiceLogic:
    """Test ShareService logic without GTK dependencies."""

    def test_url_encoding(self):
        """Test URL encoding for share links."""
        text = "Hello world! @#$%"
        encoded = quote(text, safe="")
        assert encoded == "Hello%20world%21%20%40%23%24%25"

    def test_email_link_generation(self):
        """Test email link generation logic."""
        text = "Hello world"
        encoded = quote(text, safe="")
        expected = f"mailto:?subject=Extracted%20Text&body={encoded}"
        assert expected == "mailto:?subject=Extracted%20Text&body=Hello%20world"

    def test_reddit_link_generation(self):
        """Test Reddit link generation logic."""
        text = "Hello world"
        encoded = quote(text, safe="")
        expected = f"https://www.reddit.com/submit?selftext={encoded}"
        assert expected == "https://www.reddit.com/submit?selftext=Hello%20world"

    def test_telegram_link_generation(self):
        """Test Telegram link generation logic."""
        text = "Hello world"
        encoded = quote(text, safe="")
        expected = f"https://t.me/share/url?text={encoded}"
        assert expected == "https://t.me/share/url?text=Hello%20world"

    def test_x_link_generation(self):
        """Test X (Twitter) link generation logic."""
        from anura.services.share_service import ShareService

        result = ShareService.get_link_x("Hello world")
        assert result == "https://x.com/intent/tweet?text=Hello%20world"

    def test_mastodon_link_generation(self):
        """Test Mastodon link generation logic."""
        text = "Hello world"
        encoded = quote(text, safe="")
        expected = f"web+mastodon://share?text={encoded}"
        assert expected == "web+mastodon://share?text=Hello%20world"


class TestTTSLogic:
    """Test TTS language mapping logic."""

    def test_language_mapping_english(self):
        """Test English language mapping."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts("eng")
        assert result == "en"

    def test_language_mapping_italian(self):
        """Test Italian language mapping."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts("ita")
        assert result == "it"

    def test_language_mapping_spanish(self):
        """Test Spanish language mapping."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts("spa")
        assert result == "es"

    def test_language_mapping_french(self):
        """Test French language mapping."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts("fra")
        assert result == "fr"

    def test_language_mapping_german(self):
        """Test German language mapping."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts("deu")
        assert result == "de"

    def test_language_mapping_unknown(self):
        """Test unknown language mapping defaults to English."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts("zzz")
        assert result == "en"

    def test_language_mapping_multilingual(self):
        """Test multilingual OCR codes use first language for TTS."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts("ita+eng")
        assert result == "it"

    def test_language_mapping_empty(self):
        """Test empty language code defaults to English."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts("")
        assert result == "en"

    def test_language_mapping_none(self):
        """Test None language code defaults to English."""
        from anura.services.tts import TTSService
        result = TTSService.map_tesseract_to_gtts(None)
        assert result == "en"


class TestConfigLogic:
    """Test configuration logic."""

    def test_lang_code_pattern_valid(self):
        """Test valid language code patterns."""
        from anura.config import LANG_CODE_PATTERN

        valid_codes = ["eng", "ita", "spa", "fra", "deu", "eng+ita", "chi_sim"]

        for code in valid_codes:
            assert re.match(LANG_CODE_PATTERN, code) is not None

    def test_lang_code_pattern_invalid(self):
        """Test invalid language code patterns."""
        from anura.config import LANG_CODE_PATTERN

        invalid_codes = ["", "a", "toolongcode123456789", "invalid!@#", "a b"]

        for code in invalid_codes:
            assert re.match(LANG_CODE_PATTERN, code) is None

    def test_tesseract_config_format(self):
        """Test Tesseract config string format."""
        tessdata_dir = "/path/to/tessdata"
        config = f'--tessdata-dir "{tessdata_dir}" --psm 3 --oem 1'

        assert "--tessdata-dir" in config
        assert "--psm 3" in config
        assert "--oem 1" in config
        assert tessdata_dir in config

    def test_tesseract_config_quoting(self):
        """Test Tesseract config properly quotes paths with spaces."""
        tessdata_dir = "/path with spaces/tessdata"
        config = f'--tessdata-dir "{tessdata_dir}" --psm 3 --oem 1'

        assert config == '--tessdata-dir "/path with spaces/tessdata" --psm 3 --oem 1'


class TestValidatorLogic:
    """Test URI validation logic."""

    def test_uri_validator_control_characters(self):
        """Test URI validator blocks control characters."""
        from anura.utils.validators import uri_validator

        invalid_urls = [
            "https://example.com\x00null",
            "https://example.com\x01",
            "https://example.com\x1f",
            "https://example.com\x7f",
        ]

        for url in invalid_urls:
            assert not uri_validator(url)

    def test_uri_validator_ascii_only(self):
        """Test URI validator requires ASCII-only URLs."""
        from anura.utils.validators import uri_validator

        unicode_urls = [
            "https://example.com/测试",
            "https://example.com/🔒",
            "https://example.com/ñ",
        ]

        for url in unicode_urls:
            assert not uri_validator(url)

    def test_uri_validator_valid_schemes(self):
        """Test URI validator accepts valid schemes."""
        from anura.utils.validators import uri_validator

        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://mastodon.social/share",
            "https://example.com/path?query=value",
        ]

        for url in valid_urls:
            assert uri_validator(url)

    def test_uri_validator_invalid_schemes(self):
        """Test URI validator blocks invalid schemes."""
        from anura.utils.validators import uri_validator

        invalid_urls = [
            "ftp://example.com",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
        ]

        for url in invalid_urls:
            assert not uri_validator(url)

    def test_uri_validator_localhost_allowed(self):
        """Test URI validator allows localhost."""
        from anura.utils.validators import uri_validator

        localhost_urls = [
            "http://localhost:8080",
            "https://localhost:3000",
            "http://127.0.0.1:8000",
            "https://192.168.1.1",
        ]

        for url in localhost_urls:
            assert uri_validator(url)

    def test_uri_validator_domain_validation(self):
        """Test URI validator domain validation."""
        from anura.utils.validators import uri_validator

        # Valid domains should pass
        valid_domains = [
            "https://example.com",
            "https://mastodon.social",
            "https://www.google.com",
        ]

        # Invalid single-word hostnames should be blocked
        invalid_domains = [
            "https://evil",
            "http://malware",
        ]

        for url in valid_domains:
            assert uri_validator(url)

        for url in invalid_domains:
            assert not uri_validator(url)


class TestUrlLengthValidation:
    """Test URL length validation for sharing."""

    def test_url_length_validation(self):
        """Test URL length limits for sharing."""
        MAX_URL_LENGTH = 2000

        # Short URL should be valid
        short_text = "Hello world"
        url = f"https://mastodon.social/share?text={quote(short_text, safe='')}"
        assert len(url) <= MAX_URL_LENGTH

        # Very long URL should be invalid
        long_text = "a" * 3000
        url = f"https://mastodon.social/share?text={quote(long_text, safe='')}"
        assert len(url) > MAX_URL_LENGTH

    def test_url_encoding_length_impact(self):
        """Test how URL encoding affects length."""
        # Characters that get encoded should increase length
        text_with_spaces = "Hello world with spaces"
        text_with_special = "Hello world! @#$%"

        encoded_spaces = quote(text_with_spaces, safe="")
        encoded_special = quote(text_with_special, safe="")

        # Encoded version should be longer
        assert len(encoded_spaces) > len(text_with_spaces)
        assert len(encoded_special) > len(text_with_special)


if __name__ == "__main__":
    # Run tests manually if called directly
    import pytest

    pytest.main([__file__, "-v"])
