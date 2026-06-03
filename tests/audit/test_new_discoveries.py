from unittest.mock import MagicMock, patch

import pytest


def test_idn_rejection_over_aggressive(headless_gi_mocks):
    """[NEW-011] Reproduction: Legitimate IDN with ASCII prefix is rejected."""
    from anura.utils.validators import is_safe_url_string

    # munchen.de with umlaut. This contains ASCII 'm', 'u'...
    # The current logic rejects it because it's a mixed label.
    legit = "https://münchen.de"
    assert is_safe_url_string(legit) is False  # Currently fails security check


def test_result_dispatcher_crash_on_none(headless_gi_mocks):
    """[NEW-009] Reproduction: ResultDispatcher crashes if preprocessor returns None."""
    from anura.services.result_dispatcher import ResultDispatcher

    dispatcher = ResultDispatcher()
    with patch("anura.services.result_dispatcher.get_text_preprocessor") as mock_get:
        mock_pre = MagicMock()
        mock_get.return_value = mock_pre
        mock_pre.extract_structured_data.return_value = None

        with pytest.raises(AttributeError):
            dispatcher.dispatch("Some text")


def test_tesseract_cmd_override_ignored(headless_gi_mocks):
    """[NEW-012] Reproduction: TESSERACT_CMD environment variable is ignored."""
    import os

    import pytesseract

    from anura.services.screenshot_service import _configure_tesseract_path

    with patch("anura.services.screenshot_service._is_flatpak_environment", return_value=False):
        os.environ["TESSERACT_CMD"] = "/custom/tess"
        _configure_tesseract_path()
        # Should be /custom/tess but logic pops it
        assert pytesseract.pytesseract.tesseract_cmd == "tesseract"
