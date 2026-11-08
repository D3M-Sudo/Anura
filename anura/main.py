# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
import html
import os
from pathlib import Path
import sys

# Bootstrap hardware and logging as early as possible
from anura.core.boot import boot_audit
from anura.core.logger import setup_logging

boot_audit()
setup_logging()

from anura.core.i18n import setup_i18n

setup_i18n()

from gettext import gettext as _

import gi

# Set GTK version requirements before imports
gi.require_version("Gtk", "4.0")
gi.require_version("GtkSource", "5")
gi.require_version("Adw", "1")
gi.require_version("Notify", "0.7")
gi.require_version("Xdp", "1.0")
gi.require_version("Gst", "1.0")

from gi.repository import Adw, Gio, GLib, Gtk, GtkSource
from loguru import logger

from anura.config import APP_ID, XDG_DATA_HOME
from anura.core.resources import load_gresource_bundle

# Load GResource before importing any widgets
if not load_gresource_bundle():
    logger.critical("GResource bundle is required to run Anura. The application cannot start.")
    sys.exit(1)

from anura.core.action_registry import ActionRegistry
from anura.core.dialogs import DialogManager
from anura.core.silent_runner import SilentRunner
from anura.services.clipboard_service import get_clipboard_service
from anura.services.language_manager import get_language_manager
from anura.services.legacy_flatpak_migration import (
    MIGRATION_MARKER,
    mark_legacy_flatpak_migration_skipped,
    migrate_legacy_flatpak_data,
)
from anura.services.notification_service import (
    HAS_LIBNOTIFY,
    get_notification_service,
)
from anura.services.screenshot_service import ScreenshotService, get_screenshot_service
from anura.services.settings import settings
from anura.utils import cleanup_orphaned_resources, is_local_or_private_url
from anura.utils.signal_manager import SignalManagerMixin
from anura.utils.singleton import get_existing_instance
from anura.utils.validators import launch_uri
from anura.window import AnuraWindow


class AnuraApplication(Adw.Application, SignalManagerMixin):
    __gtype_name__ = "AnuraApplication"

    def __init__(self, version: str | None = None) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)  # type: ignore[call-arg]
        SignalManagerMixin.__init__(self)
        self.backend: ScreenshotService | None = None
        self.version = version
        self._legacy_migration_pending = False
        self._activate_after_legacy_migration = False
        self._legacy_migration_hold = False
        self._legacy_migration_chooser: Gtk.FileChooserNative | None = None
        self._runtime_services_initialized = False
        self.settings = settings
        # Use the same singleton the controllers use (#537): OcrController
        # obtains notifications through get_notification_service(), so a
        # separate instance here meant shutdown cleaned up an object that never
        # owned the portal notification IDs.
        self.notification_service = get_notification_service()
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
        # GtkSourceView must register its widget GTypes before Gtk.Template
        # instantiates ExtractedPage from the compiled Blueprint resource.
        GtkSource.init()
        Adw.Application.do_startup(self)

        self._apply_color_scheme()
        self.settings.connect("changed::color-scheme", self._on_color_scheme_changed)

        active_lang = self.settings.get_string("active-language")
        cleanup_orphaned_resources(active_lang)

        self.backend = get_screenshot_service()
        # Signals are now coordinated via OcrController in AnuraWindow for GUI mode.
        # on_decoded and on_error are maintained for Headless/Silent mode entry points.
        self.connect_tracked(self.backend, "decoded", self.on_decoded)
        self.connect_tracked(self.backend, "error", self.on_error)

        get_clipboard_service().init()

        ActionRegistry(self).setup_actions()

        GLib.set_application_name("Anura OCR")
        GLib.set_prgname(APP_ID)

        # A Flatpak cannot inspect another app's private data directory. Offer
        # a portal-backed folder selection on the first normal GUI launch.
        # CLI/silent invocations remain non-interactive.
        marker = Path(XDG_DATA_HOME) / MIGRATION_MARKER
        if Path("/.flatpak-info").is_file() and len(sys.argv) == 1 and not marker.is_file():
            self._legacy_migration_pending = True
            self.hold()
            self._legacy_migration_hold = True
            try:
                self._show_legacy_migration_prompt()
            except (GLib.Error, RuntimeError) as exc:
                logger.exception(f"Could not show the legacy data migration prompt: {exc}")
                self._finish_legacy_migration()
        else:
            self._initialize_runtime_services()

    def do_shutdown(self, *args: object, **kwargs: object) -> None:
        if self.backend:
            with contextlib.suppress(Exception):
                self.backend.do_destroy()

        self._cleanup_services()
        self.teardown_all()
        try:
            get_language_manager().shutdown()
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"Failed to shutdown LanguageManager: {e}")

        from anura.core.atomic_task_manager import get_atomic_manager

        get_atomic_manager().shutdown()

        Adw.Application.do_shutdown(self)

    def _cleanup_services(self) -> None:
        if hasattr(self, "notification_service") and self.notification_service:
            self.notification_service.cleanup()
            try:
                if HAS_LIBNOTIFY:
                    from gi.repository import Notify

                    if Notify.is_initted():
                        Notify.uninit()
            except (AttributeError, RuntimeError) as e:
                logger.error(f"Failed to uninitialize Notify service: {e}")

        with contextlib.suppress(Exception):
            get_clipboard_service().cancel_pending_operations()

        # #536: clean up TTS only if it was actually used. The lazy getter used
        # to construct TTSService — and start a network fetch of the Google
        # language catalog — during shutdown of a silent CLI run that never
        # touched TTS.
        try:
            from anura.services.tts.service import TTSService

            tts_service = get_existing_instance(TTSService)
            if tts_service is not None:
                tts_service.cleanup()
        except (AttributeError, RuntimeError, OSError) as e:
            logger.debug(f"Failed to clean up TTS service: {e}")

    def _initialize_runtime_services(self) -> None:
        """Initialize services that consume persistent OCR data, exactly once."""
        if self._runtime_services_initialized:
            return
        get_language_manager().init_tessdata()
        self._runtime_services_initialized = True

    def _show_legacy_migration_prompt(self) -> None:
        # GtkFileChooserNative is portal-backed in Flatpak. A parent window is
        # optional here because startup must wait for the selection before the
        # normal application window (and OCR model discovery) is initialized.
        chooser = Gtk.FileChooserNative.new(
            _("Select the previous Anura data folder to import history and OCR models"),
            None,
            Gtk.FileChooserAction.SELECT_FOLDER,
            _("Import"),
            _("Not now"),
        )
        chooser.connect("response", self._on_legacy_migration_folder_response)
        self._legacy_migration_chooser = chooser
        chooser.show()

    def _on_legacy_migration_folder_response(self, chooser, response: int) -> None:
        if not self._legacy_migration_pending:
            return

        try:
            if response == Gtk.ResponseType.ACCEPT:
                selected = chooser.get_file()
                selected_path = selected.get_path() if selected else None
                if selected_path:
                    if not migrate_legacy_flatpak_data(old_data_dir=Path(selected_path)):
                        logger.warning("Legacy Anura data was not imported. The migration prompt will be shown again.")
                else:
                    logger.warning("The selected legacy data folder has no local portal path.")
            else:
                if not mark_legacy_flatpak_migration_skipped():
                    logger.warning("Could not persist the decision to skip legacy data migration.")
        except (GLib.Error, OSError, RuntimeError, ValueError) as exc:
            logger.exception(f"Legacy Flatpak data migration decision failed: {exc}")
        finally:
            try:
                chooser.destroy()
            finally:
                self._legacy_migration_chooser = None
                self._finish_legacy_migration()

    def _finish_legacy_migration(self) -> None:
        if not self._legacy_migration_pending:
            return
        self._legacy_migration_pending = False
        try:
            self._initialize_runtime_services()
            if self._activate_after_legacy_migration:
                self._activate_after_legacy_migration = False
                self.activate()
        finally:
            if self._legacy_migration_hold:
                self._legacy_migration_hold = False
                self.release()

    def do_activate(self) -> None:
        if self._legacy_migration_pending:
            self._activate_after_legacy_migration = True
            return

        win = self.props.active_window
        if not win:
            if self.backend is None:
                self.backend = get_screenshot_service()
            win = AnuraWindow(application=self, backend=self.backend)
            self._setup_window_signals(win)
        win.present()

    def _apply_color_scheme(self) -> None:
        """Apply color scheme preference using Adw.StyleManager."""
        scheme = self.settings.get_string("color-scheme")
        style_manager = Adw.StyleManager.get_default()

        if scheme == "force-light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif scheme == "force-dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

        logger.debug(f"Anura: Applied color scheme '{scheme}'")

    def _on_color_scheme_changed(self, _settings: Gio.Settings, _key: str) -> None:
        self._apply_color_scheme()

    def _setup_window_signals(self, win: AnuraWindow) -> None:
        """Wire up event-driven service integration via OcrController signals."""
        controller = win.ocr_controller
        self.connect_tracked(controller, "text-extracted", self._on_text_extracted)
        self.connect_tracked(controller, "uri-detected", self._on_uri_detected)
        # The window owns OCR error presentation and UI cleanup. Do not connect
        # this signal again here: duplicate handlers would show the same error
        # more than once. Portal/fallback dialogs also require the window context.

    def _on_text_extracted(self, _controller, text: str, copy_requested: bool) -> None:
        is_window_active = bool(self.get_active_window())
        win = self.get_active_window()

        if self.settings.get_boolean("autocopy") or copy_requested:
            get_clipboard_service().set(text)
            if win:
                win.show_toast(_("Text copied to clipboard"))
            if not is_window_active:
                self.notification_service.show_notification(
                    title=_("Anura OCR"), body=_("Text extracted and copied to clipboard.")
                )
        else:
            if not is_window_active:
                self.notification_service.show_notification(
                    title=_("Anura OCR"), body=_("Text extracted successfully.")
                )

    def _on_uri_detected(self, _controller, url: str, copy_requested: bool) -> None:
        win = self.get_active_window()

        # #529: loopback and private-network destinations always need an
        # explicit confirmation, even when autolinks is enabled: a crafted QR
        # code must not drive the browser into a local administration UI or an
        # intranet service that trusts browser-originated requests.
        auto_open = self.settings.get_boolean("autolinks") and not is_local_or_private_url(url)

        if auto_open:
            launch_uri(url, window=win, error_callback=lambda msg: win.show_toast(msg) if win else None)
            if win:
                win.show_toast(_("URL opened automatically"))
        else:
            target = GLib.Variant("s", url)
            self.notification_service.send_notification_with_action(
                notification_id="qr-url",
                title=_("QR Code URL Detected"),
                body=url,
                action_id="app.open-qr-url",
                action_target=target,
                priority="high",
            )

        # Handle URL Clipboard (respecting global autocopy or explicit request)
        if self.settings.get_boolean("autocopy") or copy_requested:
            get_clipboard_service().set(url)
            if win and not auto_open:
                win.show_toast(_("URL copied to clipboard"))

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        options_dict = command_line.get_options_dict()
        # A G_OPTION_ARG_FILENAME option is a bytestring ('ay'): unpack() turns it into a
        # list of ints, which Path() rejects with a TypeError. Read it before end() empties
        # the dict and decode it the way the filesystem does.
        file_variant = options_dict.lookup_value("file", None)
        options = options_dict.end().unpack()

        if "extract_to_clipboard" in options:
            return self._handle_extract_to_clipboard()
        if file_variant is not None:
            file_path = os.fsdecode(file_variant.get_bytestring())
            # A remote invocation can target an already-running primary instance.
            # Resolve relative paths against the requesting client's CWD, not the
            # primary process's working directory.
            client_cwd = command_line.get_cwd()
            if client_cwd and not os.path.isabs(file_path):
                file_path = os.path.join(client_cwd, file_path)
            return self._handle_file_option(file_path, "silent" in options)

        self.activate()
        return 0

    def _handle_extract_to_clipboard(self) -> int:
        if self.backend:
            self.backend.capture(self.settings.get_string("active-language"), copy=True)
            return 0
        return 1

    def _handle_file_option(self, file_path: str, is_silent: bool) -> int:
        try:
            _exists = Path(file_path).exists()
        except PermissionError:
            # Path.exists() raises PermissionError when the *parent directory*
            # is not readable (e.g. /root/ on a non-root CI runner).
            # Treat this as inaccessible rather than letting the exception
            # propagate to the caller.
            _exists = False
        if _exists and os.access(file_path, os.R_OK):
            if is_silent:
                return SilentRunner(self, file_path).run()
            self.activate()
            if self.props.active_window:
                self.props.active_window.process_file(file_path)
            return 0

        # An explicit --file argument must not silently fall back to the image
        # picker when the requested path does not exist.
        if not _exists:
            logger.error(f"Anura CLI: File does not exist: {file_path}")
            return 1

        if not is_silent:
            self.activate()
            if self.props.active_window:
                self.props.active_window.open_image()
            return 0
        return 1

    def _decode_image_synchronously(self, file_path: str):
        if self.backend:
            return self.backend.decode_image_sync(self.settings.get_string("active-language"), file_path)
        return False, None, "Backend not initialized", None, ""

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
        except (ImportError, AttributeError, RuntimeError) as e:
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
        DialogManager.show_about(self.get_active_window(), self.version)

    def on_github_star(self, *_) -> None:
        launch_uri("https://github.com/D3M-Sudo/Anura", window=self.props.active_window)

    def on_report_issue(self, *_) -> None:
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

    def on_find(self, *_) -> None:
        win = self.get_active_window()
        if win and hasattr(win, "show_search"):
            win.show_search()

    def on_open_external_editor(self, *_) -> None:
        win = self.get_active_window()
        if win and hasattr(win, "open_in_external_editor"):
            win.open_in_external_editor()

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

    _last_paste_time: float = 0

    def on_paste_from_clipboard(self, *_) -> None:
        now = GLib.get_monotonic_time() / 1_000_000
        if now - self._last_paste_time < 0.5:
            logger.debug("Anura: Debouncing clipboard paste")
            return
        self._last_paste_time = now

        win = self.props.active_window
        if win and hasattr(win, "welcome_page"):
            win.welcome_page.show_spinner()
        get_clipboard_service().read_texture()

    def _on_open_qr_notification(self, _, parameter: GLib.Variant | None) -> None:
        if parameter:
            launch_uri(parameter.get_string().strip(), window=self.get_active_window())

    def on_decoded(self, _sender, text: str, copy: bool, ocr_result: object, applied_name: str = "") -> None:
        win = self.get_active_window()
        if win:
            # When UI is present, OcrController handles it via signals
            # connected in _setup_window_signals.
            return

        # Headless/Silent mode: perform direct dispatching
        from anura.models.ocr import OcrResult
        from anura.services.result_dispatcher import get_result_dispatcher

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
        # When a window is present, OcrController presents the error through
        # AnuraWindow. Avoid a second notification for the same signal.
        if self.get_active_window():
            return
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


def main(version: str) -> int:
    app = AnuraApplication(version)
    return app.run(sys.argv)
