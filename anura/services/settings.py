# settings.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# Settings module - moved from anura/settings.py to anura/services/settings.py
# to avoid ModuleNotFoundError in Flatpak sandbox.

from gi.repository import Gio
from loguru import logger

# Inline APP_ID to avoid circular import with config.py
# This ensures settings can be imported independently
APP_ID = "com.github.d3msudo.anura"


class Settings(Gio.Settings):
    """
    Core settings service for Anura.
    Handles GSettings interaction using the rebranded Application ID.
    """

    __gtype_name__ = "AnuraSettings"

    def __init__(self, **kwargs):
        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source and schema_source.lookup(APP_ID, True):
            super().__init__(schema_id=APP_ID, **kwargs)
        else:
            logger.error(
                f"GSettings schema '{APP_ID}' not found. "
                "Make sure glib-compile-schemas has been run."
            )
            raise RuntimeError(f"GSettings schema '{APP_ID}' not found.")


class _LazySettings:
    """
    Lazy initializer for Settings singleton.
    Allows CLI-only operation without GSettings being available at import time.
    Settings are only initialized when first accessed.
    """

    _instance: Settings | None = None

    def _get_instance(self) -> Settings:
        if self._instance is None:
            self._instance = Settings()
        return self._instance

    def __getattr__(self, name):
        """Delegate all attribute access to the actual Settings instance."""
        return getattr(self._get_instance(), name)


# Lazy singleton - Settings only initialized on first access
settings = _LazySettings()
