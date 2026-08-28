# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from pathlib import Path
import time

from loguru import logger


class FileReadyRetry:
    """
    Utility for waiting for a file to be ready with retry logic.
    Used when processes exit before filesystem flush completes.
    """

    def __init__(self, retries: int = 50, delay: float = 0.1) -> None:
        """
        Initialize retry parameters.

        Args:
            retries: Number of retry attempts
            delay: Delay between retries in seconds
        """
        self.retries = retries
        self.delay = delay

    def wait_for_file(self, path: str | Path) -> bool:
        """
        Wait for a file to exist and have non-zero size.

        Args:
            path: Path to the file to check

        Returns:
            True if file is ready, False otherwise
        """
        path = Path(path)
        for attempt in range(self.retries):
            if path.exists() and path.stat().st_size > 0:
                return True
            if attempt < self.retries - 1:
                time.sleep(self.delay)

        # Log diagnostic info on failure
        logger.error(
            f"FileReadyRetry: File not ready after {self.retries * self.delay}s "
            f"(path={path}, exists={path.exists()}, "
            f"size={path.stat().st_size if path.exists() else 'N/A'})"
        )
        return False
