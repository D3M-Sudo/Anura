# velis/services/tts_service.py
try:
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, GObject, Gst
    HAS_GST = True
except (ImportError, ValueError):
    HAS_GST = False
    class GObject:
        class Object: pass
        SignalFlags = type('SignalFlags', (), {'RUN_LAST': 1})

import os
import uuid

import gtts

from velis.utils.singleton import get_instance


class TtsService(GObject.Object if HAS_GST else object):
    if HAS_GST:
        __gsignals__ = {
            'playback-started': (GObject.SignalFlags.RUN_LAST, None, ()),
            'playback-stopped': (GObject.SignalFlags.RUN_LAST, None, ()),
        }

    def __init__(self):
        if HAS_GST:
            super().__init__()
            Gst.init(None)
            self.player = Gst.ElementFactory.make("playbin", "player")
            self._temp_file = None

            bus = self.player.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self._on_message)

    def _on_message(self, bus, message):
        if HAS_GST:
            if message.type == Gst.MessageType.EOS or message.type == Gst.MessageType.ERROR:
                self.stop()

    def speak(self, text, lang='en'):
        if not HAS_GST:
            return
        self.stop()
        filename = f"/tmp/velis_tts_{uuid.uuid4()}.mp3"
        tts = gtts.gTTS(text=text, lang=lang)
        tts.save(filename)
        self._temp_file = filename

        self.player.set_property("uri", "file://" + os.path.abspath(filename))
        self.player.set_state(Gst.State.PLAYING)
        self.emit('playback-started')

    def stop(self):
        if not HAS_GST:
            return
        self.player.set_state(Gst.State.NULL)
        if self._temp_file and os.path.exists(self._temp_file):
            try:
                os.remove(self._temp_file)
            except:
                pass
            self._temp_file = None
        self.emit('playback-stopped')

def get_tts_service():
    return get_instance(TtsService)
