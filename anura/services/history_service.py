# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import json
import logging
import os
from pathlib import Path
import time

from anura.config import XDG_DATA_HOME
from anura.models.history import HistoryEntry

logger = logging.getLogger(__name__)

DEFAULT_HISTORY_LIMIT = 50


class HistoryService:
    """
    Simple synchronous local history persistence (JSON file).

    Stores OCR results newest-first in
    ``$XDG_DATA_HOME/anura/history/history.json`` with atomic writes and
    corruption recovery. No threading, no database — integration concerns
    are deferred to later phases.

    The stored text is user content (documents, messages, credentials), so the
    directory is kept ``0700`` and the JSON file ``0600``: the default umask
    would otherwise leave them readable by other local accounts.
    """

    _DIR_MODE = 0o700
    _FILE_MODE = 0o600

    def __init__(
        self,
        base_dir: Path | str | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> None:
        if base_dir is None:
            base_dir = Path(XDG_DATA_HOME) / "anura" / "history"
        self._base_dir = Path(base_dir)
        self._history_file = self._base_dir / "history.json"
        self._limit = limit
        self._entries: list[HistoryEntry] | None = None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def record(
        self,
        text: str,
        language: str,
        applied_name: str = "",
        conf: float = 0.0,
    ) -> HistoryEntry:
        """Create a new entry, insert it newest-first, enforce the limit and persist."""
        entry = HistoryEntry(text=text, language=language, applied_name=applied_name, conf=conf)
        entries = self._load()
        entries.insert(0, entry)
        self._entries = entries[: self._limit]
        self._persist()
        return entry

    def get_entries(self, limit: int | None = None) -> list[HistoryEntry]:
        """Return stored entries newest-first. The returned list is a copy."""
        entries = self._load()
        if limit is not None:
            return entries[:limit]
        return list(entries)

    def clear(self) -> None:
        """Remove all entries and persist the empty history.

        The in-memory cache is replaced only after the empty state has been
        written. If persistence fails, the previous entries are restored, so a
        failed clear can never look successful: without this the cache was
        empty while the old ``history.json`` was still on disk, and the entries
        "came back" after a restart (#540).
        """
        previous = self._load()
        self._entries = []
        try:
            self._persist()
        except OSError:
            self._entries = previous
            raise

    def set_limit(self, limit: int) -> None:
        """Apply a new entry limit at runtime.

        Shrinking the limit trims the in-memory list and persists it, so the
        preference takes effect without a restart (#510). A failed write is
        logged but not fatal: the limit still applies in memory and the next
        ``record()`` rewrites the file with the new limit.
        """
        new_limit = max(1, int(limit))
        if new_limit == self._limit:
            return

        self._limit = new_limit
        entries = self._load()
        if len(entries) > new_limit:
            self._entries = entries[:new_limit]
            try:
                self._persist()
            except OSError:
                logger.warning(f"History: limit set to {new_limit} but trimming could not be persisted")
        logger.debug(f"History: entry limit updated to {new_limit}")

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _load(self) -> list[HistoryEntry]:
        """Lazily load entries from disk, handling corruption defensively."""
        if self._entries is not None:
            return self._entries

        entries: list[HistoryEntry] = []
        if self._history_file.exists():
            try:
                raw = self._history_file.read_text(encoding="utf-8")
                data = json.loads(raw)
                if isinstance(data, list):
                    for item in data:
                        entry = HistoryEntry.from_dict(item)
                        if entry is not None:
                            entries.append(entry)
                else:
                    self._quarantine_corrupted()
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                self._quarantine_corrupted()
                entries = []

        self._entries = entries[: self._limit]
        return self._entries

    def _quarantine_corrupted(self) -> None:
        """Rename the corrupted file instead of deleting it; never crash."""
        quarantine = self._base_dir / f"history.json.corrupt-{int(time.time())}"
        try:
            os.replace(self._history_file, quarantine)
            logger.warning("Corrupted history file quarantined: %s", quarantine)
        except OSError:
            logger.exception("Failed to quarantine corrupted history file")

    def _ensure_base_dir(self) -> None:
        """Create the history directory private to the current user.

        ``mkdir(mode=...)`` is filtered by the process umask, so the mode is
        applied explicitly afterwards; a pre-existing permissive directory is
        tightened too. The path is always derived from ``XDG_DATA_HOME`` (never
        from a filename supplied by the caller), so chmod cannot be redirected
        to an unrelated file.
        """
        self._base_dir.mkdir(parents=True, exist_ok=True, mode=self._DIR_MODE)
        try:
            if self._base_dir.stat().st_mode & 0o777 != self._DIR_MODE:
                self._base_dir.chmod(self._DIR_MODE)
        except OSError:
            # Non-fatal: persistence can still succeed on filesystems that do
            # not support chmod (e.g. some FUSE mounts).
            logger.warning("Could not tighten history directory permissions: %s", self._base_dir)

    def _persist(self) -> None:
        """Atomically write the history file (temp file + os.replace)."""
        self._ensure_base_dir()
        payload = json.dumps([e.to_dict() for e in self._entries or []], ensure_ascii=False, indent=2)
        tmp_path = self._base_dir / f"history.json.tmp-{os.getpid()}"
        try:
            # Create the temp file ourselves with mode 0600 instead of using
            # open(): the default 0666 & ~umask would expose OCR text to other
            # local users. O_EXCL guarantees we never reuse someone else's file
            # (a stale temp from a crashed run with a recycled PID is removed
            # first, which is safe because the name is PID-scoped).
            tmp_path.unlink(missing_ok=True)
            fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, self._FILE_MODE)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            # os.replace keeps the temp file mode, so the final file stays 0600.
            os.replace(tmp_path, self._history_file)
        except OSError:
            logger.exception("Failed to persist history")
            tmp_path.unlink(missing_ok=True)
            raise
