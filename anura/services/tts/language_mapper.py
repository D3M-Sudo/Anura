# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from typing import ClassVar

import gtts
from loguru import logger
import requests


class LanguageMapper:
    """
    Maps Tesseract language codes to gTTS-compatible ISO 639-1 codes.
    """

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

    _gtts_cache: dict | None = None

    @classmethod
    def get_supported_gtts_languages(cls) -> dict:
        """Cache of gTTS supported languages (class-level fallback)."""
        if cls._gtts_cache is None:
            try:
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
        if tess_code in cls.LANG_MAP:
            return cls.LANG_MAP[tess_code]

        # 2. Validate 2-char prefix against supported languages
        supported = cls.get_supported_gtts_languages()
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
