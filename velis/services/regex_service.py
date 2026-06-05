# velis/services/regex_service.py
import json
import re

from loguru import logger

from velis.services.settings_service import get_settings
from velis.utils.singleton import get_instance


class RegexService:
    def __init__(self):
        pass

    def get_patterns(self):
        settings = get_settings()
        raw = settings.get_string("regex-patterns")
        try:
            return json.loads(raw) if raw else []
        except Exception:
            return []

    def scan_text(self, text):
        patterns = self.get_patterns()
        matches = []
        for p in patterns:
            name = p.get("name", "Unnamed")
            pattern = p.get("pattern", "")
            if not pattern:
                continue

            try:
                for match in re.finditer(pattern, text):
                    matches.append({
                        "name": name,
                        "value": match.group(0),
                        "start": match.start(),
                        "end": match.end()
                    })
            except Exception as e:
                logger.error(f"Regex error in pattern '{name}': {e}")
        return matches

def get_regex_service():
    return get_instance(RegexService)
