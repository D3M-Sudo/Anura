# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Tesseract execution is bounded in time (#533).

The OCR process pool has a single worker: an unbounded ``image_to_data()`` call
keeps that worker busy forever, queues every later request behind it, and cannot
be interrupted by the cooperative cancellation checks that surround it.
"""

from pathlib import Path

from anura.config import OCR_TIMEOUT_SECONDS


def test_timeout_is_a_positive_budget():
    assert isinstance(OCR_TIMEOUT_SECONDS, int)
    assert 0 < OCR_TIMEOUT_SECONDS <= 600


def test_both_tesseract_calls_pass_the_timeout():
    source = Path("anura/services/screenshot_service.py").read_text(encoding="utf-8")

    calls = source.count("pytesseract.image_to_data(")
    timeouts = source.count("timeout=OCR_TIMEOUT_SECONDS")

    # One call in the isolated worker, one in the synchronous path.
    assert calls == 2
    assert timeouts == 2


def test_timeout_is_translated_into_a_user_facing_error():
    source = Path("anura/services/screenshot_service.py").read_text(encoding="utf-8")

    assert "class OcrTimeoutError" in source
    assert "isinstance(e, OcrTimeoutError)" in source
    assert "raise OcrTimeoutError" in source
    # The timeout must not be swallowed by the generic RuntimeError branch.
    assert "except OcrTimeoutError:" in source
