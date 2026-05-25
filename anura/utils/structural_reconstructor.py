# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from typing import Any

from anura.types.ocr import OcrResult
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

        # Group words into lines
        words = ocr_result.words
        lines = []
        current_line = []
        last_line_id = -1

        for i, word in enumerate(words):
            if task_id and i % 50 == 0:
                from anura.core.atomic_task_manager import get_atomic_manager

                if get_atomic_manager().is_cancelled(task_id):
                    raise InterruptedError(f"Task {task_id} was cancelled")

            # Simple grouping by line_num and par_num/block_num
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

        # Merge lines into paragraphs based on geometry
        paragraphs = []
        if not lines:
            return ("", 0.0)

        current_paragraph = [lines[0]]

        for i in range(1, len(lines)):
            if task_id and i % 10 == 0:
                from anura.core.atomic_task_manager import get_atomic_manager

                if get_atomic_manager().is_cancelled(task_id):
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
            "height": bottom - top,
            "width": right - left,
        }

    def _should_merge(self, line1: dict, line2: dict) -> bool:
        """Determine if two lines should be merged into a paragraph."""
        # Vertical distance check
        v_dist = line2["top"] - line1["bottom"]
        avg_height = (line1["height"] + line2["height"]) / 2

        # If vertical distance is within threshold of line height
        if v_dist > avg_height * self.proximity_threshold:
            return False

        # Horizontal alignment check (start of lines)
        h_diff = abs(line1["left"] - line2["left"])
        return h_diff <= avg_height * 3


def get_structural_reconstructor() -> StructuralReconstructor:
    """Get the thread-safe StructuralReconstructor singleton.

    Returns:
        The singleton StructuralReconstructor instance.
    """
    return get_instance(StructuralReconstructor)
