# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import tempfile

from anura.utils.validators import validate_image_resource


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
