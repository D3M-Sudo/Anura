# velis/services/translation_service.py
from loguru import logger
import requests

from velis.services.settings_service import get_settings
from velis.utils.singleton import get_instance


class TranslationService:
    def __init__(self):
        pass

    def translate(self, text, target_lang, source_lang='auto'):
        settings = get_settings()
        endpoint = settings.get_string("translate-endpoint").rstrip('/')
        api_key = settings.get_string("translate-api-key")

        url = f"{endpoint}/translate"
        payload = {
            "q": text,
            "source": source_lang,
            "target": target_lang,
            "format": "text"
        }
        if api_key:
            payload["api_key"] = api_key

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()["translatedText"]
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise e

def get_translation_service():
    return get_instance(TranslationService)
