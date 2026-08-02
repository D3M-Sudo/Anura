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

import gi

# Set GTK version requirements before imports
gi.require_version("GLib", "2.0")
gi.require_version("GObject", "2.0")

from gi.repository import GLib, GObject  # noqa: E402
from loguru import logger  # noqa: E402

from anura.models.capture_session import CaptureSession  # noqa: E402
from anura.services.settings import settings  # noqa: E402
from anura.utils.singleton import get_instance  # noqa: E402


class HistoryService(GObject.GObject):
    """
    Thread-safe service for managing and persisting historic OCR capture sessions.
    Saves and loads CaptureSession objects to/from $XDG_STATE_HOME/anura/history/history.json.
    """

    __gtype_name__ = "HistoryService"

    __gsignals__: ClassVar[dict[str, tuple]] = {
        "changed": (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self._write_thread: threading.Thread | None = None
        self._sessions: list[CaptureSession] = []
        self.settings = settings

        # Resolve state home directory for history file
        state_home = os.environ.get(
            "XDG_STATE_HOME",
            os.path.join(os.path.expanduser("~"), ".local", "state")
        )
        self._history_dir = Path(state_home) / "anura" / "history"
        self._history_file = self._history_dir / "history.json"

        # Initial load of history on startup
        self.load_history()

    def load_history(self) -> None:
        """Loads capture history from JSON file. Performs recovery if corrupted."""
        with self._lock:
            if not self._history_file.exists():
                self._sessions = []
                return

            try:
                with open(self._history_file, encoding="utf-8") as f:
                    data = json.load(f)
                    if not isinstance(data, list):
                        raise ValueError("History data must be a JSON array")

                sessions = []
                for item in data:
                    try:
                        sessions.append(CaptureSession.from_dict(item))
                    except Exception as e:
                        logger.error(f"HistoryService: Skipping unparseable entry: {e}")

                self._sessions = sessions
                logger.info(f"HistoryService: Loaded {len(self._sessions)} entries.")
            except Exception as e:
                logger.error(f"HistoryService: Failed to parse history file: {e}")
                self._handle_corrupted_file()
                self._sessions = []

    def _handle_corrupted_file(self) -> None:
        """Rename the corrupted file and safe-degrade to empty history."""
        try:
            timestamp = int(time.time())
            corrupt_file = self._history_dir / f"history.corrupt.{timestamp}.json"
            if self._history_file.exists():
                self._history_file.rename(corrupt_file)
                logger.warning(
                    f"HistoryService: Corrupted file renamed to {corrupt_file} for safety."
                )
        except Exception as rename_err:
            logger.error(f"HistoryService: Failed to rename corrupted file: {rename_err}")

    def get_sessions(self) -> list[CaptureSession]:
        """Returns a copy of the list of loaded capture sessions."""
        with self._lock:
            return list(self._sessions)

    def add_session(
        self,
        text: str,
        language: str = "",
        transformer_name: str = "",
        thumbnail_base64: str = "",
    ) -> None:
        """Adds a new capture session to history if enabled."""
        if not self.settings.get_boolean("history-enabled"):
            logger.debug("HistoryService: History is disabled, ignoring capture.")
            return

        with self._lock:
            # Generate a clean UUID and Unix timestamp
            session_id = str(uuid.uuid4())
            timestamp = time.time()

            # Create the CaptureSession object
            session = CaptureSession(
                id=session_id,
                text=text,
                timestamp=timestamp,
                language=language,
                transformer_name=transformer_name,
                thumbnail_base64=thumbnail_base64,
            )

            # Insert at the beginning of the list (most recent first)
            self._sessions.insert(0, session)

            # Enforce history limit
            limit = max(1, self.settings.get_int("history-limit"))
            if len(self._sessions) > limit:
                self._sessions = self._sessions[:limit]

            self._save_history_async_locked()

        self._emit_changed()

    def delete_session(self, session_id: str) -> None:
        """Removes a specific capture session from history."""
        with self._lock:
            self._sessions = [s for s in self._sessions if s.id != session_id]
            self._save_history_async_locked()

        self._emit_changed()

    def clear_history(self) -> None:
        """Clears all sessions from memory and disk."""
        with self._lock:
            self._sessions = []
            self._save_history_async_locked()

        self._emit_changed()

    def _save_history_async_locked(self) -> None:
        """Serializes current memory state and writes it on a sequenced thread.

        MUST be called while holding self._lock.
        """
        # Ensure any active previous save or clear thread is joined
        if self._write_thread and self._write_thread.is_alive():
            try:
                self._write_thread.join(timeout=1.5)
            except Exception as e:
                logger.error(f"HistoryService: Failed to join previous write thread: {e}")

        # Snapshot of current state to prevent mutations in background thread
        snapshot = [s.to_dict() for s in self._sessions]

        self._write_thread = threading.Thread(
            target=self._write_to_disk,
            args=(snapshot,),
            name="AnuraHistoryWriter"
        )
        self._write_thread.start()

    def _write_to_disk(self, snapshot: list[dict]) -> None:
        """Thread worker to safely serialize and write the history snapshot to disk."""
        try:
            self._history_dir.mkdir(parents=True, exist_ok=True)
            # Restrict directory access
            with contextlib_suppress():
                self._history_dir.chmod(0o700)

            # Temporary file write + rename pattern for atomic safety
            temp_file = self._history_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(snapshot, f, ensure_ascii=False, indent=2)

            temp_file.replace(self._history_file)
            logger.debug(f"HistoryService: Successfully wrote {len(snapshot)} entries to disk.")
        except Exception as e:
            logger.error(f"HistoryService: Thread failed to write history to disk: {e}")

    def _emit_changed(self) -> None:
        """Helper to safely emit 'changed' signal on the GLib main thread."""
        def _on_changed_idle():
            try:
                self.emit("changed")
            except Exception as e:
                logger.error(f"HistoryService: Failed to emit changed signal: {e}")
            return GLib.SOURCE_REMOVE

        GLib.idle_add(_on_changed_idle, priority=GLib.PRIORITY_DEFAULT)

    def shutdown(self) -> None:
        """Block and wait for pending write/save operations before application teardown."""
        with self._lock:
            if self._write_thread and self._write_thread.is_alive():
                logger.info("HistoryService: Waiting for pending disk writes to complete...")
                self._write_thread.join(timeout=5.0)


# Simple helper contextlib.suppress equivalent to avoid import side-effects
class contextlib_suppress:
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return True


def get_history_service() -> HistoryService:
    """Get thread-safe history service singleton."""
    return get_instance(HistoryService)
