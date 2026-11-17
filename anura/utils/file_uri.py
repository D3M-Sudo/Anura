# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Conversion of local filesystem paths to ``file://`` URIs."""

from pathlib import Path


def file_uri(path: str | Path) -> str:
    """Return a properly escaped ``file://`` URI for a local path.

    A path is not a URI: spaces, ``#``, ``?``, ``%`` and non-ASCII characters
    must be percent-encoded or consumers such as GStreamer's ``uri`` property
    reject the value or read the wrong file. ``Path.as_uri()`` applies the same
    rules as ``g_filename_to_uri()`` for absolute paths (UTF-8, then
    percent-encoding of the reserved characters).

    Relative paths are made absolute first, because ``as_uri()`` requires an
    absolute path and a URI must not depend on the caller's working directory.
    """
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = candidate.absolute()
    return candidate.as_uri()
