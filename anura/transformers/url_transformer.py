# url_transformer.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

import re
from urllib.parse import urlsplit

from anura.transformers.models import OcrResult, TransformerProtocol
from anura.utils.validators import URL_RE


def _has_valid_tld(url: str) -> bool:
    """Verify the candidate has a hostname whose last label looks like a TLD.

    The previous regex required ``/`` or end-of-string immediately after the
    TLD, so ``https://example.com?next=/path``, ``https://example.com#section``
    and ``https://example.com:8443/path`` were all discarded even though the
    shared URL pattern matched them. Parsing separates the hostname from the
    port, query and fragment.
    """
    # URL_RE also matches scheme-less forms such as "www.example.com"; urlsplit
    # only fills .hostname when the authority is explicit.
    candidate = url if "://" in url else f"//{url}"
    try:
        parsed = urlsplit(candidate)
        host = parsed.hostname
        # Reading .port validates it: a non-numeric port raises ValueError, and
        # such a candidate must not be offered as a working URL.
        _ = parsed.port
    except ValueError:
        return False

    if not host:
        return False

    labels = host.rstrip(".").split(".")
    if len(labels) < 2:
        return False

    tld = labels[-1]
    return len(tld) >= 2 and tld.isascii() and tld.isalpha()


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
