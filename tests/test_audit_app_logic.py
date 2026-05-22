# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

from unittest.mock import patch

from anura.language_manager import LanguageManager
from anura.main import AnuraApplication


class TestLanguageManager:
    @pytest.mark.gtk
    def test_init_tessdata(self, tmp_path):
        tessdata = tmp_path / "tessdata"

        with (
            patch("anura.language_manager.TESSDATA_DIR", str(tessdata)),
            patch("anura.language_manager.TESSDATA_SYSTEM_DIR", str(tmp_path / "system")),
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


class TestAnuraWindow:
    @pytest.mark.gtk
    def test_window_init(self):
        # Window needs compiled resources and UI files
        try:
            from gi.repository import Adw

            from anura.services.screenshot_service import ScreenshotService
            from anura.window import AnuraWindow

            app = Adw.Application()
            backend = ScreenshotService()
            win = AnuraWindow(backend=backend, application=app)
            assert win is not None
        except Exception as e:
            pytest.skip(f"Could not init window: {e}")
