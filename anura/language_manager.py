# language_manager.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import contextlib
from gettext import gettext as _
import os
import re
import shutil
import tempfile
import threading
import time
from typing import ClassVar

import gi

# Set GTK version requirements before imports
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")

from gi.repository import GLib, GObject  # noqa: E402
from loguru import logger  # noqa: E402
import requests  # noqa: E402

from anura.config import (  # noqa: E402
    LANG_CODE_PATTERN,
    REQUEST_TIMEOUT,
    TESSDATA_BEST_URL,
    TESSDATA_DIR,
    TESSDATA_SYSTEM_DIR,
    TESSDATA_URL,
    USER_AGENT,
)
from anura.gobject_worker import GObjectWorker  # noqa: E402
from anura.types.download_state import DownloadState  # noqa: E402
from anura.types.language_item import LanguageItem  # noqa: E402
from anura.utils.singleton import get_instance  # noqa: E402


class LanguageManager(GObject.GObject):
    """
    Centralized manager for Tesseract language models.
    Handles download, removal, and ISO 639-2 mapping.
    """

    __gtype_name__ = "LanguageManager"

    # Mapping for language codes whose Anura internal code differs from the actual
    # filename in the tessdata/tessdata_best repositories. Format: {anura_code: repo_filename}.
    # Currently empty because all codes in _languages match their repo filenames exactly.
    # Add entries here if a future language code diverges (e.g. "foo": "foo_v2").
    _TESSDATA_FILENAME_MAPPING: ClassVar[dict[str, str]] = {}

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "added": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "downloading": (GObject.SignalFlags.RUN_FIRST, None, (str, int)),
        "downloaded": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "download-failed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        "removed": (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }

    _active_language: LanguageItem = LanguageItem(code="eng", title=_("English"))

    def __init__(self) -> None:
        super().__init__()

        self.loading_languages: dict[str, DownloadState] = {}
        self._downloaded_codes: list[str] = []
        self._need_update_cache = True
        self._cache_lock = threading.Lock()

        # Networking session for downloads
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.session.timeout = REQUEST_TIMEOUT  # Set default timeout here
        # Set retry logic
        adapter = requests.adapters.HTTPAdapter(
            max_retries=requests.adapters.Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        # Full ISO 639-2 mapping (Tesseract compatible)
        self._languages = {
            "afr": _("Afrikaans"),
            "amh": _("Amharic"),
            "ara": _("Arabic"),
            "asm": _("Assamese"),
            "aze": _("Azerbaijani"),
            "aze_cyrl": _("Azerbaijani - Cyrillic"),
            "bel": _("Belarusian"),
            "ben": _("Bengali"),
            "bod": _("Tibetan"),
            "bos": _("Bosnian"),
            "bre": _("Breton"),
            "bul": _("Bulgarian"),
            "cat": _("Catalan"),
            "ceb": _("Cebuano"),
            "ces": _("Czech"),
            "chi_sim": _("Chinese - Simplified"),
            "chi_sim_vert": _("Chinese - Simplified (vertical)"),
            "chi_tra": _("Chinese - Traditional"),
            "chi_tra_vert": _("Chinese - Traditional (vertical)"),
            "chr": _("Cherokee"),
            "cos": _("Corsican"),
            "cym": _("Welsh"),
            "dan": _("Danish"),
            "deu": _("German"),
            "dzo": _("Dzongkha"),
            "ell": _("Greek"),
            "eng": _("English"),
            "enm": _("English, Middle"),
            "epo": _("Esperanto"),
            # NOTE: equ (Math/Equation Detection) intentionally removed — it is a
            # Tesseract internal utility module, not an OCR language model, and should
            # not appear as a downloadable language in the UI.
            "est": _("Estonian"),
            "eus": _("Basque"),
            "fao": _("Faroese"),
            "fas": _("Persian"),
            "fil": _("Filipino"),
            "fin": _("Finnish"),
            "fra": _("French"),
            # NOTE: frk (German - Fraktur) intentionally removed — the model file
            # frk.traineddata is absent from both tessdata_best/main and tessdata/main,
            # so every install attempt would silently fail with HTTP 404.
            "frm": _("French, Middle"),
            "fry": _("Western Frisian"),
            "gla": _("Scottish Gaelic"),
            "gle": _("Irish"),
            "glg": _("Galician"),
            "grc": _("Greek, Ancient"),
            "guj": _("Gujarati"),
            "hat": _("Haitian"),
            "heb": _("Hebrew"),
            "hin": _("Hindi"),
            "hrv": _("Croatian"),
            "hun": _("Hungarian"),
            "hye": _("Armenian"),
            "iku": _("Inuktitut"),
            "ind": _("Indonesian"),
            "isl": _("Icelandic"),
            "ita": _("Italian"),
            "ita_old": _("Italian - Old"),
            "jav": _("Javanese"),
            "jpn": _("Japanese"),
            "jpn_vert": _("Japanese (vertical)"),
            "kan": _("Kannada"),
            "kat": _("Georgian"),
            "kat_old": _("Georgian - Old"),
            "kaz": _("Kazakh"),
            "khm": _("Central Khmer"),
            "kir": _("Kirghiz"),
            "kmr": _("Kurmanji"),
            "kor": _("Korean"),
            "kor_vert": _("Korean (vertical)"),
            "lao": _("Lao"),
            "lat": _("Latin"),
            "lav": _("Latvian"),
            "lit": _("Lithuanian"),
            "ltz": _("Luxembourgish"),
            "mal": _("Malayalam"),
            "mar": _("Marathi"),
            "mkd": _("Macedonian"),
            "mlt": _("Maltese"),
            "mon": _("Mongolian"),
            "mri": _("Maori"),
            "msa": _("Malay"),
            "mya": _("Burmese"),
            "nep": _("Nepali"),
            "nld": _("Dutch"),
            "nor": _("Norwegian"),
            "oci": _("Occitan"),
            "ori": _("Oriya"),
            # NOTE: osd (Orientation/Script Detection) intentionally removed — it is a
            # Tesseract internal utility module already excluded from get_downloaded_codes()
            # via the startswith("osd") filter, but it was still showing in the install list.
            "pan": _("Panjabi"),
            "pol": _("Polish"),
            "por": _("Portuguese"),
            "pus": _("Pushto"),
            "que": _("Quechua"),
            "ron": _("Romanian"),
            "rus": _("Russian"),
            "san": _("Sanskrit"),
            "sin": _("Sinhala"),
            "slk": _("Slovak"),
            "slv": _("Slovenian"),
            "snd": _("Sindhi"),
            "spa": _("Spanish"),
            "spa_old": _("Spanish - Old"),
            "sqi": _("Albanian"),
            "srp": _("Serbian"),
            "srp_latn": _("Serbian - Latin"),
            "sun": _("Sundanese"),
            "swa": _("Swahili"),
            "swe": _("Swedish"),
            "syr": _("Syriac"),
            "tam": _("Tamil"),
            "tat": _("Tatar"),
            "tel": _("Telugu"),
            "tgk": _("Tajik"),
            "tha": _("Thai"),
            "tir": _("Tigrinya"),
            "ton": _("Tonga"),
            "tur": _("Turkish"),
            "uig": _("Uighur"),
            "ukr": _("Ukrainian"),
            "urd": _("Urdu"),
            "uzb": _("Uzbek"),
            "uzb_cyrl": _("Uzbek - Cyrillic"),
            "vie": _("Vietnamese"),
            "yid": _("Yiddish"),
            "yor": _("Yoruba"),
        }

    @GObject.Property(type=GObject.TYPE_PYOBJECT)
    def active_language(self) -> LanguageItem:
        return self._active_language

    @active_language.setter  # type: ignore[no-redef]
    def active_language(self, language: LanguageItem) -> None:
        self._active_language = language
        self.notify("active_language")

    def init_tessdata(self) -> None:
        """
        Ensures the tessdata directory exists and logs its status at startup.
        Also cleans up orphaned temporary files from interrupted downloads.
        """
        # Hardening: verify Tesseract binary availability at startup
        tess_bin = os.environ.get("TESSERACT_CMD", "tesseract")
        if not shutil.which(tess_bin):
            logger.critical(
                f"Anura: Tesseract binary '{tess_bin}' not found. "
                "OCR features will be unavailable. Please install Tesseract."
            )

        # Use lock to prevent race condition when multiple threads try to create directory
        with self._cache_lock:
            if not os.path.exists(TESSDATA_DIR):
                logger.warning(
                    "Anura: tessdata directory not found. It will be created on first language download.",
                )
                with contextlib.suppress(FileExistsError):
                    # Another thread created it between check and makedirs
                    os.makedirs(TESSDATA_DIR, exist_ok=True)

        # Clean up orphaned temp files from crashed/interrupted downloads
        try:
            # Check directory readability first
            if not os.access(TESSDATA_DIR, os.R_OK | os.X_OK):
                logger.warning("Anura: Cannot read tessdata directory for cleanup")
            else:
                temp_files = [f for f in os.listdir(TESSDATA_DIR) if f.endswith(".tmp")]
                for temp_file in temp_files:
                    temp_path = os.path.join(TESSDATA_DIR, temp_file)
                    try:
                        os.remove(temp_path)
                        logger.warning("Anura: Cleaned up orphaned temporary language file")
                    except PermissionError:
                        logger.error("Anura: Permission denied removing orphaned temporary language file")
                    except OSError:
                        logger.error("Anura: Failed to remove orphaned temporary language file")
        except OSError:
            logger.error("Anura: Error scanning for orphaned temporary language files")

        installed = self.get_downloaded_codes(force=True)
        logger.info(
            f"Anura: tessdata directory ready. {len(installed)} language model(s) installed: {installed or ['none']}",
        )

    def get_language(self, code: str) -> str:
        """Returns the human-readable language name for a given ISO code."""
        return self._languages.get(code, code)

    def get_language_item(self, code: str) -> LanguageItem | None:
        if code not in self._languages:
            return None
        return LanguageItem(code=code, title=self._languages[code])

    def get_downloaded_codes(self, force: bool = False) -> list[str]:
        """Returns codes of all installed language models (user + system bundled)."""
        with self._cache_lock:
            need_update = self._need_update_cache
            if need_update or force:
                codes: set[str] = set()

                # Enhanced logging: Log paths being checked with directory status
                logger.debug(f"Anura LanguageManager: Scanning user tessdata directory: {TESSDATA_DIR}")
                logger.debug(f"Anura LanguageManager: Scanning system tessdata directory: {TESSDATA_SYSTEM_DIR}")

                # User-downloaded models (~/.var/app/.../data/anura/tessdata/)
                if os.path.exists(TESSDATA_DIR):
                    try:
                        user_files = [
                            f
                            for f in os.listdir(TESSDATA_DIR)
                            if f.endswith(".traineddata") and not f.startswith("osd")
                        ]
                        logger.debug(
                            f"Anura LanguageManager: User directory scanned, "
                            f"{len(user_files)} models found: {user_files}",
                        )
                        codes.update(os.path.splitext(f)[0] for f in user_files)
                    except OSError as e:
                        logger.exception(f"Anura LanguageManager: Error reading user tessdata directory: {e}")
                else:
                    logger.debug(f"Anura LanguageManager: User tessdata directory does not exist: {TESSDATA_DIR}")

                # Bundled system models (/app/share/tessdata/ — eng, ita pre-installed)
                if os.path.exists(TESSDATA_SYSTEM_DIR):
                    try:
                        system_files = [
                            f
                            for f in os.listdir(TESSDATA_SYSTEM_DIR)
                            if f.endswith(".traineddata") and not f.startswith("osd")
                        ]
                        logger.debug(
                            f"Anura LanguageManager: System directory scanned, "
                            f"{len(system_files)} models found: {system_files}",
                        )
                        codes.update(os.path.splitext(f)[0] for f in system_files)
                    except OSError as e:
                        logger.exception(f"Anura LanguageManager: Error reading system tessdata directory: {e}")
                else:
                    logger.debug(
                        f"Anura LanguageManager: System tessdata directory does not exist: {TESSDATA_SYSTEM_DIR}",
                    )

                total_models = len(codes)
                logger.info(f"Anura LanguageManager: Total language models discovered: {total_models} - {list(codes)}")
                self._downloaded_codes = list(codes)
                self._need_update_cache = False
            return sorted(self._downloaded_codes, key=lambda x: self.get_language(x))

    def get_downloaded_languages(self, force: bool = False) -> list[str]:
        """Returns the names of the installed languages."""
        codes = self.get_downloaded_codes(force)
        return [self.get_language(code) for code in codes]

    def get_available_codes(self) -> list[str]:
        """Returns all ISO codes supported by Tesseract (installed or not)."""
        return sorted(self._languages.keys())

    def get_language_code(self, name: str) -> str:
        """Reverse lookup: from name to ISO code."""
        for code, lang_name in self._languages.items():
            if lang_name == name:
                return code
        return "eng"

    def download(self, code: str, cancellable: gi.repository.Gio.Cancellable | None = None) -> None:
        """Thread-safe asynchronous download process."""
        with self._cache_lock:
            if code in self.loading_languages:
                return
            self.loading_languages[code] = DownloadState()

        def _on_added_idle(c):
            try:
                self.emit("added", c)
            except Exception:
                logger.exception(f"Anura: Failed to emit 'added' signal for {c}")
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_on_added_idle, code, priority=GLib.PRIORITY_DEFAULT)

        # Use a wrapper to ensure download_done knows which code was being downloaded
        # even when download_begin returns None on failure
        def download_done_wrapper(result_code: str | None) -> None:
            self.download_done(code, result_code)

        GObjectWorker.call(
            self.download_begin,
            (code, cancellable),
            download_done_wrapper,
            cancellable=cancellable,
        )

    def download_begin(self, code: str, cancellable: gi.repository.Gio.Cancellable | None = None) -> str | None:
        """Performs the physical download of the .traineddata file atomically."""
        # Hardening: verify Tesseract binary availability before downloading models
        tess_bin = os.environ.get("TESSERACT_CMD", "tesseract")
        if not shutil.which(tess_bin):
            logger.error(f"Anura: Cannot download '{code}'; Tesseract binary not found.")
            return None

        # Use filename mapping for language codes with different filenames
        filename_code = self._TESSDATA_FILENAME_MAPPING.get(code, code)

        # Validate filename is safe to prevent path traversal attacks
        if not re.match(r"^[a-zA-Z0-9_-]+$", filename_code):
            logger.error(f"Anura: Unsafe language code '{code}' -> '{filename_code}'")
            return None

        tessfile = f"{filename_code}.traineddata"
        final_path = os.path.join(TESSDATA_DIR, f"{code}.traineddata")  # Always save with original code
        tmp_path = None
        for url_base in (TESSDATA_BEST_URL, TESSDATA_URL):
            try:
                url = url_base + tessfile
                with tempfile.NamedTemporaryFile(
                    dir=TESSDATA_DIR,
                    suffix=".tmp",
                    delete=False,
                ) as tmp:
                    tmp_path = tmp.name

                try:
                    # Use central session with consistent headers and timeout
                    response = self.session.get(url, timeout=REQUEST_TIMEOUT, stream=True)
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    # Throttle progress updates to prevent main loop saturation
                    # Max 10 updates per second (every 100ms)
                    last_progress_time = time.monotonic()
                    last_progress_value = 0

                    with open(tmp_path, "wb") as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if cancellable and cancellable.is_cancelled():
                                logger.debug(f"Anura: Download of {code} cancelled")
                                return None
                            if chunk:
                                f.write(chunk)
                                downloaded += len(chunk)

                                # Throttle progress updates (max 10/sec)
                                now = time.monotonic()
                                if now - last_progress_time >= 0.1:  # 100ms throttle
                                    if total_size > 0:
                                        progress = int(downloaded * 100 / total_size)
                                        # Only emit if progress actually changed
                                        if progress != last_progress_value:

                                            def _on_progress_idle(c, p):
                                                try:
                                                    self.emit("downloading", c, p)
                                                except Exception:
                                                    logger.exception(f"Anura: Failed to emit 'downloading' for {c}")
                                                return GLib.SOURCE_REMOVE

                                            GLib.idle_add(
                                                _on_progress_idle,
                                                code,
                                                min(progress, 100),
                                                priority=GLib.PRIORITY_DEFAULT,
                                            )
                                            last_progress_value = progress
                                    else:
                                        # No content-length header, emit indeterminate progress
                                        def _on_progress_idle(c, p):
                                            try:
                                                self.emit("downloading", c, p)
                                            except Exception:
                                                logger.exception(f"Anura: Failed to emit 'downloading' for {c}")
                                            return GLib.SOURCE_REMOVE

                                        GLib.idle_add(_on_progress_idle, code, -1, priority=GLib.PRIORITY_DEFAULT)
                                    last_progress_time = now

                    # Use copy+delete for cross-filesystem compatibility
                    try:
                        shutil.copy2(tmp_path, final_path)
                        return code
                    except (OSError, shutil.Error) as e:
                        logger.error(f"Anura: Failed to install language file: {e}")
                        return None

                finally:
                    # Ensure temporary file is always cleaned up
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.unlink(tmp_path)
                            tmp_path = None
                        except OSError:
                            logger.warning(f"Anura: Failed to clean up temporary file: {tmp_path}")

            except (requests.RequestException, OSError) as e:
                logger.warning(f"Anura: download failed from {url_base}: {e}")
                # tmp_path will be cleaned up by the finally block above

        logger.error(f"Anura: Failed to download model '{code}' from all sources.")
        return None

    def download_done(self, requested_code: str, result_code: str | None) -> None:
        """Thread-safe callback when download completes.

        Args:
            requested_code: The language code that was requested for download
            result_code: The returned code from download_begin (None if failed)
        """
        with self._cache_lock:
            self._need_update_cache = True
            if requested_code in self.loading_languages:
                self.loading_languages.pop(requested_code)

            # Emit signals while holding lock to ensure consistency
            if result_code:

                def _on_downloaded_idle(c):
                    try:
                        self.emit("downloaded", c)
                    except Exception:
                        logger.exception(f"Anura: Failed to emit 'downloaded' for {c}")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_downloaded_idle, result_code, priority=GLib.PRIORITY_DEFAULT)
            else:

                def _on_failed_idle(c):
                    try:
                        self.emit("download-failed", c)
                    except Exception:
                        logger.exception(f"Anura: Failed to emit 'download-failed' for {c}")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_failed_idle, requested_code, priority=GLib.PRIORITY_DEFAULT)

    def remove_language(self, code: str) -> None:
        """Thread-safe removal of model file from system."""
        # Security: Validate lang_code is a valid ISO 639-2 code to prevent path traversal
        if not code or not re.match(LANG_CODE_PATTERN, code):
            logger.error(f"Anura: Blocked invalid language code removal attempt: '{code}'")
            return

        path = os.path.join(TESSDATA_DIR, f"{code}.traineddata")
        if not os.path.exists(path):
            return

        try:
            os.remove(path)
            with self._cache_lock:
                self._need_update_cache = True
            logger.info(f"Anura: Model '{code}' removed successfully.")

            def _on_removed_idle(c):
                try:
                    self.emit("removed", c)
                except Exception:
                    logger.exception(f"Anura: Failed to emit 'removed' for {c}")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_removed_idle, code, priority=GLib.PRIORITY_DEFAULT)
        except PermissionError as e:
            logger.error(f"Anura: Permission denied removing language '{code}': {e}")
        except OSError as e:
            logger.error(f"Anura: OS error removing language '{code}': {e}")


# Thread-safe singleton instance for global app access
def get_language_manager() -> LanguageManager:
    """Get thread-safe language manager singleton."""
    return get_instance(LanguageManager)


# Global singleton instance for direct import
language_manager = get_language_manager()
