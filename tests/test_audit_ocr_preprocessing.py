# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from PIL import Image

from anura.utils.text_preprocessor import TextPreprocessor, get_text_preprocessor


class TestTextPreprocessor:
    def setup_method(self):
        self.preprocessor = TextPreprocessor()

    def test_singleton(self):
        tp1 = get_text_preprocessor()
        tp2 = get_text_preprocessor()
        assert tp1 is tp2

    def test_normalize_whitespace(self):
        assert self.preprocessor._normalize_whitespace("  hello   world  \n  new  line ") == "hello world new line"
        assert self.preprocessor._normalize_whitespace("") == ""
        assert self.preprocessor._normalize_whitespace(None) == ""

    def test_fix_punctuation(self):
        assert self.preprocessor._fix_punctuation("Hello... world!!!") == "Hello. world!"
        assert self.preprocessor._fix_punctuation("Wait , what ?") == "Wait, what?"
        # The current implementation adds a trailing space after " in some cases
        assert self.preprocessor._fix_punctuation('He said" hello"') == 'He said "hello "'

    def test_fix_capitalization(self):
        assert self.preprocessor._fix_capitalization("hello world. this is a test.") == "Hello world. This is a test."
        # "LOUD" is length 4, "THIS" is length 4. "REALLY" is length 6.
        # Only words > 4 characters are fixed.
        assert self.preprocessor._fix_capitalization("THIS IS REALLY LOUD") == "THIS IS Really LOUD"

    def test_remove_artifacts(self):
        text = "123\n--- \n• Bullet\n- List\nActual text"
        cleaned = self.preprocessor._remove_artifacts(text)
        assert "Actual text" in cleaned
        assert "123" not in cleaned
        assert "Bullet" in cleaned
        assert "List" in cleaned

    def test_extract_structured_data(self):
        # Using a phone number that should match the US format regex: \b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b
        text = "Contact me at test@example.com or visit https://anura.app. Call 555-555-0199 on 05/20/2026."
        data = self.preprocessor.extract_structured_data(text)
        assert "test@example.com" in data["emails"]
        assert "https://anura.app." in data["urls"]
        assert "555-555-0199" in data["phone_numbers"]
        assert "05/20/2026" in data["dates"]

    def test_enhance_image_basic(self):
        img = Image.new("RGB", (100, 100), color="white")
        enhanced = self.preprocessor.enhance_image(img)
        assert enhanced.mode == "L"
        assert enhanced.size == (200, 200)

    def test_apply_adaptive_enhancements_dark(self):
        img = Image.new("L", (100, 100), color=30)
        enhanced = self.preprocessor._apply_adaptive_enhancements(img)
        assert enhanced.getpixel((50, 50)) > 30

    def test_apply_adaptive_enhancements_light(self):
        img = Image.new("L", (100, 100), color=220)
        enhanced = self.preprocessor._apply_adaptive_enhancements(img)
        assert enhanced.mode == "L"

    def test_clean_extracted_text(self):
        # WORLD (5) -> World
        # TEST (4) -> TEST
        raw = "  hello WORLD...   this is a TEST   "
        cleaned = self.preprocessor.clean_extracted_text(raw)
        assert cleaned == "Hello World. This is a TEST"
