# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from .mss_provider import MssScreenshotProvider
from .portal_provider import PortalProvider


class ScreenshotProviderFactory:
    """Factory for creating the appropriate screenshot providers.

    Returns a primary (Portal) and an optional fallback (mss/X11) provider.
    The fallback is only instantiated when on X11 (not Wayland), so
    ``get_fallback_provider()`` returns None safely on Wayland and headless environments.
    """

    @staticmethod
    def get_provider() -> PortalProvider:
        """Return the primary Portal-based provider."""
        return PortalProvider()

    @staticmethod
    def get_fallback_provider() -> MssScreenshotProvider | None:
        """Return the mss-based fallback provider if available, else None."""
        mss_provider = MssScreenshotProvider()
        return mss_provider if mss_provider.is_available() else None
