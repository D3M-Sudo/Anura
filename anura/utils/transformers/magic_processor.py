# magic_processor.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

import logging
from loguru import logger
from anura.utils.transformers.models import OcrResult, TransformerType, TransformerProtocol
from anura.utils.transformers.base_transformers import SingleLineTransformer, MultiLineTransformer, ParagraphTransformer
from anura.utils.transformers.url_transformer import UrlTransformer
from anura.utils.transformers.email_transformer import EmailTransformer

class MagicProcessor:
    def __init__(self) -> None:
        self._transformers: dict[TransformerType, TransformerProtocol] = {
            TransformerType.SINGLE_LINE: SingleLineTransformer(),
            TransformerType.MULTI_LINE: MultiLineTransformer(),
            TransformerType.PARAGRAPH: ParagraphTransformer(),
            TransformerType.MAIL: EmailTransformer(),
            TransformerType.URL: UrlTransformer(),
        }

    def process(self, ocr_data: dict) -> str:
        """
        Process raw Tesseract data (from image_to_data) and return transformed text.
        """
        # Convert Tesseract dict (lists) to list of dicts for easier processing
        words = []
        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            words.append({
                'text': ocr_data['text'][i],
                'block_num': ocr_data['block_num'][i],
                'par_num': ocr_data['par_num'][i],
                'line_num': ocr_data['line_num'][i],
                'conf': ocr_data['conf'][i]
            })

        # Base text for scoring
        raw_text = " ".join([w['text'] for w in words if w['text'].strip()])

        result = OcrResult(words=words, text=raw_text)

        # Calculate scores
        scores = {}
        for t_type, transformer in self._transformers.items():
            scores[t_type] = transformer.score(result)

        result.transformer_scores = scores

        # Select best transformer
        best_type = max(scores, key=scores.get)
        if scores[best_type] > 0:
            logger.debug(f"Anura Magics: Selected {best_type} with score {scores[best_type]}")
            transformed_parts = self._transformers[best_type].transform(result)
            final_text = "\n".join(transformed_parts)
        else:
            final_text = result.add_linebreaks()

        return final_text

# Singleton
_magic_processor = None

def get_magic_processor() -> MagicProcessor:
    global _magic_processor
    if _magic_processor is None:
        _magic_processor = MagicProcessor()
    return _magic_processor
