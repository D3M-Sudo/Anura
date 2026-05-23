# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""
Smart text preprocessing utilities for better OCR results.
Includes image enhancement, text cleanup, and intelligent formatting.
"""

import re

from loguru import logger
from PIL import Image

from anura.utils.image_filters import get_default_filter_chain


class TextPreprocessor:
    """Advanced text preprocessing for OCR accuracy improvement."""

    def __init__(self) -> None:
        # Pre-compiled regex patterns for better performance
        self._punctuation_patterns = [
            (re.compile(r"([.!?])\1+"), r"\1"),  # Multiple punctuation
            (re.compile(r",+"), ","),  # Multiple commas
            (re.compile(r"\s+([.,;:!?])"), r"\1"),  # Remove space before punctuation (first)
            (re.compile(r"(?<!\d)([.,;:!?])(?!\d)(\S)"), r"\1 \2"),  # Add space after punctuation if missing (second)
        ]

        # Pre-compiled regexes for punctuation spacing
        self._paren_open_re = re.compile(r"\s*\(\s*")
        self._paren_close_re = re.compile(r"\s*\)\s*")
        self._quote_double_re = re.compile(r'\s*"\s*')
        self._quote_single_re = re.compile(r"\s*\'\s*")

        # Pre-compiled regexes for capitalization
        self._sentence_split_re = re.compile(r"((?<!\d)[.!?]+)\s*")

        # Pre-compiled regexes for artifacts removal
        # Optimization: use [ \t] instead of \s and re.MULTILINE to allow processing the
        # entire text block at once while preserving line structure.
        self._page_num_re = re.compile(r"^[ \t]*\d+[ \t]*\r?\n?", re.MULTILINE)
        self._special_chars_re = re.compile(r"^(?:[ \t\-_+=*~`]+|[\.\-]{3,})\r?\n?", re.MULTILINE)
        self._bullets_re = re.compile(r"^[ \t•·▪▫◦‣]+[ \t]*", re.MULTILINE)
        self._list_marker_re = re.compile(r"^- +", re.MULTILINE)

        # Pre-compiled structured data patterns
        self._email_re = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        self._url_re = re.compile(
            r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.-])*(?:\?(?:[\w&=%.-])*)?(?:#(?:\w*))?)?"
        )

        self._phone_res = [
            re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b"),  # US format
            re.compile(r"\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b"),  # International
            re.compile(r"\b\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}\b"),  # US with parentheses
        ]

        self._date_res = [
            re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"),  # MM/DD/YYYY
            re.compile(r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b"),  # YYYY/MM/DD
            re.compile(
                r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",
                re.IGNORECASE,
            ),  # Month DD, YYYY
        ]

    def enhance_image(self, image: Image.Image) -> Image.Image:
        """Apply the preprocessing filter chain to improve OCR accuracy.

        Args:
            image: Input PIL Image

        Returns:
            Enhanced PIL Image, or original if enhancement fails.
        """
        try:
            return get_default_filter_chain().apply(image)
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image

    def clean_extracted_text(self, text: str) -> str:
        """
        Clean and normalize extracted OCR text.

        Args:
            text: Raw OCR extracted text

        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""

        cleaned = text

        # Normalize whitespace
        cleaned = self._normalize_whitespace(cleaned)

        # Fix punctuation
        cleaned = self._fix_punctuation(cleaned)

        # Fix capitalization
        cleaned = self._fix_capitalization(cleaned)

        # Remove artifacts
        cleaned = self._remove_artifacts(cleaned)

        return cleaned.strip()

    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text while preserving line breaks."""
        if not text:
            return ""

        # Use regex to squash horizontal whitespace while preserving vertical structure
        return re.sub(r"[ \t]+", " ", text).strip()

    def _fix_punctuation(self, text: str) -> str:
        """Fix punctuation spacing and duplication."""
        fixed = text

        for pattern, replacement in self._punctuation_patterns:
            fixed = pattern.sub(replacement, fixed)

        # Fix spacing around parentheses and quotes
        # Note: 4 separate passes are used as they are highly optimized in C and
        # avoid Python lambda callback overhead, which can be slower on frequent matches.
        fixed = self._paren_open_re.sub(" (", fixed)
        fixed = self._paren_close_re.sub(") ", fixed)
        fixed = self._quote_double_re.sub(' "', fixed)
        fixed = self._quote_single_re.sub(" '", fixed)

        return fixed

    def _fix_capitalization(self, text: str) -> str:
        """Fix capitalization issues in text."""
        if not text:
            return text

        # Capitalize first letter of sentences.
        # re.split with a capturing group returns alternating [text, sep, text, sep, …].
        # We process and rebuild the list in a single pass to minimize string allocations.
        parts = self._sentence_split_re.split(text)
        rebuilt: list[str] = []

        for i, part in enumerate(parts):
            if i % 2 == 0:  # text part
                if part.strip():
                    # Optimization: slice indexing [0:1] is safer/faster for capitalization
                    # and handles empty strings gracefully.
                    rebuilt.append(part[0:1].upper() + part[1:])
                else:
                    rebuilt.append(part)
            else:  # punctuation part (capture group)
                rebuilt.append(part + " ")

        fixed = "".join(rebuilt).strip()

        # Fix ALL CAPS words: words longer than 4 characters are likely not acronyms
        # (acronyms are typically short: NASA, FBI, HTML …).
        # words.isupper() is True for any-letter-all-uppercase word.
        words = fixed.split()
        for i, word in enumerate(words):
            # Strip trailing punctuation for the length/uppercase check
            core = word.rstrip(".,;:!?")
            if core.isupper() and len(core) > 4:
                # Optimization: word.capitalize() is more idiomatic and handles
                # the case conversion efficiently.
                words[i] = word.capitalize()

        return " ".join(words)

    def _remove_artifacts(self, text: str) -> str:
        """Remove common OCR artifacts."""
        # Optimization: Use multiline regex substitutions to process the entire
        # text block at once, avoiding expensive Python-level line splitting
        # and iteration.

        # Remove page numbers and lines with only special characters
        cleaned = self._page_num_re.sub("", text)
        cleaned = self._special_chars_re.sub("", cleaned)

        # Remove leading Unicode bullet characters and markdown-style list markers
        # re.MULTILINE ensures '^' matches the start of each line.
        cleaned = self._bullets_re.sub("", cleaned, count=0)
        cleaned = self._list_marker_re.sub("", cleaned, count=0)

        return cleaned

    def extract_structured_data(self, text: str) -> dict[str, list[str]]:
        """
        Extract structured data from text (emails, URLs, phone numbers).

        Args:
            text: Cleaned OCR text

        Returns:
            Dictionary of extracted structured data
        """
        structured: dict[str, list[str]] = {"emails": [], "urls": [], "phone_numbers": [], "dates": []}

        # Email pattern
        structured["emails"] = self._email_re.findall(text)

        # URL pattern
        structured["urls"] = self._url_re.findall(text)

        # Phone number patterns
        for pattern in self._phone_res:
            structured["phone_numbers"].extend(pattern.findall(text))

        # Date patterns
        for pattern in self._date_res:
            structured["dates"].extend(pattern.findall(text))

        return structured


# Global preprocessor instance
_text_preprocessor: TextPreprocessor | None = None


def get_text_preprocessor() -> TextPreprocessor:
    """Get singleton text preprocessor instance."""
    global _text_preprocessor
    if _text_preprocessor is None:
        _text_preprocessor = TextPreprocessor()
    return _text_preprocessor
