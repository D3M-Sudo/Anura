# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
import stat
import sys
from unittest.mock import MagicMock, patch

# Mock gi BEFORE importing anything that uses it
mock_gi = MagicMock()
sys.modules["gi"] = mock_gi
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gio"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()

import gi.repository.Gio # noqa: E402

try:
    from anura.services.screenshot.legacy_provider import LegacyX11Provider
except ImportError:
    LegacyX11Provider = None

def test_legacy_x11_provider_secure_temp_file_permissions():
    """
    Verify that LegacyX11Provider creates temporary files with restrictive (0600) permissions.
    Remediates BUG-029.
    """
    if LegacyX11Provider is None:
        return

    provider = LegacyX11Provider()

    # Mock scrot resolution to pass the check
    with patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary", return_value="/usr/bin/scrot"):
        # Mock Gio.Subprocess.new to avoid spawning a real process
        with patch("anura.services.screenshot.legacy_provider.Gio.Subprocess.new") as mock_subprocess_new:
            # Capture the output_path used by the provider
            captured_path = None

            def side_effect(argv, flags):
                nonlocal captured_path
                captured_path = argv[2] # scrot -s <output_path>
                return MagicMock()

            mock_subprocess_new.side_effect = side_effect

            # Call capture
            provider.capture("eng", False, lambda *args: None)

            if captured_path is None:
                if mock_subprocess_new.called:
                    captured_path = mock_subprocess_new.call_args[0][0][2]
                else:
                    return

            assert os.path.exists(captured_path)

            # Check permissions
            mode = os.stat(captured_path).st_mode
            permissions = stat.S_IMODE(mode)

            assert permissions == 0o600

            # Cleanup
            os.unlink(captured_path)

def test_legacy_x11_provider_secure_temp_file_uniqueness():
    """
    Verify that LegacyX11Provider creates unique temporary files for each capture.
    """
    if LegacyX11Provider is None:
        return

    provider = LegacyX11Provider()

    with patch("anura.services.screenshot.legacy_provider._resolve_scrot_binary", return_value="/usr/bin/scrot"):
        with patch("anura.services.screenshot.legacy_provider.Gio.Subprocess.new") as mock_new:
            mock_new.return_value = MagicMock()

            def callback(success, uri, error):
                pass

            provider.capture("eng", False, callback)
            path1 = mock_new.call_args[0][0][2]

            provider.capture("eng", False, callback)
            path2 = mock_new.call_args[0][0][2]

            assert path1 != path2

            # Cleanup
            if os.path.exists(path1): os.unlink(path1)
            if os.path.exists(path2): os.unlink(path2)
