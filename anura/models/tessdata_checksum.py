# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
import re
from typing import Any

_SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class TessdataChecksum:
    """Pinned SHA-256 identity of an upstream Tesseract model file."""

    filename: str
    size: int
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.filename, str) or not self.filename.endswith(".traineddata"):
            raise ValueError("filename must identify a .traineddata file")
        if self.filename.startswith("/") or ".." in self.filename.split("/"):
            raise ValueError("filename must be a relative model path")
        if type(self.size) is not int or self.size <= 0:
            raise ValueError("size must be a positive integer")
        if not isinstance(self.sha256, str) or not _SHA256_PATTERN.fullmatch(self.sha256):
            raise ValueError("sha256 must contain exactly 64 hexadecimal characters")

    @classmethod
    def from_dict(cls, filename: str, data: dict[str, Any]) -> "TessdataChecksum":
        if not isinstance(data, dict):
            raise ValueError("checksum entry must be an object")
        if "sha1" in data:
            raise ValueError("SHA-1 entries are not supported")
        size = data.get("size")
        if type(size) is not int:
            raise ValueError("size must be an integer")
        sha256 = data.get("sha256")
        if not isinstance(sha256, str):
            raise ValueError("sha256 must be a string")
        return cls(filename=filename, size=size, sha256=sha256)

    def __repr__(self) -> str:
        return f"<TessdataChecksum: {self.filename} ({self.size} bytes, {self.sha256[:12]}…)>"
