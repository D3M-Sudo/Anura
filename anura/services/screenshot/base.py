# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from abc import ABC, abstractmethod
from typing import Callable

class ScreenshotProvider(ABC):
    """Abstract base class for screenshot capture providers."""

    @abstractmethod
    def capture(self, lang: str, copy: bool, callback: Callable) -> None:
        """
        Initiate screenshot capture.

        Args:
            lang: OCR language code.
            copy: Whether to copy result to clipboard automatically.
            callback: Function to call with (success, uri, error_message).
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available in the current environment."""
        pass
