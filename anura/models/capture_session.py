# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

from gi.repository import GObject


class CaptureSession(GObject.GObject):
    """
    Represent a single captured OCR session.
    Designed for use with Gio.ListStore and Gtk.ListView.
    """

    __gtype_name__ = "CaptureSession"

    id = GObject.Property(type=str, default="")
    text = GObject.Property(type=str, default="")
    timestamp = GObject.Property(type=float, default=0.0)
    language = GObject.Property(type=str, default="")
    transformer_name = GObject.Property(type=str, default="")
    thumbnail_base64 = GObject.Property(type=str, default="")

    def __init__(
        self,
        id: str = "",
        text: str = "",
        timestamp: float = 0.0,
        language: str = "",
        transformer_name: str = "",
        thumbnail_base64: str = "",
    ) -> None:
        """
        Initialize a new CaptureSession.
        """
        super().__init__()
        self.id = id
        self.text = text
        self.timestamp = timestamp
        self.language = language
        self.transformer_name = transformer_name
        self.thumbnail_base64 = thumbnail_base64

    def to_dict(self) -> dict:
        """Convert capture session to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "text": self.text,
            "timestamp": self.timestamp,
            "language": self.language,
            "transformer_name": self.transformer_name,
            "thumbnail_base64": self.thumbnail_base64,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CaptureSession":
        """Create a CaptureSession from a dictionary."""
        return cls(
            id=data.get("id", ""),
            text=data.get("text", ""),
            timestamp=float(data.get("timestamp", 0.0)),
            language=data.get("language", ""),
            transformer_name=data.get("transformer_name", ""),
            thumbnail_base64=data.get("thumbnail_base64", ""),
        )

    def __repr__(self) -> str:
        return f"<CaptureSession: {self.props.id}, lang={self.props.language}>"
