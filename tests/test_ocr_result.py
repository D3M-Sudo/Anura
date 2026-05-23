# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import unittest
from anura.types.ocr import OcrResult, OcrWord

class TestOcrDataModel(unittest.TestCase):
    def setUp(self):
        self.raw_data = {
            "text": ["Hello", "World", ""],
            "conf": [95, 80, -1],
            "left": [10, 60, 0],
            "top": [20, 20, 0],
            "width": [40, 40, 0],
            "height": [15, 15, 0],
            "line_num": [1, 1, 1],
            "par_num": [1, 1, 1],
            "block_num": [1, 1, 1],
        }

    def test_from_tesseract_dict_parsing(self):
        result = OcrResult.from_tesseract_dict(self.raw_data)

        # Verify empty text/markers are skipped
        self.assertEqual(len(result.words), 2)
        self.assertEqual(result.words[0].text, "Hello")
        self.assertEqual(result.words[1].text, "World")

        # Verify average confidence (95 + 80) / 2 = 87.5
        self.assertAlmostEqual(result.avg_confidence, 87.5)

        # Verify raw text reconstruction
        self.assertEqual(result.raw_text, "Hello World")

    def test_immutability_frozen(self):
        result = OcrResult.from_tesseract_dict(self.raw_data)
        with self.assertRaises(AttributeError):
            result.avg_confidence = 100.0

    def test_slots_presence(self):
        result = OcrResult.from_tesseract_dict(self.raw_data)
        # frozen=True + slots=True means no __dict__
        self.assertFalse(hasattr(result, "__dict__"))
        word = result.words[0]
        self.assertFalse(hasattr(word, "__dict__"))

    def test_geometric_helpers(self):
        result = OcrResult.from_tesseract_dict(self.raw_data)
        # left: 10, right: 60+40=100 -> width 90
        # top: 20, bottom: 20+15=35 -> height 15
        bbox = result.get_bounding_box()
        self.assertEqual(bbox, (10, 20, 90, 15))

    def test_confidence_filtering(self):
        result = OcrResult.from_tesseract_dict(self.raw_data)
        filtered = result.filter_by_confidence(90)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0].text, "Hello")

if __name__ == "__main__":
    unittest.main()
