# base_transformers.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

from anura.utils.transformers.models import OcrResult, TransformerProtocol


class SingleLineTransformer(TransformerProtocol):
    def score(self, ocr_result: OcrResult) -> float:
        if not ocr_result.words:
            return 1
        return 50 if ocr_result.num_lines == 1 else 0

    def transform(self, ocr_result: OcrResult) -> list[str]:
        return [ocr_result.add_linebreaks(line_sep=" ")]

class MultiLineTransformer(TransformerProtocol):
    def score(self, ocr_result: OcrResult) -> float:
        if (ocr_result.num_lines > 1 and
            ocr_result.num_blocks == 1 and
            ocr_result.num_pars == 1):
            return 50.0
        return 0

    def transform(self, ocr_result: OcrResult) -> list[str]:
        return [ocr_result.add_linebreaks()]

class ParagraphTransformer(TransformerProtocol):
    def score(self, ocr_result: OcrResult) -> float:
        breaks = max(1, ocr_result.num_blocks + ocr_result.num_pars - 1)
        return 100 - (100 / breaks)

    def transform(self, ocr_result: OcrResult) -> list[str]:
        return [ocr_result.add_linebreaks(block_sep="\n", line_sep=" ")]
