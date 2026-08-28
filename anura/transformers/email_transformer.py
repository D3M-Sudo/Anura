# email_transformer.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

from anura.transformers.models import OcrResult, TransformerProtocol
from anura.utils.validators import EMAIL_RE


def _extract_emails(text: str) -> list[str]:
    return EMAIL_RE.findall(text)


class EmailTransformer(TransformerProtocol):
    def score(self, ocr_result: OcrResult) -> float:
        text = ocr_result.text
        emails = _extract_emails(text)
        if not emails:
            return 0

        email_chars = sum(len(e) for e in emails)
        # Simplified clean text logic
        count_chars = max(len(text.replace(" ", "")), 1)
        ratio = min(email_chars / count_chars, 1)
        return round(100 * ratio, 2)

    def transform(self, ocr_result: OcrResult) -> list[str]:
        return _extract_emails(ocr_result.text)
