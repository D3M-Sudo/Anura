# tts.py
#
# Copyright 2022-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import os

import gtts
from gi.repository import GObject, Gst
from loguru import logger


class TTSService(GObject.GObject):
    """
    Service responsible for converting text to speech and managing audio playback
    using gTTS and GStreamer.
    """

    __gtype_name__ = "TTSService"

    __gsignals__ = {
        "speak": (GObject.SIGNAL_RUN_LAST, None, (str,)),
        "stop": (GObject.SIGNAL_RUN_LAST, None, (bool,)),
    }

    _tld: str = "com"

    # FIX: use XDG_CACHE_HOME for temporary files, not XDG_DATA_HOME.
    # Cache dir is the correct location for ephemeral data; data dir is for
    # persistent user data like tessdata models.
    _cache_home = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    _speech_dir: str = os.path.join(_cache_home, "anura")
    _speech_filepath: str = os.path.join(_speech_dir, "speech.mp3")

    player: Gst.Element | None = None

    def __init__(self):
        super().__init__()
        os.makedirs(self._speech_dir, exist_ok=True)
        Gst.init(None)

    @staticmethod
    def get_languages():
        """Fetch available languages supported by gTTS."""
        return gtts.lang.tts_langs()

    def generate(self, text: str, lang: str = "en") -> str | None:
        """Generates an MP3 file from text using Google Text-to-Speech."""
        try:
            tts = gtts.gTTS(text, lang=lang, tld=self._tld)
            logger.info(f"Anura TTS: Generating speech for language: {lang}")
            tts.save(self._speech_filepath)
            logger.debug(f"Anura TTS: Speech file saved to {self._speech_filepath}")
            self.emit("speak", self._speech_filepath)
            return self._speech_filepath
        except Exception as e:
            logger.error(f"Anura TTS Error: Failed to generate speech. {e}")
            return None

    def play(self, speech_file: str):
        """Plays the generated speech file using GStreamer's playbin."""
        filepath = os.path.abspath(speech_file)

        self.player = Gst.ElementFactory.make("playbin", "player")
        if not self.player:
            logger.error("Anura TTS Error: Failed to create GStreamer playbin.")
            return

        self.player.set_property("uri", f"file://{filepath}")
        self.player.set_property("volume", 1.0)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_gst_message)
        self.player.set_state(Gst.State.PLAYING)

    def on_gst_message(self, _bus, message: Gst.Message):
        """Handle GStreamer bus messages (EOS/Error)."""
        if message.type == Gst.MessageType.EOS:
            logger.info("Anura TTS: Playback finished.")
            self.player.set_state(Gst.State.NULL)
            self.emit("stop", True)
        elif message.type == Gst.MessageType.ERROR:
            err, _debug = message.parse_error()
            logger.error(f"Anura TTS Error: GStreamer playback error: {err}")
            self.player.set_state(Gst.State.NULL)
            self.emit("stop", False)

    def stop_speaking(self):
        """Interrupts current speech playback."""
        if self.player:
            logger.info("Anura TTS: Stopping playback.")
            self.player.set_state(Gst.State.NULL)


# Singleton instance
ttsservice = TTSService()
