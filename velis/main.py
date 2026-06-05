# velis/main.py
import sys

import gi

gi.require_version("Adw", "1")
gi.require_version("Gtk", "4.0")
from gi.repository import Adw, Gio

from velis.window import VelisWindow


class VelisApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id="io.github.d3msudo.velis",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)

    def do_activate(self):
        win = self.get_active_window()
        if not win:
            win = VelisWindow(application=self)
        win.present()

def main():
    app = VelisApplication()
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
