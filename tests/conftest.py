# This file is part of Anura.
# Copyright (C) 2022-2025 Andrey Maksimov (Frog)
# Copyright (C) 2026 D3M-Sudo (Anura)
#
# SPDX-License-Identifier: MIT

import os
from pathlib import Path
import sys

import pytest

# Ensure the project root is on sys.path so `import anura` works
# without installing the package first.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _module_needs_gi(fspath: object) -> bool:
    """Return True if the test module at *fspath* depends on gi.repository.

    Scans the file content directly rather than relying on the filename or the
    test function name.  The previous heuristic (``"gi" in str(item.fspath)``)
    never matched any test file because no file path contains the literal
    two-character substring "gi" in isolation — it only appeared inside longer
    words like "github" in the runner's workspace path.

    This function is intentionally kept simple and side-effect-free: it reads
    the source file once per file (the call-site caches per fspath) and checks
    for the presence of common gi-dependency patterns.
    """
    try:
        src = Path(str(fspath)).read_text(encoding="utf-8", errors="replace")
        return (
            "import gi" in src
            or "from gi" in src
            or 'importorskip("gi")' in src
            or "importorskip('gi')" in src
        )
    except OSError:
        return False


def pytest_collection_modifyitems(items: list) -> None:
    """Add the ``gtk`` marker to every test that depends on gi.repository.

    Bug fixed: the previous implementation used two unreliable heuristics:
    - ``"gi" in str(item.fspath)``  → never matched (path contains "github",
      "gi" only as a substring of longer words, never standalone).
    - ``"gtk" in item.name.lower()`` → only caught tests explicitly named
      *test_gtk_**, missing the vast majority of gi-dependent tests.

    Result: only 7 out of ~80 gi-dependent tests were tagged, causing the
    gtk-tests CI job to run almost nothing.

    Fix: scan each file's source once (cached per fspath) for the four
    patterns that indicate a gi dependency.  A per-call dict is used as the
    cache so the hook remains stateless across test runs.
    """
    _gi_file_cache: dict[str, bool] = {}

    for item in items:
        fspath_str = str(item.fspath)

        if fspath_str not in _gi_file_cache:
            _gi_file_cache[fspath_str] = _module_needs_gi(item.fspath)

        if _gi_file_cache[fspath_str] or "gtk" in item.name.lower():
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


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before returning the exit status to the system.
    Ensures that all background executors and singleton services are explicitly shut down
    to prevent orphan processes or threads from hanging CI.
    """
    print("\nEnsuring clean session teardown...")
    # 1. Shutdown AtomicTaskManager
    try:
        from anura.core.atomic_task_manager import get_atomic_manager

        get_atomic_manager().shutdown()
    except (ImportError, AttributeError, RuntimeError):
        pass

    # 2. Shutdown LanguageManager
    try:
        from anura.services.language_manager import get_language_manager

        get_language_manager().shutdown()
    except (ImportError, AttributeError, RuntimeError):
        pass

    # 3. Cleanup TTSService
    try:
        from anura.services.tts import get_tts_service

        get_tts_service().cleanup()
    except (ImportError, AttributeError, RuntimeError):
        pass

    # 4. Reset singletons to clear references
    try:
        from anura.utils.singleton import ThreadSafeSingleton

        ThreadSafeSingleton.reset_for_testing()
    except (ImportError, AttributeError):
        pass
    print("Teardown complete.")
