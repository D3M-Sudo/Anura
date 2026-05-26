# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
from gettext import gettext as _
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
        "error": (GObject.SignalFlags.RUN_LAST, None, (str,)),
    }

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
        "afr": "af",
        "amh": "am",
        "aze_cyrl": "az",
        "bel": "be",
        "bod": "bo",
        "bos": "bs",
        "bre": "br",
        "ceb": "ceb",
        "cos": "co",
        "cym": "cy",
        "epo": "eo",
        "fas": "fa",
        "fil": "tl",
        "gla": "gd",
        "gle": "ga",
        "hat": "ht",
        "iku": "iu",
        "isl": "is",
        "jav": "jw",
        "kat_old": "ka",
        "ltz": "lb",
        "mlt": "mt",
        "mon": "mn",
        "mri": "mi",
        "msa": "ms",
        "oci": "oc",
        "pus": "ps",
        "que": "qu",
        "san": "sa",
        "snd": "sd",
        "sqi": "sq",
        "srp_latn": "sr",
        "sun": "su",
        "swa": "sw",
        "tat": "tt",
        "tir": "ti",
        "uig": "ug",
        "uzb_cyrl": "uz",
        "yid": "yi",
        "yor": "yo",
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

    @classmethod
    def get_supported_gtts_languages(cls) -> dict:
        """Cache of gTTS supported languages (class-level fallback)."""
        if not hasattr(cls, "_gtts_cache") or not cls._gtts_cache:
            try:
                # Use a background task or initialize early to avoid blocking UI.
                # Here we ensure it's at least initialized if accessed.
                cls._gtts_cache = gtts.lang.tts_langs()
            except (requests.RequestException, ValueError, OSError) as e:
                logger.debug(f"Anura TTS: Failed to fetch gTTS languages: {e}")
                cls._gtts_cache = {}
        return cls._gtts_cache

    @classmethod
    def map_tesseract_to_gtts(cls, tess_code: str) -> str | None:
        """
        Map Tesseract language code to gTTS-compatible ISO 639-1 code.
        Returns None if no mapping or fallback is available.
        """
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

        # 3. Fallback: log warning and return None for explicit UI handling
        logger.warning(f"Anura TTS: No mapping for '{tess_code}'")
        return None

    # Use XDG_CACHE_HOME for temporary files (not XDG_DATA_HOME).
    # Cache dir is the correct location for ephemeral data; data dir is for
    # persistent user data like tessdata models.
    _cache_home = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
    _speech_dir: str = os.path.join(_cache_home, "anura")

    def __init__(self) -> None:
        super().__init__()
        logger.debug("Anura TTSService: Initializing TTS service singleton")

        # Pre-cache supported languages in background to avoid UI hang during first use
        threading.Thread(target=self.get_supported_gtts_languages, daemon=True).start()
        os.makedirs(self._speech_dir, exist_ok=True)

        # Initialize all instance attributes (fixes class-level state
        # leaking between instances)
        self._gtts_languages: dict | None = None
        self._bus_watch_active: bool = False
        self._bus_watch_setup_in_progress: bool = False
        self._bus: Gst.Bus | None = None
        self._bus_message_handler_id: int | None = None
        self._current_speech_file: str | None = None
        self._cleanup_lock = threading.Lock()
        self._bus_watch_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._init_lock = threading.Lock()
        # Monotonic generation counter: stale bus callbacks from a torn-down
        # pipeline are ignored when the counter no longer matches.
        self._generation_id: int = 0
        self.player = None

        # Initialize GStreamer only once to prevent crashes on multiple instantiations
        if not Gst.is_initialized():
            logger.info("Anura TTSService: Initializing GStreamer pipeline")
            Gst.init(None)
        else:
            logger.debug("Anura TTSService: GStreamer already initialized")

        logger.debug("Anura TTSService: TTS service initialization complete")

    @staticmethod
    def get_languages() -> dict:
        """Fetch available languages supported by gTTS."""
        return gtts.lang.tts_langs()

    def generate(self, text: str, lang: str = "en") -> str:
        """Thread-safe MP3 generation with proper state management."""
        # Clean up any previously orphaned file from this instance before starting new generation
        with self._state_lock:
            if self._current_speech_file and os.path.exists(self._current_speech_file):
                try:
                    os.unlink(self._current_speech_file)
                except OSError:
                    pass
            self._current_speech_file = None

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
                except OSError:
                    logger.debug("Anura TTS: Failed to remove temporary speech file during cleanup")
            # Don't re-raise: AtomicTaskManager errorback handles exceptions from
            # the worker thread.  Let it catch the return value "" instead.
            return ""

        logger.debug("Anura TTS: Speech file saved to cache directory")

        # Thread-safe update of current speech file
        with self._state_lock:
            self._current_speech_file = filepath

        GLib.idle_add(self.emit, "speak", filepath)
        return filepath

    def get_effective_language(self, ocr_lang: str) -> str | None:
        """Return TTS language: user preference or fallback to OCR language."""
        tts_lang = settings.get_string("tts-language")
        if tts_lang:
            return tts_lang
        # Fallback: map OCR language to TTS
        return self.map_tesseract_to_gtts(ocr_lang)

    def play(self, speech_file: str) -> None:
        """Plays the generated speech file using GStreamer's playbin."""
        filepath = os.path.abspath(speech_file)

        # If a player already exists (PLAYING or PAUSED), tear it down cleanly
        # before creating a new one for the new file.
        # We call _cleanup_gst_resources() directly — NOT stop_speaking() — to
        # avoid emitting a spurious "stop" signal that would reset UI state while
        # the new audio is already being set up.
        with self._cleanup_lock:
            if self.player:
                self._cleanup_gst_resources()
            # Bump generation counter to invalidate stale bus callbacks.
            with self._state_lock:
                self._generation_id += 1
                current_gen = self._generation_id

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

        # Order of operations is critical:
        # 1. Get bus
        # 2. Add signal watch and connect handler
        # 3. ONLY THEN set state to PLAYING
        self._bus = self.player.get_bus()

        # Setup bus watch synchronously before starting playback to avoid race
        # conditions on End-of-Stream (EOS) events for short audio clips.
        self._setup_bus_watch(current_gen)

        logger.info("Anura TTSService: Setting GStreamer state to PLAYING")
        self.player.set_state(Gst.State.PLAYING)

    def _setup_bus_watch(self, generation_id: int) -> bool:
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
                    self._bus_message_handler_id = self._bus.connect(
                        "message",
                        lambda bus, msg, gen=generation_id: self.on_gst_message(bus, msg, gen),
                    )
                    logger.debug("Anura TTS: Bus watch setup completed")
            finally:
                self._bus_watch_setup_in_progress = False

        return False  # Don't repeat

    def on_gst_message(self, _bus: Gst.Bus, message: Gst.Message, generation_id: int) -> None:
        """Thread-safe GStreamer bus message handling.

        This is a Gst.Bus "message" signal callback, not a GLib timeout, so
        the return value is ignored — don't return False/True for "don't
        repeat".

        Stale callback detection: if _generation_id has advanced since this
        callback was connected, it belongs to a torn-down pipeline.
        """
        with self._state_lock:
            if generation_id != self._generation_id:
                logger.debug(
                    f"Anura TTS: Ignoring stale bus message (gen {generation_id} != current {self._generation_id})"
                )
                return
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

            def _on_stop_idle():
                self.emit("stop", True)
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_stop_idle)
            return

        elif message.type == Gst.MessageType.ERROR:
            err, _debug = message.parse_error()
            error_msg = f"{err}"
            logger.error(f"Anura TTS Error: GStreamer playback error: {error_msg}")
            with self._cleanup_lock:
                self._cleanup_gst_resources()
                # Ensure bus watch is cleaned up on error
                if self._bus_watch_active and self._bus:
                    with contextlib.suppress(GLib.Error, RuntimeError):
                        self._bus.remove_signal_watch()
                        self._bus_watch_active = False

            def _on_error_idle(msg: str):
                try:
                    self.emit("error", msg)
                    self.emit("stop", False)
                except Exception:
                    logger.exception("Anura TTS: Failed to emit playback error")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_error_idle, _("GStreamer playback error: {error}").format(error=error_msg))

    def _cleanup_gst_resources(self) -> None:
        """Remove signal watcher and release player resources.

        Suppresses teardown errors (e.g. dbus bus connection failures in
        sandboxed/CI environments where no dbus-daemon is available).
        """
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
                    # Explicitly flush the bus to prevent stale messages from firing
                    # callbacks during rapid teardown or navigation.
                    self._bus.set_flushing(True)
                    self._bus.remove_signal_watch()
                    logger.debug("Anura TTSService: Bus flushed and signal watch removed")
                self._bus_watch_active = False
                self._bus = None

            logger.info("Anura TTSService: Setting GStreamer state to NULL")
            try:
                # Use synchronous state change to ensure pipeline is fully stopped
                # before returning, preventing race conditions with rapid restarts.
                self.player.set_state(Gst.State.NULL)
                self.player.get_state(Gst.CLOCK_TIME_NONE)
            except Exception as e:
                logger.debug(f"Anura TTSService: Suppressed GStreamer NULL state error: {e}")
            self.player = None
            logger.debug("Anura TTSService: GStreamer resource cleanup complete")

    def stop_speaking(self) -> None:
        """Thread-safe interruption of playback and cleanup."""
        with self._cleanup_lock:
            had_player = self.player is not None
            if had_player:
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
                except OSError:
                    logger.warning("Anura TTS: Failed to cleanup temporary speech file on stop")
            elif filepath:
                logger.debug("Anura TTS: Cleanup skipped on stop, file already removed")

            # Only emit 'stop' when there was an active player to stop.
            # Emitting unconditionally caused spurious UI state resets
            # (e.g. flickering of TTS controls) when stop_speaking() was
            # called with no playback in progress.
            if had_player:
                def _on_stop_idle():
                    self.emit("stop", False)
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_stop_idle)

    def pause(self) -> None:
        """Pauses the GStreamer player."""
        if not self.player:
            return
        logger.info("Anura TTSService: Setting GStreamer state to PAUSED")
        ret = self.player.set_state(Gst.State.PAUSED)
        if ret == Gst.StateChangeReturn.ASYNC:
            self.player.get_state(500 * Gst.MSECOND)

        def _on_paused_idle():
            self.emit("paused", True)
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_on_paused_idle)

    def resume(self) -> None:
        """Resumes the GStreamer player."""
        if not self.player:
            return
        logger.info("Anura TTSService: Setting GStreamer state to PLAYING (resume)")
        ret = self.player.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.ASYNC:
            self.player.get_state(500 * Gst.MSECOND)

        def _on_resumed_idle():
            self.emit("paused", False)
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_on_resumed_idle)

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

        _, state, _ = self.player.get_state(100 * Gst.MSECOND)
        if state == Gst.State.PLAYING:
            self.pause()
        elif state == Gst.State.PAUSED:
            self.resume()
        else:
            logger.debug(f"Anura TTS: toggle_pause called in unexpected state {state.value_nick}, ignoring")

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
                except OSError:
                    logger.debug("Anura TTS: Failed to cleanup temporary speech file on shutdown")

        # Also cleanup the speech directory from old files (best effort)
        try:
            if os.path.exists(self._speech_dir):
                for f in os.listdir(self._speech_dir):
                    if f.startswith("speech_") and f.endswith(".mp3"):
                        file_path = os.path.join(self._speech_dir, f)
                        # Only delete files older than 1 hour to avoid deleting active files from other instances
                        if time.time() - os.path.getmtime(file_path) > 3600:
                            with contextlib.suppress(OSError):
                                os.unlink(file_path)
        except Exception as e:
            logger.debug(f"Anura TTS: Error during directory cleanup: {e}")


# Thread-safe singleton instance for global app access
def get_tts_service() -> TTSService:
    """Get thread-safe TTS service singleton."""
    return get_instance(TTSService)
