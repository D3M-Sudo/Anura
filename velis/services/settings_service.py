# velis/services/settings_service.py
try:
    from gi.repository import Gio
    HAS_GIO = True
except (ImportError, ValueError):
    HAS_GIO = False

from velis.utils.singleton import get_instance


class SettingsService:
    def __init__(self):
        if HAS_GIO:
            self.settings = Gio.Settings.new("io.github.d3msudo.velis")
        else:
            self.settings = None

    def get_string(self, key):
        if self.settings:
            return self.settings.get_string(key)
        return ""

    def set_string(self, key, value):
        if self.settings:
            self.settings.set_string(key, value)

    def get_int(self, key):
        if self.settings:
            return self.settings.get_int(key)
        return 0

    def set_int(self, key, value):
        if self.settings:
            self.settings.set_int(key, value)

def get_settings():
    return get_instance(SettingsService)
