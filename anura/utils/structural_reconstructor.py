# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT



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

    def reconstruct(self, ocr_data: dict) -> str:
        """
        Reconstructs text from raw Tesseract data using spatial analysis.

        Args:
            ocr_data: Dictionary from pytesseract.image_to_data(..., output_type=Output.DICT)

        Returns:
            Reconstructed text string.
        """
        words = []
        n_boxes = len(ocr_data["text"])
        for i in range(n_boxes):
            # Skip empty entries or low confidence if needed
            text = ocr_data["text"][i].strip()
            if not text:
                continue

            words.append(
                {
                    "text": text,
                    "left": ocr_data["left"][i],
                    "top": ocr_data["top"][i],
                    "width": ocr_data["width"][i],
                    "height": ocr_data["height"][i],
                    "line_num": ocr_data["line_num"][i],
                    "block_num": ocr_data["block_num"][i],
                    "par_num": ocr_data["par_num"][i],
                }
            )

        if not words:
            return ""

        # Group words into lines
        lines = []
        current_line = []
        last_line_id = -1

        for word in words:
            # Simple grouping by line_num and par_num/block_num
            line_id = (word["block_num"], word["par_num"], word["line_num"])
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
            return ""

        current_paragraph = [lines[0]]

        for i in range(1, len(lines)):
            prev_line = lines[i - 1]
            curr_line = lines[i]

            if self._should_merge(prev_line, curr_line):
                current_paragraph.append(curr_line)
            else:
                paragraphs.append(" ".join([line["text"] for line in current_paragraph]))
                current_paragraph = [curr_line]

        if current_paragraph:
            paragraphs.append(" ".join([line["text"] for line in current_paragraph]))

        return "\n\n".join(paragraphs)

    def _process_line(self, words: list[dict]) -> dict:
        """Calculate line geometry from its words."""
        text = " ".join([w["text"] for w in words])
        left = min([w["left"] for w in words])
        top = min([w["top"] for w in words])
        right = max([w["left"] + w["width"] for w in words])
        bottom = max([w["top"] + w["height"] for w in words])

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


# Global singleton instance
_structural_reconstructor = None


def get_structural_reconstructor() -> StructuralReconstructor:
    global _structural_reconstructor
    if _structural_reconstructor is None:
        _structural_reconstructor = StructuralReconstructor()
    return _structural_reconstructor
