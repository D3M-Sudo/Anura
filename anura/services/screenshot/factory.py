# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from .legacy_provider import LegacyX11Provider
from .portal_provider import PortalProvider


class ScreenshotProviderFactory:
    """Factory for creating the appropriate screenshot providers.

    Returns a primary (Portal) and an optional fallback (X11/scrot) provider.
    The fallback is only instantiated when scrot is reachable and the session
    is on X11 (not Wayland), so ``get_fallback_provider()`` returns None safely
    on Wayland and headless environments.
    """

    @staticmethod
    def get_provider() -> PortalProvider:
        """Return the primary Portal-based provider."""
        return PortalProvider()

    @staticmethod
    def get_fallback_provider() -> LegacyX11Provider | None:
        """Return the X11/scrot fallback provider if available, else None."""
        legacy = LegacyX11Provider()
        return legacy if legacy.is_available() else None
