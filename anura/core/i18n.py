# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import gettext
import locale
import os

from loguru import logger

from anura.config import APP_ID


def _glib_bindtextdomain(domain: str, localedir: str) -> None:
    """Bind the translation domain at the GLib/C-library level via ctypes."""
    import ctypes
    import ctypes.util

    try:
        try:
            _lib = ctypes.CDLL("libglib-2.0.so.0")
        except OSError:
            _libname = ctypes.util.find_library("glib-2.0") or ctypes.util.find_library("c")
            if not _libname:
                return
            _lib = ctypes.CDLL(_libname)

        _lib.bindtextdomain(domain.encode(), localedir.encode())
        _lib.bind_textdomain_codeset(domain.encode(), b"UTF-8")
        _lib.textdomain(domain.encode())
    except (OSError, AttributeError):
        pass


def setup_i18n():
    """Initialize localization."""
    project_name = APP_ID
    possible_localedirs = [
        "/app/share/locale",
        os.path.join(os.path.dirname(__file__), "..", "..", "builddir", "po"),
        os.path.join(os.path.dirname(__file__), "..", "..", "po"),
        "/usr/local/share/locale",
        "/usr/share/locale",
    ]

    localedir = None
    for path in possible_localedirs:
        if os.path.exists(path):
            localedir = path
            break

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error as e:
        logger.warning(f"locale.setlocale(LC_ALL, '') failed: {e}")

    if not localedir:
        return

    gettext.bindtextdomain(project_name, localedir)
    gettext.textdomain(project_name)

    try:
        locale.bindtextdomain(project_name, localedir)
        locale.textdomain(project_name)
        if hasattr(locale, "bind_textdomain_codeset"):
            locale.bind_textdomain_codeset(project_name, "UTF-8")
    except (AttributeError, OSError) as e:
        logger.warning(f"C-level locale binding failed: {e}")

    _glib_bindtextdomain(project_name, localedir)
    logger.debug(f"I18n initialized with localedir: {localedir}")
