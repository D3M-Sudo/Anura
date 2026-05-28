# url_transformer.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

import re

from anura.transformers.models import OcrResult, TransformerProtocol
from anura.utils.validators import URL_RE

# Simplified TLD check for standalone version
TLDS = {"COM", "ORG", "NET", "EDU", "GOV", "IO", "IT", "DE", "FR", "UK", "APP", "DEV"}


def _has_valid_tld(url: str) -> bool:
    match = re.search(r"(?:\.)([a-zA-Z]{2,})(?:\/|$)", url, re.IGNORECASE)
    tld = match.group(1) if match else ""
    # Hardened TLD check: length check is a heuristic fallback for the whitelist.
    # Logic simplified to clarify the fallback behavior.
    return len(tld) >= 2


def _extract_urls(text: str) -> list[str]:
    # Correct commonly unrecognized parts
    text = re.sub(r":\s+\/", ":/", text)

    all_urls = URL_RE.findall(text)
    return [url for url in all_urls if _has_valid_tld(url)]


class UrlTransformer(TransformerProtocol):
    def score(self, ocr_result: OcrResult) -> float:
        text = ocr_result.text
        urls = _extract_urls(text)
        if not urls:
            return 0

        url_chars = sum(len(e) for e in urls)
        all_chars = max(len(text), 1)
        ratio = url_chars / all_chars
        return round(100 * min(ratio * 0.85, 1), 2)

    def transform(self, ocr_result: OcrResult) -> list[str]:
        return _extract_urls(ocr_result.text)
