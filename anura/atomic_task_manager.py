# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
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
        self._process_executor = None
        self._process_manager = None
        self._isolated_cancellation_map = None
        self._state_lock = threading.Lock()
        logger.debug("AtomicTaskManager: Initialized with single-worker pool")

    def _ensure_process_executor_locked(self) -> ProcessPoolExecutor:
        """Initialize process executor if needed. MUST be called with _state_lock held."""
        if self._process_executor is None:
            # Use a single worker for process-isolated tasks (OCR) to avoid
            # memory thrashing while still bypassing the GIL.
            # We use 'spawn' to be safe with GTK/GObject.
            ctx = multiprocessing.get_context("spawn")
            self._process_executor = ProcessPoolExecutor(
                max_workers=1,
                mp_context=ctx
            )
            self._process_manager = ctx.Manager()
            self._isolated_cancellation_map = self._process_manager.dict()
            logger.info("AtomicTaskManager: Initialized process executor for OCR isolation")
        return self._process_executor

    def _get_process_executor(self) -> ProcessPoolExecutor:
        """Lazy initialization of the process executor for OCR isolation."""
        with self._state_lock:
            return self._ensure_process_executor_locked()

    def execute_isolated(
        self,
        command: Callable,
        args: tuple = (),
        callback: Callable | None = None,
        errorback: Callable | None = None,
    ) -> str:
        """
        Executes a command in a separate process, invalidating any previous task.
        Use this for CPU-bound tasks like Tesseract to bypass the GIL.
        """
        new_task_id = str(uuid.uuid4())
        old_task_id = None

        with self._state_lock:
            if self._cancellable:
                self._cancellable.cancel()
                old_task_id = self._current_task_id

            self._current_task_id = new_task_id
            self._cancellable = Gio.Cancellable.new()
            current_cancellable = self._cancellable

            # NEW-01: Use ensure_locked version to avoid deadlock
            self._ensure_process_executor_locked()
            shared_map = self._isolated_cancellation_map

        # NEW-06: Perform IPC operations outside the _state_lock to avoid UI stuttering.
        # We use setdefault for the new task to ensure we don't overwrite a cancellation
        # from a very fast subsequent execute_isolated call.
        if shared_map is not None:
            shared_map.setdefault(new_task_id, False)
            if old_task_id:
                shared_map[old_task_id] = True

        logger.debug(f"AtomicTaskManager: Enqueuing isolated process task {new_task_id}")

        def process_wrapper():
            # This runs in the process executor (separate process)
            # We must set the shared cancellation map in the child process's singleton
            mgr = get_atomic_manager()
            mgr.set_isolated_cancellation_map(shared_map)

            # Call the command with its arguments
            return command(*args, task_id=new_task_id)

        def result_wrapper(future):
            # This runs in the ThreadPoolExecutor (main process) to handle the callback
            try:
                if current_cancellable.is_cancelled():
                    return

                result_data = future.result()

                if current_cancellable.is_cancelled():
                    return

                result = AtomicTaskResult(task_id=new_task_id, data=result_data)
                GLib.idle_add(self._handle_success, result, callback)

            except Exception as e:
                tb_str = traceback.format_exc()
                result = AtomicTaskResult(task_id=new_task_id, error=e, traceback_str=tb_str)
                GLib.idle_add(self._handle_error, result, errorback)
            finally:
                # Cleanup the shared map to prevent memory leaks
                with self._state_lock:
                    if self._isolated_cancellation_map is not None:
                        # We only remove it if it's not the CURRENT task,
                        # but since we're in the result_wrapper, the task is done.
                        # However, we might want to keep some history or just clear it.
                        # Given single-slot execution, we can safely clear the ID.
                        self._isolated_cancellation_map.pop(new_task_id, None)

        # Submit to process pool, then attach result handler
        executor = self._get_process_executor()
        future = executor.submit(process_wrapper)
        future.add_done_callback(result_wrapper)

        return new_task_id

    def execute(
        self,
        command: Callable,
        args: tuple = (),
        callback: Callable | None = None,
        errorback: Callable | None = None,
        pass_task_id: bool = False,
    ) -> str:
        """
        Executes a command atomically, invalidating any previous task.

        Args:
            command: The function to execute.
            args: Arguments for the command.
            callback: Function to call on the main thread upon success.
            errorback: Function to call on the main thread upon failure.
            pass_task_id: Whether to pass the task_id as the last argument to the command.

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
                if pass_task_id:
                    result_data = command(*args, task_id=new_task_id)
                else:
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

    def set_isolated_cancellation_map(self, cancellation_map) -> None:
        """Set the shared cancellation map (used by isolated processes)."""
        self._isolated_cancellation_map = cancellation_map

    def is_cancelled(self, task_id: str) -> bool:
        """Check if a specific task ID has been cancelled or invalidated."""
        # 1. Check shared map for isolated processes
        if (
            hasattr(self, "_isolated_cancellation_map")
            and self._isolated_cancellation_map is not None
            and self._isolated_cancellation_map.get(task_id, False)
        ):
            return True

        # 2. Check local state for threads
        with self._state_lock:
            # If the task_id is not the current one, it's considered cancelled/obsolete
            if task_id != self._current_task_id:
                return True
            # If it is the current one, check the GIO cancellable
            return self._cancellable.is_cancelled() if self._cancellable else True

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
        """Shut down the executors."""
        self._executor.shutdown(wait=False)
        if self._process_executor:
            self._process_executor.shutdown(wait=False)
        if hasattr(self, "_process_manager") and self._process_manager:
            self._process_manager.shutdown()


def get_atomic_manager() -> AtomicTaskManager:
    """Get the thread-safe AtomicTaskManager singleton.

    Returns:
        The singleton AtomicTaskManager instance.
    """
    return get_instance(AtomicTaskManager)
