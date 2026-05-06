# test_services_simple.py
#
# Simple unit tests for core services without GTK dependencies
# Tests business logic and utility functions

from unittest.mock import patch


class TestShareServiceLogic:
    """Test ShareService logic without GTK dependencies."""

    def test_validate_share_url_valid_http(self):
        """Test validation of valid HTTP URLs."""
        # Import the validation function from pure Python utilities
        from anura.utils.share_utils import validate_share_url

        valid_urls = [
            "https://example.com",
            "http://localhost:8080",
            "https://mastodon.social",
            "https://example.com/path?query=value",
        ]

        for url in valid_urls:
            assert validate_share_url(url) is True

    def test_validate_share_url_valid_special_schemes(self):
        """Test validation of special scheme URLs."""
        from anura.utils.share_utils import validate_share_url

        special_urls = [
            "mailto:test@example.com",
            "web+mastodon://share?text=hello",
        ]

        for url in special_urls:
            assert validate_share_url(url) is True

    def test_validate_share_url_invalid(self):
        """Test validation of invalid URLs."""
        from anura.utils.share_utils import validate_share_url

        invalid_urls = [
            "ftp://example.com",
            "javascript:alert('xss')",
            "",
            None,
            "not-a-url",
            "https://example.com<script>alert('xss')</script>",
        ]

        for url in invalid_urls:
            assert validate_share_url(url) is False

    def test_get_link_email(self):
        """Test email link generation."""
        from anura.utils.share_utils import get_link_email

        text = "Hello World"
        link = get_link_email(text)
        assert link.startswith("mailto:?")
        assert "subject=" in link
        assert "body=" in link
        assert "Hello+World" in link or "Hello%20World" in link

    def test_get_link_reddit(self):
        """Test Reddit link generation."""
        from anura.utils.share_utils import get_link_reddit

        text = "Hello world"
        link = get_link_reddit(text)
        # Since text is short (< 100 chars), it should include title
        expected = "https://www.reddit.com/submit?title=Extracted%20Text&selftext=Hello%20world"
        assert link == expected

    def test_get_link_telegram(self):
        """Test Telegram link generation."""
        from anura.utils.share_utils import get_link_telegram

        text = "Hello World"
        link = get_link_telegram(text)
        assert "t.me/share/url" in link
        assert "text=" in link
        # Check for either URL encoding format
        assert "Hello+World" in link or "Hello%20World" in link or "Hello World" in link

    def test_get_link_x(self):
        """Test X (Twitter) link generation."""
        from anura.utils.share_utils import get_link_x

        text = "Hello world"
        link = get_link_x(text)
        assert "x.com/intent/tweet" in link
        assert "text=" in link
        # Check for either URL encoding format
        assert "Hello+world" in link or "Hello%20world" in link or "Hello world" in link

    def test_get_link_mastodon(self):
        """Test Mastodon link generation."""
        from anura.utils.share_utils import get_link_mastodon

        text = "Hello World"
        link = get_link_mastodon(text)
        assert "web+mastodon://share" in link
        assert "text=" in link
        # Check for either URL encoding format
        assert "Hello+World" in link or "Hello%20World" in link or "Hello World" in link

    def test_providers(self):
        """Test provider list."""
        from anura.utils.share_utils import get_providers

        providers = get_providers()
        expected = ["email", "reddit", "telegram", "x", "mastodon"]
        assert providers == expected



    

class TestConfigLogic:
    """Test configuration logic without system dependencies."""

    def test_get_tesseract_config_valid_english(self):
        """Test Tesseract config generation for valid English."""
        from anura.config import get_tesseract_config

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
        import re

        from anura.config import LANG_CODE_PATTERN

        valid_codes = ["eng", "ita", "spa", "fra", "deu", "eng+ita", "chi_sim"]

        for code in valid_codes:
            assert re.match(LANG_CODE_PATTERN, code) is not None

    def test_lang_code_pattern_invalid(self):
        """Test language code validation pattern for invalid codes."""
        import re

        from anura.config import LANG_CODE_PATTERN

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
