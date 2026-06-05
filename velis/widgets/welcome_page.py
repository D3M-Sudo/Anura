# velis/widgets/welcome_page.py
try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")
    from gi.repository import Gtk, Gdk, Adw, GLib
    HAS_GTK = True
except (ImportError, ValueError):
    HAS_GTK = False
    class Gtk:
        class Box: pass
        def Template(*args, **kwargs): return lambda x: x
    class GLib:
        def Variant(*args, **kwargs): return None

@Gtk.Template(resource_path="/io/github/d3msudo/velis/welcome_page.ui")
class WelcomePage(Gtk.Box):
    __gtype_name__ = "WelcomePage"

    def __init__(self, **kwargs):
        if HAS_GTK:
            super().__init__(**kwargs)
            self._setup_dnd()

    def _setup_dnd(self):
        if not HAS_GTK:
            return
        target = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        target.connect("drop", self._on_drop)
        self.add_controller(target)

    def _on_drop(self, target, value, x, y):
        if isinstance(value, Gdk.FileList):
            files = value.get_files()
            if files:
                file_path = files[0].get_path()
                self.activate_action("win.process_file", GLib.Variant("s", file_path))
                return True
        return False

    if HAS_GTK:
        @Gtk.Template.Callback()
        def on_screenshot_clicked(self, button):
            self.activate_action("win.screenshot_clicked", None)

        @Gtk.Template.Callback()
        def on_history_clicked(self, button):
            self.activate_action("win.show_history", None)
