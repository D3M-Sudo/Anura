# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CaptureSession:
    """Immutable representation of a single capture stored in history."""

    id: str  # Unique identifier (usually UUID)
    timestamp: float  # Epoch timestamp of capture
    text: str  # Extracted/processed text
    lang: str  # Language code used (e.g. 'eng')
    thumbnail: str | None = None  # Optional Base64 encoded thumbnail image (small size)
