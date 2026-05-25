# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import html
import os
import sys

# Bootstrap hardware and logging as early as possible
from anura.core.boot import boot_audit, setup_logging

boot_audit()
setup_logging()

from anura.core.i18n import setup_i18n

setup_i18n()

from gettext import gettext as _

import gi

# Set GTK version requirements before imports
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Notify", "0.7")
gi.require_version("Xdp", "1.0")
gi.require_version("Gst", "1.0")

from gi.repository import Adw, Gio, GLib
from loguru import logger

from anura.config import APP_ID
from anura.core.resources import load_gresource_bundle

# Load GResource before importing any widgets
if not load_gresource_bundle():
    print("CRITICAL: GResource bundle is required to run Anura. The application cannot start.", file=sys.stderr)
    sys.exit(1)

from anura.core.action_registry import ActionRegistry
from anura.core.dialogs import DialogManager
from anura.core.silent_runner import SilentRunner
from anura.language_manager import get_language_manager
from anura.services.clipboard_service import get_clipboard_service
from anura.services.notification_service import (
    HAS_LIBNOTIFY,
    NotificationService,
)
from anura.services.screenshot_service import ScreenshotService
from anura.services.settings import settings
from anura.utils import cleanup_orphaned_resources
from anura.utils.signal_manager import SignalManagerMixin
from anura.window import AnuraWindow


class AnuraApplication(Adw.Application, SignalManagerMixin):
    __gtype_name__ = "AnuraApplication"

    def __init__(self, version: str | None = None) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        SignalManagerMixin.__init__(self)
        self.backend: ScreenshotService | None = None
        self.version = version
        self.settings = settings
        self.notification_service = NotificationService(APP_ID)
        self._setup_options()

    def _setup_options(self) -> None:
        self.add_main_option(
            "extract_to_clipboard",
            ord("e"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            _("Extract directly into the clipboard"),
            None,
        )
        self.add_main_option(
            "file",
            ord("f"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.FILENAME,
            _("Process image file for OCR"),
            None,
        )
        self.add_main_option(
            "silent",
            ord("s"),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            _("Run OCR without UI (copy result to clipboard)"),
            None,
        )

    def do_startup(self, *args: object, **kwargs: object) -> None:
        Adw.init()
        Adw.Application.do_startup(self)

        active_lang = self.settings.get_string("active-language")
        cleanup_orphaned_resources(active_lang)

        self.backend = ScreenshotService()
        self.connect_tracked(self.backend, "decoded", self.on_decoded)
        self.connect_tracked(self.backend, "error", self.on_error)

        get_language_manager().init_tessdata()
        get_clipboard_service().init()

        ActionRegistry(self).setup_actions()

        GLib.set_application_name("Anura OCR")
        GLib.set_prgname(APP_ID)

    def do_shutdown(self, *args: object, **kwargs: object) -> None:
        self._cleanup_services()
        self.teardown_all()
        try:
            get_language_manager().shutdown()
        except Exception as e:
            logger.debug(f"Failed to shutdown LanguageManager: {e}")
        Adw.Application.do_shutdown(self)

    def _cleanup_services(self) -> None:
        if hasattr(self, "notification_service") and self.notification_service:
            self.notification_service.cleanup()
            try:
                if HAS_LIBNOTIFY:
                    from gi.repository import Notify

                    if Notify.is_initted():
                        Notify.uninit()
            except Exception:
                pass

        with contextlib.suppress(Exception):
            get_clipboard_service().cancel_pending_operations()

        with contextlib.suppress(Exception):
            from anura.services.tts import get_tts_service

            get_tts_service().cleanup()

    def do_activate(self) -> None:
        win = self.props.active_window
        if not win:
            if self.backend is None:
                self.backend = ScreenshotService()
            win = AnuraWindow(application=self, backend=self.backend)
        win.present()

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        options = command_line.get_options_dict().end().unpack()

        if "extract_to_clipboard" in options:
            return self._handle_extract_to_clipboard()
        if "file" in options:
            return self._handle_file_option(options["file"], "silent" in options)

        self.activate()
        return 0

    def _handle_extract_to_clipboard(self) -> int:
        if self.backend:
            self.backend.capture(self.settings.get_string("active-language"), copy=True)
            return 0
        return 1

    def _handle_file_option(self, file_path: str, is_silent: bool) -> int:
        if os.path.exists(file_path) and os.access(file_path, os.R_OK):
            if is_silent:
                return SilentRunner(self, file_path).run()
            self.activate()
            if self.props.active_window:
                self.props.active_window.process_file(file_path)
            return 0

        if not is_silent:
            self.activate()
            if self.props.active_window:
                self.props.active_window.open_image()
            return 0
        return 1

    def _decode_image_synchronously(self, file_path: str):
        if self.backend:
            return self.backend.decode_image_sync(self.settings.get_string("active-language"), file_path)
        return False, None, "Backend not initialized", None

    def _get_release_notes(self) -> str:
        """Get release notes from generated _release_notes module.

        Adw.AboutDialog parses the value as AppStream/Pango markup and rejects
        bare text (libxml: "The document must start with an element"). Wrap any
        non-element-leading content in <p> as a safety net so the Novità window
        always opens, even with stale or empty release notes.
        """
        notes: str | None = None
        try:
            from anura._release_notes import get_release_notes

            notes = get_release_notes()
        except Exception as e:
            logger.debug(f"Could not load release notes: {e}")

        if not notes or not notes.strip():
            notes = _("Bug fixes and improvements.")

        stripped = notes.lstrip()
        if not stripped.startswith("<"):
            # Bare text — wrap so libxml accepts it as a valid document
            notes = f"<p>{html.escape(notes)}</p>"
        return notes

    def on_preferences(self, *_) -> None:
        DialogManager.show_preferences(self.get_active_window())

    def on_about(self, *_) -> None:
        DialogManager.show_about(self.get_active_window(), self.version, self._get_release_notes())

    def on_github_star(self, *_) -> None:
        from anura.utils.validators import launch_uri

        launch_uri("https://github.com/D3M-Sudo/Anura", window=self.props.active_window)

    def on_report_issue(self, *_) -> None:
        from anura.utils.validators import launch_uri

        launch_uri("https://github.com/D3M-Sudo/Anura/issues", window=self.props.active_window)

    def on_shortcuts(self, *_) -> None:
        win = self.get_active_window()
        if win:
            win.show_shortcuts()

    def on_copy_to_clipboard(self, _, variant: GLib.Variant | None) -> None:
        win = self.get_active_window()
        if not win:
            return

        text = variant.get_string() if variant else ""
        if text:
            get_clipboard_service().set(text)
            win.show_toast(_("Text copied to clipboard"))
        elif hasattr(win, "_do_copy_to_clipboard"):
            win._do_copy_to_clipboard()

    def get_screenshot(self, *_) -> None:
        win = self.get_active_window()
        if win:
            win.get_screenshot()

    def get_screenshot_and_copy(self, *_) -> None:
        win = self.get_active_window()
        if win:
            win.get_screenshot(copy=True)

    def open_image(self, *_) -> None:
        win = self.get_active_window()
        if win and hasattr(win, "ocr_controller"):
            win.ocr_controller.open_image()

    def on_paste_from_clipboard(self, *_) -> None:
        win = self.props.active_window
        if win and hasattr(win, "welcome_page"):
            win.welcome_page.show_spinner()
        get_clipboard_service().read_texture()

    def _on_open_qr_notification(self, _, parameter: GLib.Variant | None) -> None:
        if parameter:
            from anura.utils.validators import launch_uri

            launch_uri(parameter.get_string().strip(), window=self.get_active_window())

    def on_decoded(self, _sender, text: str, copy: bool, ocr_result: object) -> None:
        if self.props.active_window:
            return

        from anura.services.result_dispatcher import get_result_dispatcher
        from anura.types.ocr import OcrResult

        result = get_result_dispatcher().dispatch(text, ocr_result if isinstance(ocr_result, OcrResult) else None)

        if not result.text:
            self.notification_service.show_notification(title=_("Anura OCR"), body=_("No text found."))
            return

        if self.settings.get_boolean("autocopy") or copy:
            get_clipboard_service().set(result.text)
            self.notification_service.show_notification(title=_("Anura OCR"), body=_("Text copied to clipboard."))
        else:
            self.notification_service.show_notification(title=_("Anura OCR"), body=_("Text extracted."))

    def on_error(self, _sender, message: str) -> None:
        if message and message != _("Cancelled"):
            GLib.idle_add(
                lambda: (
                    self.notification_service.show_notification(title=_("Anura OCR"), body=message)
                    or GLib.SOURCE_REMOVE
                )
            )

    def on_listen(self, *_) -> None:
        win = self.get_active_window()
        if win:
            win.on_listen()

    def on_listen_cancel(self, *_) -> None:
        win = self.get_active_window()
        if win:
            win.on_listen_cancel()

    def on_listen_pause(self, *_) -> None:
        win = self.get_active_window()
        if win:
            win.on_listen_pause()


import contextlib


def main(version: str) -> int:
    app = AnuraApplication(version)
    return app.run(sys.argv)
