# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
import stat
from unittest.mock import MagicMock, patch

import pytest

# Respect Pillar 2: skip if gi is missing and not mocked by conftest
pytest.importorskip("gi")

from anura.services.screenshot.legacy_provider import LegacyX11Provider


def test_legacy_x11_provider_secure_temp_file_permissions():
    """
    Verify that LegacyX11Provider creates temporary files with restrictive (0600) permissions.
    Remediates BUG-029.
    """
    provider = LegacyX11Provider()

    # Mock scrot resolution to pass the check
    with (
        patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary", return_value="/usr/bin/scrot"),
        patch("anura.services.screenshot.legacy_provider.Gio.Subprocess.new") as mock_subprocess_new,
    ):
        mock_subprocess_new.return_value = MagicMock()

        # Capture the output_path used by the provider
        captured_path = None

        def side_effect(argv, _flags):
            nonlocal captured_path
            captured_path = argv[2]  # scrot -s <output_path>
            return MagicMock()

        mock_subprocess_new.side_effect = side_effect

        # Call capture
        provider.capture("eng", False, lambda *args: None)

        if captured_path is None and mock_subprocess_new.called:
            # Fallback for some reason side_effect didn't capture it
            captured_path = mock_subprocess_new.call_args[0][0][2]

        assert captured_path is not None
        assert os.path.exists(captured_path)

        # Check permissions
        mode = os.stat(captured_path).st_mode
        permissions = stat.S_IMODE(mode)

        # Ensure it's 0600 (User read/write only)
        assert permissions == 0o600

        # Cleanup
        os.unlink(captured_path)


def test_legacy_x11_provider_secure_temp_file_uniqueness():
    """
    Verify that LegacyX11Provider creates unique temporary files for each capture.
    """
    provider = LegacyX11Provider()

    with (
        patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary", return_value="/usr/bin/scrot"),
        patch("anura.services.screenshot.legacy_provider.Gio.Subprocess.new") as mock_new,
    ):
        mock_new.return_value = MagicMock()

        def callback(success, uri, error):
            pass

        provider.capture("eng", False, callback)
        path1 = mock_new.call_args[0][0][2]

        provider.capture("eng", False, callback)
        path2 = mock_new.call_args[0][0][2]

        assert path1 != path2

        # Cleanup
        if os.path.exists(path1):
            os.unlink(path1)
        if os.path.exists(path2):
            os.unlink(path2)
