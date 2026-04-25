# telemetry.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# Telemetry is fully disabled in Anura (privacy-first fork of Frog).
# This stub satisfies any remaining call sites without any data transmission.

from typing import Any

from gi.repository import GObject


class TelemetryService(GObject.GObject):
    # FIX: was `_gtype_name` (single underscore) — GObject silently ignored it.
    # Correct dunder attribute is `__gtype_name__` (double underscore on each side).
    __gtype_name__ = "TelemetryService"

    def __init__(self):
        super().__init__()
        self.posthog = None
        self.installation_id = None
        self.is_active = False

    def set_installation_id(self, installation_id: str):
        pass  # Telemetry disabled in Anura

    def set_is_active(self, is_active: bool):
        pass  # Telemetry disabled in Anura

    def capture(self, event: str, props: Any = None):
        pass  # Telemetry disabled in Anura

    def capture_page_view(self, page_name: str):
        pass  # Telemetry disabled in Anura


telemetry = TelemetryService()
