# singleton.py
#
# Copyright 2026 D3MS-Sudo (Anura thread safety improvements)
#
# Thread-safe lazy singleton pattern for Anura services
# Provides double-checked locking for safe initialization

import threading
from typing import Any, ClassVar, TypeVar

T = TypeVar('T')

class ThreadSafeSingleton:
    """
    Thread-safe lazy singleton implementation using double-checked locking.

    This ensures:
    - Only one instance is ever created
    - Initialization is thread-safe
    - Instance is created only when first accessed
    - Minimal performance overhead after initialization
    """

    _instances: ClassVar[dict[type, Any]] = {}
    _locks: ClassVar[dict[type, threading.Lock]] = {}
    _meta_lock = threading.Lock()

    def __new__(cls, wrapped_class: type[T]) -> T:
        """
        Create or return the singleton instance of the wrapped class.

        Args:
            wrapped_class: The class to make singleton

        Returns:
            The singleton instance of wrapped_class
        """
        # First check without lock for performance
        if wrapped_class in cls._instances:
            return cls._instances[wrapped_class]

        # Double-checked locking pattern
        with cls._get_lock(wrapped_class):
            # Check again inside lock to prevent race condition
            if wrapped_class not in cls._instances:
                # Create the instance
                instance = wrapped_class()
                cls._instances[wrapped_class] = instance
                return instance

            return cls._instances[wrapped_class]

    @classmethod
    def _get_lock(cls, wrapped_class: type[Any]) -> threading.Lock:
        """Get or create lock for the specific class."""
        with cls._meta_lock:
            if wrapped_class not in cls._locks:
                cls._locks[wrapped_class] = threading.Lock()
            return cls._locks[wrapped_class]

    @classmethod
    def get_instance(cls, wrapped_class: type[T]) -> T:
        """
        Explicit method to get singleton instance.

        Args:
            wrapped_class: The class to get singleton instance of

        Returns:
            The singleton instance
        """
        return cls(wrapped_class)

    @classmethod
    def reset_for_testing(cls) -> None:
        """
        Reset all singletons for testing purposes only.
        This should never be used in production code.
        """
        with cls._meta_lock:
            cls._instances.clear()
            cls._locks.clear()


def singleton[T](wrapped_class: type[T]) -> type[T]:
    """
    Decorator to make a class a thread-safe singleton.

    Usage:
        @singleton
        class MyService:
            pass

        # Both work:
        service1 = MyService()
        service2 = singleton(MyService)
    """
    return ThreadSafeSingleton(wrapped_class)


def get_instance[T](wrapped_class: type[T]) -> T:
    """
    Function to get singleton instance of a class.

    Usage:
        service = get_instance(MyService)
    """
    return ThreadSafeSingleton.get_instance(wrapped_class)
