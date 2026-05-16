import contextlib
import gettext
import locale
import os
import sys
import threading


# Initialize localization
def _glib_bindtextdomain(domain: str, localedir: str) -> None:
    """Bind the translation domain at the GLib/C-library level via ctypes.

    GLib.bindtextdomain() è stato rimosso dalle PyGObject bindings in GLib 2.76+.
    GtkBuilder usa g_dgettext() / dgettext() al livello C per risolvere le stringhe
    translatable="yes" nei file .ui. La soluzione primaria è translation-domain in
    ogni .blp; questa funzione è un fallback belt-and-suspenders for the C domain.
    """
    import ctypes
    import ctypes.util

    try:
        _libname = ctypes.util.find_library("glib-2.0") or ctypes.util.find_library("c")
        if not _libname:
            return
        _lib = ctypes.CDLL(_libname)
        _lib.bindtextdomain(domain.encode(), localedir.encode())
        _lib.bind_textdomain_codeset(domain.encode(), b"UTF-8")
        _lib.textdomain(domain.encode())
    except (OSError, AttributeError):
        # Non-fatal: the translation-domain in .blp is the primary mechanism
        pass


def _setup_i18n():

    from anura.config import APP_ID

    project_name = APP_ID
    # Priority: standard installation -> Flatpak -> relative (dev)
    possible_localedirs = [
        "/app/share/locale",
        os.path.join(os.path.dirname(__file__), "..", "builddir", "po"),
        os.path.join(os.path.dirname(__file__), "..", "po"),
        "/usr/local/share/locale",
        "/usr/share/locale",
    ]

    localedir = None
    for path in possible_localedirs:
        if os.path.exists(path):
            localedir = path
            break

    # Step 1: C-level locale for GTK/Libadwaita
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error as e:
        print(f"Warning: Could not set locale: {e}. Falling back to 'C'.", file=sys.stderr)
        try:
            locale.setlocale(locale.LC_ALL, "C")
        except locale.Error:
            pass
        # Force English to avoid hybrid UI
        os.environ.setdefault("LANGUAGE", "C")
        os.environ["LC_ALL"] = "C"
        os.environ["LANG"] = "C"

    if not localedir:
        return

    # Step 2: Python gettext (used by _() in all .py files)
    gettext.bindtextdomain(project_name, localedir)
    gettext.textdomain(project_name)

    # Step 3: C-level textdomain — separate from GLib block so that a
    # GLib failure cannot mask a local setup failure.
    # GtkBuilder falls back to dgettext(NULL, ...) which uses this domain when
    # <interface> doesn't have an explicit domain attribute.
    try:
        locale.bindtextdomain(project_name, localedir)
        locale.textdomain(project_name)
        if hasattr(locale, "bind_textdomain_codeset"):
            locale.bind_textdomain_codeset(project_name, "UTF-8")
    except (AttributeError, OSError) as e:
        print(f"Warning: C-level locale binding failed: {e}", file=sys.stderr)

    # Step 4: GLib-level binding via ctypes (belt-and-suspenders).
    # GLib.bindtextdomain() has been removed from PyGObject in GLib 2.76+.
    # The primary fix is translation-domain in each .blp; this is the fallback.
    _glib_bindtextdomain(project_name, localedir)


_setup_i18n()

from gettext import gettext as _
import html

# Suppress a11y bus warnings in headless CI environments
if not sys.stdin.isatty():
    os.environ["NO_AT_BRIDGE"] = "1"

import gi

# Set GTK version requirements before imports
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Notify", "0.7")
gi.require_version("Xdp", "1.0")
gi.require_version("Gst", "1.0")

from gi.repository import Adw, Gio, GLib, Gtk
from loguru import logger

from anura.config import APP_ID, LOG_LEVEL

# Configure logging with professional format
# Production default is INFO; override via ANURA_LOG_LEVEL env var for debugging
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}:{function}:{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level=LOG_LEVEL,
    colorize=True,
    catch=True,
)


def _load_gresource_bundle() -> bool:
    """Load the GResource bundle containing UI files and icons.

    This must be called before importing any widgets that use @Gtk.Template
    with resource_path, as those decorators validate resource existence at
    class definition time (import time).
    """
    # Check if GResource is already registered (e.g., by anura.in launcher script)
    # This prevents double registration when running via the standard entry point
    with contextlib.suppress(GLib.Error):
        # Try to lookup a known resource - if found, bundle is already loaded
        Gio.resources_lookup_data("/com/github/d3msudo/anura/window.ui", Gio.ResourceLookupFlags.NONE)
        return True

    # Determine possible paths for the gresource bundle
    # Priority: Flatpak -> system -> user -> relative
    possible_paths = [
        "/app/share/anura/com.github.d3msudo.anura.gresource",
        "/usr/share/anura/com.github.d3msudo.anura.gresource",
        "/usr/local/share/anura/com.github.d3msudo.anura.gresource",
        os.path.expanduser("~/.local/share/anura/com.github.d3msudo.anura.gresource"),
        # Development fallback: relative to this file
        os.path.join(os.path.dirname(__file__), "..", "data", "com.github.d3msudo.anura.gresource"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            try:
                resource = Gio.Resource.load(path)
                Gio.resources_register(resource)
                return True
            except Exception:
                continue

    return False


# Load GResource before importing any widgets with @Gtk.Template decorators
if not _load_gresource_bundle():
    # If logger isn't initialized yet, use print
    print("CRITICAL: GResource bundle is required to run Anura. The application cannot start.", file=sys.stderr)
    sys.exit(1)


from anura.language_manager import get_language_manager
from anura.services.clipboard_service import get_clipboard_service
from anura.services.notification_service import (
    HAS_LIBNOTIFY,
    NotificationService,
)
from anura.services.screenshot_service import ScreenshotService
from anura.services.settings import settings
from anura.utils import cleanup_orphaned_resources
from anura.window import AnuraWindow


class AnuraApplication(Adw.Application):
    __gtype_name__ = "AnuraApplication"

    def __init__(self, version: str | None = None) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.backend: ScreenshotService | None = None
        self.version = version
        self.settings = settings

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

        self.notification_service = NotificationService(APP_ID)

        # Track backend signal handler IDs for cleanup in do_shutdown
        self._backend_decoded_handler_id: int | None = None
        self._backend_error_handler_id: int | None = None

    def do_startup(self, *args: object, **kwargs: object) -> None:
        Adw.init()
        Adw.Application.do_startup(self)

        # Clean up orphaned resources from previous sessions
        cleanup_orphaned_resources()

        self.backend = ScreenshotService()
        self._backend_decoded_handler_id = self.backend.connect("decoded", self.on_decoded)
        self._backend_error_handler_id = self.backend.connect("error", self.on_error)

        # Initialize services on main thread to avoid race conditions
        language_manager_instance = get_language_manager()
        language_manager_instance.init_tessdata()

        clipboard_service_instance = get_clipboard_service()
        clipboard_service_instance.init()

        self._setup_actions()

        GLib.set_application_name("Anura OCR")
        GLib.set_prgname(APP_ID)

    def do_shutdown(self, *args: object, **kwargs: object) -> None:
        """Clean up resources on application shutdown."""
        self._cleanup_backend_signals()
        self._cleanup_notification_service()
        self._cleanup_clipboard_service()
        self._cleanup_tts_service()
        Adw.Application.do_shutdown(self)

    def _cleanup_backend_signals(self) -> None:
        """Clean up backend signal handlers."""
        if self.backend is not None:
            self._disconnect_signal_handler(self._backend_decoded_handler_id)
            self._disconnect_signal_handler(self._backend_error_handler_id)

    def _disconnect_signal_handler(self, handler_id: int | None) -> None:
        """Safely disconnect a signal handler."""
        if handler_id is not None and hasattr(self, "backend") and self.backend is not None:
            with contextlib.suppress(TypeError, RuntimeError, AttributeError):
                self.backend.disconnect(handler_id)

    def _cleanup_notification_service(self) -> None:
        """Clean up notification service."""
        if hasattr(self, "notification_service") and self.notification_service:
            try:
                if HAS_LIBNOTIFY:
                    from gi.repository import Notify

                    if Notify.is_initted():
                        Notify.uninit()
            except (ImportError, AttributeError, TypeError) as e:
                logger.debug(f"Failed to uninitialize libnotify: {e}")

    def _cleanup_clipboard_service(self) -> None:
        """Clean up clipboard service."""
        try:
            clipboard_service_instance = get_clipboard_service()
            clipboard_service_instance.cancel_pending_operations()
        except (AttributeError, TypeError) as e:
            logger.debug(f"Failed to cleanup clipboard service: {e}")

    def _cleanup_tts_service(self) -> None:
        """Clean up TTS service to prevent broken pipe errors."""
        try:
            from anura.services.tts import get_tts_service

            tts_service = get_tts_service()
            tts_service.cleanup()
        except (ImportError, AttributeError, TypeError) as e:
            logger.debug(f"Failed to cleanup TTS service: {e}")

    def _setup_actions(self) -> None:
        self.create_action("get_screenshot", self.get_screenshot, ["<primary>g"])
        self.create_action("get_screenshot_and_copy", self.get_screenshot_and_copy, ["<primary><shift>g"])
        self.create_action("copy_to_clipboard", self.on_copy_to_clipboard, ["<primary>c"])
        self.create_action("open_image", self.open_image, ["<primary>o"])
        self.create_action("paste_from_clipboard", self.on_paste_from_clipboard, ["<primary>v"])
        self.create_action("listen", self.on_listen, ["<primary>l"])
        self.create_action("listen_pause", self.on_listen_pause, ["<primary><alt>l"])
        self.create_action("listen_cancel", self.on_listen_cancel, ["<primary><shift>l"])
        self.create_action("shortcuts", self.on_shortcuts, ["<primary>question", "<primary>slash", "<primary>h"])
        self.create_action(
            "quit", lambda *_: logger.debug("Anura: Quit action triggered") or self.quit(), ["<primary>q", "<primary>w"]
        )
        self.create_action("preferences", self.on_preferences, ["<primary>comma"])
        self.create_action("about", self.on_about)
        self.create_action("github_star", self.on_github_star)
        self.create_action("report_issue", self.on_report_issue)

        # Register action for QR code notification clicks (Flatpak-safe Gio.Notification)
        open_qr_action = Gio.SimpleAction.new("open-qr-url", GLib.VariantType.new("s"))
        open_qr_action.connect("activate", self._on_open_qr_notification)
        self.add_action(open_qr_action)
        logger.debug("Anura: Registered action 'app.open-qr-url' for notification click handling")

    def do_activate(self) -> None:
        win = self.props.active_window
        if not win:
            win = AnuraWindow(application=self, backend=self.backend)
        win.present()

    def do_command_line(self, command_line: Gio.ApplicationCommandLine) -> int:
        """Handle command line arguments and execute appropriate actions."""
        options = command_line.get_options_dict().end().unpack()

        if "extract_to_clipboard" in options:
            return self._handle_extract_to_clipboard()

        if "file" in options:
            return self._handle_file_option(options["file"], "silent" in options)

        return self._handle_default_mode()

    def _handle_extract_to_clipboard(self) -> int:
        """Handle extract to clipboard command line option."""
        logger.info("Anura: CLI Extraction triggered.")
        self.backend.capture(self.settings.get_string("active-language"), copy=True)
        return 0

    def _handle_file_option(self, file_path: str, is_silent: bool) -> int:
        """Handle file processing command line option."""
        logger.debug(f"Anura: CLI file processing: {file_path}")

        try:
            if self._is_file_accessible(file_path):
                return self._process_accessible_file(file_path, is_silent)
            else:
                return self._handle_inaccessible_file(file_path, is_silent)
        except (OSError, PermissionError) as e:
            return self._handle_file_access_error(file_path, e, is_silent)

    def _is_file_accessible(self, file_path: str) -> bool:
        """Check if file is accessible for reading."""
        return os.path.exists(file_path) and os.access(file_path, os.R_OK)

    def _process_accessible_file(self, file_path: str, is_silent: bool) -> int:
        """Process an accessible file."""
        if is_silent:
            return self._run_silent_mode(file_path)
        else:
            self._activate_window_and_process_file(file_path)
            return 0

    def _handle_inaccessible_file(self, file_path: str, is_silent: bool) -> int:
        """Handle files not accessible in sandbox."""
        if is_silent:
            logger.error(f"File not accessible in sandbox: {file_path}")
            logger.error("Use files from ~/Downloads or run without --silent for file picker")
            return 1
        else:
            logger.info("File not directly accessible, opening file picker")
            self._activate_window_and_open_image()
            return 0

    def _handle_file_access_error(self, file_path: str, error: Exception, is_silent: bool) -> int:
        """Handle file access errors."""
        logger.error(f"Error accessing file {file_path}: {error}")
        if is_silent:
            return 1
        else:
            self._activate_window_and_open_image()
            return 0

    def _activate_window_and_process_file(self, file_path: str) -> None:
        """Activate window and process the specified file."""
        self.activate()
        win = self.props.active_window
        if win:
            win.process_file(file_path)

    def _activate_window_and_open_image(self) -> None:
        """Activate window and open image file picker."""
        self.activate()
        win = self.props.active_window
        if win:
            win.open_image()

    def _handle_default_mode(self) -> int:
        """Handle default application mode (no specific options)."""
        self.activate()
        win = self.props.active_window
        if win:
            win.present()
        return 0

    def _run_silent_mode(self, file_path: str) -> int:
        """Run OCR in silent mode without UI, return exit code."""
        import threading

        interrupted = threading.Event()
        signal_handlers = self._setup_signal_handlers(interrupted)

        try:
            return self._execute_silent_ocr_with_context(file_path, interrupted)
        finally:
            # Always restore handlers on every exit path (including return).
            self._restore_signal_handlers(signal_handlers)

    def _setup_signal_handlers(self, interrupted: threading.Event) -> dict[str, object]:
        """Setup signal handlers for clean shutdown."""
        import signal as sig

        def on_signal(signum: int, frame: object) -> None:
            """Handle SIGINT/SIGTERM for clean shutdown."""
            logger.info(f"Anura: Received signal {signum}, shutting down silently...")
            interrupted.set()

        old_sigint = sig.signal(sig.SIGINT, on_signal)
        old_sigterm = sig.signal(sig.SIGTERM, on_signal)
        return {"sigint": old_sigint, "sigterm": old_sigterm}

    def _restore_signal_handlers(self, signal_handlers: dict[str, object]) -> None:
        """Restore original signal handlers."""
        import signal as sig

        sig.signal(sig.SIGINT, signal_handlers["sigint"])
        sig.signal(sig.SIGTERM, signal_handlers["sigterm"])

    def _execute_silent_ocr_with_context(self, file_path: str, interrupted: threading.Event) -> int:
        """Execute OCR in silent mode with proper GLib context management."""
        # Create custom context and loop
        ctx = GLib.MainContext.new()
        loop = GLib.MainLoop.new(ctx, False)

        # Store sources for proper cleanup
        sources = []

        # Attach interruption checker to custom context
        def check_interrupted() -> bool:
            if interrupted.is_set():
                loop.quit()
                return False  # Stop checking
            return True  # Continue checking

        check_source = GLib.timeout_source_new(100)  # 100ms
        check_source.set_callback(check_interrupted)
        check_source.attach(ctx)
        sources.append(check_source)

        # Schedule OCR on custom context
        def do_ocr() -> bool:
            if interrupted.is_set():
                loop.quit()
                return False  # Don't repeat

            try:
                success, text, error_message = self._decode_image_synchronously(file_path)

                if interrupted.is_set():
                    loop.quit()
                    return False

                if success and text:
                    clipboard_service_instance = get_clipboard_service()
                    clipboard_service_instance.set(text)
                    logger.info("Anura: OCR completed successfully in silent mode.")
                    loop.quit()
                else:
                    logger.error(f"Anura: Silent mode failed: {error_message}")
                    loop.quit()
            except Exception as e:
                logger.error(f"Anura: Silent mode unexpected error: {e}")
                loop.quit()
            return False  # Don't repeat

        idle_source = GLib.idle_source_new()
        idle_source.set_callback(do_ocr)
        idle_source.attach(ctx)
        sources.append(idle_source)

        # Run the loop with timeout to prevent infinite hangs
        timeout_source = GLib.timeout_source_new_seconds(60)  # 60 second timeout
        timeout_source.set_callback(lambda: loop.quit() or False)
        timeout_source.attach(ctx)
        sources.append(timeout_source)

        # Push context and run loop
        ctx.push()
        try:
            loop.run()
        finally:
            ctx.pop()
            # Clean up all sources to prevent resource leaks
            for source in sources:
                source.destroy()

        # Check final interruption state
        if interrupted.is_set():
            logger.info("Anura: Silent mode interrupted by user.")
            return 130

        return 0

    def _decode_image_synchronously(self, file_path: str) -> tuple[bool, str | None, str | None]:
        """Decode image synchronously for silent mode."""
        try:
            return self.backend.decode_image_sync(
                self.settings.get_string("active-language"),
                file_path,
                remove_source=False,
            )
        except FileNotFoundError:
            error_msg = f"File not found: {file_path}"
            logger.error(f"Anura: Silent mode - {error_msg}")
            return False, None, error_msg
        except PermissionError:
            error_msg = f"Permission denied accessing file: {file_path}"
            logger.error(f"Anura: Silent mode - {error_msg}")
            return False, None, error_msg
        except OSError as e:
            error_msg = f"File system error accessing {file_path}: {e}"
            logger.error(f"Anura: Silent mode - {error_msg}")
            return False, None, error_msg
        except ImportError as e:
            error_msg = f"Missing dependency for OCR: {e}"
            logger.error(f"Anura: Silent mode - {error_msg}")
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Unexpected error processing {file_path}: {e}"
            logger.error(f"Anura: Silent mode - {error_msg}")
            return False, None, error_msg

    def on_preferences(self, _action: object, _param: object) -> None:
        logger.debug("Anura: Preferences action triggered")
        window = self.get_active_window()
        if window:
            window.show_preferences()

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

    def on_about(self, _action: object, _param: object) -> None:
        window = self.props.active_window

        # GTK interprets copyright/license strings as Pango markup,
        # so we must escape special characters like &
        _copyright = html.escape(
            "© 2025-2026 D3M-Sudo & Anura Contributors\n© 2022-2025 Frog OCR Contributors"
        )

        def _schedule_present() -> bool:
            """Stage 2: Present the AboutDialog in a separate iteration.

            This runs AFTER Stage 1 has completed, ensuring the popover's
            internal teardown has fully propagated through the GTK event loop
            before the AboutDialog causes a widget hierarchy update.
            """
            if window:
                window.set_focus(None)

            about_window = Adw.AboutDialog(
                application_name="Anura",
                application_icon=APP_ID,
                version=self.version,
                copyright=_copyright,
                website="https://github.com/D3M-Sudo/Anura",
                license_type=Gtk.License.MIT_X11,
                license=(
                    "MIT License\n\n"
                    "Permission is hereby granted, free of charge, to any person obtaining a copy of "
                    'this software and associated documentation files (the "Software"), to deal in '
                    "the Software without restriction, including without limitation the rights to "
                    "use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of "
                    "the Software, and to permit persons to whom the Software is furnished to do so, "
                    "subject to the following conditions:\n\n"
                    "The above copyright notice and this permission notice shall be included in all "
                    "copies or substantial portions of the Software.\n\n"
                    'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR '
                    "IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, "
                    "FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE "
                    "AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER "
                    "LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, "
                    "OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE "
                    "SOFTWARE."
                ),
                developers=["Andrey Maksimov (Frog OCR)", "D3M-Sudo (Anura)"],
                designers=["D3M-Sudo"],
                release_notes=self._get_release_notes(),
            )

            # Add legal sections BEFORE presenting to prevent widget lifecycle warnings
            about_window.add_legal_section(
                _("Acknowledgements"),
                "© 2022-2025 Andrey Maksimov",
                Gtk.License.MIT_X11,
                _(
                    "Anura is a fork of Frog OCR. This software uses Tesseract OCR, Leptonica, "
                    "GTK4, Libadwaita, gTTS, Pillow, PyZBar, and other open source components."
                ),
            )
            about_window.add_link(_("Changelog"), "https://github.com/D3M-Sudo/Anura/blob/main/CHANGELOG.md")

            about_window.present(window)
            return GLib.SOURCE_REMOVE

        def _close_popovers() -> bool:
            """Stage 1: Close open popovers and defer dialog presentation.

            This runs first to pop down any visible popovers (primary menu,
            share popup) before the AboutDialog is created. The popover's
            internal state machine needs an iteration to complete teardown,
            so we schedule the dialog presentation in a second idle callback.
            """
            if window and hasattr(window, "close_popovers"):
                window.set_focus(None)
                window.close_popovers()

            # Schedule Stage 2 in a separate idle iteration to allow
            # GTK to finish the popover teardown.
            GLib.idle_add(_schedule_present)
            return GLib.SOURCE_REMOVE

        # Stage 0: Immediate focus release
        if window:
            window.set_focus(None)

        # Stage 1: Close popovers (first idle callback)
        GLib.idle_add(_close_popovers)

    def on_github_star(self, _action: object, _param: object) -> None:
        """Open GitHub repository page in the default browser."""
        launcher = Gtk.UriLauncher.new("https://github.com/D3M-Sudo/Anura")

        def on_launch_finish(_launcher: object, result: Gio.AsyncResult) -> None:
            try:
                launcher.launch_finish(result)
            except GLib.Error as e:
                logger.error(f"Anura: Failed to open browser: {e.message}")
                # Show error dialog to user using Adw.AlertDialog
                window = self.props.active_window
                if window:
                    dialog = Adw.AlertDialog()
                    dialog.set_heading(_("Failed to Open Browser"))
                    dialog.set_body(_("No web browser could be launched. Please open the link manually."))
                    dialog.add_response("ok", _("OK"))
                    dialog.present(window)

        launcher.launch(self.props.active_window, None, on_launch_finish)

    def on_report_issue(self, _action: object, _param: object) -> None:
        """Open GitHub issues page in the default browser."""
        launcher = Gtk.UriLauncher.new("https://github.com/D3M-Sudo/Anura/issues")

        def on_launch_finish(_launcher: object, result: Gio.AsyncResult) -> None:
            try:
                launcher.launch_finish(result)
            except GLib.Error as e:
                logger.error(f"Anura: Failed to open browser: {e.message}")
                # Show error dialog to user using Adw.AlertDialog
                window = self.props.active_window
                if window:
                    dialog = Adw.AlertDialog()
                    dialog.set_heading(_("Failed to Open Browser"))
                    dialog.set_body(_("No web browser could be launched. Please open the link manually."))
                    dialog.add_response("ok", _("OK"))
                    dialog.present(window)

        launcher.launch(self.props.active_window, None, on_launch_finish)

    def on_shortcuts(self, _action: object, _param: object) -> None:
        window = self.get_active_window()
        if window:
            window.show_shortcuts()

    def on_copy_to_clipboard(self, _action: Gio.SimpleAction, variant: GLib.Variant | None) -> None:
        """Copy text to clipboard from action.

        The action is registered without a parameter type, so when triggered by
        the toolbar button or the Ctrl+C accelerator the variant is None. In
        that case fall back to the currently extracted text on the active
        window so the toolbar Copy button and shortcut actually copy something.
        """
        window = self.get_active_window()
        if not window:
            return

        text = ""
        if variant is not None:
            try:
                text = variant.get_string()
            except (TypeError, AttributeError):
                text = ""

        if text:
            clipboard_service_instance = get_clipboard_service()
            clipboard_service_instance.set(text)
            window.show_toast(_("Text copied to clipboard"))
            return

        # No explicit text passed via the action — copy whatever the window has.
        if hasattr(window, "_do_copy_to_clipboard"):
            window._do_copy_to_clipboard()
        else:
            window.show_toast(_("No text available to copy"))

    def get_screenshot(self, _action: object, _param: object) -> None:
        window = self.get_active_window()
        if window:
            window.get_screenshot()

    def get_screenshot_and_copy(self, _action: object, _param: object) -> None:
        window = self.get_active_window()
        if window:
            window.get_screenshot(copy=True)

    def open_image(self, _action: object, _param: object) -> None:
        window = self.get_active_window()
        if window:
            window.open_image()

    def on_paste_from_clipboard(self, _action: Gio.SimpleAction, _param: object) -> None:
        """Read image from clipboard and perform OCR."""
        # Show spinner so the user has visual feedback while the async read runs
        win = self.props.active_window
        if win and hasattr(win, "welcome_page"):
            win.welcome_page.show_spinner()
        clipboard_service_instance = get_clipboard_service()
        clipboard_service_instance.read_texture()

    def _on_open_qr_notification(self, _action: Gio.SimpleAction, parameter: GLib.Variant | None) -> None:
        """Handle QR code notification click — open the URL in the default browser.

        Triggered when the user clicks a Gio.Notification sent via
        send_notification_with_action(). The URL is extracted from the
        action's target parameter, sanitized, validated, and launched.

        This runs inside the Flatpak sandbox via Gio.SimpleAction, avoiding
        libnotify callback sandbox issues.
        """
        if parameter is None:
            logger.warning("Anura: open-qr-url action triggered without a URL parameter")
            return

        # Sanitize: strip all control characters and whitespace (defense in depth)
        url = parameter.get_string().strip()
        url = url.strip("\n\r\t\v\f")

        if not url:
            logger.warning("Anura: open-qr-url action triggered with empty URL")
            return

        # Security: validate URL before launching (defense in depth)
        from anura.utils import uri_validator

        if not uri_validator(url):
            logger.warning(f"Anura: Blocked invalid URL from notification: {url}")
            window = self.get_active_window()
            if window and hasattr(window, "show_toast"):
                window.show_toast(_("Invalid URL blocked for security"))
            return

        # Launch URL via Gtk.UriLauncher
        window = self.get_active_window()
        if window and hasattr(window, "_launch_uri"):
            window._launch_uri(url)
        else:
            # Fallback: launch directly if no window available
            launcher = Gtk.UriLauncher.new(url)

            def on_launch_finish(_launcher: object, result: Gio.AsyncResult) -> None:
                try:
                    launcher.launch_finish(result)
                except GLib.Error as e:
                    logger.error(f"Anura: Failed to open URL from notification: {e.message}")

            launcher.launch(None, None, on_launch_finish)

    def on_decoded(self, _sender: object, text: str, copy: bool) -> None:
        if not text:
            self.notification_service.show_notification(
                title=_("Anura OCR"),
                body=_("No text found. Try to grab another region."),
            )
            return

        if copy:
            clipboard_service_instance = get_clipboard_service()
            clipboard_service_instance.set(text)
            self.notification_service.show_notification(
                title=_("Anura OCR"),
                body=_("Text extracted and copied to clipboard."),
            )
        else:
            # Text extracted but not copied - show notification
            self.notification_service.show_notification(
                title=_("Anura OCR"),
                body=_("Text extracted successfully."),
            )

    def on_error(self, _sender: object, message: str) -> None:
        """Handle screenshot service errors, skipping cancellation messages."""
        if message == _("Cancelled"):
            # User cancelled - no notification needed
            logger.info("Anura: Screenshot cancelled by user.")
            return
        # Real error - show notification
        self.notification_service.show_notification(title=_("Anura OCR"), body=message)

    def on_listen(self, _sender: object, _event: object) -> None:
        window = self.get_active_window()
        if window:
            window.on_listen()

    def on_listen_cancel(self, _sender: object, _event: object) -> None:
        window = self.get_active_window()
        if window:
            window.on_listen_cancel()

    def on_listen_pause(self, _sender: object, _event: object) -> None:
        window = self.get_active_window()
        if window:
            window.on_listen_pause()

    def create_action(self, name: str, callback: object, shortcuts: list[str] | None = None) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        logger.debug(f"Anura: Registered action 'app.{name}'")
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
            logger.debug(f"Anura: Set accelerators for 'app.{name}': {shortcuts}")


def main(version: str) -> int:
    app = AnuraApplication(version)
    return app.run(sys.argv)
