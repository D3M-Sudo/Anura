# velis/core/atomic_task_manager.py
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing
import threading
import uuid

from loguru import logger

from velis.utils.singleton import get_instance

try:
    from gi.repository import GLib
    HAS_GLIB = True
except (ImportError, ValueError):
    HAS_GLIB = False

class AtomicTaskResult:
    def __init__(self, task_id: str, data: object = None, error: Exception | None = None):
        self.task_id = task_id
        self.data = data
        self.error = error

class AtomicTaskManager:
    def __init__(self) -> None:
        self._current_task_id = None
        self._state_lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._process_executor = None

    def _get_process_executor(self):
        with self._state_lock:
            if self._process_executor is None:
                ctx = multiprocessing.get_context("spawn")
                self._process_executor = ProcessPoolExecutor(max_workers=1, mp_context=ctx)
            return self._process_executor

    def execute(self, command, args=(), callback=None, errorback=None):
        new_id = str(uuid.uuid4())
        with self._state_lock:
            self._current_task_id = new_id

        def wrapper():
            try:
                result_data = command(*args)
                with self._state_lock:
                    if self._current_task_id != new_id:
                        return
                if callback:
                    if HAS_GLIB:
                        GLib.idle_add(callback, result_data)
                    else:
                        callback(result_data)
            except Exception as e:
                logger.error(f"Task error: {e}")
                if errorback:
                    if HAS_GLIB:
                        GLib.idle_add(errorback, e)
                    else:
                        errorback(e)

        self._executor.submit(wrapper)
        return new_id

    def is_cancelled(self, task_id: str) -> bool:
        with self._state_lock:
            return task_id != self._current_task_id

def get_atomic_manager():
    return get_instance(AtomicTaskManager)
