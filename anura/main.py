import datetime
import os
import sys
import threading
from gettext import gettext as _

from gi.repository import Adw, Gio, GLib, Gtk, Notify
from loguru import logger


def _load_gresource_bundle():
    """Load the GResource bundle containing UI files and icons.

    This must be called before importing any widgets that use @Gtk.Template
    with resource_path, as those decorators validate resource existence at
    class definition time (import time).
    """
    # Check if GResource is already registered (e.g., by anura.in launcher script)
    # This prevents double registration when running via the standard entry point
    try:
        # Try to lookup a known resource - if found, bundle is already loaded
        Gio.resources_lookup_data("/com/github/d3msudo/anura/window.ui", Gio.ResourceLookupFlags.NONE)
        logger.debug("GResource bundle already registered (likely by anura.in)")
        return True
    except GLib.Error:
        pass  # Not registered yet, continue with loading

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
                resource._register()
                logger.debug(f"Loaded GResource bundle from {path}")
                return True
            except Exception as e:
                logger.warning(f"Failed to load GResource from {path}: {e}")
                continue

    logger.error("Could not find or load GResource bundle - UI files may not be available")
    return False


# Load GResource before importing any widgets with @Gtk.Template decorators
_load_gresource_bundle()

from anura.config import APP_ID  # noqa: E402
from anura.language_manager import language_manager  # noqa: E402
from anura.services.clipboard_service import clipboard_service  # noqa: E402
from anura.services.screenshot_service import ScreenshotService  # noqa: E402
from anura.services.settings import settings  # noqa: E402
from anura.window import AnuraWindow  # noqa: E402


class AnuraApplication(Adw.Application):
    __gtype_name__ = 'AnuraApplication'

    def __init__(self, version=None):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)
        self.backend = None
        self.version = version
        self.settings = settings

        self.add_main_option(
            'extract_to_clipboard',
            ord('e'),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            _("Extract directly into the clipboard"),
            None
        )

        self.add_main_option(
            'file',
            ord('f'),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.FILENAME,
            _("Process image file for OCR"),
            None
        )

        self.add_main_option(
            'silent',
            ord('s'),
            GLib.OptionFlags.NONE,
            GLib.OptionArg.NONE,
            _("Run OCR without UI (copy result to clipboard)"),
            None
        )

        language_manager.init_tessdata()
        Notify.init(APP_ID)

    def do_startup(self, *args, **kwargs):
        Adw.Application.do_startup(self)

        self.backend = ScreenshotService()
        self.backend.connect('decoded', self.on_decoded)
        self.backend.connect('error', self.on_error)

        self._setup_actions()

        GLib.set_application_name("Anura OCR")
        GLib.set_prgname(APP_ID)

    def _setup_actions(self):
        self.create_action('get_screenshot', self.get_screenshot, ['<primary>g'])
        self.create_action('get_screenshot_and_copy', self.get_screenshot_and_copy, ['<primary><shift>g'])
        self.create_action('copy_to_clipboard', self.on_copy_to_clipboard, ['<primary>c'])
        self.create_action('open_image', self.open_image, ['<primary>o'])
        self.create_action('paste_from_clipboard', self.on_paste_from_clipboard, ['<primary>v'])
        self.create_action('listen', self.on_listen, ['<primary>l'])
        self.create_action('listen_cancel', self.on_listen_cancel, ['<primary><shift>l'])
        self.create_action('shortcuts', self.on_shortcuts, ['<primary>question'])
        self.create_action('quit', lambda *_: self.quit(), ['<primary>q', '<primary>w'])
        self.create_action('preferences', self.on_preferences, ['<primary>comma'])
        self.create_action('about', self.on_about)
        self.create_action('github_star', self.on_github_star)

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = AnuraWindow(application=self, backend=self.backend)
        win.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict().end().unpack()

        if "extract_to_clipboard" in options:
            logger.info("Anura: CLI Extraction triggered.")
            self.backend.capture(self.settings.get_string("active-language"), copy=True)
            return 0

        if "file" in options:
            file_path = options["file"]
            logger.info(f"Anura: CLI file processing: {file_path}")

            if "silent" in options:
                return self._run_silent_mode(file_path)
            else:
                # UI mode: activate app and tell window to process the file
                self.activate()
                win = self.props.active_window
                if win:
                    win.process_file(file_path)
                return 0

        self.activate()
        return 0

    def _run_silent_mode(self, file_path: str) -> int:
        """Run OCR in silent mode without UI, return exit code."""
        done_event = threading.Event()
        result = {"success": False, "text": None}
        _interrupted = threading.Event()

        def on_silent_decoded(_sender, text: str, copy: bool) -> None:
            result["success"] = True
            result["text"] = text
            done_event.set()

        def on_silent_error(_sender, message: str) -> None:
            result["success"] = False
            result["error"] = message
            done_event.set()

        def on_signal(signum, frame):
            """Handle SIGINT/SIGTERM for clean shutdown."""
            logger.info(f"Anura: Received signal {signum}, shutting down silently...")
            _interrupted.set()
            done_event.set()

        # Track handler IDs for safe cleanup
        decoded_handler_id: int | None = None
        error_handler_id: int | None = None

        import signal as sig
        old_sigint = sig.signal(sig.SIGINT, on_signal)
        old_sigterm = sig.signal(sig.SIGTERM, on_signal)

        try:
            # Temporarily connect to both signals for this operation
            decoded_handler_id = self.backend.connect('decoded', on_silent_decoded)
            error_handler_id = self.backend.connect('error', on_silent_error)

            self.backend.decode_image(
                self.settings.get_string("active-language"),
                file_path,
                copy=True,
                remove_source=False
            )

            # Wait for completion with timeout using GLib MainLoop (event-driven)
            # Create a main loop that will run until done_event is set or timeout
            timeout_seconds = 60.0

            # Create a main loop with new context (not default) for thread safety
            ctx = GLib.MainContext.new()
            loop = GLib.MainLoop.new(ctx, False)

            def on_timeout():
                """Timeout callback - stop loop and mark as timed out."""
                nonlocal timed_out
                timed_out = True
                result["success"] = False
                result["error"] = "Timeout"
                logger.error("Anura: Silent mode timeout waiting for OCR")
                loop.quit()
                return False  # Don't repeat

            def on_done():
                """Check if done_event is set, if so quit the loop."""
                if done_event.is_set() or _interrupted.is_set():
                    loop.quit()
                    return False  # Stop checking
                return True  # Continue checking

            # Add timeout source (60 seconds)
            timeout_id = GLib.timeout_add_seconds(int(timeout_seconds), on_timeout)
            # Add idle source to check for completion (more efficient than polling)
            idle_id = GLib.idle_add(on_done)

            timed_out = False
            loop.run()

            # Cleanup sources
            GLib.source_remove(timeout_id)
            if not done_event.is_set() and not _interrupted.is_set():
                GLib.source_remove(idle_id)

            if _interrupted.is_set():
                return 130  # Standard exit code for SIGINT

            if timed_out:
                return 1

            return 0 if result["success"] else 1

        except Exception as e:
            logger.error(f"Anura: Silent mode unexpected error: {e}")
            return 1
        finally:
            # Restore original signal handlers
            sig.signal(sig.SIGINT, old_sigint)
            sig.signal(sig.SIGTERM, old_sigterm)
            # Always disconnect handlers in all scenarios
            if decoded_handler_id is not None and self.backend:
                try:
                    self.backend.disconnect(decoded_handler_id)
                except Exception:
                    pass
            if error_handler_id is not None and self.backend:
                try:
                    self.backend.disconnect(error_handler_id)
                except Exception:
                    pass

    def on_preferences(self, _action, _param) -> None:
        window = self.get_active_window()
        if window:
            window.show_preferences()

    def on_about(self, _action, _param):
        about_window = Adw.AboutDialog(
            application_name="Anura",
            application_icon=APP_ID,
            version=self.version,
            copyright=f'© {datetime.date.today().year} D3M-Sudo & Anura Contributors',
            website="https://github.com/d3msudo/anura",
            license_type=Gtk.License.MIT,
            developers=["Andrey Maksimov", "D3M-Sudo"],
            designers=["Andrey Maksimov"],
            release_notes="<p>" + _("Extract text from anywhere on your screen.") + "</p>"
        )
        about_window.present(self.props.active_window)

    def on_github_star(self, _action, _param) -> None:
        """Open the GitHub repository page in the default browser."""
        launcher = Gtk.UriLauncher.new("https://github.com/d3msudo/anura")

        def on_launch_finish(_launcher, result):
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
                    dialog.add_response("copy", _("Copy Link"))
                    dialog.add_response("close", _("Close"))
                    dialog.set_default_response("close")
                    dialog.set_close_response("close")

                    def on_dialog_response(_dlg, response):
                        if response == "copy":
                            clipboard_service.set("https://github.com/d3msudo/anura")
                        _dlg.destroy()

                    dialog.connect("response", on_dialog_response)
                    dialog.present(window)

        launcher.launch(self.props.active_window, None, on_launch_finish)

    def on_shortcuts(self, _action, _param):
        window = self.get_active_window()
        if window:
            window.show_shortcuts()

    def on_copy_to_clipboard(self, _action, _param) -> None:
        window = self.get_active_window()
        if window:
            window.on_copy_to_clipboard(self)

    def get_screenshot(self, _action, _param) -> None:
        window = self.get_active_window()
        if window:
            window.get_screenshot()

    def get_screenshot_and_copy(self, _action, _param) -> None:
        window = self.get_active_window()
        if window:
            window.get_screenshot(copy=True)

    def open_image(self, _action, _param) -> None:
        window = self.get_active_window()
        if window:
            window.open_image()

    def on_paste_from_clipboard(self, _action, _param) -> None:
        window = self.get_active_window()
        if window:
            window.on_paste_from_clipboard(self)

    def on_decoded(self, _sender, text: str, copy: bool) -> None:
        if not text:
            notification = Notify.Notification.new(
                summary='Anura OCR',
                body=_("No text found. Try to grab another region.")
            )
            notification.show()
            return

        if copy:
            clipboard_service.set(text)
            notification = Notify.Notification.new(
                summary='Anura OCR',
                body=_("Text extracted and copied to clipboard.")
            )
            notification.show()
        else:
            logger.debug(f'Extracted: {text}')

    def on_error(self, _sender, message: str) -> None:
        """Handle screenshot service errors, skipping cancellation messages."""
        if message == _("Cancelled"):
            # User cancelled - no notification needed
            logger.info("Anura: Screenshot cancelled by user.")
            return
        # Real error - show notification
        notification = Notify.Notification.new(
            summary='Anura OCR',
            body=message
        )
        notification.show()

    def on_listen(self, _sender, _event):
        window = self.get_active_window()
        if window:
            window.on_listen()

    def on_listen_cancel(self, _sender, _event):
        window = self.get_active_window()
        if window:
            window.on_listen_cancel()

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)


def main(version):
    app = AnuraApplication(version)
    return app.run(sys.argv)
