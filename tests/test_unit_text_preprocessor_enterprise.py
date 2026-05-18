# tests/test_unit_text_preprocessor_enterprise.py
from PIL import Image
import pytest

from anura.utils.text_preprocessor import TextPreprocessor


class TestTextPreprocessorEnterprise:
    """
    Enterprise-grade unit tests for TextPreprocessor.
    """

    @pytest.fixture
    def preprocessor(self):
        return TextPreprocessor()

    def test_normalize_whitespace(self, preprocessor):
        """Test whitespace normalization logic."""
        input_text = "  Hello   world! \n New  line.  "
        assert preprocessor._normalize_whitespace(input_text) == "Hello world! New line."
        assert preprocessor._normalize_whitespace("") == ""
        assert preprocessor._normalize_whitespace(None) == ""

    def test_fix_punctuation(self, preprocessor):
        """Test punctuation spacing and deduplication."""
        input_text = "Hello!! This is a test... ,,, duplicated , and missing space. ( inside )"
        # Multiple punctuation -> single
        # Remove space before punct
        # Add space after punct
        result = preprocessor._fix_punctuation(input_text)
        assert "Hello!" in result
        assert "test." in result
        assert ", duplicated" in result
        assert "space." in result
        assert " (inside)" in result

    def test_fix_capitalization(self, preprocessor):
        """Test sentence capitalization and ALL CAPS word fixing."""
        input_text = "hello world. this is a TEST. SHOUTING IS LOUD."
        result = preprocessor._fix_capitalization(input_text)
        assert result.startswith("Hello")
        assert ". This" in result
        assert "Shouting" in result  # SHOUTING > 4 chars, should be fixed

    def test_remove_artifacts(self, preprocessor):
        """Test removal of common OCR artifacts."""
        lines = [
            "  123  ",  # Page number
            "---",  # Separator
            "• Bullet point",
            "- List item",
            "Normal text",
        ]
        text = "\n".join(lines)
        result = preprocessor._remove_artifacts(text)
        assert "123" not in result
        assert "---" not in result
        assert "Bullet point" in result
        assert "•" not in result
        assert "List item" in result
        assert "- " not in result

    def test_extract_structured_data(self, preprocessor):
        """Test extraction of emails, URLs, phones, and dates."""
        text = "Contact me at test@example.com or visit https://anura.app/ Call 555-555-0199. Date: 12/31/2026."
        data = preprocessor.extract_structured_data(text)
        assert "test@example.com" in data["emails"]
        assert "https://anura.app/" in data["urls"]
        assert "555-555-0199" in data["phone_numbers"]
        assert "12/31/2026" in data["dates"]

    def test_enhance_image_smoke(self, preprocessor):
        """Smoke test for image enhancement (verifies it doesn't crash)."""
        img = Image.new("RGB", (100, 100), color="white")
        enhanced = preprocessor.enhance_image(img)
        assert isinstance(enhanced, Image.Image)
        assert enhanced.mode == "L"

    def test_rescale_if_needed(self, preprocessor):
        """Test that small images are rescaled."""
        small_img = Image.new("L", (100, 100))
        rescaled = preprocessor._rescale_if_needed(small_img)
        assert rescaled.size == (200, 200)

        large_img = Image.new("L", (1200, 1200))
        not_rescaled = preprocessor._rescale_if_needed(large_img)
        assert not_rescaled.size == (1200, 1200)

    def test_apply_thresholding(self, preprocessor):
        """Test that thresholding produces near-binary results."""
        img = Image.new("L", (2, 2))
        img.putdata([50, 200, 100, 150])
        thresholded = preprocessor._apply_thresholding(img)
        data = list(thresholded.getdata())
        assert data[0] == 0
        assert data[1] == 255
        assert data[2] == 0
        assert data[3] == 255
