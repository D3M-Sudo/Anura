# tests/conftest.py
#
# Shared fixtures and setup for Anura test suite.
# GTK/GLib are NOT initialized here — tests that need them must be
# marked with @pytest.mark.gtk and skipped in CI without a display.

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
