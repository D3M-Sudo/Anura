# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from unittest.mock import patch

from anura.main import AnuraApplication
from anura.services.language_manager import LanguageManager


class TestLanguageManager:
    @pytest.mark.gtk
    def test_init_tessdata(self, tmp_path):
        tessdata = tmp_path / "tessdata"

        with (
            patch("anura.services.language_manager.TESSDATA_DIR", str(tessdata)),
            patch("anura.services.language_manager.TESSDATA_SYSTEM_DIR", str(tmp_path / "system")),
        ):
            lm = LanguageManager()
            lm.init_tessdata()
            assert tessdata.exists()

    @pytest.mark.gtk
    def test_get_language(self):
        lm = LanguageManager()
        assert lm.get_language("eng") == "English"
        assert lm.get_language("ita") == "Italian"
        assert lm.get_language("unknown") == "unknown"

    @pytest.mark.gtk
    def test_get_language_item(self):
        lm = LanguageManager()
        item = lm.get_language_item("eng")
        assert item.code == "eng"
        assert item.title == "English"
        assert lm.get_language_item("unknown") is None

    @pytest.mark.gtk
    def test_get_language_code(self):
        lm = LanguageManager()
        assert lm.get_language_code("English") == "eng"
        assert lm.get_language_code("Unknown") == "eng"  # Default fallback


class TestAnuraApplication:
    @pytest.mark.gtk
    def test_app_init(self):
        # We need a GResource for Anura to start, but we can mock it or just check init
        with patch("anura.main.Gio.Resource.load"):
            app = AnuraApplication()
            assert app.get_application_id() == "io.github.d3msudo.anura"


# NOTE: TestAnuraWindow.test_window_init was removed.
#
# AnuraWindow instantiation in a shared pytest-gtk session triggers a known
# PyGObject + Python ABC interaction bug:
#
#   gi/_gtktemplate.py::_extract_handler_and_args() calls
#   isinstance(gtk_widget_instance, collections.abc.Mapping).
#   Python's ABC __subclasshook__ recursion on certain GObject subclasses
#   causes an infinite __subclasscheck__ loop → GLib g_error() → SIGABRT
#   (exit 134).  SIGABRT is a C-level signal; it cannot be caught by
#   try/except and kills the entire pytest process.
#
# AnuraWindow integration is covered by:
#   - tests/test_stability.py::test_lifecycle_teardown_loop  (GTK, full lifecycle)
#   - tests/test_audit_ui_widgets.py                          (individual widgets)
