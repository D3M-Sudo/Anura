# language_manager.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

import os
from gettext import gettext as _
from typing import List, Dict
from urllib import request

from gi.repository import GObject
from loguru import logger

from anura.config import TESSDATA_DIR, TESSDATA_URL, TESSDATA_BEST_URL
from anura.gobject_worker import GObjectWorker
from anura.types.download_state import DownloadState
from anura.types.language_item import LanguageItem


class LanguageManager(GObject.GObject):
    """
    Centralized manager for Tesseract language models.
    Handles download, removal, and ISO 639-2 mapping.
    """
    __gtype_name__ = 'LanguageManager'

    # Signals for synchronization with UI widgets
    __gsignals__ = {
        'added': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'downloading': (GObject.SIGNAL_RUN_FIRST, None, (str, int)),
        'downloaded': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        'removed': (GObject.SIGNAL_RUN_FIRST, None, (str,)),
    }

    _active_language: LanguageItem = LanguageItem(code='eng', title=_("English"))

    def __init__(self):
        super().__init__()

        self.loading_languages: Dict[str, DownloadState] = dict()
        self._downloaded_codes = []
        self._need_update_cache = True

        # Full ISO 639-2 Mapping (Tesseract compatible)
        self._languages = {
            "afr": _("Afrikaans"), "amh": _("Amharic"), "ara": _("Arabic"),
            "asm": _("Assamese"), "aze": _("Azerbaijani"), "aze_cyrl": _("Azerbaijani - Cyrillic"),
            "bel": _("Belarusian"), "ben": _("Bengali"), "bod": _("Tibetan"),
            "bos": _("Bosnian"), "bre": _("Breton"), "bul": _("Bulgarian"),
            "cat": _("Catalan"), "ceb": _("Cebuano"), "ces": _("Czech"),
            "chi_sim": _("Chinese - Simplified"), "chi_tra": _("Chinese - Traditional"),
            "chr": _("Cherokee"), "cos": _("Corsican"), "cym": _("Welsh"),
            "dan": _("Danish"), "deu": _("German"), "dzo": _("Dzongkha"),
            "ell": _("Greek"), "eng": _("English"), "enm": _("English, Middle"),
            "epo": _("Esperanto"), "equ": _("Math / Equation Detection"),
            "est": _("Estonian"), "eus": _("Basque"), "fao": _("Faroese"),
            "fas": _("Persian"), "fil": _("Filipino"), "fin": _("Finnish"),
            "fra": _("French"), "frk": _("German - Fraktur"), "frm": _("French, Middle"),
            "fry": _("Western Frisian"), "gla": _("Scottish Gaelic"), "gle": _("Irish"),
            "glg": _("Galician"), "grc": _("Greek, Ancient"), "guj": _("Gujarati"),
            "hat": _("Haitian"), "heb": _("Hebrew"), "hin": _("Hindi"),
            "hrv": _("Croatian"), "hun": _("Hungarian"), "hye": _("Armenian"),
            "iku": _("Inuktitut"), "ind": _("Indonesian"), "isl": _("Icelandic"),
            "ita": _("Italian"), "ita_old": _("Italian - Old"), "jav": _("Javanese"),
            "jpn": _("Japanese"), "jpn_vert": _("Japanese (vertical)"),
            "kan": _("Kannada"), "kat": _("Georgian"), "kat_old": _("Georgian - Old"),
            "kaz": _("Kazakh"), "khm": _("Central Khmer"), "kir": _("Kirghiz"),
            "kmr": _("Kurmanji"), "kor": _("Korean"), "kor_vert": _("Korean (vertical)"),
            "lao": _("Lao"), "lat": _("Latin"), "lav": _("Latvian"),
            "lit": _("Lithuanian"), "ltz": _("Luxembourgish"), "mal": _("Malayalam"),
            "mar": _("Marathi"), "mkd": _("Macedonian"), "mlt": _("Maltese"),
            "mon": _("Mongolian"), "mri": _("Maori"), "msa": _("Malay"),
            "mya": _("Burmese"), "nep": _("Nepali"), "nld": _("Dutch"),
            "nor": _("Norwegian"), "oci": _("Occitan"), "ori": _("Oriya"),
            "osd": _("OSD Module"), "pan": _("Panjabi"), "pol": _("Polish"),
            "por": _("Portuguese"), "pus": _("Pushto"), "que": _("Quechua"),
            "ron": _("Romanian"), "rus": _("Russian"), "san": _("Sanskrit"),
            "sin": _("Sinhala"), "slk": _("Slovak"), "slv": _("Slovenian"),
            "snd": _("Sindhi"), "spa": _("Spanish"), "spa_old": _("Spanish - Old"),
            "sqi": _("Albanian"), "srp": _("Serbian"), "srp_latn": _("Serbian - Latin"),
            "sun": _("Sundanese"), "swa": _("Swahili"), "swe": _("Swedish"),
            "syr": _("Syriac"), "tam": _("Tamil"), "tat": _("Tatar"),
            "tel": _("Telugu"), "tgk": _("Tajik"), "tha": _("Thai"),
            "tir": _("Tigrinya"), "ton": _("Tonga"), "tur": _("Turkish"),
            "uig": _("Uighur"), "ukr": _("Ukrainian"), "urd": _("Urdu"),
            "uzb": _("Uzbek"), "uzb_cyrl": _("Uzbek - Cyrillic"), "vie": _("Vietnamese"),
            "yid": _("Yiddish"), "yor": _("Yoruba"),
        }

    @GObject.Property(type=GObject.TYPE_PYOBJECT)
    def active_language(self) -> LanguageItem:
        return self._active_language

    @active_language.setter
    def active_language(self, language: LanguageItem):
        self._active_language = language
        self.notify('active_language')

    def get_language(self, code: str) -> str:
        """Returns the human-readable language name for a given ISO code."""
        return self._languages.get(code, code)

    def get_language_item(self, code: str) -> LanguageItem:
        return LanguageItem(code=code, title=self.get_language(code))

    def get_downloaded_codes(self, force: bool = False) -> List[str]:
        """Returns the codes of the currently installed languages."""
        if self._need_update_cache or force:
            if not os.path.exists(TESSDATA_DIR):
                return []
            self._downloaded_codes = [
                os.path.splitext(f)[0] 
                for f in os.listdir(TESSDATA_DIR) 
                if f.endswith('.traineddata')
            ]
            self._need_update_cache = False
        return sorted(self._downloaded_codes, key=lambda x: self.get_language(x))

    def get_downloaded_languages(self, force: bool = False) -> List[str]:
        """Returns the names of the installed languages."""
        codes = self.get_downloaded_codes(force)
        return [self.get_language(code) for code in codes]

    def get_language_code(self, name: str) -> str:
        """Reverse lookup: from name to ISO code."""
        for code, lang_name in self._languages.items():
            if lang_name == name:
                return code
        return 'eng'

    def download(self, code: str):
        """Starts the asynchronous download process."""
        if code in self.loading_languages:
            return
        
        self.emit('added', code)
        self.loading_languages[code] = DownloadState()
        GObjectWorker.call(self.download_begin, (code,), self.download_done)

    def download_begin(self, code: str) -> str:
        """Performs the physical download of the .traineddata file."""
        def update_progress(block_num, block_size, total_size):
            if total_size > 0:
                progress = int(block_num * block_size * 100 / total_size)
                self.emit('downloading', code, min(progress, 100))

        tessfile = f'{code}.traineddata'
        tessfile_path = os.path.join(TESSDATA_DIR, tessfile)
        
        # Try 1: tessdata_best (High quality)
        try:
            request.urlretrieve(TESSDATA_BEST_URL + tessfile, tessfile_path, update_progress)
            return code
        except Exception:
            logger.debug(f"Anura: tessdata_best not available for {code}, trying fallback...")
            # Try 2: tessdata (Standard)
            try:
                request.urlretrieve(TESSDATA_URL + tessfile, tessfile_path, update_progress)
                return code
            except Exception as e:
                logger.error(f"Anura: Failed to download model {code}: {e}")
                return None

    def download_done(self, code: str):
        """Callback when download completes."""
        self._need_update_cache = True
        if code and code in self.loading_languages:
            self.loading_languages.pop(code)
        self.emit('downloaded', code)

    def remove_language(self, code: str):
        """Removes the model file from the system."""
        try:
            path = os.path.join(TESSDATA_DIR, f"{code}.traineddata")
            if os.path.exists(path):
                os.remove(path)
                self._need_update_cache = True
                logger.info(f"Anura: Model {code} removed successfully.")
                self.emit('removed', code)
        except Exception as e:
            logger.error(f"Anura: Error removing language {code}: {e}")


# Singleton instance for the application
language_manager = LanguageManager()