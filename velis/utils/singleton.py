# velis/utils/singleton.py
import threading

_instances = {}
_lock = threading.Lock()

def get_instance(cls, *args, **kwargs):
    global _instances
    if cls not in _instances:
        with _lock:
            if cls not in _instances:
                _instances[cls] = cls(*args, **kwargs)
    return _instances[cls]
