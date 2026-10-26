# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from concurrent.futures.process import BrokenProcessPool
import multiprocessing
import multiprocessing.managers
import threading
import traceback
from typing import Any
import uuid

import gi

# Set GTK version requirements before imports
gi.require_version("GLib", "2.0")
gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib  # noqa: E402
from loguru import logger  # noqa: E402

from anura.utils.singleton import get_instance  # noqa: E402

# Lane used by callers that do not care about task kinds. Tasks in one lane
# supersede each other; tasks in different lanes never do (#507).
DEFAULT_LANE = "default"

# Lanes used by the application: a new screenshot/OCR must not cancel a TTS
# generation, and a file cleanup must not cancel an OCR task.
OCR_LANE = "ocr"
TTS_LANE = "tts"
CLEANUP_LANE = "cleanup"


class _Lane:
    """The single in-flight task of one lane."""

    __slots__ = ("cancellable", "task_id")

    def __init__(self, task_id: str, cancellable: Gio.Cancellable) -> None:
        self.task_id = task_id
        self.cancellable = cancellable


def _isolated_process_worker(command: "Callable", args: tuple, task_id: str, shared_map) -> object:
    """
    Top-level picklable entry point for ProcessPoolExecutor.

    Must live at module level: local closures (nested functions that capture
    the enclosing scope via ``self``) cannot be pickled by the 'spawn'
    multiprocessing context required for safe GTK/GObject interaction.

    Child-process logging note: with the 'spawn' context, loguru is freshly
    imported inside the worker and re-installs its default DEBUG stderr sink,
    flooding the terminal during every OCR run (e.g. after drag & drop).
    Silence it here: the parent process already owns stderr + rotary file
    logging, and results/errors are reported back via the Future/shared_map.

    Note: cross-process status callbacks via ``GLib.idle_add`` are not
    supported here because ``idle_add`` in a child process targets the
    child's (non-existent) GLib main loop, not the parent's.  Status
    updates from isolated workers must be delivered through the shared
    cancellation map or a dedicated IPC channel.
    """
    mgr = get_atomic_manager()
    logger.remove()  # Silence child's re-imported default DEBUG stderr sink.
    mgr.set_isolated_cancellation_map(shared_map)
    return command(*args, task_id=task_id, status_callback=None)


class AtomicTaskResult:
    """Wrapper for task results with versioning metadata."""

    def __init__(
        self,
        task_id: str,
        lane: str = DEFAULT_LANE,
        data: object = None,
        error: Exception | None = None,
        traceback_str: str | None = None,
    ) -> None:
        self.task_id = task_id
        self.lane = lane
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
        # One slot per lane: a task only supersedes the previous task of its own
        # lane, so OCR, TTS and cleanup cannot invalidate each other (#507).
        self._lanes: dict[str, _Lane] = {}
        self._executor: ThreadPoolExecutor | None = None
        self._process_executor: ProcessPoolExecutor | None = None
        self._process_manager: multiprocessing.managers.SyncManager | None = None
        self._isolated_cancellation_map: Any | None = None
        self._state_lock = threading.Lock()
        logger.debug("AtomicTaskManager: Initialized (lazy executors, per-lane slots)")

    @property
    def _current_task_id(self) -> str | None:
        """Task id of the DEFAULT_LANE (backwards-compatible read-only view)."""
        state = self._lanes.get(DEFAULT_LANE)
        return state.task_id if state is not None else None

    @property
    def _cancellable(self) -> Gio.Cancellable | None:
        """Cancellable of the DEFAULT_LANE (backwards-compatible read-only view)."""
        state = self._lanes.get(DEFAULT_LANE)
        return state.cancellable if state is not None else None

    def _begin_lane_locked(self, lane: str, task_id: str) -> tuple[Gio.Cancellable, str | None]:
        """Start *task_id* in *lane*, cancelling the previous task of that lane.

        MUST be called with ``_state_lock`` held. Returns the new cancellable and
        the superseded task id (if any).
        """
        previous = self._lanes.get(lane)
        superseded: str | None = None
        if previous is not None:
            if not previous.cancellable.is_cancelled():
                previous.cancellable.cancel()
            superseded = previous.task_id

        cancellable = Gio.Cancellable.new()
        self._lanes[lane] = _Lane(task_id, cancellable)
        return cancellable, superseded

    def _get_executor(self) -> ThreadPoolExecutor:
        """Lazy initialization of the thread executor."""
        with self._state_lock:
            if self._executor is None:
                # Note: ThreadPoolExecutor doesn't support setting daemon=True directly.
                # Lazy initialization ensures these threads only exist when needed.
                self._executor = ThreadPoolExecutor(
                    max_workers=1,
                    thread_name_prefix="AnuraAtomicWorker",
                )
            return self._executor

    def _ensure_process_executor_locked(self) -> ProcessPoolExecutor:
        """Initialize or recover the process executor. MUST be called with _state_lock held."""
        if self._process_executor is not None:
            # Detect a broken pool (e.g. Tesseract segfault killed the worker).
            # A broken executor raises BrokenProcessPool on every subsequent submit();
            # we must tear it down and recreate it before the next task.
            try:
                if self._process_executor._broken:  # type: ignore[attr-defined]
                    logger.warning("AtomicTaskManager: Detected broken process pool — recovering")
                    self._teardown_process_executor_locked()
            except AttributeError:
                # _broken is a CPython implementation detail; if it's missing,
                # we'll catch BrokenProcessPool at submit() time in result_wrapper.
                pass

        if self._process_executor is None:
            # Use a single worker for process-isolated tasks (OCR) to avoid
            # memory thrashing while still bypassing the GIL.
            # We use 'spawn' to be safe with GTK/GObject.
            ctx = multiprocessing.get_context("spawn")
            self._process_executor = ProcessPoolExecutor(max_workers=1, mp_context=ctx)
            self._process_manager = ctx.Manager()
            self._isolated_cancellation_map = self._process_manager.dict()
            logger.info("AtomicTaskManager: Initialized process executor for OCR isolation")
        return self._process_executor

    def _teardown_process_executor_locked(self) -> None:
        """Shut down and discard the broken process executor. MUST be called with _state_lock held."""
        try:
            if self._process_executor:
                # Use wait=True during teardown to ensure worker processes are reaped
                # and don't become orphans.
                self._process_executor.shutdown(wait=True, cancel_futures=True)
        except (RuntimeError, OSError) as e:
            logger.debug(f"AtomicTaskManager: Executor shutdown omitted or failed: {e}")
        try:
            if self._process_manager is not None:
                self._process_manager.shutdown()
        except (RuntimeError, OSError) as e:
            logger.debug(f"AtomicTaskManager: Process manager shutdown omitted or failed: {e}")
        self._process_executor = None
        self._process_manager = None
        self._isolated_cancellation_map = None

    def _handle_broken_pool(self, failed_executor: ProcessPoolExecutor) -> None:
        """Reset the process pool only if it is still the one that failed (#526).

        A stale ``BrokenProcessPool`` callback can run after another submission
        already detected the failure and installed a replacement; tearing down
        unconditionally would kill that healthy pool.
        """
        with self._state_lock:
            if self._process_executor is not failed_executor:
                logger.debug("AtomicTaskManager: broken-pool report from a replaced executor ignored")
                return
            logger.error(
                "AtomicTaskManager: Process pool broken (worker crashed) — resetting executor for next task"
            )
            self._teardown_process_executor_locked()

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
        status_callback: Callable | None = None,
        lane: str = DEFAULT_LANE,
        on_superseded: Callable[[str], None] | None = None,
    ) -> str:
        """
        Executes a command in a separate process, superseding the previous task
        **of the same lane**. Use this for CPU-bound tasks like Tesseract to
        bypass the GIL.

        Args:
            lane: Task kind. Tasks in other lanes are left untouched (#507).
            on_superseded: Called with the task id when this task is replaced by
                a newer one in the same lane, instead of dropping the result
                silently.
        """
        new_task_id = str(uuid.uuid4())

        with self._state_lock:
            current_cancellable, old_task_id = self._begin_lane_locked(lane, new_task_id)
            self._ensure_process_executor_locked()
            shared_map = self._isolated_cancellation_map

        # We use setdefault for the new task to ensure we don't overwrite a cancellation
        # from a very fast subsequent execute_isolated call.
        if shared_map is not None:
            shared_map.setdefault(new_task_id, False)
            if old_task_id:
                shared_map[old_task_id] = True

        if old_task_id:
            logger.debug(f"AtomicTaskManager: lane '{lane}' supersedes {old_task_id}")

        logger.debug(f"AtomicTaskManager: Enqueuing isolated process task {new_task_id} (lane={lane})")

        def result_wrapper(future):
            # This runs in the ThreadPoolExecutor (main process) to handle the callback
            try:
                if current_cancellable.is_cancelled():
                    GLib.idle_add(self._handle_superseded, new_task_id, on_superseded)
                    return

                result_data = future.result()

                if current_cancellable.is_cancelled():
                    GLib.idle_add(self._handle_superseded, new_task_id, on_superseded)
                    return

                result = AtomicTaskResult(task_id=new_task_id, lane=lane, data=result_data)
                GLib.idle_add(self._handle_success, result, callback, on_superseded)

            except BrokenProcessPool as e:
                # The worker process was killed (e.g. Tesseract segfault).
                # Only the pool that actually failed may be reset (#526).
                self._handle_broken_pool(executor)
                tb_str = traceback.format_exc()
                result = AtomicTaskResult(task_id=new_task_id, lane=lane, error=e, traceback_str=tb_str)
                GLib.idle_add(self._handle_error, result, errorback, on_superseded)

            except Exception as e:
                tb_str = traceback.format_exc()
                result = AtomicTaskResult(task_id=new_task_id, lane=lane, error=e, traceback_str=tb_str)
                GLib.idle_add(self._handle_error, result, errorback, on_superseded)
            finally:
                # Cleanup the shared map to prevent memory leaks
                with self._state_lock:
                    if self._isolated_cancellation_map is not None:
                        self._isolated_cancellation_map.pop(new_task_id, None)

        # Submit to process pool, then attach result handler.
        # _isolated_process_worker is module-level (not a closure) so it can
        # be pickled by the 'spawn' multiprocessing context.
        executor = self._get_process_executor()
        future = executor.submit(_isolated_process_worker, command, args, new_task_id, shared_map)
        future.add_done_callback(result_wrapper)

        return new_task_id

    def execute(
        self,
        command: Callable,
        args: tuple = (),
        callback: Callable | None = None,
        errorback: Callable | None = None,
        pass_task_id: bool = False,
        lane: str = DEFAULT_LANE,
        on_superseded: Callable[[str], None] | None = None,
    ) -> str:
        """
        Executes a command on the thread pool, superseding the previous task
        **of the same lane**.

        Args:
            command: The function to execute.
            args: Arguments for the command.
            callback: Function to call on the main thread upon success.
            errorback: Function to call on the main thread upon failure.
            pass_task_id: Whether to pass the task_id as the last argument to the command.
            lane: Task kind. Tasks in other lanes are left untouched (#507).
            on_superseded: Called with the task id when a newer task in the same
                lane replaces this one, instead of dropping the result silently.

        Returns:
            str: The new Task ID.
        """
        new_task_id = str(uuid.uuid4())

        with self._state_lock:
            # 1. Invalidate only the previous task of this lane.
            current_cancellable, old_task_id = self._begin_lane_locked(lane, new_task_id)

        if old_task_id:
            logger.debug(f"AtomicTaskManager: lane '{lane}' supersedes {old_task_id}")
        logger.debug(f"AtomicTaskManager: Enqueuing task {new_task_id} (lane={lane})")

        self._get_executor().submit(
            self._run_task,
            command,
            args,
            new_task_id,
            lane,
            current_cancellable,
            callback,
            errorback,
            on_superseded,
            pass_task_id,
        )
        return new_task_id

    def execute_daemon(
        self,
        command: Callable,
        args: tuple = (),
        callback: Callable | None = None,
        errorback: Callable | None = None,
        lane: str = DEFAULT_LANE,
        on_superseded: Callable[[str], None] | None = None,
    ) -> str:
        """Run *command* on a dedicated daemon thread instead of the pool.

        Same lane/versioning semantics as :meth:`execute`, but the thread is a
        daemon: CPython joins ``ThreadPoolExecutor`` workers at interpreter
        exit, so a blocking request that cannot be cancelled (gTTS `save()`)
        would otherwise keep the process alive after the window closed (#506).
        """
        new_task_id = str(uuid.uuid4())

        with self._state_lock:
            current_cancellable, old_task_id = self._begin_lane_locked(lane, new_task_id)

        if old_task_id:
            logger.debug(f"AtomicTaskManager: lane '{lane}' supersedes {old_task_id}")
        logger.debug(f"AtomicTaskManager: Starting daemon task {new_task_id} (lane={lane})")

        thread = threading.Thread(
            target=self._run_task,
            args=(
                command,
                args,
                new_task_id,
                lane,
                current_cancellable,
                callback,
                errorback,
                on_superseded,
                False,
            ),
            name=f"AnuraDaemonTask-{lane}",
            daemon=True,
        )
        thread.start()
        return new_task_id

    def _run_task(
        self,
        command: Callable,
        args: tuple,
        task_id: str,
        lane: str,
        cancellable: Gio.Cancellable,
        callback: Callable | None,
        errorback: Callable | None,
        on_superseded: Callable[[str], None] | None,
        pass_task_id: bool = False,
    ) -> None:
        """Execute a task and marshal its outcome to the main thread."""
        try:
            # Early check for cancellation
            if cancellable.is_cancelled():
                GLib.idle_add(self._handle_superseded, task_id, on_superseded)
                return

            # Execute the actual work
            result_data = command(*args, task_id=task_id) if pass_task_id else command(*args)

            # Post-execution check for cancellation
            if cancellable.is_cancelled():
                GLib.idle_add(self._handle_superseded, task_id, on_superseded)
                return

            result = AtomicTaskResult(task_id=task_id, lane=lane, data=result_data)
            GLib.idle_add(self._handle_success, result, callback, on_superseded)

        except Exception as e:
            tb_str = traceback.format_exc()
            result = AtomicTaskResult(task_id=task_id, lane=lane, error=e, traceback_str=tb_str)
            GLib.idle_add(self._handle_error, result, errorback, on_superseded)

    def set_isolated_cancellation_map(self, cancellation_map) -> None:
        """Set the shared cancellation map (used by isolated processes)."""
        self._isolated_cancellation_map = cancellation_map

    def is_cancelled(self, task_id: str) -> bool:
        """Check if a specific task ID has been cancelled or invalidated."""
        # 1. Check shared map for isolated processes.
        # This map is shared between the main process and the worker process via a Manager.
        if (
            hasattr(self, "_isolated_cancellation_map")
            and self._isolated_cancellation_map is not None
            and task_id in self._isolated_cancellation_map
        ):
            # If the task is in the map, its value determines the cancellation state.
            # This is critical for worker processes where _current_task_id is always None.
            return self._isolated_cancellation_map.get(task_id, False)

        # 2. Check every lane for the task id.
        with self._state_lock:
            for state in self._lanes.values():
                if state.task_id == task_id:
                    return state.cancellable.is_cancelled()
            # Not the current task of any lane: superseded, or never existed.
            return True

    def _current_lane_task_id(self, lane: str) -> str | None:
        """Return the task id currently owning *lane* (thread-safe)."""
        with self._state_lock:
            state = self._lanes.get(lane)
            return state.task_id if state is not None else None

    def _lane_owns(self, lane: str, task_id: str) -> bool:
        """True when *task_id* is still the live, non-cancelled task of *lane*."""
        with self._state_lock:
            state = self._lanes.get(lane)
            if state is None or state.task_id != task_id:
                return False
            return not state.cancellable.is_cancelled()

    def cancel_lane(self, lane: str) -> None:
        """Cancel the current task of *lane* without starting a replacement.

        Used by watchdogs (TTS generation timeout) and shutdown: the worker may
        not observe the cancellation while blocked in I/O, but its result is
        then discarded as superseded instead of being delivered to a caller that
        already gave up (#508).
        """
        with self._state_lock:
            state = self._lanes.get(lane)
            cancellable = state.cancellable if state is not None else None

        if cancellable is not None and not cancellable.is_cancelled():
            logger.debug(f"AtomicTaskManager: cancelling lane '{lane}'")
            cancellable.cancel()

    def cancel_all_lanes(self) -> None:
        """Cancel the current task of every lane (used at shutdown, #506)."""
        with self._state_lock:
            lanes = list(self._lanes)

        for lane in lanes:
            self.cancel_lane(lane)

    def _handle_superseded(self, task_id: str, on_superseded: Callable[[str], None] | None) -> bool:
        """Main thread: report that a task no longer owns its lane (#507)."""
        if on_superseded is None:
            logger.debug(f"AtomicTaskManager: Task {task_id} was superseded; result dropped")
            return GLib.SOURCE_REMOVE

        try:
            on_superseded(task_id)
        except (AttributeError, TypeError, RuntimeError) as e:
            logger.error(f"AtomicTaskManager: Unhandled error in on_superseded callback: {e}")

        return GLib.SOURCE_REMOVE

    def _handle_success(
        self,
        result: AtomicTaskResult,
        callback: Callable | None,
        on_superseded: Callable[[str], None] | None = None,
    ) -> bool:
        """Main thread success handler with lane validation."""
        if not self._lane_owns(result.lane, result.task_id):
            return self._handle_superseded(result.task_id, on_superseded)

        if not callback:
            return GLib.SOURCE_REMOVE

        try:
            callback(result.data)
        except (AttributeError, TypeError, RuntimeError) as e:
            logger.error(f"AtomicTaskManager: Unhandled error in success callback: {e}")

        return GLib.SOURCE_REMOVE

    def _handle_error(
        self,
        result: AtomicTaskResult,
        errorback: Callable | None,
        on_superseded: Callable[[str], None] | None = None,
    ) -> bool:
        """Main thread error handler with lane validation."""
        if not self._lane_owns(result.lane, result.task_id):
            return self._handle_superseded(result.task_id, on_superseded)

        # Use default errorback if none provided
        eb = errorback or self._default_errorback
        if result.error is None:
            return GLib.SOURCE_REMOVE
        try:
            eb(result.error, result.traceback_str)
        except (AttributeError, TypeError, RuntimeError) as e:
            logger.error(f"AtomicTaskManager: Unhandled error in error callback: {e}")

        return GLib.SOURCE_REMOVE

    def _default_errorback(self, error: Exception, traceback_str: str | None = None) -> None:
        """Standardized error logging."""
        tb = traceback_str or getattr(error, "__traceback__", None)
        if tb:
            logger.error(f"AtomicTaskManager Error: {tb}")
        else:
            logger.error(f"AtomicTaskManager Error: {error}")

    def shutdown(self) -> None:
        """Shut down the executors cleanly without deadlocking.

        Deadlock scenario that this method must avoid:
          1. shutdown() acquires _state_lock.
          2. ProcessPoolExecutor.shutdown(wait=True) blocks waiting for
             _executor_manager_thread to join.
          3. _executor_manager_thread tries to deliver a future result by
             calling result_wrapper, which does `with self._state_lock`.
          4. _state_lock is already held by step 1 → both threads wait
             forever (pytest-timeout fires after 30 s as Timeout).

        Fix: capture the executor references under the lock, clear them so
        no new work can be submitted, then release the lock *before* calling
        .shutdown(). The actual wait happens outside the lock so
        future callbacks can acquire it freely.
        """
        # Capture + clear under lock so no new submissions can race.
        with self._state_lock:
            thread_executor = self._executor
            process_executor = self._process_executor
            process_manager = self._process_manager

            self._executor = None
            self._process_executor = None
            self._process_manager = None
            self._isolated_cancellation_map = None

        # Shut down OUTSIDE the lock — prevents the deadlock described above.

        # 0. Cancel every lane so cooperative tasks stop at their next check
        #    (#506); a task blocked in I/O still finishes, but its result is
        #    discarded as superseded.
        self.cancel_all_lanes()

        # 1. Thread executor (main process tasks)
        if thread_executor is not None:
            # NEW-001 + #506: do not wait for the running task. Waiting here
            # blocked do_shutdown() until the task finished (e.g. OCR up to its
            # 120 s budget); TTS no longer lives in this pool (execute_daemon),
            # so nothing unbounded is joined by the interpreter exit.
            try:
                thread_executor.shutdown(wait=False, cancel_futures=True)
            except Exception as e:
                logger.debug(f"AtomicTaskManager: Thread executor shutdown warning: {e}")

        # 2. Process executor
        # We use wait=False here because ProcessPoolExecutor.shutdown(wait=True)
        # can deadlock in Python 3.12 when used with a multiprocessing.Manager
        # and 'spawn' context, especially if a task is still active.
        if process_executor is not None:
            try:
                logger.debug("AtomicTaskManager: Shutting down process executor...")
                process_executor.shutdown(wait=False, cancel_futures=True)
                logger.debug("AtomicTaskManager: Process executor shutdown initiated.")
            except (RuntimeError, OSError) as e:
                logger.debug(f"AtomicTaskManager: process executor shutdown failed: {e}")

        # 3. Process manager
        # Shutting down the manager will forcefully terminate the manager process
        # and should help clean up any remaining resources/workers.
        if process_manager is not None:
            try:
                logger.debug("AtomicTaskManager: Shutting down process manager...")
                process_manager.shutdown()
                logger.debug("AtomicTaskManager: Process manager shut down.")
            except (RuntimeError, OSError) as e:
                logger.debug(f"AtomicTaskManager: process manager shutdown failed: {e}")


def get_atomic_manager() -> AtomicTaskManager:
    """Get the thread-safe AtomicTaskManager singleton.

    Returns:
        The singleton AtomicTaskManager instance.
    """
    return get_instance(AtomicTaskManager)
