# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TessdataChecksum:
    """Pinned identity of an upstream Tesseract model file.

    ``sha1`` is the *git blob* hash of the file (the hash GitHub's tree API
    publishes for the pinned upstream ref). Git blob hashes are
    content-addressed and reproduce locally by hashing git's ``blob <size>``
    header, a NUL byte and then the file content — which is what makes them
    usable as an integrity anchor without shipping the model itself.
    """

    filename: str
    size: int
    sha1: str

    @classmethod
    def from_dict(cls, filename: str, data: dict[str, Any]) -> "TessdataChecksum":
        """Build a checksum entry from its JSON representation."""
        return cls(filename=filename, size=int(data["size"]), sha1=str(data["sha1"]))

    def __repr__(self) -> str:
        return f"<TessdataChecksum: {self.filename} ({self.size} bytes, {self.sha1[:12]}…)>"
