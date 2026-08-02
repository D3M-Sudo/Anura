# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import MagicMock, patch

from anura.services.history_service import HistoryService


class TestHistoryService(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for history files during tests
        self.test_dir = tempfile.TemporaryDirectory()
        self.history_dir_path = self.test_dir.name

        # Patch GSettings to control settings in tests
        self.mock_settings = MagicMock()
        self.mock_settings.get_boolean.return_value = True
        self.mock_settings.get_int.return_value = 5

        # Initialize HistoryService with mocked settings and path
        with patch("anura.services.history_service.settings", self.mock_settings), \
             patch.object(HistoryService, "_get_history_directory", return_value=Path(self.history_dir_path)):
            self.service = HistoryService()

    def tearDown(self):
        self.service.shutdown()
        self.test_dir.cleanup()

    def test_initialization_empty(self):
        self.assertEqual(len(self.service.get_sessions()), 0)

    def test_add_session(self):
        with patch("anura.services.history_service.settings", self.mock_settings):
            self.service.add_session("Hello World", "eng")
            sessions = self.service.get_sessions()
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0].text, "Hello World")
            self.assertEqual(sessions[0].lang, "eng")
            self.assertIsNotNone(sessions[0].id)
            self.assertTrue(sessions[0].timestamp <= time.time())

    def test_add_empty_session_skipped(self):
        with patch("anura.services.history_service.settings", self.mock_settings):
            self.service.add_session("", "eng")
            self.service.add_session("   ", "eng")
            self.assertEqual(len(self.service.get_sessions()), 0)

    def test_history_disabled_does_not_save(self):
        self.mock_settings.get_boolean.return_value = False
        with patch("anura.services.history_service.settings", self.mock_settings):
            self.service.add_session("Should not save", "eng")
            self.assertEqual(len(self.service.get_sessions()), 0)

    def test_history_limit_enforced(self):
        self.mock_settings.get_int.return_value = 3
        with patch("anura.services.history_service.settings", self.mock_settings):
            for i in range(5):
                self.service.add_session(f"Session {i}", "eng")
                time.sleep(0.01)  # Ensure distinct timestamps

            sessions = self.service.get_sessions()
            self.assertEqual(len(sessions), 3)
            # The most recent 3 sessions should be kept (index 4, 3, 2)
            self.assertEqual(sessions[0].text, "Session 4")
            self.assertEqual(sessions[1].text, "Session 3")
            self.assertEqual(sessions[2].text, "Session 2")

    def test_delete_session(self):
        with patch("anura.services.history_service.settings", self.mock_settings):
            self.service.add_session("Item to delete", "eng")
            session_id = self.service.get_sessions()[0].id
            self.assertTrue(self.service.delete_session(session_id))
            self.assertEqual(len(self.service.get_sessions()), 0)

    def test_clear_history(self):
        with patch("anura.services.history_service.settings", self.mock_settings):
            self.service.add_session("Item 1", "eng")
            self.service.add_session("Item 2", "eng")
            self.assertEqual(len(self.service.get_sessions()), 2)

            self.service.clear_history()
            self.assertEqual(len(self.service.get_sessions()), 0)

    def test_corrupt_file_graceful_degradation(self):
        # Write some malformed/invalid JSON into the history file
        history_file_path = os.path.join(self.history_dir_path, "history.json")
        with open(history_file_path, "w", encoding="utf-8") as f:
            f.write("{invalid-json-content}")

        # Re-initialize the service and ensure it handles it gracefully (degrades to empty state)
        with patch("anura.services.history_service.settings", self.mock_settings), \
             patch.object(HistoryService, "_get_history_directory", return_value=Path(self.history_dir_path)):
            corrupt_service = HistoryService()
            self.assertEqual(len(corrupt_service.get_sessions()), 0)


if __name__ == "__main__":
    unittest.main()
