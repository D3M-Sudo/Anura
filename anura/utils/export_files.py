# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT
# anura/utils/export_files.py

"""Secure creation and cleanup of OCR export files.

Export files contain potentially sensitive recognized text, so they must
never live in a world-readable directory with a predictable name:

- Preferred location: ``$XDG_RUNTIME_DIR/anura/exports`` (per-session,
  per-user, tmpfs-backed on most distributions).
- Fallback: ``$XDG_CACHE_HOME/anura/exports`` (per-user, never shared).

Files are created with :func:`tempfile.mkstemp` inside that directory,
which yields a random, unguessable name and a ``0600`` file mode, immune
to symlink races and temporary-file collisions.
"""

import os
from pathlib import Path
import stat
import tempfile

from loguru import logger


def _enforce_private_dir(path: Path) -> Path:
    """Create ``path`` (and parents) and enforce ``0700`` on it.

    Raises on any filesystem error so callers fail closed instead of
    silently exporting text into an unsafe location.
    """
    path.mkdir(parents=True, exist_ok=True)
    os.chmod(path, stat.S_IRWXU)  # 0700 — owner only
    return path


def get_exports_dir() -> Path:
    """Return the per-user directory where export files are written.

    Prefers the XDG runtime directory (cleaned automatically at logout);
    falls back to the per-user cache directory. Never falls back to the
    shared system temporary directory.
    """
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    if runtime_dir:
        return _enforce_private_dir(Path(runtime_dir) / "anura" / "exports")

    cache_dir = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return _enforce_private_dir(Path(cache_dir) / "anura" / "exports")


def write_export_file(text: str, suffix: str = ".txt") -> Path:
    """Write ``text`` to a private, randomly-named file and return its path.

    Uses :func:`tempfile.mkstemp` so the file is created exclusively
    (mode ``0600``, O_EXCL) with an unguessable name.
    """
    exports_dir = get_exports_dir()
    fd, raw_path = tempfile.mkstemp(prefix="extracted_", suffix=suffix, dir=exports_dir)
    path = Path(raw_path)
    try:
        handle = os.fdopen(fd, "w", encoding="utf-8")
    except BaseException:
        os.close(fd)
        path.unlink(missing_ok=True)
        raise
    try:
        with handle:
            handle.write(text)
    except BaseException:
        # Never leave a partially-written sensitive file behind.
        path.unlink(missing_ok=True)
        raise
    logger.debug(f"Anura Export: wrote export file {path.name} in {exports_dir}")
    return path


def cleanup_stale_export_files(cutoff_time: float) -> int:
    """Remove regular export files older than ``cutoff_time`` (epoch seconds).

    Symlinks and directories are never followed or removed. Returns the
    number of files removed.
    """
    removed = 0
    exports_dir = get_exports_dir()
    for path in exports_dir.iterdir():
        if path.is_symlink() or not path.is_file():
            continue
        try:
            if path.stat().st_mtime < cutoff_time:
                path.unlink()
                removed += 1
        except OSError as error:
            logger.debug(f"Anura Export: could not remove {path.name}: {error}")
    return removed
