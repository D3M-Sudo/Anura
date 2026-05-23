# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import pytest

pytest.importorskip("gi")

import threading
import time

from gi.repository import GLib, GObject

from anura.atomic_task_manager import get_atomic_manager
from anura.utils.signal_manager import SignalManagerMixin
from anura.utils.singleton import ThreadSafeSingleton, get_instance
from anura.utils.validators import uri_validator


class TestAtomicTaskManager:
    """Tests for AtomicTaskManager — verifies execute, callback, errorback, and task versioning."""

    def setup_method(self):
        """Reset singleton before each test to ensure isolation."""
        from anura.utils.singleton import ThreadSafeSingleton
        ThreadSafeSingleton.reset_for_testing()

    @pytest.mark.gtk
    def test_execute_success_callback(self):
        """execute() invokes callback with result on the main thread."""
        result_container = []
        event = threading.Event()

        def command(x):
            return x * 2

        def callback(res):
            result_container.append(res)
            event.set()

        get_atomic_manager().execute(command, args=(21,), callback=callback)

        ctx = GLib.MainContext.default()
        start_time = time.time()
        while not event.is_set() and time.time() - start_time < 2:
            ctx.iteration(False)

        assert result_container == [42]

    @pytest.mark.gtk
    def test_execute_errorback_on_exception(self):
        """execute() invokes errorback with the exception when command raises."""
        error_container = []
        event = threading.Event()

        def command():
            raise ValueError("Intentional error")

        def errorback(err, tb):
            error_container.append(err)
            event.set()

        get_atomic_manager().execute(command, errorback=errorback)

        ctx = GLib.MainContext.default()
        start_time = time.time()
        while not event.is_set() and time.time() - start_time < 2:
            ctx.iteration(False)

        assert len(error_container) == 1
        assert isinstance(error_container[0], ValueError)

    @pytest.mark.gtk
    def test_task_versioning_drops_obsolete_results(self):
        """
        When a second task is submitted before the first completes,
        the first task's callback is silently dropped (stale UUID).
        """
        results = []
        event = threading.Event()
        barrier = threading.Barrier(2)

        def slow_command():
            barrier.wait(timeout=2)  # Wait until second task is submitted
            return "slow"

        def fast_command():
            return "fast"

        def callback(res):
            results.append(res)
            event.set()

        manager = get_atomic_manager()
        manager.execute(slow_command, callback=callback)
        barrier.wait(timeout=2)   # Ensure slow_command is running
        manager.execute(fast_command, callback=callback)  # Supersedes slow

        ctx = GLib.MainContext.default()
        start_time = time.time()
        while not event.is_set() and time.time() - start_time < 3:
            ctx.iteration(False)

        # Only the fast (newest) result should reach the callback
        assert results == ["fast"]

    def test_singleton_identity(self):
        """get_atomic_manager() always returns the same instance."""
        m1 = get_atomic_manager()
        m2 = get_atomic_manager()
        assert m1 is m2

    def test_shutdown_does_not_raise(self):
        """shutdown() completes without error."""
        manager = get_atomic_manager()
        manager.shutdown()  # Should not raise


class TestSingleton:
    def test_singleton_identity(self):
        class MyService:
            pass

        s1 = get_instance(MyService)
        s2 = get_instance(MyService)
        assert s1 is s2

    def test_singleton_reset(self):
        class MyService:
            pass

        s1 = get_instance(MyService)
        ThreadSafeSingleton.reset_for_testing()
        s2 = get_instance(MyService)
        assert s1 is not s2


class TestSignalManager:
    @pytest.mark.gtk
    def test_signal_manager_cleanup(self):
        from typing import ClassVar

        class MockObject(GObject.GObject, SignalManagerMixin):
            __gsignals__: ClassVar[dict[str, tuple]] = {
                "test-signal": (GObject.SignalFlags.RUN_FIRST, None, ()),
            }

            def __init__(self):
                GObject.GObject.__init__(self)
                SignalManagerMixin.__init__(self)

        obj = MockObject()
        handler_id = obj.connect_tracked(obj, "test-signal", lambda *args: None)
        assert handler_id > 0
        assert obj.get_tracked_signal_count() == 1

        obj.disconnect_all_signals()
        assert obj.get_tracked_signal_count() == 0


class TestUriValidator:
    def test_uri_validator_basics(self):
        assert uri_validator("https://google.com") is True
        assert uri_validator("http://localhost:8080") is True
        assert uri_validator("file:///etc/passwd") is False
        assert uri_validator("javascript:alert(1)") is False
        assert uri_validator("   https://google.com   ") is True  # Should strip
