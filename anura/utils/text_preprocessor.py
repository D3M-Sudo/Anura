# text_preprocessor.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
"""
Smart text preprocessing utilities for better OCR results.
Includes image enhancement, text cleanup, and intelligent formatting.
"""

import re

from loguru import logger
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


class TextPreprocessor:
    """Advanced text preprocessing for OCR accuracy improvement."""

    def __init__(self) -> None:
        self._whitespace_patterns = [
            (r"\s+", " "),  # Multiple spaces to single
            (r"\n\s*\n\s*\n+", "\n\n"),  # Multiple newlines to double
            (r"[ \t]+$", ""),  # Trailing spaces
            (r"^[ \t]+", ""),  # Leading spaces
        ]

        self._punctuation_patterns = [
            (r"([.!?])\1+", r"\1"),  # Multiple punctuation
            (r",+", ","),  # Multiple commas
            (r"\s*([.,;:!?])\s*", r"\1 "),  # Space around punctuation
            (r"\s+([.,;:!?])", r"\1"),  # Remove space before punctuation
        ]

    def enhance_image(self, image: Image.Image) -> Image.Image:
        """
        Apply intelligent image enhancement for better OCR accuracy.
        Includes grayscale conversion, adaptive thresholding, and noise reduction.

        Args:
            image: Input PIL Image

        Returns:
            Enhanced PIL Image
        """
        try:
            # 1. Grayscale conversion
            if image.mode != "L":
                image = image.convert("L")

            # 2. Rescale for better OCR if image is too small
            image = self._rescale_if_needed(image)

            # 3. Adaptive enhancements (Brightness/Contrast)
            enhanced = self._apply_adaptive_enhancements(image)

            # 4. Noise reduction (Median Filter)
            enhanced = enhanced.filter(ImageFilter.MedianFilter(size=3))

            # 5. Adaptive Thresholding (Otsu-like via numpy if available, or basic auto-contrast)
            enhanced = self._apply_thresholding(enhanced)

            # 6. Final Sharpening
            enhancer = ImageEnhance.Sharpness(enhanced)
            enhanced = enhancer.enhance(1.5)

            logger.debug("Applied advanced image enhancement preprocessing")
            return enhanced

        except Exception as e:
            logger.warning(f"Advanced image enhancement failed: {e}")
            return image

    def _rescale_if_needed(self, image: Image.Image) -> Image.Image:
        """Rescale image if it's too small for reliable OCR."""
        width, height = image.size
        # OCR works best with text height around 30-40 pixels
        if width < 1000 or height < 1000:
            scale_factor = 2
            logger.debug(f"Rescaling image by {scale_factor}x for better OCR")
            return image.resize((width * scale_factor, height * scale_factor), Image.Resampling.LANCZOS)
        return image

    def _apply_thresholding(self, image: Image.Image) -> Image.Image:
        """Apply thresholding for better text/background separation."""
        try:
            # Use ImageOps for automatic contrast and normalization
            # This helps in separating text from background in various lighting
            image = ImageOps.autocontrast(image, cutoff=2)

            # Use a simple but effective PIL-based thresholding.
            # Optimization: Using a LUT (Look-Up Table) instead of a lambda is faster
            # for the Image.point() operation as it avoids Python callback overhead.
            threshold = 128
            lut = [0 if i < threshold else 255 for i in range(256)]
            return image.point(lut, "1").convert("L")
        except Exception as e:
            logger.warning(f"Thresholding failed: {e}")
            return image

    def _apply_adaptive_enhancements(self, image: Image.Image) -> Image.Image:
        """Apply adaptive enhancements based on image analysis."""
        # Calculate image statistics
        histogram = image.histogram()
        total_pixels = sum(histogram)

        # Determine if image is too dark or too light
        dark_pixels = sum(histogram[:128]) / total_pixels
        light_pixels = sum(histogram[128:]) / total_pixels

        enhanced = image.copy()

        if dark_pixels > 0.7:  # Image is too dark
            logger.debug("Applying brightness enhancement for dark image")
            enhancer = ImageEnhance.Brightness(enhanced)
            enhanced = enhancer.enhance(1.3)

        elif light_pixels > 0.8:  # Image is too light
            logger.debug("Applying contrast enhancement for light image")
            enhancer = ImageEnhance.Contrast(enhanced)
            enhanced = enhancer.enhance(1.4)

        # Always apply contrast enhancement for better text definition
        enhancer = ImageEnhance.Contrast(enhanced)
        enhanced = enhancer.enhance(1.2)

        return enhanced

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
        """Normalize whitespace in text."""
        normalized = text

        for pattern, replacement in self._whitespace_patterns:
            normalized = re.sub(pattern, replacement, normalized)

        return normalized

    def _fix_punctuation(self, text: str) -> str:
        """Fix punctuation spacing and duplication."""
        fixed = text

        for pattern, replacement in self._punctuation_patterns:
            fixed = re.sub(pattern, replacement, fixed)

        # Fix spacing around parentheses and quotes
        fixed = re.sub(r"\s*\(\s*", " (", fixed)
        fixed = re.sub(r"\s*\)\s*", ") ", fixed)
        fixed = re.sub(r'\s*"\s*', ' "', fixed)
        fixed = re.sub(r"\s*\'\s*", " '", fixed)

        return fixed

    def _fix_capitalization(self, text: str) -> str:
        """Fix capitalization issues in text."""
        if not text:
            return text

        # Capitalize first letter of sentences.
        # re.split with a capturing group returns alternating [text, sep, text, sep, …].
        # We join them with a space so the whitespace consumed by \s* is restored.
        parts = re.split(r"([.!?]+)\s*", text)
        for i in range(0, len(parts), 2):
            if parts[i].strip():
                parts[i] = (
                    parts[i][0].upper() + parts[i][1:] if len(parts[i]) > 1 else parts[i].upper()
                )

        # Rebuild: interleave text and punctuation, adding a space after each punctuation
        # block to replace the whitespace that the split consumed.
        rebuilt: list[str] = []
        for i, part in enumerate(parts):
            if i % 2 == 1:  # punctuation capture group
                rebuilt.append(part + " ")
            else:
                rebuilt.append(part)
        fixed = "".join(rebuilt).strip()

        # Fix ALL CAPS words: words longer than 4 characters are likely not acronyms
        # (acronyms are typically short: NASA, FBI, HTML …).
        # words.isupper() is True for any-letter-all-uppercase word.
        words = fixed.split()
        for i, word in enumerate(words):
            # Strip trailing punctuation for the length/uppercase check
            core = word.rstrip(".,;:!?")
            if core.isupper() and len(core) > 4:
                words[i] = word[0].upper() + word[1:].lower()

        return " ".join(words)

    def _remove_artifacts(self, text: str) -> str:
        """Remove common OCR artifacts."""
        # Remove page numbers and headers/footers patterns
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Skip likely page numbers
            if re.match(r"^\s*\d+\s*$", line):
                continue

            # Skip lines with only special characters
            if re.match(r"^[\s\-_+=*~`]+$|^[\.\-]{3,}$", line):
                continue

            # Remove leading bullet characters
            line = re.sub(r"^[\s•·▪▫◦‣-]+\s*", "", line)

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    def extract_structured_data(self, text: str) -> dict[str, list[str]]:
        """
        Extract structured data from text (emails, URLs, phone numbers).

        Args:
            text: Cleaned OCR text

        Returns:
            Dictionary of extracted structured data
        """
        structured = {"emails": [], "urls": [], "phone_numbers": [], "dates": []}

        # Email pattern
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        structured["emails"] = re.findall(email_pattern, text)

        # URL pattern
        url_pattern = r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?"
        structured["urls"] = re.findall(url_pattern, text)

        # Phone number pattern (various formats)
        phone_patterns = [
            r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # US format
            r"\b\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}\b",  # International
            r"\b\(\d{3}\)[-.\s]?\d{3}[-.\s]?\d{4}\b",  # US with parentheses
        ]

        for pattern in phone_patterns:
            structured["phone_numbers"].extend(re.findall(pattern, text))

        # Date patterns
        date_patterns = [
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",  # MM/DD/YYYY
            r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",  # YYYY/MM/DD
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b",  # Month DD, YYYY
        ]

        for pattern in date_patterns:
            structured["dates"].extend(re.findall(pattern, text, re.IGNORECASE))

        return structured


# Global preprocessor instance
_text_preprocessor: TextPreprocessor | None = None


def get_text_preprocessor() -> TextPreprocessor:
    """Get singleton text preprocessor instance."""
    global _text_preprocessor
    if _text_preprocessor is None:
        _text_preprocessor = TextPreprocessor()
    return _text_preprocessor
