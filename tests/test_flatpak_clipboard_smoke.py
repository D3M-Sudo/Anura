# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Regression checks for the Flatpak clipboard-lifetime CI harness."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_clipboard_smoke_waits_for_a_real_retention_lifecycle_outcome() -> None:
    workflow = (REPO_ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8")
    start = workflow.index("Functional test - clipboard lifetime in Flatpak sandbox")
    end = workflow.index("Functional test - OCR negativo", start)
    block = workflow[start:end]

    assert "for attempt in $(seq 1 160)" in block
    assert 'kill -0 "$APP_PID"' in block
    assert "Clipboard content handed over to the clipboard manager" in block
    assert "Clipboard content was replaced by another application" in block
    assert "Clipboard serving period ended" in block
    assert "flatpak kill" not in block
    assert 'kill -TERM "$APP_PID"' not in block
