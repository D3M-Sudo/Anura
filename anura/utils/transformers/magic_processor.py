# magic_processor.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

from loguru import logger

from anura.types.ocr import OcrResult as OcrData
from anura.utils.singleton import get_instance
from anura.utils.transformers.base_transformers import MultiLineTransformer, ParagraphTransformer, SingleLineTransformer
from anura.utils.transformers.email_transformer import EmailTransformer
from anura.utils.transformers.models import OcrResult, TransformerProtocol, TransformerType
from anura.utils.transformers.url_transformer import UrlTransformer


class MagicProcessor:
    def __init__(self) -> None:
        self._transformers: dict[TransformerType, TransformerProtocol] = {
            TransformerType.SINGLE_LINE: SingleLineTransformer(),
            TransformerType.MULTI_LINE: MultiLineTransformer(),
            TransformerType.PARAGRAPH: ParagraphTransformer(),
            TransformerType.MAIL: EmailTransformer(),
            TransformerType.URL: UrlTransformer(),
        }

    def process(self, ocr_data: OcrData) -> tuple[str, float]:
        """
        Process OcrData and return transformed text
        along with the average confidence score.
        """
        # Compatibility layer: convert OcrData back to words for legacy Transformer logic
        # (Transformer refactoring will happen in a future phase)
        words = []
        for w in ocr_data.words:
            words.append({
                'text': w.text,
                'block_num': w.block_num,
                'par_num': w.par_num,
                'line_num': w.line_num,
                'conf': w.conf
            })

        result = OcrResult(words=words, text=ocr_data.raw_text)
        avg_conf = ocr_data.avg_confidence

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

        return final_text, avg_conf

def get_magic_processor() -> MagicProcessor:
    """Get the thread-safe MagicProcessor singleton.

    Returns:
        The singleton MagicProcessor instance.
    """
    return get_instance(MagicProcessor)
