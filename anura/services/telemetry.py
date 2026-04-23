# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (modifiche Anura)
# Distributed under the MIT License.

from typing import Any
from gi.repository import GObject

class TelemetryService(GObject.GObject):
    _gtype_name = 'TelemetryService'

    def __init__(self):
        super().__init__()
        self.posthog = None
        self.installation_id = None
        self.is_active = False

    def set_installation_id(self, installation_id: str):
        pass

    def set_is_active(self, is_active: bool):
        pass

    def capture(self, event: str, props: Any = None):
        # Telemetria disabilitata in Anura
        pass

    def capture_page_view(self, page_name: str):
        # Telemetria disabilitata in Anura
        pass

telemetry = TelemetryService()