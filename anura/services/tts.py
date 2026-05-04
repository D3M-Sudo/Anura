# tts.py
#
# Copyright 2022-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import os
import threading
import time
from typing import ClassVar

from gi.repository import GLib, GObject, Gst
import gtts
from loguru import logger

from anura.services.settings import settings


class TTSService(GObject.GObject):
    """
    Service responsible for converting text to speech and managing audio playback
    using gTTS and GStreamer.
    """

    __gtype_name__ = "TTSService"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "speak": (GObject.SIGNAL_RUN_LAST, None, (str,)),
        "stop": (GObject.SIGNAL_RUN_LAST, None, (bool,)),
    }

    __slots__ = ("player",)

    _tld: str = "com"

    # Mapping Tesseract 3-letter → gTTS 2-letter ISO 639-1
    LANG_MAP: ClassVar[dict[str, str]] = {
        "eng": "en", "ita": "it", "fra": "fr", "deu": "de", "spa": "es",
        "por": "pt", "rus": "ru", "chi_sim": "zh-CN", "chi_tra": "zh-TW",
        "jpn": "ja", "kor": "ko", "ara": "ar", "hin": "hi", "tha": "th",
        "vie": "vi", "tur": "tr", "pol": "pl", "nld": "nl", "ces": "cs",
        "slk": "sk", "hun": "hu", "ron": "ro", "swe": "sv", "dan": "da",
        "nor": "no", "fin": "fi", "ell": "el", "heb": "he", "ind": "id",
        "ukr": "uk", "srp": "sr", "hrv": "hr", "slv": "sl", "bul": "bg",
        "lit": "lt", "lav": "lv", "est": "et", "mkd": "mk", "cat": "ca",
        "eus": "eu", "glg": "gl", "hye": "hy", "kat": "ka", "aze": "az",
        "ben": "bn", "tam": "ta", "tel": "te", "mal": "ml", "kan": "kn",
        "ori": "or", "pan": "pa", "guj": "gu", "mar": "mr", "nep": "ne",
        "sin": "si", "urd": "ur", "uzb": "uz", "kaz": "kk", "kir": "ky",
        "tgk": "tg", "lao": "lo", "mya": "my", "khm": "km",
        # Historical/specialty variants (fallback to modern equivalent)
        "lat": "la", "grc": "el",  # Ancient Greek → Modern Greek
        "enm": "en", "frm": "fr",  # Middle English/French → Modern
        # Vertical/special variants
        "jpn_vert": "ja", "kor_vert": "ko", "chi_sim_vert": "zh-CN",
        "chi_tra_vert": "zh-TW", "ita_old": "it", "eng_old": "en",
        "fra_old": "fr", "deu_old": "de", "spa_old": "es",
    }

    _gtts_languages: dict | None = None
    _bus_watch_active: bool = False
    _bus_watch_setup_in_progress: bool = False
    _bus: Gst.Bus | None = None
    _bus_message_handler_id: int | None = None
    _cleanup_lock: threading.Lock = threading.Lock()
    _bus_watch_lock: threading.Lock = threading.Lock()

    @classmethod
    def get_supported_gtts_languages(cls) -> dict:
        """Cache of gTTS supported languages."""
        if cls._gtts_languages is None:
            try:
                cls._gtts_languages = gtts.lang.tts_langs()
            except Exception:
                # Network or API error - fallback to empty dict
                cls._gtts_languages = {}
        return cls._gtts_languages

    @staticmethod
    def map_tesseract_to_gtts(tess_code: str) -> str:
        """Map Tesseract language code to gTTS-compatible ISO 639-1 code."""
        # Normalize to lowercase for case-insensitive matching
        tess_code = tess_code.lower()

        # 1. Direct lookup in explicit map
        if tess_code in TTSService.LANG_MAP:
            return TTSService.LANG_MAP[tess_code]

        # 2. Validate 2-char prefix against supported languages
        supported = TTSService.get_supported_gtts_languages()
        # Only use 2-char codes that look like valid ISO 639-1 (lowercase letters only)
        # Require at least 2 characters to prevent single-char false matches
        if len(tess_code) >= 2:
            two_char = tess_code[:2]
            # Must be exactly 2 lowercase letters (ISO 639-1 format)
            if len(two_char) == 2 and two_char.isalpha() and two_char.islower() and two_char in supported:
                return two_char

        # 3. Fallback to English
        logger.warning(f"Anura TTS: No mapping for '{tess_code}', falling back to 'en'")
        return "en"

    # Use XDG_CACHE_HOME for temporary files (not XDG_DATA_HOME).
    # Cache dir is the correct location for ephemeral data; data dir is for
    # persistent user data like tessdata models.
    _cache_home = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    _speech_dir: str = os.path.join(_cache_home, "anura")

    _current_speech_file: str | None = None

    player: Gst.Element | None = None

    def __init__(self):
        super().__init__()
        os.makedirs(self._speech_dir, exist_ok=True)
        # Initialize GStreamer only once to prevent crashes on multiple instantiations
        if not Gst.is_initialized():
            Gst.init(None)

    @staticmethod
    def get_languages():
        """Fetch available languages supported by gTTS."""
        return gtts.lang.tts_langs()

    def generate(self, text: str, lang: str = "en") -> str:
        """Generates MP3. Raises exception on failure for errorback handling."""
        # Input validation: avoid unnecessary gTTS calls for empty/whitespace text
        if not text or not text.strip():
            logger.debug("Anura TTS: Empty text provided, returning empty path")
            return ""
        timestamp = int(time.monotonic() * 1000)
        filepath = os.path.join(self._speech_dir, f"speech_{timestamp}.mp3")

        tts = gtts.gTTS(text, lang=lang, tld=self._tld)
        logger.info(f"Anura TTS: Generating speech for language: {lang}")
        try:
            tts.save(filepath)
        except Exception as e:
            logger.error(f"Anura TTS: Failed to save speech file: {e}")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass
            raise

        logger.debug("Anura TTS: Speech file saved to cache directory")

        self._current_speech_file = filepath
        GLib.idle_add(self.emit, "speak", filepath)
        return filepath

    def get_effective_language(self, ocr_lang: str) -> str:
        """Return TTS language: user preference or fallback to OCR language."""
        tts_lang = settings.get_string("tts-language")
        if tts_lang:
            return tts_lang
        # Fallback: map OCR language to TTS
        return self.map_tesseract_to_gtts(ocr_lang)

    def play(self, speech_file: str):
        """Plays the generated speech file using GStreamer's playbin."""
        filepath = os.path.abspath(speech_file)

        self.player = Gst.ElementFactory.make("playbin3", "player")
        if not self.player:
            logger.error("Anura TTS Error: Failed to create GStreamer playbin.")
            return

        self.player.set_property("uri", f"file://{filepath}")

        # Read volume from settings and clamp to valid range
        volume = max(0.0, min(1.0, settings.get_double("tts-volume")))
        self.player.set_property("volume", volume)

        self._bus = self.player.get_bus()

        # Thread-safety: schedule bus operations on main thread via idle_add
        GLib.idle_add(self._setup_bus_watch)

        self.player.set_state(Gst.State.PLAYING)

    def _setup_bus_watch(self) -> bool:
        """Set up GStreamer bus signal watch on main thread."""
        # Thread-safe guard against concurrent setup calls
        with self._bus_watch_lock:
            if self._bus_watch_setup_in_progress:
                return False
            # Check if bus watch is already active to prevent duplicates
            if self._bus_watch_active and self._bus_message_handler_id is not None:
                return False
            self._bus_watch_setup_in_progress = True
        try:
            if self._bus is not None:
                # Double-check under lock to prevent race conditions
                with self._bus_watch_lock:
                    if not self._bus_watch_active:
                        self._bus.add_signal_watch()
                        self._bus_watch_active = True
                        self._bus_message_handler_id = self._bus.connect("message", self.on_gst_message)
        finally:
            with self._bus_watch_lock:
                self._bus_watch_setup_in_progress = False
        return False  # Don't repeat

    def on_gst_message(self, _bus, message: Gst.Message):
        """Handle GStreamer bus messages; clean up temp file on EOS."""
        if message.type == Gst.MessageType.EOS:
            logger.info("Anura TTS: Playback finished.")
            with self._cleanup_lock:
                self._cleanup_gst_resources()
                # Cleanup temp file after playback
                filepath = self._current_speech_file
                self._current_speech_file = None
            # File operations outside the lock to minimize lock time
            if filepath and os.path.exists(filepath):
                try:
                    os.unlink(filepath)
                    logger.debug("Anura TTS: Cleaned up temporary speech file")
                except Exception:
                    logger.warning("Anura TTS: Failed to cleanup temporary speech file")
            GLib.idle_add(self.emit, "stop", True)
        elif message.type == Gst.MessageType.ERROR:
            err, _debug = message.parse_error()
            logger.error(f"Anura TTS Error: GStreamer playback error: {err}")
            with self._cleanup_lock:
                self._cleanup_gst_resources()
            GLib.idle_add(self.emit, "stop", False)

    def _cleanup_gst_resources(self) -> None:
        """Remove signal watcher and release player resources."""
        if self.player:
            # Explicitly disconnect the bus message handler
            if self._bus_message_handler_id is not None and self._bus is not None:
                try:
                    self._bus.disconnect(self._bus_message_handler_id)
                except (TypeError, RuntimeError):
                    pass  # Already disconnected or invalid
                self._bus_message_handler_id = None

            if self._bus_watch_active and self._bus:
                try:
                    self._bus.remove_signal_watch()
                except (GLib.Error, RuntimeError):
                    pass  # Already removed or invalid
                self._bus_watch_active = False
                self._bus = None
            self.player.set_state(Gst.State.NULL)
            self.player = None

    def stop_speaking(self) -> None:
        """Interrupts playback and cleans up temp file."""
        with self._cleanup_lock:
            if self.player:
                logger.info("Anura TTS: Stopping playback.")
                self._cleanup_gst_resources()

            # Capture and clear filepath atomically under lock
            filepath = self._current_speech_file
            self._current_speech_file = None

        # File operations outside the lock to minimize lock time
        if filepath and os.path.exists(filepath):
            try:
                os.unlink(filepath)
                logger.debug("Anura TTS: Cleaned up temporary speech file on stop")
            except (OSError, PermissionError):
                logger.warning("Anura TTS: Failed to cleanup temporary speech file on stop")


# Singleton instance
ttsservice = TTSService()
