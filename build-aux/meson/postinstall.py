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
from subprocess import call

# Meson sets these environment variables during the install process
prefix = os.environ.get('MESON_INSTALL_PREFIX', '/usr/local')
datadir = os.path.join(prefix, 'share')
destdir = os.environ.get('DESTDIR', '')

# Skip system updates if DESTDIR is set (usually for packaging like .deb or flatpak)
if not destdir:
    # Update Hicolor Icon Theme cache
    print('Anura: Updating icon cache...')
    call(['gtk-update-icon-cache', '-qtf', os.path.join(datadir, 'icons', 'hicolor')])

    # Update Desktop File database for Cinnamon menu integration
    print('Anura: Updating desktop database...')
    call(['update-desktop-database', '-q', os.path.join(datadir, 'applications')])

    # Compile GSettings XML schemas into gschemas.compiled
    # This must match the APP_ID: com.github.d3msudo.anura
    print('Anura: Compiling GSettings schemas...')
    call(['glib-compile-schemas', os.path.join(datadir, 'glib-2.0', 'schemas')])

    # Note: Ensure that the schema file com.github.d3msudo.anura.gschema.xml 
    # is actually installed in datadir/glib-2.0/schemas/