# models.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License
"""Models for the Magic Transformer pattern."""

from dataclasses import dataclass, field
import enum
from typing import Any, Protocol


class TransformerType(enum.StrEnum):
    SINGLE_LINE = "SINGLE_LINE"
    MULTI_LINE = "MULTI_LINE"
    PARAGRAPH = "PARAGRAPH"
    MAIL = "MAIL"
    URL = "URL"


@dataclass
class OcrResult:
    """Encapsulate recognized text and layout information from image_to_data."""

    words: list[Any]
    text: str = ""
    transformer_scores: dict[TransformerType, float] = field(default_factory=dict)
    parsed: list[str] = field(default_factory=list)

    def _get_val(self, obj: Any, attr: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(attr)
        return getattr(obj, attr, None)

    def _count_unique_sections(self, level: str) -> int:
        keys: set[tuple[Any, ...]]
        if level == "block_num":
            keys = {(self._get_val(w, "block_num"),) for w in self.words}
        elif level == "par_num":
            keys = {(self._get_val(w, "block_num"), self._get_val(w, "par_num")) for w in self.words}
        elif level == "line_num":
            keys = {
                (self._get_val(w, "block_num"), self._get_val(w, "par_num"), self._get_val(w, "line_num"))
                for w in self.words
            }
        else:
            keys = {(self._get_val(w, level),) for w in self.words}

        return len(keys)

    @property
    def num_lines(self) -> int:
        return self._count_unique_sections("line_num")

    @property
    def num_pars(self) -> int:
        return self._count_unique_sections("par_num")

    @property
    def num_blocks(self) -> int:
        return self._count_unique_sections("block_num")

    def add_linebreaks(
        self,
        block_sep: str = "\n\n",
        par_sep: str = "\n",
        line_sep: str = "\n",
        word_sep: str = " ",
    ) -> str:
        if not self.words:
            return ""

        last_block_num = None
        last_par_num = None
        last_line_num = None
        text_parts = []

        for word in self.words:
            # Skip empty entries often returned by Tesseract for layout markers
            text = self._get_val(word, "text")
            if not text or not text.strip():
                continue

            block_num = self._get_val(word, "block_num")
            par_num = self._get_val(word, "par_num")
            line_num = self._get_val(word, "line_num")

            if last_block_num is not None and block_num != last_block_num:
                text_parts.append(block_sep)
            elif last_par_num is not None and par_num != last_par_num:
                text_parts.append(par_sep)
            elif last_line_num is not None and line_num != last_line_num:
                text_parts.append(line_sep)
            elif last_line_num is not None:
                text_parts.append(word_sep)

            text_parts.append(text)

            last_block_num = block_num
            last_par_num = par_num
            last_line_num = line_num

        return "".join(text_parts).strip()


class ITransformer(Protocol):
    """Protocol for OCR result transformers."""

    def score(self, ocr_result: OcrResult) -> float:
        """Calculate a score (0.0 to 1.0) indicating how well this transformer fits the result."""
        ...

    def transform(self, ocr_result: OcrResult) -> list[str]:
        """Transform the OCR result into a list of strings."""
        ...


# Compatibility alias
TransformerProtocol = ITransformer
