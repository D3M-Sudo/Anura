# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

# BUG-035 — Dynamic URI scheme validation in ShareService._validate_share_url
#
# Root cause: _validate_share_url previously used a static whitelist only,
# blocking legitimate app-protocol URIs (tg://, slack://, zoommtg://) when no
# handler was registered.  The fix adds a Gio.AppInfo.get_default_for_uri_scheme
# dynamic check AFTER the is_safe_url_string security gate.
#
# Test strategy: import ShareService after gi is available, then patch
# anura.services.share_service.Gio (module-level name) and sys.modules
# ["gi.repository.Gio"] (covers the inline `from gi.repository import Gio`
# inside _validate_share_url) to control dynamic handler lookups.
#
# Marker: @pytest.mark.gtk — routed to the gtk-tests CI job which installs
# python3-gi and libadwaita-1-dev before running.

import sys
from unittest.mock import MagicMock, patch

import pytest

gi = pytest.importorskip("gi")

# libadwaita may be absent in some environments; skip gracefully.
try:
    gi.require_version("Adw", "1")
    gi.require_version("Gio", "2.0")
    gi.require_version("GLib", "2.0")
    gi.require_version("GObject", "2.0")
    gi.require_version("Gtk", "4.0")
    from anura.services.share_service import ShareService
except (ValueError, ImportError) as _e:
    pytest.skip(f"GTK/Adw not available: {_e}", allow_module_level=True)


class TestBug035Remediation:
    """Unit tests for BUG-035 remediation (dynamic URI scheme validation)."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _gio_mock(has_handler: bool) -> MagicMock:
        """Return a Gio mock with AppInfo configured per has_handler."""
        m = MagicMock()
        m.AppInfo.get_default_for_uri_scheme.return_value = (
            MagicMock() if has_handler else None
        )
        return m

    def _patch_gio(self, mock_gio: MagicMock):
        """Patch both the module-level name and sys.modules (inline import)."""
        return [
            patch("anura.services.share_service.Gio", mock_gio),
            patch.dict(sys.modules, {"gi.repository.Gio": mock_gio}),
        ]

    # ------------------------------------------------------------------
    # Parametrised — validate_share_url logic
    # ------------------------------------------------------------------

    @pytest.mark.gtk
    @pytest.mark.parametrize(
        "url, has_handler, expected",
        [
            # Custom-app schemes — handler registered
            ("tg://share?text=hello", True, True),
            ("slack://open", True, True),
            ("zoommtg://join", True, True),
            # Custom-app schemes — no handler, whitelist decides
            ("tg://share?text=hello", False, True),    # tg in whitelist
            ("slack://open", False, True),              # slack in whitelist
            ("zoommtg://join", False, False),           # zoommtg NOT in whitelist
            # Whitelist-only schemes (no dynamic check needed)
            ("mailto:test@example.com", False, True),
            ("web+mastodon://share", False, True),
            # Standard web URL — goes through uri_validator
            ("https://google.com", False, True),
            # Completely invalid scheme — no handler, not in whitelist
            ("invalid-scheme://test", False, False),
        ],
    )
    def test_validate_share_url_logic(self, url: str, has_handler: bool, expected: bool) -> None:
        """_validate_share_url must pass the security gate then resolve via dynamic check or whitelist."""
        mock_gio = self._gio_mock(has_handler)
        patches = self._patch_gio(mock_gio)
        for p in patches:
            p.start()
        try:
            result = ShareService._validate_share_url(url)
        finally:
            for p in patches:
                p.stop()
        assert result == expected, (
            f"URL={url!r}  has_handler={has_handler}  expected={expected}  got={result}"
        )

    # ------------------------------------------------------------------
    # Exception handling — Gio raises at runtime
    # ------------------------------------------------------------------

    @pytest.mark.gtk
    def test_validate_share_url_gio_exception_falls_back_to_whitelist(self) -> None:
        """When Gio.AppInfo raises, validation falls back to the scheme whitelist."""
        mock_gio = MagicMock()
        mock_gio.AppInfo.get_default_for_uri_scheme.side_effect = RuntimeError("Gio error")

        patches = self._patch_gio(mock_gio)
        for p in patches:
            p.start()
        try:
            assert ShareService._validate_share_url("tg://test") is True       # tg in whitelist
            assert ShareService._validate_share_url("unknown://test") is False  # not in whitelist
        finally:
            for p in patches:
                p.stop()

    # ------------------------------------------------------------------
    # Security gate — is_safe_url_string must run first
    # ------------------------------------------------------------------

    @pytest.mark.gtk
    def test_security_check_gates_before_dynamic_lookup(self) -> None:
        """is_safe_url_string returning False must block validation regardless of Gio."""
        mock_gio = self._gio_mock(has_handler=True)  # handler exists — must NOT matter

        patches = self._patch_gio(mock_gio) + [
            patch("anura.services.share_service.is_safe_url_string", return_value=False),
        ]
        for p in patches:
            p.start()
        try:
            assert ShareService._validate_share_url("tg://test") is False
        finally:
            for p in patches:
                p.stop()

        # Gio must never have been consulted
        mock_gio.AppInfo.get_default_for_uri_scheme.assert_not_called()

    # ------------------------------------------------------------------
    # HTTP/HTTPS — goes through uri_validator, not dynamic check
    # ------------------------------------------------------------------

    @pytest.mark.gtk
    def test_http_url_uses_uri_validator(self) -> None:
        """HTTP/HTTPS URLs must be validated by uri_validator, not Gio."""
        mock_gio = self._gio_mock(has_handler=False)

        patches = self._patch_gio(mock_gio) + [
            patch("anura.services.share_service.uri_validator", return_value=True),
        ]
        for p in patches:
            p.start()
        try:
            result = ShareService._validate_share_url("https://example.com")
        finally:
            for p in patches:
                p.stop()

        assert result is True
        mock_gio.AppInfo.get_default_for_uri_scheme.assert_not_called()
