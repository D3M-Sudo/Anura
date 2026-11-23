# Temporary QA-only callback timing probe for PR #648.
#
# This module is intentionally isolated on qa/perf-callback-timing-648.
# Remove it together with its imports/decorators after the measurements.

from collections.abc import Callable
from functools import wraps
from time import perf_counter_ns
from typing import ParamSpec, TypeVar

from loguru import logger

P = ParamSpec("P")
R = TypeVar("R")


def measure_callback(name: str) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Log inclusive wall-clock duration for one synchronous callback."""

    def decorate(callback: Callable[P, R]) -> Callable[P, R]:
        @wraps(callback)
        def measured(*args: P.args, **kwargs: P.kwargs) -> R:
            started_ns = perf_counter_ns()
            try:
                return callback(*args, **kwargs)
            finally:
                elapsed_ms = (perf_counter_ns() - started_ns) / 1_000_000
                logger.info("QA_PERF callback={} elapsed_ms={:.3f}", name, elapsed_ms)

        return measured

    return decorate
