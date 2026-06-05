# velis/widgets/preferences_dialog.py
from velis.services.settings_service import get_settings

try:
    import gi
    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, Gio, Gtk
    HAS_GTK = True
except (ImportError, ValueError):
    HAS_GTK = False
    class Adw:
        class PreferencesDialog:
            pass
    class Gtk:
        def Template(*args, **kwargs):
            return lambda x: x

@Gtk.Template(resource_path="/io/github/d3msudo/velis/preferences_dialog.ui")
class PreferencesDialog(Adw.PreferencesDialog):
    __gtype_name__ = "PreferencesDialog"

    if HAS_GTK:
        language_row = Gtk.Template.Child()
        translate_endpoint_row = Gtk.Template.Child()
        translate_api_key_row = Gtk.Template.Child()

    def __init__(self, **kwargs):
        if HAS_GTK:
            super().__init__(**kwargs)
            self.settings = get_settings()
            self._setup_bindings()

    def _setup_bindings(self):
        if not HAS_GTK:
            return

        model = Gtk.StringList.new(["eng", "ita", "fra", "deu", "spa"])
        self.language_row.set_model(model)

        self.settings.settings.bind(
            "translate-endpoint",
            self.translate_endpoint_row,
            "text",
            Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.settings.bind(
            "translate-api-key",
            self.translate_api_key_row,
            "text",
            Gio.SettingsBindFlags.DEFAULT
        )

        self.language_row.connect("notify::selected", self._on_language_changed)

    def _on_language_changed(self, *args):
        selected = self.language_row.get_selected_item().get_string()
        self.settings.set_string("active-language", selected)
