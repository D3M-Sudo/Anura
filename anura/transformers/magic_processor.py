# magic_processor.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License

from loguru import logger

from anura.types.ocr import OcrResult as OcrData
from anura.utils.singleton import get_instance
from anura.transformers.models import OcrResult, ITransformer


class MagicProcessor:
    """
    Orchestrates OCR result transformations using a Chain of Responsibility pattern.
    Iterates over a registry of ITransformer implementations to select the best fit.
    """

    def __init__(self) -> None:
        self._transformers: list[ITransformer] = []
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return

        from anura.transformers.base_transformers import (
            MultiLineTransformer,
            ParagraphTransformer,
            SingleLineTransformer,
        )
        from anura.transformers.email_transformer import EmailTransformer
        from anura.transformers.url_transformer import UrlTransformer

        self.register_transformer(SingleLineTransformer())
        self.register_transformer(MultiLineTransformer())
        self.register_transformer(ParagraphTransformer())
        self.register_transformer(EmailTransformer())
        self.register_transformer(UrlTransformer())
        self._initialized = True

    def register_transformer(self, transformer: ITransformer) -> None:
        """Register a new transformer in the chain."""
        self._transformers.append(transformer)
        logger.debug(f"MagicProcessor: Registered transformer {type(transformer).__name__}")

    def process(self, ocr_data: OcrData, task_id: str | None = None) -> tuple[str, float]:
        """
        Process OcrData and return transformed text
        along with the average confidence score.
        """
        # Compatibility layer: convert OcrData back to words for legacy Transformer logic
        # (Transformer refactoring will happen in a future phase)
        words = []
        for w in ocr_data.words:
            words.append(
                {"text": w.text, "block_num": w.block_num, "par_num": w.par_num, "line_num": w.line_num, "conf": w.conf}
            )

        result = OcrResult(words=words, text=ocr_data.raw_text)
        avg_conf = ocr_data.avg_confidence

        self._ensure_initialized()

        # Calculate scores using Chain of Responsibility
        best_score = -1.0
        best_transformer = None

        for i, transformer in enumerate(self._transformers):
            if task_id and i % 2 == 0:
                from anura.core.atomic_task_manager import get_atomic_manager

                if get_atomic_manager().is_cancelled(task_id):
                    raise InterruptedError(f"Task {task_id} was cancelled during Magic score calculation")

            current_score = transformer.score(result)
            if current_score > best_score:
                best_score = current_score
                best_transformer = transformer

        # Select best transformer
        if best_transformer and best_score > 0:
            logger.debug(f"Anura Magics: Selected {type(best_transformer).__name__} with score {best_score}")
            transformed_parts = best_transformer.transform(result)
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
