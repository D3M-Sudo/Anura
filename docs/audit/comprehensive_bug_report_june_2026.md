# Anura Comprehensive Bug Report - June 2026

## Overview
This report details the findings of a comprehensive deep-dive audit of the Anura codebase. It focuses exclusively on **newly discovered** bugs not documented in previous reports. The audit employed static analysis (Ruff, Bandit, Safety, Mypy, Semgrep), dynamic chaos testing, and manual UI/UX logic verification.

---

## [NEW-007] LanguageManager: Model Pooling Race Condition
- **Severity:** HIGH
- **Area:** Concurrency / Data Integrity
- **Description:** Multi-language OCR (`eng+ita`) uses a dynamic pool directory (`TESSDATA_POOL_DIR`). The function `get_tesseract_config` unlinks and re-links model files into this shared directory without any cross-thread or cross-process locking.
- **Steps to Reproduce:**
    1. Initiate two OCR tasks for different multi-language pairs (e.g., `eng+ita` and `eng+fra`) in rapid succession.
    2. The second call will unlink files while the first task's Tesseract process is still starting, leading to `FileNotFoundError` or corrupted OCR engine initialization.
- **Logs/Evidence:** `anura/services/language_manager.py` line 520 (approx). No lock is held during the loop that calls `dest_path.unlink()` and `os.link()`.
- **Suggested Fix:** Wrap the pooling logic in a named file lock or use a unique subdirectory per `task_id` within the pool.

## [NEW-008] OcrController: Navigation Interlock is Logic-Broken
- **Severity:** MEDIUM
- **Area:** UI/UX Logic / Race Conditions
- **Description:** To prevent "focus jumps" during rapid captures, `OcrController` checks if the result's task ID is still the active one. However, it looks for `backend._current_task_id`, which is **not defined** in `ScreenshotService`.
- **Steps to Reproduce:**
    1. Trigger a capture.
    2. Before it finishes, trigger another capture (or cancel).
    3. The first capture's callback fires. `getattr(self._window.backend, "_current_task_id", None)` returns `None`.
    4. `_navigate_to_extracted_page(None)` is called.
    5. The check `if task_id:` (line 178) fails, and the UI **always** navigates to the Extracted Page, even if the task was cancelled.
- **Evidence:** `anura/controllers/ocr_controller.py` line 112 and `anura/services/screenshot_service.py` (missing attribute).
- **Suggested Fix:** Implement `_current_task_id` property in `ScreenshotService` that tracks the last ID emitted by `AtomicTaskManager`.

## [NEW-009] ResultDispatcher: AttributeError on Malformed Structured Data
- **Severity:** MEDIUM
- **Area:** Stability
- **Description:** `ResultDispatcher.dispatch()` assumes `get_text_preprocessor().extract_structured_data()` always returns a dictionary. If it returns `None` (e.g., due to an internal error or crash), the dispatcher crashes with `AttributeError`.
- **Steps to Reproduce:**
    1. Force `extract_structured_data` to return `None`.
    2. Call `dispatcher.dispatch("some text")`.
- **Evidence:** `anura/services/result_dispatcher.py` line 44: `urls = tuple(structured.get("urls", []))`.
- **Suggested Fix:** Add a null check: `structured = preprocessor.extract_structured_data(text) or {}`.

## [NEW-010] LanguageRow: Idle Source and Memory Leak
- **Severity:** LOW
- **Area:** Memory Management
- **Description:** `LanguageRow` tracks idle IDs in `self._idle_ids`. While it prunes them in `do_destroy`, it fails to remove them from the set once they have naturally fired and returned `GLib.SOURCE_REMOVE`. Over time, the set grows with stale integers. Additionally, `_progress_idle_id` is reset to `0` instead of being removed from the tracking set.
- **Steps to Reproduce:**
    1. Perform 100+ language downloads/progress updates.
    2. Inspect `len(self._idle_ids)`.
- **Evidence:** `anura/widgets/language_row.py` lines 96, 105.
- **Suggested Fix:** Use a helper that wraps `GLib.idle_add` and automatically discards the ID from the tracking set upon execution.

## [NEW-011] Validators: Legitimate IDN Rejection
- **Severity:** MEDIUM
- **Area:** Security / Usability
- **Description:** The homograph defense in `is_safe_url_string` is too aggressive. It rejects ANY label that mixes ASCII and non-ASCII. This blocks legitimate international domains like `münchen.de` because 'm', 'u', 'n', 'c', 'h', 'e', 'n' are ASCII and 'ü' is not.
- **Steps to Reproduce:**
    1. Extract text containing `https://münchen.de`.
    2. The URL validator will return `False`.
- **Evidence:** `anura/utils/validators.py` lines 103-105: `has_ascii = any(ch.isascii()...) if has_ascii: return False`.
- **Suggested Fix:** Refine the check to allow mixing if the characters belong to the same script (e.g., Latin-1) or if they are not "confusable" with ASCII.

## [NEW-012] ScreenshotService: User TESSERACT_CMD Ignored
- **Severity:** MEDIUM
- **Area:** Configuration
- **Description:** `_configure_tesseract_path` is intended to handle Flatpak vs. Host paths. However, in non-Flatpak environments, it unconditionally calls `os.environ.pop("TESSERACT_CMD", None)`, effectively deleting any custom path a user might have set to point to a specific Tesseract installation.
- **Steps to Reproduce:**
    1. Run `TESSERACT_CMD=/opt/tess/bin/tesseract anura`.
    2. `ScreenshotService` will clear the variable and use `tesseract` from PATH instead.
- **Evidence:** `anura/services/screenshot_service.py` line 199.
- **Suggested Fix:** Only pop the variable if it wasn't already set by the user, or if we are specifically switching *to* system mode from a known Flatpak state.

## [NEW-013] ExtractedPage: Dead UI State 'cancel'
- **Severity:** LOW
- **Area:** UI/UX
- **Description:** The `listen_stack` in `extracted_page.ui` contains a page named "cancel" with a stop button. However, the Python code only ever transitions between "button", "spinner", and "pause". The "cancel" state is unreachable dead code/UI.
- **Evidence:** `data/ui/extracted_page.blp` line 52 vs `anura/widgets/extracted_page.py`.
- **Suggested Fix:** Remove the "cancel" stack page or implement the intended transition logic.

## [NEW-014] StructuralReconstructor: Incompatible Type Assignment
- **Severity:** LOW
- **Area:** Stability / Lint
- **Description:** Mypy correctly identified a type mismatch where a variable expected to hold a list or specific structure is assigned a tuple/int in a loop, potentially leading to runtime errors if the reconstruction logic is extended.
- **Evidence:** `anura/utils/structural_reconstructor.py` line 54.
- **Suggested Fix:** Correct the type hint or the assignment to match the intended data structure.

## [NEW-015] ClipboardService: GObject Source ID Warning
- **Severity:** LOW
- **Area:** Stability / Logs
- **Description:** `ClipboardService` emits `Warning: Source ID ... was not found when attempting to remove it` on stderr. This occurs because it attempts to remove a source ID that has already fired (one-shot timeout) or was already removed by another thread/callback.
- **Evidence:** Log evidence: `/app/.../clipboard_service.py:590: Warning: Source ID 1121 was not found...`. In the current source, this is triggered at `anura/services/clipboard_service.py` line 312 (inside `_remove_source`).
- **Suggested Fix:** Ensure `GLib.source_remove` is only called if the source still exists, or use a safer cleanup pattern. Note: BUG-6 attempted to fix this but the race condition persists.

## [NEW-016] LegacyX11Provider: Screenshot Timing Race (scrot)
- **Severity:** MEDIUM
- **Area:** Fallback Screenshot / Reliability
- **Description:** `LegacyX11Provider` (scrot fallback) may fail with "Screenshot tool produced no output" if the filesystem is slow to flush the PNG file. The retry loop (10 attempts every 100ms) might be insufficient in heavily loaded environments (like Flatpak on some distros or slow disks), leading to a premature failure even if scrot exited successfully.
- **Steps to Reproduce:**
    1. Run Anura on a slow filesystem/X11 session.
    2. Trigger a scrot-based capture (e.g., portal missing).
    3. If scrot takes > 1s to flush the file, capture fails.
- **Evidence:** `anura/services/screenshot/legacy_provider.py` line 179 and reproduction test `tests/audit/test_scrot_timing.py`.
- **Suggested Fix:** Increase the retry count/delay or use `Gio.File.monitor` to wait for file content.

---
**Report Generated by Jules (AI Engineering Lead)**
**Date:** June 3, 2026
