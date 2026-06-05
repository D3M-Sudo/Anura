# velis/widgets/extracted_page.py
try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, Gdk, Gio, GLib, Gtk
    HAS_GTK = True
except (ImportError, ValueError):
    HAS_GTK = False
    class Gtk:
        class Box: pass
        def Template(*args, **kwargs): return lambda x: x
    class Gio:
        class AsyncResult: pass

from loguru import logger

from velis.core.atomic_task_manager import get_atomic_manager
from velis.services.settings_service import get_settings
from velis.services.translation_service import get_translation_service
from velis.services.tts_service import get_tts_service
from velis.utils.file_utils import save_text_to_file


@Gtk.Template(resource_path="/io/github/d3msudo/velis/extracted_page.ui")
class ExtractedPage(Gtk.Box):
    __gtype_name__ = "ExtractedPage"

    if HAS_GTK:
        text_view = Gtk.Template.Child()
        source_image = Gtk.Template.Child()
        side_by_side_toggle = Gtk.Template.Child()

    def __init__(self, **kwargs):
        if HAS_GTK:
            super().__init__(**kwargs)
        self.tts_service = get_tts_service()
        self.translation_service = get_translation_service()
        self.settings = get_settings()

    def set_text(self, text):
        if HAS_GTK:
            buffer = self.text_view.get_buffer()
            buffer.set_text(text)

    def set_image(self, path):
        if HAS_GTK:
            self.source_image.set_from_file(path)

    if HAS_GTK:
        @Gtk.Template.Callback()
        def on_back_clicked(self, button):
            self.activate_action("win.show_welcome", None)

        @Gtk.Template.Callback()
        def on_copy_clicked(self, button):
            buffer = self.text_view.get_buffer()
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            clipboard = self.get_clipboard()
            clipboard.set(text)

        @Gtk.Template.Callback()
        def on_save_clicked(self, button):
            dialog = Gtk.FileDialog.new()
            dialog.set_initial_name("extracted_text.txt")
            win = self.get_root()
            dialog.save(win, None, self._on_save_response)

        def _on_save_response(self, dialog, result):
            try:
                file = dialog.save_finish(result)
                if file:
                    path = file.get_path()
                    buffer = self.text_view.get_buffer()
                    text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
                    if save_text_to_file(text, path):
                        logger.info(f"Saved text to {path}")
            except Exception as e:
                logger.error(f"Save error: {e}")

        @Gtk.Template.Callback()
        def on_listen_clicked(self, button):
            buffer = self.text_view.get_buffer()
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            self.tts_service.speak(text)

        @Gtk.Template.Callback()
        def on_translate_clicked(self, button):
            buffer = self.text_view.get_buffer()
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            target_lang = "en" # Should be configurable in a popover

            get_atomic_manager().execute(
                self.translation_service.translate,
                args=(text, target_lang),
                callback=self._on_translation_finished,
                errorback=lambda e: logger.error(f"Translation failed: {e}")
            )

        def _on_translation_finished(self, translated_text):
            # Append translated text or replace? Let's append with a separator
            buffer = self.text_view.get_buffer()
            current_text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            new_text = current_text + "\n\n--- Translation ---\n\n" + translated_text
            buffer.set_text(new_text)
