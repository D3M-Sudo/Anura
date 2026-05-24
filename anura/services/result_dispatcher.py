# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from loguru import logger

from anura.types.ocr import ExtractionResult, OcrResult
from anura.utils.singleton import get_instance
from anura.utils.text_preprocessor import get_text_preprocessor


class ResultDispatcher:
    """
    Pure Python service for analyzing and structured extraction results.
    Decoupled from UI, settings, and side effects.
    """

    def dispatch(self, text: str, ocr_result: OcrResult | None = None) -> ExtractionResult:
        """
        Process and analyze the extracted text.

        Args:
            text: The extracted text or barcode content.
            ocr_result: Optional OCR result containing layout information.

        Returns:
            ExtractionResult containing structured data and metadata.
        """
        if not text:
            return ExtractionResult(
                text="",
                raw_text="",
                urls=(),
                emails=(),
                phone_numbers=(),
                avg_confidence=0.0,
                bounding_box=(0, 0, 0, 0)
            )

        preprocessor = get_text_preprocessor()
        structured = preprocessor.extract_structured_data(text)

        urls = tuple(structured.get("urls", []))
        emails = tuple(structured.get("emails", []))
        phone_numbers = tuple(structured.get("phone_numbers", []))

        # Identify if the result is primarily a URL (e.g. from a QR code)
        is_primary_url = False
        if urls:
            # If the entire text is just a URL (allowing for whitespace/newlines)
            candidate = urls[0]
            if candidate.strip() == text.strip():
                is_primary_url = True

        avg_conf = ocr_result.avg_confidence if ocr_result else 0.0
        bbox = ocr_result.get_bounding_box() if ocr_result else (0, 0, 0, 0)

        result = ExtractionResult(
            text=text,
            raw_text=text,  # For now raw_text is same as text in this context
            urls=urls,
            emails=emails,
            phone_numbers=phone_numbers,
            avg_confidence=avg_conf,
            bounding_box=bbox,
            is_primary_url=is_primary_url
        )

        logger.debug(f"ResultDispatcher: Analyzed text. Primary URL: {is_primary_url}")
        return result


def get_result_dispatcher() -> ResultDispatcher:
    """Get the thread-safe ResultDispatcher singleton."""
    return get_instance(ResultDispatcher)
