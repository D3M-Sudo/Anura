# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import contextlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time

from loguru import logger

from anura.config import XDG_DATA_HOME
from anura.models.history import HistoryEntry

DEFAULT_HISTORY_LIMIT = 50

# Upper bound for a single stored entry (#511). The OCR pipeline accepts up to
# MAX_TEXT_LENGTH (1,000,000) characters; storing that per entry, multiplied by
# the history limit, turned every rewrite into hundreds of MB.
MAX_HISTORY_ENTRY_CHARS = 100_000


class HistoryService:
    """Local history persistence (JSON file) with coalesced background writes.

    Stores OCR results newest-first in
    ``$XDG_DATA_HOME/anura/history/history.json`` with atomic writes and
    corruption recovery.

    ``record()`` only mutates memory and schedules a background write:
    serialising and fsyncing the whole file on the GTK main thread blocked the
    UI after every extraction (#511). ``clear()`` and ``set_limit()`` stay
    synchronous because they must report a failure and roll back (#540), and
    ``close()`` flushes pending entries at shutdown.

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
        persist_async: bool = True,
    ) -> None:
        if base_dir is None:
            base_dir = Path(XDG_DATA_HOME) / "anura" / "history"
        self._base_dir = Path(base_dir)
        self._history_file = self._base_dir / "history.json"
        self._limit = limit
        self._entries: list[HistoryEntry] | None = None

        # _lock guards the in-memory state; _write_lock serialises filesystem
        # writes so a background snapshot can never land after a newer one.
        self._lock = threading.RLock()
        self._write_lock = threading.Lock()
        self._changed = threading.Condition(self._lock)
        self._dirty = False
        self._generation = 0
        self._closing = False
        self._writer: threading.Thread | None = None

        if persist_async:
            self._writer = threading.Thread(
                target=self._persist_loop,
                name="AnuraHistoryWriter",
                daemon=True,
            )
            self._writer.start()

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
        """Create a new entry newest-first and schedule a background write."""
        if len(text) > MAX_HISTORY_ENTRY_CHARS:
            logger.debug(f"History: entry truncated from {len(text)} to {MAX_HISTORY_ENTRY_CHARS} characters")
            text = text[:MAX_HISTORY_ENTRY_CHARS]

        entry = HistoryEntry(text=text, language=language, applied_name=applied_name, conf=conf)
        snapshot: list[HistoryEntry] | None = None
        with self._lock:
            entries = self._load_locked()
            entries.insert(0, entry)
            self._entries = entries[: self._limit]
            if self._writer is None:
                # Synchronous mode (no writer thread): persist before returning
                # so callers keep the old at-return durability guarantee.
                snapshot = list(self._entries)
                self._dirty = False
            else:
                self._mark_dirty_locked()

        if snapshot is not None:
            with self._write_lock:
                self._write_entries(snapshot)
        return entry

    def get_entries(self, limit: int | None = None) -> list[HistoryEntry]:
        """Return stored entries newest-first. The returned list is a copy."""
        with self._lock:
            entries = self._load_locked()
            if limit is not None:
                return entries[:limit]
            return list(entries)

    def clear(self) -> None:
        """Remove all entries and persist the empty history (synchronously).

        The in-memory cache is replaced only after the empty state has been
        written. If persistence fails, the previous entries are restored, so a
        failed clear can never look successful: without this the cache was
        empty while the old ``history.json`` was still on disk, and the entries
        "came back" after a restart (#540).
        """
        with self._write_lock:
            with self._lock:
                previous = list(self._load_locked())
                self._entries = []
                self._dirty = False
                self._generation += 1
            try:
                self._write_entries([])
            except OSError:
                with self._lock:
                    self._entries = previous
                    self._generation += 1
                raise

    def set_limit(self, limit: int) -> None:
        """Apply a new entry limit at runtime.

        Shrinking the limit trims the in-memory list and persists it before
        returning, so the preference takes effect without a restart (#510). A
        failed write is logged but not fatal: the limit still applies in memory
        and a later write persists the trimmed list.
        """
        new_limit = max(1, int(limit))

        with self._write_lock:
            with self._lock:
                if new_limit == self._limit:
                    return
                self._limit = new_limit
                entries = self._load_locked()
                if len(entries) <= new_limit:
                    logger.debug(f"History: entry limit updated to {new_limit}")
                    return
                self._entries = entries[:new_limit]
                self._dirty = False
                self._generation += 1
                snapshot = list(self._entries)

            try:
                self._write_entries(snapshot)
            except OSError:
                logger.warning(f"History: limit set to {new_limit} but trimming could not be persisted")
                with self._lock:
                    self._dirty = True
        logger.debug(f"History: entry limit updated to {new_limit}")

    def flush(self) -> bool:
        """Write pending entries synchronously; True when nothing is pending."""
        with self._write_lock:
            with self._lock:
                if not self._dirty:
                    return True
                snapshot = list(self._entries or [])
                generation = self._generation

            try:
                self._write_entries(snapshot)
            except OSError:
                logger.exception("History: failed to flush pending entries")
                with self._lock:
                    self._dirty = True
                return False

            with self._lock:
                if generation == self._generation:
                    self._dirty = False
            return True

    def close(self) -> None:
        """Flush pending entries and stop the writer (idempotent)."""
        with self._lock:
            if self._closing:
                return
            self._closing = True
            self._changed.notify_all()

        writer = self._writer
        if writer is not None:
            writer.join(timeout=2.0)

        self.flush()
        logger.debug("History: writer stopped")

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #

    def _mark_dirty_locked(self) -> None:
        """Mark the in-memory state as pending and wake the writer."""
        self._dirty = True
        self._generation += 1
        self._changed.notify()

    def _persist_loop(self) -> None:
        """Write coalesced snapshots until :meth:`close` is called."""
        while True:
            with self._lock:
                while not self._dirty and not self._closing:
                    self._changed.wait()
                if self._closing and not self._dirty:
                    return

            # The snapshot is taken while holding _write_lock, so a concurrent
            # flush()/clear() can never interleave between "read state" and
            # "write it": whoever holds the write lock owns the next state.
            with self._write_lock:
                with self._lock:
                    if not self._dirty:
                        continue
                    snapshot = list(self._entries or [])
                    self._dirty = False

                try:
                    self._write_entries(snapshot)
                except OSError:
                    logger.exception("History: background persist failed; will retry on the next change")
                    with self._lock:
                        self._dirty = True
                        self._changed.notify()
                        if self._closing:
                            return
                    # Avoid a hot retry loop when the filesystem stays broken.
                    time.sleep(0.05)

    def _load_locked(self) -> list[HistoryEntry]:
        """Lazily load entries from disk. The caller must hold ``_lock``."""
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
            logger.warning(f"Corrupted history file quarantined: {quarantine}")
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
            logger.warning(f"Could not tighten history directory permissions: {self._base_dir}")

    def _write_entries(self, entries: list[HistoryEntry]) -> None:
        """Atomically write *entries* to ``history.json``.

        ``mkstemp`` gives a unique name (concurrent writers cannot collide) and
        creates the file 0600, so OCR text never becomes readable by other
        local users; ``os.replace`` keeps that mode (#527).
        """
        self._ensure_base_dir()
        payload = json.dumps([entry.to_dict() for entry in entries], ensure_ascii=False, indent=2)

        fd, tmp_name = tempfile.mkstemp(prefix="history.", suffix=".tmp", dir=self._base_dir)
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(payload)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_path, self._history_file)
        except OSError:
            logger.exception("Failed to persist history")
            with contextlib.suppress(OSError):
                tmp_path.unlink(missing_ok=True)
            raise
