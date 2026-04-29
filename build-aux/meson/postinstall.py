#!/usr/bin/env python3
#
# postinstall.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# Standard post-installation script for Meson build system.
# Updates system databases to recognize Anura's icons, schemas, and desktop files.

import os
import sys
from subprocess import run

# Meson sets these environment variables during the install process
prefix = os.environ.get('MESON_INSTALL_PREFIX', '/usr/local')
datadir = os.path.join(prefix, 'share')
destdir = os.environ.get('DESTDIR', '')

def run_or_fail(cmd: list, description: str) -> None:
    """Execute a command and exit on failure."""
    result = run(cmd, capture_output=True)
    if result.returncode != 0:
        print(f"ERROR: {description} failed with exit code {result.returncode}", file=sys.stderr)
        if result.stderr:
            print(f"stderr: {result.stderr.decode()}", file=sys.stderr)
        sys.exit(result.returncode)

# Skip system updates if DESTDIR is set (usually for packaging like .deb or flatpak)
if not destdir:
    # Update Hicolor Icon Theme cache
    print('Anura: Updating icon cache...')
    run_or_fail(
        ['gtk-update-icon-cache', '-qtf', os.path.join(datadir, 'icons', 'hicolor')],
        "Icon cache update"
    )

    # Update Desktop File database (XDG standard, distro-agnostic)
    print('Anura: Updating desktop database...')
    run_or_fail(
        ['update-desktop-database', '-q', os.path.join(datadir, 'applications')],
        "Desktop database update"
    )

    # Compile GSettings XML schemas into gschemas.compiled
    # This must match the APP_ID: com.github.d3msudo.anura
    print('Anura: Compiling GSettings schemas...')
    run_or_fail(
        ['glib-compile-schemas', os.path.join(datadir, 'glib-2.0', 'schemas')],
        "GSettings schema compilation"
    )
