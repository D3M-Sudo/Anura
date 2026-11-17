# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Decoded-image pixel budget (#522).

A highly compressed image can stay under the 50 MiB byte limit while decoding
to a bitmap far larger than the machine can hold. These tests pin the budget
and the fact that both OCR paths consult it before decoding.
"""

from io import BytesIO
from pathlib import Path
import struct
import zlib

from PIL import Image
import pytest

from anura.config import MAX_IMAGE_PIXELS
from anura.utils.validators import validate_image_dimensions

_MAX_SIDE = 65_535


def _png_header_only(width: int, height: int) -> bytes:
    """Build a PNG with a valid IHDR declaring the given size and no pixel data.

    Pillow parses the header on ``Image.open()`` without allocating the bitmap,
    which is exactly the property the production check relies on.
    """
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    chunk = struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr
    chunk += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk + b"\x00\x00\x00\x00IEND\xaeB`\x82"


def test_header_dimensions_are_readable_without_decoding():
    with Image.open(BytesIO(_png_header_only(7000, 6000))) as img:
        assert img.size == (7000, 6000)


def test_oversized_header_is_rejected_by_the_budget():
    with Image.open(BytesIO(_png_header_only(7000, 6000))) as img:
        is_valid, error = validate_image_dimensions(*img.size)

    assert not is_valid
    assert error is not None
    assert "42.0MP" in error


def test_normal_dimensions_are_accepted():
    assert validate_image_dimensions(1920, 1080) == (True, None)


def test_exact_budget_is_accepted():
    width = 8000
    height = MAX_IMAGE_PIXELS // width
    assert width * height == MAX_IMAGE_PIXELS

    assert validate_image_dimensions(width, height) == (True, None)


def test_one_pixel_over_budget_is_rejected():
    width = 8000
    height = (MAX_IMAGE_PIXELS // width) + 1

    is_valid, error = validate_image_dimensions(width, height)

    assert not is_valid
    assert error is not None


@pytest.mark.parametrize(("width", "height"), [(0, 100), (100, 0), (-1, 100)])
def test_invalid_dimensions_are_rejected(width, height):
    is_valid, error = validate_image_dimensions(width, height)

    assert not is_valid
    assert error == "Invalid image dimensions"


def test_both_ocr_paths_consult_the_budget():
    source = Path("anura/services/screenshot_service.py").read_text(encoding="utf-8")

    # One call in the isolated worker (run_ocr_pipeline), one in the synchronous
    # path (_process_image_decode). Removing either re-opens the bomb path.
    assert source.count("validate_image_dimensions(*") == 2


def test_clipboard_decode_consults_the_budget():
    source = Path("anura/services/clipboard_service.py").read_text(encoding="utf-8")

    assert "validate_image_dimensions(*img.size)" in source
