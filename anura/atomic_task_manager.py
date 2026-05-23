# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
import threading
import traceback
import uuid

import gi

# Set GTK version requirements before imports
gi.require_version("GLib", "2.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib  # noqa: E402
from loguru import logger  # noqa: E402

from anura.utils.singleton import get_instance  # noqa: E402


class AtomicTaskResult:
    """Wrapper for task results with versioning metadata."""

    def __init__(
        self,
        task_id: str,
        data: object = None,
        error: Exception | None = None,
        traceback_str: str | None = None,
    ) -> None:
        self.task_id = task_id
        self.data = data
        self.error = error
        self.traceback_str = traceback_str


class AtomicTaskManager:
    """
    Atomic Task Manager for Anura.
    Handles single-slot execution with task versioning to prevent race conditions
    and UI micro-stutters.
    """

    def __init__(self) -> None:
        self._current_task_id: str | None = None
        self._cancellable: Gio.Cancellable | None = None
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="AnuraAtomicWorker")
        self._state_lock = threading.Lock()
        logger.debug("AtomicTaskManager: Initialized with single-worker pool")

    def execute(
        self,
        command: Callable,
        args: tuple = (),
        callback: Callable | None = None,
        errorback: Callable | None = None,
    ) -> str:
        """
        Executes a command atomically, invalidating any previous task.

        Args:
            command: The function to execute.
            args: Arguments for the command.
            callback: Function to call on the main thread upon success.
            errorback: Function to call on the main thread upon failure.

        Returns:
            str: The new Task ID.
        """
        new_task_id = str(uuid.uuid4())

        with self._state_lock:
            # 1. Invalidate previous task
            if self._cancellable:
                logger.debug(f"AtomicTaskManager: Cancelling previous task {self._current_task_id}")
                self._cancellable.cancel()

            # 2. Update state for the new task
            self._current_task_id = new_task_id
            self._cancellable = Gio.Cancellable.new()
            current_cancellable = self._cancellable

        logger.debug(f"AtomicTaskManager: Enqueuing task {new_task_id}")

        def wrapper():
            try:
                # Early check for cancellation
                if current_cancellable.is_cancelled():
                    return

                # Execute the actual work
                result_data = command(*args)

                # Post-execution check for cancellation
                if current_cancellable.is_cancelled():
                    return

                result = AtomicTaskResult(task_id=new_task_id, data=result_data)
                GLib.idle_add(self._handle_success, result, callback)

            except Exception as e:
                tb_str = traceback.format_exc()
                result = AtomicTaskResult(task_id=new_task_id, error=e, traceback_str=tb_str)
                GLib.idle_add(self._handle_error, result, errorback)

        self._executor.submit(wrapper)
        return new_task_id

    def _handle_success(self, result: AtomicTaskResult, callback: Callable | None) -> bool:
        """Main thread success handler with ID validation."""
        if not callback:
            return GLib.SOURCE_REMOVE

        with self._state_lock:
            if result.task_id != self._current_task_id:
                logger.debug(f"AtomicTaskManager: Ignoring obsolete success result from {result.task_id}")
                return GLib.SOURCE_REMOVE

        try:
            callback(result.data)
        except Exception:
            logger.exception("AtomicTaskManager: Unhandled error in success callback")

        return GLib.SOURCE_REMOVE

    def _handle_error(self, result: AtomicTaskResult, errorback: Callable | None) -> bool:
        """Main thread error handler with ID validation."""
        with self._state_lock:
            if result.task_id != self._current_task_id:
                logger.debug(f"AtomicTaskManager: Ignoring obsolete error result from {result.task_id}")
                return GLib.SOURCE_REMOVE

        # Use default errorback if none provided
        eb = errorback or self._default_errorback
        try:
            eb(result.error, result.traceback_str)
        except Exception:
            logger.exception("AtomicTaskManager: Unhandled error in error callback")

        return GLib.SOURCE_REMOVE

    def _default_errorback(self, error: Exception, traceback_str: str | None = None) -> None:
        """Standardized error logging."""
        tb = traceback_str or getattr(error, "__traceback__", None)
        if tb:
            logger.error(f"AtomicTaskManager Error: {tb}")
        else:
            logger.error(f"AtomicTaskManager Error: {error}")

    def shutdown(self) -> None:
        """Shut down the executor."""
        self._executor.shutdown(wait=False)


def get_atomic_manager() -> AtomicTaskManager:
    """Get the thread-safe AtomicTaskManager singleton.

    Returns:
        The singleton AtomicTaskManager instance.
    """
    return get_instance(AtomicTaskManager)
