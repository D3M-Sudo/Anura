# models.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# MIT License
"""Models for the Magic Transformer pattern."""

from dataclasses import dataclass, field
import enum
from typing import Protocol


class TransformerType(enum.StrEnum):
    SINGLE_LINE = "SINGLE_LINE"
    MULTI_LINE = "MULTI_LINE"
    PARAGRAPH = "PARAGRAPH"
    MAIL = "MAIL"
    URL = "URL"


@dataclass
class OcrResult:
    """Encapsulate recognized text and layout information from image_to_data."""

    words: list[dict]
    text: str = ""
    transformer_scores: dict[TransformerType, float] = field(default_factory=dict)
    parsed: list[str] = field(default_factory=list)

    def _count_unique_sections(self, level: str) -> int:
        unique_sections = {w[level] for w in self.words if level in w}
        return len(unique_sections)

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
            if not word.get("text", "").strip():
                continue

            block_num = word.get("block_num")
            par_num = word.get("par_num")
            line_num = word.get("line_num")

            if last_block_num is not None and block_num != last_block_num:
                text_parts.append(block_sep)
            elif last_par_num is not None and par_num != last_par_num:
                text_parts.append(par_sep)
            elif last_line_num is not None and line_num != last_line_num:
                text_parts.append(line_sep)
            elif last_line_num is not None:
                text_parts.append(word_sep)

            text_parts.append(word["text"])

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
