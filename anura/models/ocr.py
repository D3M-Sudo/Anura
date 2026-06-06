# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class OcrWord:
    """Immutable representation of a single recognized word."""

    text: str
    left: int
    top: int
    width: int
    height: int
    conf: float
    line_num: int
    par_num: int
    block_num: int


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Immutable encapsulation of processed extraction results for UI consumption."""

    text: str
    raw_text: str
    urls: tuple[str, ...]
    emails: tuple[str, ...]
    phone_numbers: tuple[str, ...]
    avg_confidence: float
    bounding_box: tuple[int, int, int, int] = (0, 0, 0, 0)
    is_primary_url: bool = False


@dataclass(frozen=True, slots=True)
class OcrResult:
    """Immutable encapsulation of recognized text and layout information."""

    words: tuple[OcrWord, ...]
    raw_text: str = ""
    avg_confidence: float = 0.0

    @classmethod
    def from_tesseract_dict(cls, ocr_data: dict[str, list[Any]]) -> "OcrResult":
        """
        Factory method to parse Tesseract image_to_data dictionary into OcrResult.
        Performs a single $O(N)$ pass over the raw data.
        """
        words = []
        n_boxes = len(ocr_data.get("text", []))
        total_conf = 0.0
        conf_count = 0

        for i in range(n_boxes):
            text = ocr_data["text"][i]
            # Skip layout markers (empty text)
            if not text or not text.strip():
                continue

            conf = float(ocr_data["conf"][i])
            word = OcrWord(
                text=text,
                left=int(ocr_data["left"][i]),
                top=int(ocr_data["top"][i]),
                width=int(ocr_data["width"][i]),
                height=int(ocr_data["height"][i]),
                conf=conf,
                line_num=int(ocr_data["line_num"][i]),
                par_num=int(ocr_data["par_num"][i]),
                block_num=int(ocr_data["block_num"][i]),
            )
            words.append(word)

            if conf >= 0:
                total_conf += conf
                conf_count += 1

        avg_conf = total_conf / conf_count if conf_count > 0 else 0.0
        raw_text = " ".join([w.text for w in words])

        return cls(words=tuple(words), raw_text=raw_text, avg_confidence=avg_conf)

    def filter_by_confidence(self, min_confidence: float) -> list[OcrWord]:
        """Return words with confidence greater than or equal to the threshold."""
        return [w for w in self.words if w.conf >= min_confidence]

    def get_bounding_box(self) -> tuple[int, int, int, int]:
        """Return the overall bounding box of all recognized words (left, top, width, height)."""
        if not self.words:
            return 0, 0, 0, 0

        left = min(w.left for w in self.words)
        top = min(w.top for w in self.words)
        right = max(w.left + w.width for w in self.words)
        bottom = max(w.top + w.height for w in self.words)

        return left, top, right - left, bottom - top

    def _count_unique_sections(self, level: str) -> int:
        """
        Count unique layout sections at a given level (block, paragraph, line).
        Uses composite keys to prevent hierarchical ID collisions.
        """
        if level == "block_num":
            keys = {(w.block_num,) for w in self.words}
        elif level == "par_num":
            keys = {(w.block_num, w.par_num) for w in self.words}
        elif level == "line_num":
            keys = {(w.block_num, w.par_num, w.line_num) for w in self.words}
        else:
            keys = {(getattr(w, level),) for w in self.words}

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
