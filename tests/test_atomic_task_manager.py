# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import time
import pytest
from unittest.mock import MagicMock, patch
from anura.atomic_task_manager import AtomicTaskManager, get_atomic_manager


class TestAtomicTaskManager:
    def test_singleton(self):
        manager1 = get_atomic_manager()
        manager2 = get_atomic_manager()
        assert manager1 is manager2

    def test_execute_and_callback(self):
        manager = AtomicTaskManager()
        mock_command = MagicMock(return_value="success")
        mock_callback = MagicMock()

        # Patch GLib in the module where it's used
        with patch("anura.atomic_task_manager.GLib") as mock_glib:
            task_id = manager.execute(mock_command, callback=mock_callback)
            assert task_id is not None

            # Simulate thread completion
            timeout = time.time() + 2
            while not mock_glib.idle_add.called and time.time() < timeout:
                time.sleep(0.1)

            assert mock_glib.idle_add.called
            args, kwargs = mock_glib.idle_add.call_args
            # args[1] is result object
            assert args[1].data == "success"
            # args[2] is callback
            assert args[2] == mock_callback

    def test_task_versioning_and_cancellation(self):
        manager = AtomicTaskManager()

        def slow_command():
            time.sleep(0.5)
            return "slow"

        mock_callback = MagicMock()

        with patch("anura.atomic_task_manager.GLib") as mock_glib:
            mock_glib.SOURCE_REMOVE = 1
            # Start task 1
            id1 = manager.execute(slow_command, callback=mock_callback)

            # Immediately start task 2 (this should invalidate task 1)
            id2 = manager.execute(lambda: "fast", callback=mock_callback)

            assert id1 != id2

            # Wait for fast task to finish and call idle_add
            timeout = time.time() + 2
            found_id2 = False
            while time.time() < timeout:
                for call in mock_glib.idle_add.call_args_list:
                    res = call.args[1]
                    if res.task_id == id2:
                        found_id2 = True
                        break
                if found_id2:
                    break
                time.sleep(0.1)

            assert found_id2

            # Simulate calling the success handler for id2
            for call in mock_glib.idle_add.call_args_list:
                res = call.args[1]
                if res.task_id == id2:
                    handler = call.args[0]
                    handler(res, call.args[2])

            assert mock_callback.called
            mock_callback.assert_called_with("fast")

            # Reset mock
            mock_callback.reset_mock()

            # Wait for slow task to finish and call idle_add
            found_id1 = False
            while time.time() < timeout:
                for call in mock_glib.idle_add.call_args_list:
                    res = call.args[1]
                    if res.task_id == id1:
                        found_id1 = True
                        break
                if found_id1:
                    break
                time.sleep(0.1)

            assert found_id1

            # Now simulate calling the success handler for task 1 (it should be ignored)
            for call in mock_glib.idle_add.call_args_list:
                res = call.args[1]
                if res.task_id == id1:
                    handler = call.args[0]
                    ret = handler(res, call.args[2])
                    assert ret == 1 # GLib.SOURCE_REMOVE

            assert not mock_callback.called
