from anura.types.ocr import OcrResult, OcrWord
from anura.utils.structural_reconstructor import get_structural_reconstructor


def test_structural_reconstructor_basic():
    reconstructor = get_structural_reconstructor()

    # Simulate two lines that should be merged (small vertical distance)
    # line 1: top=10, height=10 -> bottom=20
    # line 2: top=25, height=10 -> v_dist = 5 (0.5 * height)
    words = [
        OcrWord("Line1", 10, 10, 50, 10, 90.0, 1, 1, 1),
        OcrWord("Line2", 10, 25, 50, 10, 90.0, 2, 1, 1),
    ]
    ocr_res = OcrResult(words=tuple(words), raw_text="Line1 Line2", avg_confidence=90.0)

    text, conf = reconstructor.reconstruct(ocr_res)
    # Should be merged into one paragraph with a space
    assert text == "Line1 Line2"
    assert conf == 90.0

def test_structural_reconstructor_paragraphs():
    reconstructor = get_structural_reconstructor()

    # Simulate two lines that should NOT be merged (large vertical distance)
    # line 1: top=10, height=10 -> bottom=20
    # line 2: top=50, height=10 -> v_dist = 30 (3 * height)
    words = [
        OcrWord("Para1", 10, 10, 50, 10, 90.0, 1, 1, 1),
        OcrWord("Para2", 10, 50, 50, 10, 90.0, 2, 2, 1),
    ]
    ocr_res = OcrResult(words=tuple(words), raw_text="Para1 Para2", avg_confidence=90.0)

    text, _conf = reconstructor.reconstruct(ocr_res)
    # Should be separate paragraphs with \n\n
    assert text == "Para1\n\nPara2"

def test_structural_reconstructor_horizontal_separation():
    reconstructor = get_structural_reconstructor()

    # Simulate two lines that should NOT be merged due to horizontal offset
    # line 1: left=10, height=10
    # line 2: left=100, top=25, height=10 -> h_diff = 90 (9 * height)
    words = [
        OcrWord("Left", 10, 10, 50, 10, 90.0, 1, 1, 1),
        OcrWord("Right", 100, 25, 50, 10, 90.0, 2, 1, 1),
    ]
    ocr_res = OcrResult(words=tuple(words), raw_text="Left Right", avg_confidence=90.0)

    text, _conf = reconstructor.reconstruct(ocr_res)
    # Should be separate paragraphs with \n\n
    assert text == "Left\n\nRight"

def test_structural_reconstructor_empty():
    reconstructor = get_structural_reconstructor()
    ocr_res = OcrResult(words=(), raw_text="", avg_confidence=0.0)
    text, conf = reconstructor.reconstruct(ocr_res)
    assert text == ""
    assert conf == 0.0
