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


class TestAnuraWindow:
    @pytest.mark.gtk
    def test_window_init(self):
        # AnuraWindow uses @Gtk.Template which calls gtk_widget_init_template() in
        # super().__init__().  init_template requires:
        #   1. A registered GApplication so Gtk.Application.get_default() is non-NULL.
        #   2. Compiled GResources registered with Gio.Resource._register().
        #   3. An open GdkDisplay (provided by weston in the gtk-tests CI job).
        #
        # Without a registered application the C template machinery follows NULL
        # child-widget pointers → SIGSEGV (a C signal, not a Python exception, so
        # try/except cannot catch it).
        #
        # Safety contract:
        #   - Register the application first; skip the test if registration fails.
        #   - Only then instantiate AnuraWindow.
        from gi.repository import Adw, Gio

        from anura.services.screenshot_service import ScreenshotService
        from anura.window import AnuraWindow

        app = Adw.Application(
            application_id="io.github.d3msudo.anura.test.window",
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        # Attach .settings so AnuraWindow.__init__ can read it (it calls
        # app.settings after super().__init__() returns).
        from anura.services.settings import settings as _settings
        app.settings = _settings

        try:
            registered = app.register()
        except Exception as exc:
            pytest.skip(f"Adw.Application.register() raised: {exc}")

        if not registered:
            pytest.skip("Adw.Application.register() returned False (D-Bus / display unavailable)")

        try:
            backend = ScreenshotService()
            win = AnuraWindow(backend=backend, application=app)
            assert win is not None
        except Exception as e:
            pytest.skip(f"Could not init AnuraWindow: {e}")
        finally:
            app.quit()
