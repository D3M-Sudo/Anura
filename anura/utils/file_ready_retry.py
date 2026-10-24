# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Retry policy for waiting for a file to become ready.

The wait itself is driven by the GLib main loop (``GLib.timeout_add``) in
``LegacyX11Provider._await_output_ready``: a blocking ``time.sleep()`` loop in
an async completion callback froze the UI for up to five seconds (#523).
"""

from loguru import logger


class FileReadyRetry:
    """Retry policy: how many times to poll and how long to wait between polls.

    Used when a helper process exits before the filesystem has flushed its
    output (scrot writes the PNG asynchronously).
    """

    def __init__(self, retries: int = 50, delay: float = 0.1) -> None:
        """
        Initialize retry parameters.

        Args:
            retries: Number of polling attempts
            delay: Delay between attempts in seconds
        """
        self.retries = retries
        self.delay = delay

        if retries < 1 or delay <= 0:
            logger.warning(f"FileReadyRetry: unusual policy (retries={retries}, delay={delay})")
