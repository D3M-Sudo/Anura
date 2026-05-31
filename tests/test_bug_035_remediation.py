# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest
from unittest.mock import MagicMock, patch
import sys
import re

# We use a trick to test the static method without loading the whole GObject-based module
# which might fail in headless environments or due to mock conflicts.

def get_validate_share_url():
    with open("anura/services/share_service.py", "r") as f:
        content = f.read()

    # Extract _validate_share_url method
    match = re.search(r"    @staticmethod\s+def _validate_share_url\(url: str\) -> bool:.*?(?=\s+def share)", content, re.DOTALL)
    if not match:
        raise RuntimeError("Could not find _validate_share_url in share_service.py")

    method_code = match.group(0)
    # Remove indentation
    method_code = "\n".join([line[4:] if line.startswith("    ") else line for line in method_code.splitlines()])

    # Mock dependencies
    test_ns = {
        "is_safe_url_string": MagicMock(return_value=True),
        "uri_validator": MagicMock(side_effect=lambda u: u.startswith("http")),
    }

    # Execute the method definition in the namespace
    exec(method_code, test_ns)
    return test_ns["_validate_share_url"], test_ns

class TestBug035Remediation:
    """
    Unit tests for BUG-035 remediation (dynamic URI scheme validation).
    """

    @pytest.fixture
    def mock_gio(self):
        """Setup mock for gi.repository.Gio used in the inline import."""
        mock_gio = MagicMock()
        repo_mock = MagicMock()
        repo_mock.Gio = mock_gio

        with patch.dict(sys.modules, {
            "gi": MagicMock(),
            "gi.repository": repo_mock
        }):
            yield mock_gio

    def test_validate_share_url_logic(self, mock_gio):
        _validate_share_url, test_ns = get_validate_share_url()

        # Test 1: Handler exists (Dynamic detection)
        mock_gio.AppInfo.get_default_for_uri_scheme.return_value = "handler"
        assert _validate_share_url("tg://test") is True
        mock_gio.AppInfo.get_default_for_uri_scheme.assert_called_with("tg")

        # Test 2: No handler, but in whitelist
        mock_gio.AppInfo.get_default_for_uri_scheme.return_value = None
        assert _validate_share_url("slack://test") is True

        # Test 3: No handler, NOT in whitelist
        mock_gio.AppInfo.get_default_for_uri_scheme.return_value = None
        assert _validate_share_url("unknown-app://test") is False

        # Test 4: Dynamic detection for non-whitelisted app
        mock_gio.AppInfo.get_default_for_uri_scheme.return_value = "some-handler"
        assert _validate_share_url("new-app://test") is True

        # Test 5: Standard HTTP/HTTPS
        assert _validate_share_url("https://google.com") is True
        assert _validate_share_url("http://localhost") is True

    def test_validate_share_url_exception_handling(self, mock_gio):
        _validate_share_url, test_ns = get_validate_share_url()

        # Test: Gio raises exception, fallback to whitelist
        mock_gio.AppInfo.get_default_for_uri_scheme.side_effect = RuntimeError("Gio error")

        # 'whatsapp' is in whitelist
        assert _validate_share_url("whatsapp://test") is True
        # 'evil' is not
        assert _validate_share_url("evil://test") is False

    def test_security_check_precedence(self, mock_gio):
        _validate_share_url, test_ns = get_validate_share_url()
        test_ns["is_safe_url_string"].return_value = False

        # Should be false even if handler exists
        mock_gio.AppInfo.get_default_for_uri_scheme.return_value = "handler"
        assert _validate_share_url("tg://test") is False
