# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TessdataChecksum:
    """Pinned identity of an upstream Tesseract model file.

    ``sha256`` is the SHA-256 digest of the *raw file bytes* as published by
    the upstream repository. It is the primary integrity anchor used to
    reject corrupted or tampered models before installation.

    ``sha1`` is the *git blob* hash of the file (the hash GitHub's tree API
    publishes for the pinned upstream ref). Git blob hashes are
    content-addressed and reproduce locally by hashing git's ``blob <size>``
    header, a NUL byte and then the file content — which makes them usable as
    an additional integrity anchor without shipping the model itself.
    ``sha1`` is retained as a secondary, defence-in-depth check.
    """

    filename: str
    size: int
    sha256: str
    sha1: str

    @classmethod
    def from_dict(cls, filename: str, data: dict[str, Any]) -> "TessdataChecksum":
        """Build a checksum entry from its JSON representation.

        Fails closed: a missing or non-hex ``sha256`` raises ``ValueError`` so
        the entry can never be trusted without a real SHA-256 digest.
        """
        size = int(data["size"])
        sha256 = str(data["sha256"])
        sha1 = str(data["sha1"])

        if len(sha256) != 64 or any(c not in "0123456789abcdef" for c in sha256):
            raise ValueError(f"invalid sha256 for {filename}: {sha256!r}")
        if len(sha1) != 40 or any(c not in "0123456789abcdef" for c in sha1):
            raise ValueError(f"invalid sha1 for {filename}: {sha1!r}")
        if size < 0:
            raise ValueError(f"invalid size for {filename}: {size}")

        return cls(filename=filename, size=size, sha256=sha256, sha1=sha1)

    def __repr__(self) -> str:
        return f"<TessdataChecksum: {self.filename} ({self.size} bytes, {self.sha256[:12]}…)>"
