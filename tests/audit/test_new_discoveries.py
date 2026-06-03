import os
from unittest.mock import MagicMock, patch


def test_idn_validation_allows_latin1_supplement(headless_gi_mocks):
    """[NEW-011] Verification: Legitimate IDN (Latin-1) is now accepted."""
    from anura.utils.validators import is_safe_url_string

    # munchen.de with umlaut. Previously rejected, now allowed.
    legit = "https://münchen.de"
    assert is_safe_url_string(legit) is True


def test_result_dispatcher_null_safe(headless_gi_mocks):
    """[NEW-009] Verification: ResultDispatcher no longer crashes on None."""
    from anura.services.result_dispatcher import ResultDispatcher

    dispatcher = ResultDispatcher()
    with patch("anura.services.result_dispatcher.get_text_preprocessor") as mock_get:
        mock_pre = MagicMock()
        mock_get.return_value = mock_pre
        mock_pre.extract_structured_data.return_value = None

        # Should NOT raise AttributeError anymore
        result = dispatcher.dispatch("Some text")
        assert result.text == "Some text"


def test_tesseract_cmd_override_preserved(headless_gi_mocks):
    """[NEW-012] Verification: TESSERACT_CMD environment variable is preserved."""
    import pytesseract

    from anura.services.screenshot_service import _configure_tesseract_path

    # Clean env for test
    with patch("os.environ", {}), patch("shutil.which", return_value=True):
        os.environ["TESSERACT_CMD"] = "/custom/tess"
        with patch("anura.services.screenshot_service._is_flatpak_environment", return_value=False):
            _configure_tesseract_path()
            # Should be preserved
            assert pytesseract.pytesseract.tesseract_cmd == "/custom/tess"
