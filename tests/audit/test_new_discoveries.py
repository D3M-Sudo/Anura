import os
import sys
from unittest.mock import MagicMock, patch

import pytest


# Pillar 2: Mock gi BEFORE any imports
class MockGi:
    @staticmethod
    def require_version(a, b):
        pass


if "gi" not in sys.modules:
    mock_gi = MagicMock()
    mock_gi.require_version = MockGi.require_version
    sys.modules["gi"] = mock_gi
    sys.modules["gi.repository"] = MagicMock()
    sys.modules["gi.repository.Gio"] = MagicMock()
    sys.modules["gi.repository.GLib"] = MagicMock()
    sys.modules["gi.repository.GObject"] = MagicMock()
    sys.modules["gi.repository.Adw"] = MagicMock()
    sys.modules["gi.repository.Gtk"] = MagicMock()

from anura.services.result_dispatcher import ResultDispatcher  # noqa: E402
from anura.utils.validators import is_safe_url_string  # noqa: E402


def test_idn_rejection_over_aggressive():
    """[NEW-011] Reproduction: Legitimate IDN with ASCII prefix is rejected."""
    # munchen.de with umlaut. This contains ASCII 'm', 'u'...
    # The current logic rejects it because it's a mixed label.
    legit = "https://münchen.de"
    assert is_safe_url_string(legit) is False  # Currently fails security check


def test_result_dispatcher_crash_on_none():
    """[NEW-009] Reproduction: ResultDispatcher crashes if preprocessor returns None."""
    dispatcher = ResultDispatcher()
    with patch("anura.services.result_dispatcher.get_text_preprocessor") as mock_get:
        mock_pre = MagicMock()
        mock_get.return_value = mock_pre
        mock_pre.extract_structured_data.return_value = None

        with pytest.raises(AttributeError):
            dispatcher.dispatch("Some text")


def test_tesseract_cmd_override_ignored():
    """[NEW-012] Reproduction: TESSERACT_CMD environment variable is ignored."""
    import pytesseract

    from anura.services.screenshot_service import _configure_tesseract_path

    with patch("anura.services.screenshot_service._is_flatpak_environment", return_value=False):
        os.environ["TESSERACT_CMD"] = "/custom/tess"
        _configure_tesseract_path()
        assert pytesseract.pytesseract.tesseract_cmd == "tesseract"
