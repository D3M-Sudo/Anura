# velis/services/history_service.py
from datetime import datetime
import os
from pathlib import Path
import shutil
import sqlite3

from velis.utils.singleton import get_instance


class HistoryService:
    def __init__(self):
        self.data_dir = Path(os.path.expanduser("~/.local/share/velis"))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.image_dir = self.data_dir / "images"
        self.image_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = self.data_dir / "history.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    text TEXT,
                    image_path TEXT
                )
            """)

    def add_entry(self, text, source_image_path=None):
        timestamp = datetime.now().isoformat()
        saved_image_path = None

        if source_image_path and os.path.exists(source_image_path):
            ext = os.path.splitext(source_image_path)[1]
            saved_image_name = f"snippet_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}{ext}"
            saved_image_path = str(self.image_dir / saved_image_name)
            shutil.copy2(source_image_path, saved_image_path)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO history (timestamp, text, image_path) VALUES (?, ?, ?)",
                (timestamp, text, saved_image_path)
            )

        self._enforce_limits()

    def _enforce_limits(self):
        # TODO: Implement configurable limits from settings
        pass

    def get_history(self, limit=50):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM history ORDER BY timestamp DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

def get_history_service():
    return get_instance(HistoryService)
