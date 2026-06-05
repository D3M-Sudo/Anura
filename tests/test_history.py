# tests/test_history.py
import shutil
import tempfile
import unittest
from unittest.mock import patch

from velis.services.history_service import HistoryService


class TestHistoryService(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.patcher = patch('os.path.expanduser', return_value=self.test_dir)
        self.patcher.start()
        self.service = HistoryService()

    def tearDown(self):
        self.patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_add_and_get_history(self):
        self.service.add_entry("Test text")
        history = self.service.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["text"], "Test text")

if __name__ == '__main__':
    unittest.main()
