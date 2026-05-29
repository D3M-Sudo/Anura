# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import threading
from typing import Any

import gi

# Set GTK version requirements before imports
gi.require_version("Gio", "2.0")

from gi.repository import Gio  # noqa: E402
from loguru import logger  # noqa: E402

from anura.utils.singleton import get_instance  # noqa: E402

# Inline APP_ID to avoid circular import with config.py
# This ensures settings can be imported independently
APP_ID = "io.github.d3msudo.anura"


class Settings(Gio.Settings):
    """
    Core settings service for Anura.
    Handles GSettings interaction using the rebranded Application ID.
    """

    __gtype_name__ = "AnuraSettings"

    def __init__(self, **kwargs: object) -> None:
        schema_source = Gio.SettingsSchemaSource.get_default()
        if schema_source and schema_source.lookup(APP_ID, True):
            super().__init__(schema_id=APP_ID, **kwargs)
        else:
            logger.error(
                f"GSettings schema '{APP_ID}' not found. Make sure glib-compile-schemas has been run.",
            )
            raise RuntimeError(f"GSettings schema '{APP_ID}' not found.")


class _SettingsProxy:
    """
    Proxy for the Settings singleton that handles lazy initialization.
    Allows CLI-only operation without GSettings being available at import time.
    """

    def __getattr__(self, name: str) -> Any:
        """Delegate all attribute access to the thread-safe Settings singleton."""
        return getattr(get_instance(Settings), name)


# Lazy singleton proxy - Settings only initialized on first access
settings = _SettingsProxy()
