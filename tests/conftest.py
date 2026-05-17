# tests/conftest.py
#
# Shared fixtures and setup for Anura test suite.
# GTK/GLib are NOT initialized here — tests that need them must be
# marked with @pytest.mark.gtk and skipped in CI without a display.
#
# === ESSENTIAL TESTING GUIDE ===
#
# 🚀 DAILY DEVELOPMENT (always use this):
#   uv run pytest tests/ -m "not gtk" -v
#   Expected: 148 passed, 9 skipped, 29 deselected ✅
#
# 🧪 GTK TESTING (two methods):
#   Method A (Recommended): Flatpak Sandbox
#     flatpak run --devel --command=bash com.github.d3msudo.anura
#     python3 -m pytest tests/ -m "gtk" -v
#
#   Method B (Host System): Requires setup
#     ./setup-gschema.sh
#     export GSETTINGS_SCHEMA_DIR="builddir"
#     uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" \
#         GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" \
#         GSETTINGS_SCHEMA_DIR="builddir" pytest tests/ -m "gtk" -v
#
# ❌ NEVER USE THIS COMMAND (without GI_TYPELIB_PATH, tests that need gi will skip/fail):
#   uv run pytest tests/ -v
#   Current result: 172 passed, 14 skipped (imports that need gi are skipped gracefully)
#
# === TECHNICAL DETAILS ===
#
# @pytest.mark.gtk tests require special environment because anura depends on:
# - Xdp (libportal) — only available in /app inside the Flatpak sandbox
# - GTK4/Adwaita GI bindings — may differ between host and Flatpak runtime
#
# On the host system, always use: pytest tests/ -m "not gtk"

import os
import sys

import pytest

# Ensure the project root is on sys.path so `import anura` works
# without installing the package first.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def pytest_collection_modifyitems(items):
    for item in items:
        if "gi" in str(item.fspath) or "gtk" in item.name.lower():
            item.add_marker(pytest.mark.gtk)


@pytest.fixture
def tmp_tessdata(tmp_path):
    """
    Provides a temporary tessdata directory with a fake 'eng.traineddata' file.
    Useful for testing language model detection without a real Tesseract install.
    """
    tessdata = tmp_path / "tessdata"
    tessdata.mkdir()
    (tessdata / "eng.traineddata").write_bytes(b"fake-model")
    (tessdata / "ita.traineddata").write_bytes(b"fake-model")
    return tessdata


@pytest.fixture(autouse=True)
def isolate_env(monkeypatch, tmp_path):
    """
    Isolates all tests from the real user environment.
    Overrides XDG dirs so tests never touch ~/.local or ~/.cache.
    """
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("TESSDATA_PREFIX_SYSTEM", str(tmp_path / "system-tessdata"))
