# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from typing import Any

from anura.core.atomic_task_manager import get_atomic_manager
from anura.models.ocr import OcrResult
from anura.utils.singleton import get_instance


class StructuralReconstructor:
    """
    Reconstructs text paragraphs based on geometric spatial proximity.
    Uses Tesseract bounding boxes to determine if blocks should be merged.
    """

    def __init__(self, proximity_threshold: float = 1.5) -> None:
        """
        Args:
            proximity_threshold: Multiplier for line height to determine merging.
        """
        self.proximity_threshold = proximity_threshold

    def reconstruct(self, ocr_result: OcrResult, task_id: str | None = None) -> tuple[str, float]:
        """
        Reconstructs text from OcrResult using spatial analysis.

        Args:
            ocr_result: Immutable OcrResult containing parsed Tesseract data.
            task_id: Optional task ID for cooperative cancellation.

        Returns:
            tuple: (Reconstructed text string, Average confidence score)
        """
        if not ocr_result.words:
            return "", 0.0

        words = ocr_result.words
        lines = []
        current_line = []
        last_line_id = -1

        for i, word in enumerate(words):
            if task_id and i % 50 == 0 and get_atomic_manager().is_cancelled(task_id):
                raise InterruptedError(f"Task {task_id} was cancelled")

            line_id = (word.block_num, word.par_num, word.line_num)
            if line_id != last_line_id:
                if current_line:
                    lines.append(self._process_line(current_line))
                current_line = [word]
                last_line_id = line_id
            else:
                current_line.append(word)

        if current_line:
            lines.append(self._process_line(current_line))

        paragraphs = []
        if not lines:
            return ("", 0.0)

        current_paragraph = [lines[0]]

        for i in range(1, len(lines)):
            if task_id and i % 10 == 0 and get_atomic_manager().is_cancelled(task_id):
                raise InterruptedError(f"Task {task_id} was cancelled")

            prev_line = lines[i - 1]
            curr_line = lines[i]

            if self._should_merge(prev_line, curr_line):
                current_paragraph.append(curr_line)
            else:
                paragraphs.append(" ".join([line["text"] for line in current_paragraph]))
                current_paragraph = [curr_line]

        if current_paragraph:
            paragraphs.append(" ".join([line["text"] for line in current_paragraph]))

        return "\n\n".join(paragraphs), ocr_result.avg_confidence

    def _process_line(self, words: list[Any]) -> dict:
        """Calculate line geometry from its words."""
        if not words:
            return {
                "text": "",
                "left": 0,
                "top": 0,
                "right": 0,
                "bottom": 0,
                "height": 0,
                "width": 0,
            }

        text = " ".join([w.text for w in words])
        left = min([w.left for w in words])
        top = min([w.top for w in words])
        right = max([w.left + w.width for w in words])
        bottom = max([w.top + w.height for w in words])

        return {
            "text": text,
            "left": left,
            "top": top,
            "right": right,
            "bottom": bottom,
            "height": max(0, bottom - top),
            "width": max(0, right - left),
        }

    def _should_merge(self, line1: dict, line2: dict) -> bool:
        """Determine if two lines should be merged into a paragraph."""
        v_dist = line2["top"] - line1["bottom"]
        avg_height = (line1["height"] + line2["height"]) / 2

        # Numerical stability: avoid division by zero or merging based on empty lines
        if avg_height <= 0:
            return False

        # If vertical distance is within threshold of line height
        if v_dist > avg_height * self.proximity_threshold:
            return False

        # Heuristic: also prevent merging if lines are physically too far apart vertically (overlap or huge gap)
        # but the proximity_threshold check above already handles the gap.
        # If v_dist is negative, it means lines overlap. We usually merge overlapping lines in OCR.

        h_diff = abs(line1["left"] - line2["left"])
        return h_diff <= avg_height * 3


def get_structural_reconstructor() -> StructuralReconstructor:
    """Get the thread-safe StructuralReconstructor singleton.

    Returns:
        The singleton StructuralReconstructor instance.
    """
    return get_instance(StructuralReconstructor)
