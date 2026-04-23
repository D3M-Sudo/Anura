# settings.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from gi.repository import Gio, GLib
from loguru import logger
from anura.config import APP_ID

class Settings(Gio.Settings):
    """
    Core settings service for Anura.
    Handles GSettings interaction using the rebranded Application ID.
    """
    __gtype_name__ = 'AnuraSettings'

    def __init__(self, **kwargs):
        # Verifica se lo schema esiste prima di inizializzare per evitare crash fatali
        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source.lookup(APP_ID, True):
            super().__init__(schema_id=APP_ID, **kwargs)
        else:
            logger.error(f"GSettings schema {APP_ID} non trovato. Assicurarsi di aver compilato gli schemi.")
            # Fallback o gestione errore qui se necessario

# Singleton instance
settings = Settings()