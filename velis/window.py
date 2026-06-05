# velis/window.py
import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gio, GLib, Gtk
from loguru import logger

from velis.core.atomic_task_manager import get_atomic_manager
from velis.core.signal_manager import SignalManagerMixin
from velis.services.history_service import get_history_service
from velis.services.ocr_service import get_ocr_service
from velis.services.regex_service import get_regex_service
from velis.services.screenshot_service import get_screenshot_service
from velis.services.settings_service import get_settings
from velis.services.tts_service import get_tts_service
from velis.widgets.preferences_dialog import PreferencesDialog


@Gtk.Template(resource_path="/io/github/d3msudo/velis/window.ui")
class VelisWindow(Adw.ApplicationWindow, SignalManagerMixin):
    __gtype_name__ = "VelisWindow"

    nav_view = Gtk.Template.Child()
    welcome_page = Gtk.Template.Child()
    extracted_page = Gtk.Template.Child()
    history_page = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        SignalManagerMixin.__init__(self)

        self.settings = get_settings()
        self.screenshot_service = get_screenshot_service()
        self.ocr_service = get_ocr_service()
        self.history_service = get_history_service()
        self.tts_service = get_tts_service()
        self.regex_service = get_regex_service()

        self.connect_tracked(self.screenshot_service, "screenshot-captured", self._on_screenshot_captured)
        self.connect_tracked(self.screenshot_service, "error", self._on_service_error)

        self._setup_actions()

    def _setup_actions(self):
        action_group = Gio.SimpleActionGroup.new()
        self.insert_action_group("win", action_group)

        screenshot_action = Gio.SimpleAction.new("screenshot_clicked", None)
        screenshot_action.connect("activate", lambda *_: self.screenshot_service.capture(self))
        action_group.add_action(screenshot_action)

        show_welcome_action = Gio.SimpleAction.new("show_welcome", None)
        show_welcome_action.connect("activate", lambda *_: self.nav_view.pop())
        action_group.add_action(show_welcome_action)

        show_history_action = Gio.SimpleAction.new("show_history", None)
        show_history_action.connect("activate", self._on_show_history)
        action_group.add_action(show_history_action)

        process_file_action = Gio.SimpleAction.new("process_file", GLib.VariantType.new("s"))
        process_file_action.connect("activate", self._on_process_file)
        action_group.add_action(process_file_action)

        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self._on_preferences)
        action_group.add_action(preferences_action)

    def _on_preferences(self, *args):
        dialog = PreferencesDialog()
        dialog.present(self)

    def _on_process_file(self, action, variant):
        path = variant.get_string()
        self._on_screenshot_captured(None, path)

    def _on_show_history(self, *args):
        self.history_page.refresh()
        self.nav_view.push_by_tag("history")

    def _on_screenshot_captured(self, service, path):
        lang = self.settings.get_string("active-language")
        get_atomic_manager().execute(
            self.ocr_service.extract_text,
            args=(path, lang),
            callback=lambda text: self._on_ocr_finished(text, path)
        )

    def _on_ocr_finished(self, text, path):
        if not text:
            text = "No text detected."

        # Smart Regex Scanning
        matches = self.regex_service.scan_text(text)
        if matches:
            header = "--- Smart Matches ---\n"
            for m in matches:
                header += f"{m['name']}: {m['value']}\n"
            text = header + "\n" + text

        self.extracted_page.set_text(text)
        self.extracted_page.set_image(path)
        self.history_service.add_entry(text, path)
        self.nav_view.push_by_tag("extracted")

    def _on_service_error(self, service, error):
        logger.error(f"Service error: {error}")
        toast = Adw.Toast.new(f"Error: {error}")
        self.get_first_child().add_toast(toast)
