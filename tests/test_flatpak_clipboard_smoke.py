# This file is part of Anura.
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

"""Regression checks for the Flatpak clipboard-lifetime CI harness."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_clipboard_smoke_signals_the_sandboxed_app_not_the_flatpak_launcher() -> None:
    workflow = (REPO_ROOT / ".github/workflows/main.yml").read_text(encoding="utf-8")
    start = workflow.index("Functional test - clipboard lifetime in Flatpak sandbox")
    end = workflow.index("Functional test - OCR negativo", start)
    block = workflow[start:end]

    assert "flatpak kill --signal=TERM io.github.d3m_sudo.anura" in block
    assert 'kill -TERM "$APP_PID"' not in block
    assert "Clipboard serving interrupted by a signal" in block
