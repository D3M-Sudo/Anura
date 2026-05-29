# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from anura.utils.singleton import get_instance

from .legacy_provider import LegacyX11Provider
from .portal_provider import PortalProvider


class ScreenshotProviderFactory:
    """Factory for creating the appropriate screenshot providers.

    Returns a primary (Portal) and an optional fallback (X11/scrot) provider.
    Maintains singleton instances for consistent resource management.
    """

    _provider: PortalProvider | None = None
    _fallback_provider: LegacyX11Provider | None = None

    @staticmethod
    def get_provider() -> PortalProvider:
        """Return the primary Portal-based provider singleton."""
        return get_instance(PortalProvider)

    @staticmethod
    def get_fallback_provider() -> LegacyX11Provider | None:
        """Return the X11/scrot fallback provider singleton if available, else None."""
        legacy = get_instance(LegacyX11Provider)
        return legacy if legacy.is_available() else None
