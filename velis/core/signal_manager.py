# velis/core/signal_manager.py
from typing import Any, Protocol, runtime_checkable
import weakref


@runtime_checkable
class Teardownable(Protocol):
    def teardown(self) -> None:
        ...

class SignalManagerMixin:
    def __init__(self) -> None:
        self._signal_connections = {}
        self._registered_controllers = weakref.WeakSet()
        # Only try GObject if gi is available
        try:
            import gi
            gi.require_version("GObject", "2.0")
            from gi.repository import GObject
            if isinstance(self, GObject.Object):
                if GObject.signal_lookup("destroy", self.__class__):
                    self.connect("destroy", lambda _: self.teardown_all())
        except (ImportError, ValueError, Exception):
            pass

    def register_controller(self, controller: Teardownable) -> None:
        self._registered_controllers.add(controller)

    def connect_tracked(self, emitter: Any, signal_name: str, callback: Any) -> int:
        handler_id = emitter.connect(signal_name, callback)
        if emitter not in self._signal_connections:
            self._signal_connections[emitter] = []
        self._signal_connections[emitter].append(handler_id)
        return handler_id

    def teardown_all(self) -> None:
        for controller in list(self._registered_controllers):
            if hasattr(controller, 'teardown'):
                controller.teardown()
        self._registered_controllers.clear()
        self.disconnect_all_signals()

    def disconnect_all_signals(self) -> None:
        for emitter, handler_ids in self._signal_connections.items():
            for handler_id in handler_ids:
                try:
                    if emitter:
                        emitter.disconnect(handler_id)
                except Exception:
                    pass
        self._signal_connections.clear()
