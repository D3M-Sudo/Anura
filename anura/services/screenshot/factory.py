# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from .portal_provider import PortalProvider
from .legacy_provider import LegacyX11Provider

class ScreenshotProviderFactory:
    """Factory for creating the appropriate screenshot provider."""

    @staticmethod
    def get_provider():
        portal = PortalProvider()
        # In a real environment detection we might test portal availability via DBus
        # For now, Portal is always preferred.
        return portal

    @staticmethod
    def get_fallback_provider():
        legacy = LegacyX11Provider()
        if legacy.is_available():
            return legacy
        return None
