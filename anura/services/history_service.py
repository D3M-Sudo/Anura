# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import json
import os
from pathlib import Path
import threading
import time
from typing import ClassVar
import uuid

from gi.repository import GObject
from loguru import logger

from anura.models.history import CaptureSession
from anura.services.settings import settings
from anura.utils.singleton import get_instance


class HistoryService(GObject.GObject):
    """Singleton service for managing capture history with async persistence."""

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "history-changed": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self) -> None:
        GObject.GObject.__init__(self)
        self._sessions: list[CaptureSession] = []
        self._history_dir = self._get_history_directory()
        self._history_file = self._history_dir / "history.json"
        self._load_history()

    def _get_history_directory(self) -> Path:
        """Resolve history directory: XDG_STATE_HOME -> ~/.local/state/anura/history"""
        state_home = os.environ.get("XDG_STATE_HOME")
        state_home_path = Path(state_home) if state_home else Path.home() / ".local" / "state"
        hist_dir = state_home_path / "anura" / "history"
        try:
            hist_dir.mkdir(parents=True, exist_ok=True)
            hist_dir.chmod(0o700)
        except OSError as e:
            logger.error(f"HistoryService: Failed to create history directory: {e}")
        return hist_dir

    def _load_history(self) -> None:
        """Synchronously load history on startup, degrading gracefully if corrupted."""
        if not self._history_file.exists():
            self._sessions = []
            return

        try:
            with open(self._history_file, encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("History data is not a list")

                sessions = []
                for item in data:
                    try:
                        session = CaptureSession(
                            id=str(item["id"]),
                            timestamp=float(item["timestamp"]),
                            text=str(item["text"]),
                            lang=str(item["lang"]),
                            thumbnail=item.get("thumbnail"),
                        )
                        sessions.append(session)
                    except (KeyError, ValueError, TypeError) as e:
                        logger.warning(f"HistoryService: Skipping malformed item: {e}")
                self._sessions = sorted(sessions, key=lambda s: s.timestamp, reverse=True)
                logger.info(f"HistoryService: Loaded {len(self._sessions)} capture history entries")
        except (json.JSONDecodeError, ValueError, OSError) as e:
            logger.error(f"HistoryService: Failed to load history (file may be corrupt): {e}")
            self._handle_corrupt_file()

    def _handle_corrupt_file(self) -> None:
        """Safely isolate corrupted history and start with empty state."""
        self._sessions = []
        if self._history_file.exists():
            try:
                backup_path = self._history_file.with_name(f"history.corrupt.{int(time.time())}.json")
                self._history_file.rename(backup_path)
                logger.warning(f"HistoryService: Corrupted file renamed to {backup_path}")
            except OSError as e:
                logger.error(f"HistoryService: Failed to rename corrupt history file: {e}")

    def _save_history_async(self) -> None:
        """Asynchronously serialize and save history to avoid blocking the main thread."""
        if not settings.get_boolean("history-enabled"):
            return

        # Prepare serializable list
        serializable = [
            {
                "id": s.id,
                "timestamp": s.timestamp,
                "text": s.text,
                "lang": s.lang,
                "thumbnail": s.thumbnail,
            }
            for s in self._sessions
        ]

        def save_in_thread():
            try:
                # Atomically write using a temporary file in the same directory
                temp_file = self._history_file.with_suffix(".tmp")
                with open(temp_file, "w", encoding="utf-8") as f:
                    json.dump(serializable, f, indent=2, ensure_ascii=False)
                temp_file.replace(self._history_file)
                logger.debug("HistoryService: Successfully wrote history to disk asynchronously")
            except OSError as e:
                logger.error(f"HistoryService: Async write failed: {e}")

        # Dispatch via GLib's ThreadPool / thread executor (we can use standard Python thread for disk I/O)
        t = threading.Thread(target=save_in_thread, daemon=True)
        t.start()

    def add_session(self, text: str, lang: str, thumbnail: str | None = None) -> None:
        """Add a new capture session if history-enabled is True."""
        if not settings.get_boolean("history-enabled"):
            logger.debug("HistoryService: Capture history is disabled, skipping save")
            return

        if not text or not text.strip():
            logger.debug("HistoryService: Skipping empty text session")
            return

        limit = max(1, settings.get_int("history-limit"))
        session = CaptureSession(
            id=str(uuid.uuid4()),
            timestamp=time.time(),
            text=text,
            lang=lang,
            thumbnail=thumbnail,
        )

        self._sessions.insert(0, session)

        # Enforce history limit
        if len(self._sessions) > limit:
            self._sessions = self._sessions[:limit]

        self._save_history_async()
        self.emit("history-changed")

    def get_sessions(self) -> list[CaptureSession]:
        """Return a copy of the capture history list."""
        return list(self._sessions)

    def delete_session(self, session_id: str) -> bool:
        """Delete a single session from history."""
        original_len = len(self._sessions)
        self._sessions = [s for s in self._sessions if s.id != session_id]
        if len(self._sessions) != original_len:
            self._save_history_async()
            self.emit("history-changed")
            return True
        return False

    def clear_history(self) -> None:
        """Clear all session history and delete the history file on disk."""
        self._sessions = []

        def delete_file_in_thread():
            try:
                if self._history_file.exists():
                    self._history_file.unlink()
                logger.info("HistoryService: Deleted history file from disk")
            except OSError as e:
                logger.error(f"HistoryService: Failed to delete history file: {e}")

        t = threading.Thread(target=delete_file_in_thread, daemon=True)
        t.start()

        self.emit("history-changed")


def get_history_service() -> HistoryService:
    """Get the thread-safe singleton instance of HistoryService."""
    return get_instance(HistoryService)
