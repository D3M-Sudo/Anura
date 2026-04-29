# settings.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# FIX: file moved from anura/settings.py to anura/services/settings.py
# All widgets import from `anura.services.settings` — the old path caused
# a ModuleNotFoundError at runtime inside the Flatpak sandbox.

from gi.repository import Gio
from loguru import logger

from anura.config import APP_ID


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


# Singleton instance
settings = Settings()
