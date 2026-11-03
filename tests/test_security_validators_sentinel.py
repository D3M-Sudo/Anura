# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import tempfile

from anura.utils.validators import is_local_or_private_url, validate_image_resource


def test_validate_image_resource_rejects_directory():
    """
    Security Test: Ensure that validate_image_resource rejects directory paths.
    Using os.path.isfile() instead of os.path.exists() prevents processing
    directories as image files, which could cause unexpected behavior.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Pass the directory path itself
        is_valid, size, error = validate_image_resource(tmp_dir)

        assert is_valid is False
        assert size == 0
        assert error == "File not found"


def test_validate_image_resource_accepts_regular_file():
    """
    Verify that validate_image_resource still accepts regular files.
    """
    with tempfile.NamedTemporaryFile(suffix=".png") as tmp_file:
        tmp_file.write(b"dummy image data")
        tmp_file.flush()

        is_valid, size, error = validate_image_resource(tmp_file.name)

        assert is_valid is True
        assert size > 0
        assert error is None



def test_local_or_private_url_rejects_legacy_ipv4_notation() -> None:
    for url in (
        "http://127.1/",
        "http://127.0.1/",
        "http://0x7f.0.0.1/",
        "http://0177.0.0.1/",
        "http://10.1/",
    ):
        assert is_local_or_private_url(url) is True


def test_local_or_private_url_keeps_public_ipv4_public() -> None:
    assert is_local_or_private_url("https://8.8.8.8/") is False
