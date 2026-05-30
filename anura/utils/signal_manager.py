# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from collections.abc import Callable
from typing import Any
import weakref

from loguru import logger

try:
    import gi

    # Set GTK version requirements before imports
    gi.require_version("GObject", "2.0")
    from gi.repository import GObject

    HAS_GI = True
except (ImportError, ValueError):
    HAS_GI = False

    class GObject:
        class Object:
            pass


class SignalManagerMixin:
    """
    Mixin class that provides automatic signal tracking, controller registry, and cleanup.

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
                self.teardown_all()
                super().do_destroy()
    """

    def __init__(self) -> None:
        """Explicitly initialize the mixin state.

        Note: GTK classes using this mixin must call SignalManagerMixin.__init__(self)
        if they don't want to rely on lazy initialization.
        """
        self._ensure_state_initialized()
        self._maybe_connect_destroy_signal()

    def _maybe_connect_destroy_signal(self) -> None:
        """Automatically connect to the 'destroy' signal if available."""
        if not HAS_GI:
            return

        from gi.repository import GObject

        if isinstance(self, GObject.Object):
            try:
                # Check if the object has a 'destroy' signal (typical for Gtk.Widget)
                if GObject.signal_lookup("destroy", self.__class__):
                    self.connect("destroy", lambda _: self.teardown_all())
                    logger.debug(f"SignalManagerMixin: Auto-connected 'destroy' signal for {type(self).__name__}")
            except (AttributeError, RuntimeError, TypeError) as e:
                logger.debug(f"SignalManagerMixin: Could not auto-connect 'destroy' for {type(self).__name__}: {e}")

    def _ensure_state_initialized(self) -> None:
        """Ensures that the mixin's internal state is initialized."""
        if not hasattr(self, "_signal_connections"):
            self._signal_connections: dict[Any, list[int]] = {}
        if not hasattr(self, "_registered_controllers"):
            # Use Any for type hint to avoid Protocol-related CI crashes (BUG-041/Hardening)
            self._registered_controllers: weakref.WeakSet[Any] = weakref.WeakSet()

    def register_controller(self, controller: Any) -> None:
        """Register a controller for automatic teardown."""
        self._ensure_state_initialized()
        self._registered_controllers.add(controller)
        logger.debug(f"SignalManagerMixin: Registered controller {type(controller).__name__}")

    def connect_tracked(
        self,
        emitter: GObject.Object,
        signal_name: str,
        callback: Callable,
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
        self._ensure_state_initialized()
        handler_id = emitter.connect(signal_name, callback)

        if emitter not in self._signal_connections:
            self._signal_connections[emitter] = []
        self._signal_connections[emitter].append(handler_id)

        logger.debug(
            f"SignalManagerMixin: Connected {signal_name} on {type(emitter).__name__}, handler_id={handler_id}",
        )
        return handler_id

    def teardown_all(self) -> None:
        """
        Perform unified teardown: cleanup controllers and disconnect all signals.
        """
        self._ensure_state_initialized()
        logger.debug("SignalManagerMixin: Starting unified teardown")

        # 1. Teardown registered controllers
        controllers = list(self._registered_controllers)
        for controller in controllers:
            try:
                # Use hasattr check instead of Protocol/isinstance to avoid SIGABRT
                # in some GTK environments (CI Hardening).
                if hasattr(controller, "teardown"):
                    controller.teardown()
            except (AttributeError, RuntimeError, TypeError) as e:
                logger.warning(f"SignalManagerMixin: Error during controller teardown: {e}")

        self._registered_controllers.clear()

        # 2. Disconnect all tracked signals
        self.disconnect_all_signals()

    def disconnect_all_signals(self) -> None:
        """
        Disconnect all tracked signal handlers and clear the storage.

        This method is safe to call even if some emitters have already been
        finalized or disconnected. It uses try-except to handle these cases
        gracefully.
        """
        disconnected_count = 0
        failed_count = 0

        # Create a copy of items to prevent race condition if dict is modified during iteration
        signal_items = list(self._signal_connections.items())

        for emitter, handler_ids in signal_items:
            for handler_id in handler_ids:
                try:
                    if emitter:
                        emitter.disconnect(handler_id)
                        disconnected_count += 1
                except (TypeError, RuntimeError, AttributeError) as e:
                    logger.debug(
                        f"SignalManagerMixin: Could not disconnect handler {handler_id} "
                        f"from {type(emitter).__name__}: {e}",
                    )
                    failed_count += 1

        if disconnected_count > 0 or failed_count > 0:
            logger.debug(
                f"SignalManagerMixin: Disconnected {disconnected_count} signals ({failed_count} failed)",
            )

        self._signal_connections.clear()

    def get_tracked_signal_count(self) -> int:
        """Return the total number of tracked signal connections."""
        return sum(len(ids) for ids in self._signal_connections.values())
