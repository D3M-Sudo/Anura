# tests/test_gi_atomic_task_manager_unit.py
#
# Unit tests for AtomicTaskManager — no GTK display required.
# Tests run directly in CI without xvfb-run.

import pytest

pytest.importorskip("gi")

import threading
import uuid

from anura.core.atomic_task_manager import AtomicTaskManager, AtomicTaskResult, get_atomic_manager
from anura.utils.singleton import ThreadSafeSingleton


class TestAtomicTaskResult:
    def test_result_stores_data(self):
        task_id = str(uuid.uuid4())
        result = AtomicTaskResult(task_id=task_id, data=42)
        assert result.task_id == task_id
        assert result.data == 42
        assert result.error is None

    def test_result_stores_error(self):
        task_id = str(uuid.uuid4())
        err = ValueError("test")
        result = AtomicTaskResult(task_id=task_id, error=err, traceback_str="tb")
        assert result.error is err
        assert result.traceback_str == "tb"


class TestAtomicTaskManagerUnit:
    def setup_method(self):
        ThreadSafeSingleton.reset_for_testing()

    def test_singleton_returns_same_instance(self):
        m1 = get_atomic_manager()
        m2 = get_atomic_manager()
        assert m1 is m2

    def test_init_state(self):
        manager = AtomicTaskManager()
        assert manager._current_task_id is None
        assert manager._cancellable is None

    def test_execute_returns_task_id(self):
        manager = AtomicTaskManager()
        event = threading.Event()
        task_id = manager.execute(lambda: event.set())
        assert isinstance(task_id, str)
        assert len(task_id) == 36  # UUID format

    def test_execute_updates_current_task_id(self):
        manager = AtomicTaskManager()
        barrier = threading.Barrier(2)

        def blocking():
            barrier.wait(timeout=2)

        task_id = manager.execute(blocking)
        assert manager._current_task_id == task_id
        barrier.wait(timeout=2)

    def test_second_execute_invalidates_first(self):
        """Submitting a second task updates _current_task_id, making first stale."""
        manager = AtomicTaskManager()
        barrier = threading.Barrier(2)

        def blocking():
            barrier.wait(timeout=2)

        id1 = manager.execute(blocking)
        barrier.wait(timeout=2)
        id2 = manager.execute(lambda: None)

        assert id1 != id2
        assert manager._current_task_id == id2

    def test_state_lock_exists_and_is_lock(self):
        manager = AtomicTaskManager()
        assert isinstance(manager._state_lock, type(threading.Lock()))

    def test_default_errorback_logs_without_raising(self):
        manager = AtomicTaskManager()
        err = RuntimeError("test error")
        # Should not raise
        manager._default_errorback(err, "traceback string")
        manager._default_errorback(err, None)

    def test_shutdown_completes(self):
        manager = AtomicTaskManager()
        manager.shutdown()  # Must not raise
