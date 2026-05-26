# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
import os

from gi.repository import Gio, GLib
from loguru import logger


def load_gresource_bundle() -> bool:
    """Load the GResource bundle containing UI files and icons."""
    # Check if already registered
    with contextlib.suppress(GLib.Error):
        Gio.resources_lookup_data("/io/github/d3msudo/anura/window.ui", Gio.ResourceLookupFlags.NONE)
        return True

    possible_paths = [
        "/app/share/anura/io.github.d3msudo.anura.gresource",
        "/usr/share/anura/io.github.d3msudo.anura.gresource",
        "/usr/local/share/anura/io.github.d3msudo.anura.gresource",
        os.path.expanduser("~/.local/share/anura/io.github.d3msudo.anura.gresource"),
        os.path.join(os.path.dirname(__file__), "..", "..", "data", "io.github.d3msudo.anura.gresource"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                resource = Gio.Resource.load(path)
                Gio.resources_register(resource)
                logger.debug(f"GResource bundle loaded from: {path}")
                return True
            except (GLib.Error, RuntimeError) as e:
                logger.error(f"Failed to load GResource from {path}: {e}")
                continue

    return False
