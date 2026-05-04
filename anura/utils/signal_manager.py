# signal_manager.py
#
# Copyright 2026 D3M-Sudo (Anura fork and modifications)
#
# Centralized signal management mixin to prevent memory leaks from
# forgotten signal disconnections.

from collections.abc import Callable
from typing import Any

from gi.repository import GObject
from loguru import logger


class SignalManagerMixin:
    """
    Mixin class that provides automatic signal tracking and cleanup.

    Use connect_tracked() instead of direct .connect() to automatically
    store handler IDs. Call disconnect_all_signals() in do_destroy() to
    clean up all tracked signals.

    Usage:
        class MyWidget(Gtk.Box, SignalManagerMixin):
            def __init__(self):
                super().__init__()
                SignalManagerMixin.__init__(self)
                self._handler_id = self.connect_tracked(
                    some_object, "signal-name", self._on_signal
                )

            def do_destroy(self):
                self.disconnect_all_signals()
                super().do_destroy()
    """

    def __init__(self) -> None:
        self._signal_connections: dict[Any, list[int]] = {}

    def connect_tracked(
        self, emitter: GObject.Object, signal_name: str, callback: Callable
    ) -> int:
        """
        Connect to a signal and track the handler ID for automatic cleanup.

        Args:
            emitter: The GObject to connect to (e.g., a service, another widget)
            signal_name: The signal name to listen for
            callback: The callback function to invoke when signal fires

        Returns:
            The handler ID that can be used for manual disconnection
        """
        handler_id = emitter.connect(signal_name, callback)

        if emitter not in self._signal_connections:
            self._signal_connections[emitter] = []
        self._signal_connections[emitter].append(handler_id)

        logger.debug(
            f"SignalManagerMixin: Connected {signal_name} on {type(emitter).__name__}, "
            f"handler_id={handler_id}"
        )
        return handler_id

    def disconnect_all_signals(self) -> None:
        """
        Disconnect all tracked signal handlers and clear the storage.

        This method is safe to call even if some emitters have already been
        finalized or disconnected. It uses try-except to handle these cases
        gracefully.
        """
        disconnected_count = 0
        failed_count = 0

        for emitter, handler_ids in self._signal_connections.items():
            for handler_id in handler_ids:
                try:
                    if emitter:
                        emitter.disconnect(handler_id)
                        disconnected_count += 1
                except (TypeError, RuntimeError, AttributeError) as e:
                    logger.debug(
                        f"SignalManagerMixin: Could not disconnect handler {handler_id} "
                        f"from {type(emitter).__name__}: {e}"
                    )
                    failed_count += 1

        if disconnected_count > 0 or failed_count > 0:
            logger.debug(
                f"SignalManagerMixin: Disconnected {disconnected_count} signals "
                f"({failed_count} failed)"
            )

        self._signal_connections.clear()

    def get_tracked_signal_count(self) -> int:
        """Return the total number of tracked signal connections."""
        return sum(len(ids) for ids in self._signal_connections.values())
