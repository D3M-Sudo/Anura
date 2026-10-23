# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""File-size pre-check before reading user-selected images (#509).

``process_file()`` used to call ``gfile.load_contents_async()`` first and pass
the loaded bytes to ``validate_image_resource()``, so a multi-gigabyte file
selected through the "All files" filter was read into memory before being
rejected. The metadata check must run first.
"""

from pathlib import Path


def _process_file_source() -> str:
    source = Path("anura/window.py").read_text(encoding="utf-8")
    start = source.index("def process_file")
    end = source.index("def _do_copy_to_clipboard")
    return source[start:end]


def test_process_file_validates_before_loading_contents():
    body = _process_file_source()

    assert "validate_image_resource(file_path)" in body
    assert body.index("validate_image_resource(file_path)") < body.index("gfile.load_contents_async(None")


def test_process_file_keeps_the_post_load_check():
    body = _process_file_source()

    # Defence in depth: the file can change between stat() and load.
    assert "validate_image_resource(contents)" in body


def test_oversized_file_is_rejected_by_the_metadata_check(tmp_path):
    from anura.config import MAX_IMAGE_SIZE_BYTES
    from anura.utils.validators import validate_image_resource

    oversized = tmp_path / "huge.bin"
    with open(oversized, "wb") as fh:
        fh.truncate(MAX_IMAGE_SIZE_BYTES + 1)

    is_valid, size, error = validate_image_resource(str(oversized))

    assert not is_valid
    assert size > MAX_IMAGE_SIZE_BYTES
    assert error is not None and "too large" in error
