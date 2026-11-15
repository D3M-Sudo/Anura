# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from pathlib import Path

from gi.repository import Gio, GLib
from loguru import logger


def load_gresource_bundle() -> bool:
    """Load the GResource bundle containing UI files and icons."""
    # Check if already registered
    with contextlib.suppress(GLib.Error):
        Gio.resources_lookup_data("/io/github/d3msudo/anura/window.ui", Gio.ResourceLookupFlags.NONE)
        return True

    possible_paths = [
        Path("/app/share/anura/io.github.d3m_sudo.anura.gresource"),
        Path("/usr/share/anura/io.github.d3m_sudo.anura.gresource"),
        Path("/usr/local/share/anura/io.github.d3m_sudo.anura.gresource"),
        Path.home() / ".local" / "share" / "anura" / "io.github.d3m_sudo.anura.gresource",
        Path(__file__).parent.parent.parent / "data" / "io.github.d3m_sudo.anura.gresource",
    ]

    for path in possible_paths:
        if path.exists():
            try:
                resource = Gio.Resource.load(str(path))
                Gio.resources_register(resource)
                logger.debug(f"GResource bundle loaded from: {path}")
                return True
            except (GLib.Error, RuntimeError) as e:
                logger.error(f"Failed to load GResource from {path}: {e}")
                continue

    return False


def load_css_provider():
    """Load and register the application stylesheet for the active GTK display.

    Returns None when GTK is running without a display (for example, a
    headless CLI invocation). The caller must retain the returned provider
    while the application is running.
    """
    from gi.repository import Gdk, Gtk

    display = Gdk.Display.get_default()
    if display is None:
        logger.debug("No GDK display available; skipping application stylesheet registration")
        return None

    provider = Gtk.CssProvider()
    provider.load_from_resource("/io/github/d3msudo/anura/style.css")
    Gtk.StyleContext.add_provider_for_display(display, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    logger.debug("Registered application stylesheet from GResource")
    return provider
