# download_state.py
#
# Copyright 2021-2025 Andrey Maksimov
# Copyright 2026 D3M-Sudo (Anura fork and modifications)

from dataclasses import dataclass


@dataclass
class DownloadState:
    """
    Data structure to track the progress of OCR model downloads.
    Used by LanguageManager to communicate with the UI.
    """
    total: int = 0
    progress: int = 0

    @property
    def percentage(self) -> float:
        """
        Calculates the download percentage.
        Returns 0.0 if total is 0 to avoid division by zero.
        """
        if self.total <= 0:
            return 0.0
        return (self.progress / self.total) * 100