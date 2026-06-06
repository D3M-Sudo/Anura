# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from concurrent.futures import ThreadPoolExecutor
import contextlib
from gettext import gettext as _
import os
from pathlib import Path
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
gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib, GObject  # noqa: E402
from loguru import logger  # noqa: E402
import requests  # noqa: E402

from anura.config import (  # noqa: E402
    LANG_CODE_PATTERN,
    REQUEST_TIMEOUT,
    TESSDATA_BEST_URL,
    TESSDATA_DIR,
    TESSDATA_POOL_DIR,
    TESSDATA_STANDARD_URL,
    TESSDATA_SYSTEM_DIR,
    TESSDATA_URL,
    USER_AGENT,
)
from anura.models.download_state import DownloadState  # noqa: E402
from anura.models.language_item import LanguageItem  # noqa: E402
from anura.services.settings import settings  # noqa: E402
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
        self._download_executor: ThreadPoolExecutor | None = None
        self._downloaded_codes: list[str] = []
        self._need_update_cache = True
        self._cache_lock = threading.Lock()

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        # Note: requests.Session does not have a built-in .timeout attribute.
        # The actual timeout is passed explicitly in session.get(timeout=REQUEST_TIMEOUT).
        # Removed the no-op self.session.timeout assignment.
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
            "deu_latf": _("German - Fraktur"),  # Correct code for Fraktur, available in tessdata_best
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
        self.notify("active-language")

    def _get_model_quality_dir(self, quality: str | None = None) -> Path:
        """Get the directory for the specified model quality."""
        if quality is None:
            quality = settings.get_string("tessdata-model")

        base_dir = Path(TESSDATA_DIR)
        if quality == "best":
            return base_dir / "tessdata_best"
        if quality == "standard":
            return base_dir / "tessdata"
        return base_dir

    def _get_model_quality_url(self, quality: str | None = None) -> str:
        """Get the GitHub base URL for the specified model quality."""
        if quality is None:
            quality = settings.get_string("tessdata-model")

        if quality == "best":
            return TESSDATA_BEST_URL
        if quality == "standard":
            return TESSDATA_STANDARD_URL
        return TESSDATA_URL

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
            tess_path = Path(TESSDATA_DIR)
            if not tess_path.exists():
                logger.warning(
                    "Anura: tessdata directory not found. It will be created on first language download.",
                )
                with contextlib.suppress(FileExistsError):
                    # Another thread created it between check and makedirs
                    tess_path.mkdir(parents=True, exist_ok=True)

            # Security: Ensure tessdata directory has restrictive permissions (0700)
            if tess_path.exists():
                with contextlib.suppress(OSError):
                    tess_path.chmod(0o700)

        # Clean up orphaned temp files from crashed/interrupted downloads
        try:
            tess_path = Path(TESSDATA_DIR)
            # Check directory readability first
            if not os.access(tess_path, os.R_OK | os.X_OK):
                logger.warning("Anura: Cannot read tessdata directory for cleanup")
            else:
                for file_path in tess_path.iterdir():
                    if file_path.suffix == ".tmp":
                        try:
                            # NEW-017: Only delete .tmp files older than 1 hour to avoid
                            # interrupting active downloads from other instances.
                            if time.time() - file_path.stat().st_mtime > 3600:
                                file_path.unlink()
                                logger.warning(
                                    f"Anura: Cleaned up orphaned temporary file: {file_path.name}"
                                )
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
                quality = settings.get_string("tessdata-model")

                # Enhanced logging: Log paths being checked with directory status
                tess_path = self._get_model_quality_dir(quality)
                logger.debug(f"Anura LanguageManager: Scanning user tessdata directory: {tess_path}")
                logger.debug(f"Anura LanguageManager: Scanning system tessdata directory: {TESSDATA_SYSTEM_DIR}")

                # User-downloaded models (~/.var/app/.../data/anura/tessdata/ or quality subdir)
                if tess_path.exists():
                    try:
                        user_files = [
                            f.name
                            for f in tess_path.iterdir()
                            if f.name.endswith(".traineddata") and not f.name.startswith("osd")
                        ]
                        logger.debug(
                            f"Anura LanguageManager: User directory scanned, "
                            f"{len(user_files)} models found: {user_files}",
                        )
                        codes.update(Path(f).stem for f in user_files)
                    except OSError as e:
                        logger.exception(f"Anura LanguageManager: Error reading user tessdata directory: {e}")
                else:
                    logger.debug(f"Anura LanguageManager: User tessdata directory does not exist: {TESSDATA_DIR}")

                # Bundled system models (/app/share/tessdata/ — eng, ita pre-installed)
                system_path = Path(TESSDATA_SYSTEM_DIR)
                if system_path.exists():
                    try:
                        system_files = [
                            f.name
                            for f in system_path.iterdir()
                            if f.name.endswith(".traineddata") and not f.name.startswith("osd")
                        ]
                        logger.debug(
                            f"Anura LanguageManager: System directory scanned, "
                            f"{len(system_files)} models found: {system_files}",
                        )
                        codes.update(Path(f).stem for f in system_files)
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

    def _get_download_executor(self) -> ThreadPoolExecutor:
        """Lazy initialization of the download executor."""
        with self._cache_lock:
            if self._download_executor is None:
                self._download_executor = ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="AnuraDownloadWorker",
                )
            return self._download_executor

    def download(self, code: str, cancellable: Gio.Cancellable | None = None) -> None:
        """Thread-safe asynchronous download process."""
        with self._cache_lock:
            if code in self.loading_languages:
                return
            self.loading_languages[code] = DownloadState()

        def _on_added_idle(c):
            try:
                self.emit("added", c)
            except (AttributeError, RuntimeError, TypeError) as e:
                logger.exception(f"Anura: Failed to emit 'added' signal for {c}: {e}")
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_on_added_idle, code, priority=GLib.PRIORITY_DEFAULT)

        # Use a wrapper to ensure download_done knows which code was being downloaded
        # even when download_begin returns None on failure
        def download_done_wrapper(future) -> None:
            try:
                result_code = future.result()
            except (AttributeError, RuntimeError, TypeError, ValueError, OSError) as e:
                logger.error(f"Anura: Unexpected error during download of {code}: {e}")
                result_code = None

            def _on_done_idle():
                self.download_done(code, result_code)
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_done_idle)

        future = self._get_download_executor().submit(
            self.download_begin,
            code,
            cancellable,
        )
        future.add_done_callback(download_done_wrapper)

    def download_begin(self, code: str, cancellable: Gio.Cancellable | None = None) -> str | None:
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

        quality = settings.get_string("tessdata-model")
        tessfile = f"{filename_code}.traineddata"
        quality_dir = self._get_model_quality_dir(quality)

        # Security: Ensure quality-specific tessdata directories have restrictive permissions (0700)
        quality_dir.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            quality_dir.chmod(0o700)

        final_path = quality_dir / f"{code}.traineddata"
        tmp_path = None

        url_base = self._get_model_quality_url(quality)
        try:
            url = url_base + tessfile
            with tempfile.NamedTemporaryFile(
                dir=quality_dir,
                suffix=".tmp",
                delete=False,
            ) as tmp:
                tmp_path = Path(tmp.name)

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

                    with tmp_path.open("wb") as f:
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
                                                except (AttributeError, RuntimeError, TypeError) as e:
                                                    logger.error(f"Anura: Failed to emit 'downloading' for {c}: {e}")
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
                                        def _on_progress_idle(c, _):
                                            try:
                                                self.emit("downloading", c, -1)
                                            except (AttributeError, RuntimeError, TypeError) as e:
                                                logger.error(f"Anura: Failed to emit 'downloading' for {c}: {e}")
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
                    if tmp_path and tmp_path.exists():
                        try:
                            tmp_path.unlink()
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
                    except (AttributeError, RuntimeError, TypeError) as e:
                        logger.exception(f"Anura: Failed to emit 'downloaded' for {c}: {e}")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_downloaded_idle, result_code, priority=GLib.PRIORITY_DEFAULT)
            else:

                def _on_failed_idle(c):
                    try:
                        self.emit("download-failed", c)
                    except (AttributeError, RuntimeError, TypeError) as e:
                        logger.exception(f"Anura: Failed to emit 'download-failed' for {c}: {e}")
                    return GLib.SOURCE_REMOVE

                GLib.idle_add(_on_failed_idle, requested_code, priority=GLib.PRIORITY_DEFAULT)

    def shutdown(self) -> None:
        """Shut down the download executor."""
        with self._cache_lock:
            executor = self._download_executor
            self._download_executor = None

        if executor is not None:
            executor.shutdown(wait=False, cancel_futures=True)

    def remove_language(self, code: str) -> None:
        """Thread-safe removal of model file from system."""
        # Security: Validate lang_code is a valid ISO 639-2 code to prevent path traversal
        if not code or not re.match(LANG_CODE_PATTERN, code):
            logger.error(f"Anura: Blocked invalid language code removal attempt: '{code}'")
            return

        quality = settings.get_string("tessdata-model")
        path = self._get_model_quality_dir(quality) / f"{code}.traineddata"
        if not path.exists():
            return

        try:
            path.unlink()
            with self._cache_lock:
                self._need_update_cache = True
            logger.info(f"Anura: Model '{code}' removed successfully.")

            def _on_removed_idle(c):
                try:
                    self.emit("removed", c)
                except (AttributeError, RuntimeError, TypeError) as e:
                    logger.exception(f"Anura: Failed to emit 'removed' for {c}: {e}")
                return GLib.SOURCE_REMOVE

            GLib.idle_add(_on_removed_idle, code, priority=GLib.PRIORITY_DEFAULT)
        except PermissionError as e:
            logger.error(f"Anura: Permission denied removing language '{code}': {e}")
        except OSError as e:
            logger.error(f"Anura: OS error removing language '{code}': {e}")


def get_tesseract_config(lang_code: str, task_id: str | None = None) -> str:
    """
    Returns Tesseract config string with correct --tessdata-dir.

    Tesseract only supports a single --tessdata-dir path. For multi-language
    configurations (e.g. 'eng+ita') where models may be split between system
    (/app/share/tessdata) and user (~/.local/share/anura/tessdata) directories,
    this function creates a dynamic pool in the sandbox cache.

    Args:
        lang_code: The ISO 639-2 language code (e.g., 'eng', 'eng+ita')
        task_id: Optional ID for task-isolated pooling (prevents race conditions).

    Returns:
        Config string with --tessdata-dir pointing to the correct directory.
    """
    # Security: Validate lang_code
    if not lang_code or not re.match(LANG_CODE_PATTERN, lang_code):
        logger.error(f"Anura: Invalid language code '{lang_code}' - using 'eng'")
        lang_code = "eng"

    quality = settings.get_string("tessdata-model")
    quality_dir = get_language_manager()._get_model_quality_dir(quality)
    quality_dir_str = str(quality_dir)

    # If it's a single language, use standard priority logic without pooling
    if "+" not in lang_code:
        user_model = quality_dir / f"{lang_code}.traineddata"
        if user_model.exists():
            return f'--tessdata-dir "{quality_dir_str}" --psm 3 --oem 1'

        system_model = Path(TESSDATA_SYSTEM_DIR) / f"{lang_code}.traineddata"
        if system_model.exists():
            return f'--tessdata-dir "{TESSDATA_SYSTEM_DIR}" --psm 3 --oem 1'

        return f'--tessdata-dir "{quality_dir_str}" --psm 3 --oem 1'

    # Multi-language: Dynamic Pooling Approach
    codes = lang_code.split("+")

    # BUG-P1-REPRO / NEW-007: Use task-isolated subdirectories to prevent race conditions.
    # If no task_id provided (e.g. CLI or legacy call), fallback to shared directory.
    pool_dir = Path(TESSDATA_POOL_DIR)
    if task_id:
        pool_dir = pool_dir / task_id

    # Security: Ensure tessdata pool directory has restrictive permissions (0700)
    pool_dir.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        pool_dir.chmod(0o700)

    for code in codes:
        # Resolve source
        source_path = None
        user_path = quality_dir / f"{code}.traineddata"
        system_path = Path(TESSDATA_SYSTEM_DIR) / f"{code}.traineddata"

        if user_path.exists():
            source_path = user_path
        elif system_path.exists():
            source_path = system_path

        if source_path:
            dest_path = pool_dir / f"{code}.traineddata"
            # NEW-004: Create hard link with fallback to copy (for cross-filesystem)
            try:
                if dest_path.exists():
                    dest_path.unlink()
                os.link(source_path, dest_path)
            except OSError as e:
                import errno

                if e.errno == errno.EXDEV:
                    # Cross-device link failure: use copy instead, suppress error noise
                    try:
                        shutil.copy2(source_path, dest_path)
                    except OSError as copy_err:
                        logger.error(f"Anura Pooling: Failed to copy {code}: {copy_err}")
                else:
                    logger.error(f"Anura Pooling: Failed to link {code}: {e}")
            except AttributeError:
                # Fallback for systems where os.link might be missing
                try:
                    shutil.copy2(source_path, dest_path)
                except OSError as copy_err:
                    logger.error(f"Anura Pooling: Failed to copy {code}: {copy_err}")

    return f'--tessdata-dir "{pool_dir}" --psm 3 --oem 1'


# Thread-safe singleton instance for global app access
def get_language_manager() -> LanguageManager:
    """Get thread-safe language manager singleton."""
    return get_instance(LanguageManager)
