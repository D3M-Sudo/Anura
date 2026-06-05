# tests/test_regex.py
import json
import unittest
from unittest.mock import MagicMock, patch

from velis.services.regex_service import RegexService


class TestRegexService(unittest.TestCase):
    @patch('velis.services.regex_service.get_settings')
    def test_scan_text(self, mock_get_settings):
        # Mock settings to return a test pattern
        mock_settings = MagicMock()
        mock_settings.get_string.return_value = json.dumps([
            {"name": "Email", "pattern": r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}"}
        ])
        mock_get_settings.return_value = mock_settings

        service = RegexService()
        text = "Contact me at test@example.com for info."
        matches = service.scan_text(text)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["name"], "Email")
        self.assertEqual(matches[0]["value"], "test@example.com")

if __name__ == '__main__':
    unittest.main()
