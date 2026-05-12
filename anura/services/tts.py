# tts.py
#
# Copyright 2022-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib
import os
import threading
import time
from typing import ClassVar

import gi

# Set GTK version requirements before imports
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")
gi.require_version("Gst", "1.0")

from gi.repository import GLib, GObject, Gst  # noqa: E402
import gtts  # noqa: E402
from loguru import logger  # noqa: E402
import requests  # noqa: E402

from anura.services.settings import settings  # noqa: E402
from anura.utils.singleton import get_instance  # noqa: E402


class TTSService(GObject.GObject):
    """
    Service responsible for converting text to speech and managing audio playback
    using gTTS and GStreamer.
    """

    __gtype_name__ = "TTSService"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "speak": (GObject.SignalFlags.RUN_LAST, None, (str,)),
        "stop": (GObject.SignalFlags.RUN_LAST, None, (bool,)),
        "paused": (GObject.SignalFlags.RUN_LAST, None, (bool,)),
    }

    __slots__ = ("player",)

    _tld: str = "com"

    # Mapping Tesseract 3-letter → gTTS 2-letter ISO 639-1
    LANG_MAP: ClassVar[dict[str, str]] = {
        "eng": "en",
        "ita": "it",
        "fra": "fr",
        "deu": "de",
        "spa": "es",
        "por": "pt",
        "rus": "ru",
        "chi_sim": "zh-CN",
        "chi_tra": "zh-TW",
        "jpn": "ja",
        "kor": "ko",
        "ara": "ar",
        "hin": "hi",
        "tha": "th",
        "vie": "vi",
        "tur": "tr",
        "pol": "pl",
        "nld": "nl",
        "ces": "cs",
        "slk": "sk",
        "hun": "hu",
        "ron": "ro",
        "swe": "sv",
        "dan": "da",
        "nor": "no",
        "fin": "fi",
        "ell": "el",
        "heb": "he",
        "ind": "id",
        "ukr": "uk",
        "srp": "sr",
        "hrv": "hr",
        "slv": "sl",
        "bul": "bg",
        "lit": "lt",
        "lav": "lv",
        "est": "et",
        "mkd": "mk",
        "cat": "ca",
        "eus": "eu",
        "glg": "gl",
        "hye": "hy",
        "kat": "ka",
        "aze": "az",
        "ben": "bn",
        "tam": "ta",
        "tel": "te",
        "mal": "ml",
        "kan": "kn",
        "ori": "or",
        "pan": "pa",
        "guj": "gu",
        "mar": "mr",
        "nep": "ne",
        "sin": "si",
        "urd": "ur",
        "uzb": "uz",
        "kaz": "kk",
        "kir": "ky",
        "tgk": "tg",
        "lao": "lo",
        "mya": "my",
        "khm": "km",
        # Historical/specialty variants (fallback to modern equivalent)
        "lat": "la",
        "grc": "el",  # Ancient Greek → Modern Greek
        "enm": "en",
        "frm": "fr",  # Middle English/French → Modern
        # Vertical/special variants
        "jpn_vert": "ja",
        "kor_vert": "ko",
        "chi_sim_vert": "zh-CN",
        "chi_tra_vert": "zh-TW",
        "ita_old": "it",
        "eng_old": "en",
        "fra_old": "fr",
        "deu_old": "de",
        "spa_old": "es",
    }

    _gtts_languages: dict | None = None
    _bus_watch_active: bool = False
    _bus_watch_setup_in_progress: bool = False
    _bus: Gst.Bus | None = None
    _bus_message_handler_id: int | None = None
    _cleanup_lock: threading.Lock = threading.Lock()
    _bus_watch_lock: threading.Lock = threading.Lock()
    _state_lock: threading.Lock = threading.Lock()
    _init_lock: threading.Lock = threading.Lock()

    @classmethod
    def get_supported_gtts_languages(cls) -> dict:
        """Cache of gTTS supported languages."""
        if cls._gtts_languages is None:
            try:
                cls._gtts_languages = gtts.lang.tts_langs()
            except (requests.RequestException, ValueError, OSError):
                # Network or API error - fallback to empty dict
                cls._gtts_languages = {}
        return cls._gtts_languages

    @staticmethod
    def map_tesseract_to_gtts(tess_code: str) -> str:
        """Map Tesseract language code to gTTS-compatible ISO 639-1 code."""
        if tess_code is None:
            return "en"  # Default to English

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

    def __init__(self) -> None:
        super().__init__()
        logger.debug("Anura TTSService: Initializing TTS service singleton")
        os.makedirs(self._speech_dir, exist_ok=True)
        # Initialize GStreamer only once to prevent crashes on multiple instantiations
        with TTSService._init_lock:
            if not Gst.is_initialized():
                logger.info("Anura TTSService: Initializing GStreamer pipeline")
                Gst.init(None)
            else:
                logger.debug("Anura TTSService: GStreamer already initialized")
        # Initialize player slot to prevent AttributeError before play() is called
        self.player = None
        logger.debug("Anura TTSService: TTS service initialization complete")

    @staticmethod
    def get_languages() -> dict:
        """Fetch available languages supported by gTTS."""
        return gtts.lang.tts_langs()

    def generate(self, text: str, lang: str = "en") -> str:
        """Thread-safe MP3 generation with proper state management."""
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
        except (SystemExit, KeyboardInterrupt):
            # Re-raise system exceptions that should terminate the application
            raise
        except (requests.RequestException, OSError) as e:
            logger.error(f"Anura TTS: Failed to save speech file: {e}")
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError as e:
                    logger.debug(f"Anura TTS: Failed to remove temporary speech file during cleanup: {e}")
            raise

        logger.debug("Anura TTS: Speech file saved to cache directory")

        # Thread-safe update of current speech file
        with self._state_lock:
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

    def play(self, speech_file: str) -> None:
        """Plays the generated speech file using GStreamer's playbin."""
        filepath = os.path.abspath(speech_file)

        # If already playing or paused, don't recreate player
        if self.player:
            _, state, _ = self.player.get_state(0)
            if state == Gst.State.PAUSED:
                self.resume()
                return

        self.player = Gst.ElementFactory.make("playbin3", "player")
        if not self.player:
            logger.error("Anura TTS Error: Failed to create GStreamer playbin.")
            GLib.idle_add(self.emit, "stop", False)
            return

        self.player.set_property("uri", f"file://{filepath}")

        # Read volume from settings and clamp to valid range
        volume = max(0.0, min(1.0, settings.get_double("tts-volume")))
        self.player.set_property("volume", volume)
        logger.debug(f"Anura TTSService: Set volume to {volume:.2f}")

        self._bus = self.player.get_bus()

        # Thread-safety: schedule bus operations on main thread via idle_add
        GLib.idle_add(self._setup_bus_watch)

        logger.info("Anura TTSService: Setting GStreamer state to PLAYING")
        self.player.set_state(Gst.State.PLAYING)

    def _setup_bus_watch(self) -> bool:
        """Thread-safe GStreamer bus signal watch setup on main thread."""
        # Thread-safe guard against concurrent setup calls
        with self._bus_watch_lock:
            if self._bus_watch_setup_in_progress:
                return False
            # Check if bus watch is already active to prevent duplicates
            if self._bus_watch_active and self._bus_message_handler_id is not None:
                return False

            self._bus_watch_setup_in_progress = True

            try:
                if self._bus is not None and not self._bus_watch_active:
                    # Setup bus watch within the same lock to prevent race conditions
                    self._bus.add_signal_watch()
                    self._bus_watch_active = True
                    self._bus_message_handler_id = self._bus.connect("message", self.on_gst_message)
                    logger.debug("Anura TTS: Bus watch setup completed")
            finally:
                self._bus_watch_setup_in_progress = False

        return False  # Don't repeat

    def on_gst_message(self, _bus: Gst.Bus, message: Gst.Message) -> None:
        """Thread-safe GStreamer bus message handling.

        This is a Gst.Bus "message" signal callback, not a GLib timeout, so
        the return value is ignored — don't return False/True for "don't
        repeat".
        """
        if message.type == Gst.MessageType.EOS:
            logger.info("Anura TTSService: GStreamer state changed to EOS (End of Stream)")
            with self._cleanup_lock:
                self._cleanup_gst_resources()
                # Thread-safe cleanup of temp file after playback
                with self._state_lock:
                    filepath = self._current_speech_file
                    self._current_speech_file = None

                # Atomic file cleanup: check existence and remove inside lock
                if filepath and os.path.exists(filepath):
                    try:
                        os.unlink(filepath)
                        logger.debug("Anura TTS: Cleaned up temporary speech file")
                    except (OSError, GLib.Error):
                        logger.warning("Anura TTS: Failed to cleanup temporary speech file")
                elif filepath:
                    logger.debug("Anura TTS: Cleanup skipped, file already removed")
            GLib.idle_add(self.emit, "stop", True)
            return

        elif message.type == Gst.MessageType.ERROR:
            err, _debug = message.parse_error()
            logger.error(f"Anura TTS Error: GStreamer playback error: {err}")
            with self._cleanup_lock:
                self._cleanup_gst_resources()
                # Ensure bus watch is cleaned up on error
                if self._bus_watch_active and self._bus:
                    with contextlib.suppress(GLib.Error, RuntimeError):
                        self._bus.remove_signal_watch()
                        self._bus_watch_active = False
            GLib.idle_add(self.emit, "stop", False)

    def _cleanup_gst_resources(self) -> None:
        """Remove signal watcher and release player resources."""
        if self.player:
            logger.debug("Anura TTSService: Starting GStreamer resource cleanup")

            # Disconnect bus message handler if connected
            if self._bus_message_handler_id is not None:
                if self._bus and self._bus_message_handler_id is not None:
                    self._bus.disconnect(self._bus_message_handler_id)
                    logger.debug("Anura TTSService: Disconnected bus message handler")
                self._bus_message_handler_id = None

            if self._bus_watch_active and self._bus:
                with contextlib.suppress(GLib.Error, RuntimeError):
                    self._bus.remove_signal_watch()
                    logger.debug("Anura TTSService: Removed signal watch")
                self._bus_watch_active = False
                self._bus = None
            logger.info("Anura TTSService: Setting GStreamer state to NULL")
            self.player.set_state(Gst.State.NULL)
            self.player = None
            logger.debug("Anura TTSService: GStreamer resource cleanup complete")

    def stop_speaking(self) -> None:
        """Thread-safe interruption of playback and cleanup."""
        with self._cleanup_lock:
            if self.player:
                logger.info("Anura TTS: Stopping playback.")
                self._cleanup_gst_resources()

            # Thread-safe capture and clear filepath
            with self._state_lock:
                filepath = self._current_speech_file
                self._current_speech_file = None

            # Atomic file cleanup: check existence and remove inside lock
            if filepath and os.path.exists(filepath):
                try:
                    os.unlink(filepath)
                    logger.debug("Anura TTS: Cleaned up temporary speech file on stop")
                except (OSError, PermissionError):
                    logger.warning("Anura TTS: Failed to cleanup temporary speech file on stop")
            elif filepath:
                logger.debug("Anura TTS: Cleanup skipped on stop, file already removed")

            # Fix Bug 3: Emit stop signal to ensure proper UI cleanup
            GLib.idle_add(self.emit, "stop", False)

    def pause(self) -> None:
        """Pauses the GStreamer player."""
        if self.player:
            logger.info("Anura TTSService: Setting GStreamer state to PAUSED")
            self.player.set_state(Gst.State.PAUSED)
            GLib.idle_add(self.emit, "paused", True)

    def resume(self) -> None:
        """Resumes the GStreamer player."""
        if self.player:
            logger.info("Anura TTSService: Setting GStreamer state to PLAYING (resume)")
            self.player.set_state(Gst.State.PLAYING)
            GLib.idle_add(self.emit, "paused", False)

    def is_playing(self) -> bool:
        """Returns True if the GStreamer player is in the PLAYING state."""
        if not self.player:
            return False
        _, state, _ = self.player.get_state(0)
        return state == Gst.State.PLAYING

    def toggle_pause(self) -> None:
        """Toggles between paused and playing states."""
        if not self.player:
            return

        _, state, _ = self.player.get_state(0)
        if state == Gst.State.PLAYING:
            self.pause()
        elif state == Gst.State.PAUSED:
            self.resume()

    def cleanup(self) -> None:
        """Complete cleanup for application shutdown - prevents broken pipe errors."""
        with self._cleanup_lock:
            if self.player:
                logger.debug("Anura TTS: Performing shutdown cleanup")
                self._cleanup_gst_resources()

            # Clean up any remaining temporary files
            with self._state_lock:
                filepath = self._current_speech_file
                self._current_speech_file = None

            if filepath and os.path.exists(filepath):
                try:
                    os.unlink(filepath)
                    logger.debug("Anura TTS: Cleaned up temporary speech file on shutdown")
                except (OSError, PermissionError):
                    logger.debug("Anura TTS: Failed to cleanup temporary speech file on shutdown")


# Thread-safe singleton instance for global app access
def get_tts_service() -> TTSService:
    """Get thread-safe TTS service singleton."""
    return get_instance(TTSService)


# Global singleton instance for direct import
ttsservice = get_tts_service()
