import pytest

pytest.importorskip("gi")

from anura.models.ocr import OcrResult
from anura.transformers.magic_processor import get_magic_processor


def create_mock_ocr_result(text_list, conf=90.0):
    """Utility to create a mock OcrResult for testing."""
    return OcrResult.from_tesseract_dict(
        {
            "text": text_list,
            "conf": [conf] * len(text_list),
            "left": [10 * i for i in range(len(text_list))],
            "top": [10] * len(text_list),
            "width": [5] * len(text_list),
            "height": [5] * len(text_list),
            "line_num": [1] * len(text_list),
            "par_num": [1] * len(text_list),
            "block_num": [1] * len(text_list),
        }
    )


def test_magic_processor_single_line():
    processor = get_magic_processor()
    ocr_res = create_mock_ocr_result(["Hello", "World"])
    text, conf, name = processor.process(ocr_res)
    assert "Hello World" in text
    assert conf == 90.0
    assert name == "SingleLine"


def test_magic_processor_url():
    processor = get_magic_processor()
    ocr_res = create_mock_ocr_result(["https://github.com/d3msudo/anura"])
    text, _conf, name = processor.process(ocr_res)
    assert "https://github.com/d3msudo/anura" in text
    assert name == "Url"


def test_magic_processor_email():
    processor = get_magic_processor()
    ocr_res = create_mock_ocr_result(["test@example.com"])
    text, _conf, name = processor.process(ocr_res)
    assert "test@example.com" in text
    assert name == "Email"


def test_magic_processor_multi_line():
    # Simulate multiple lines by varying line_num
    processor = get_magic_processor()
    ocr_res = OcrResult.from_tesseract_dict(
        {
            "text": ["Line", "One", "Line", "Two"],
            "conf": [90.0] * 4,
            "left": [10, 20, 10, 20],
            "top": [10, 10, 30, 30],
            "width": [5] * 4,
            "height": [5] * 4,
            "line_num": [1, 1, 2, 2],
            "par_num": [1, 1, 1, 1],
            "block_num": [1, 1, 1, 1],
        }
    )
    text, _conf, name = processor.process(ocr_res)
    assert "Line One" in text
    assert "Line Two" in text
    assert "\n" in text
    assert name == "MultiLine"


def test_magic_processor_empty():
    processor = get_magic_processor()
    ocr_res = OcrResult(words=(), raw_text="", avg_confidence=0.0)
    text, conf, name = processor.process(ocr_res)
    assert text == ""
    assert conf == 0.0
    assert name == ""
