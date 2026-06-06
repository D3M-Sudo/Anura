# Anura Comprehensive Bug Report - June 2026

## Overview
This report details the findings of a comprehensive deep-dive audit of the Anura codebase. It identifies 10 new bugs (NEW-007 to NEW-016) and documents their successful remediation. The audit employed static analysis (Ruff, Bandit, Safety, Mypy, Semgrep), dynamic chaos testing, and manual UI/UX logic verification.

---

## [NEW-007] LanguageManager: Model Pooling Race Condition
- **Severity:** HIGH
- **Status:** FIXED
- **Area:** Concurrency / Data Integrity
- **Description:** Multi-language OCR (`eng+ita`) used a shared dynamic pool directory. `get_tesseract_config` unlinked and re-linked model files without locking, risking `FileNotFoundError` during concurrent operations.
- **Fix:** Implemented **task-isolated subdirectories** within `TESSDATA_POOL_DIR`. Each OCR task now has its own unique, sandboxed pooling directory based on its UUID.
- **Evidence:** `anura/services/language_manager.py` line 673 (approx).

## [NEW-008] OcrController: Navigation Interlock is Logic-Broken
- **Severity:** MEDIUM
- **Status:** FIXED
- **Area:** UI/UX Logic / Race Conditions
- **Description:** `OcrController` checked for a non-existent `backend._current_task_id` attribute, causing the UI to always navigate to the result page, even if the task was cancelled.
- **Fix:** Implemented a public `current_task_id` GObject property in `ScreenshotService` that accurately tracks the most recent task emitted by the atomic manager.
- **Evidence:** `anura/services/screenshot_service.py` line 250 and `anura/controllers/ocr_controller.py` line 112.

## [NEW-009] ResultDispatcher: AttributeError on Malformed Structured Data
- **Severity:** MEDIUM
- **Status:** FIXED
- **Area:** Stability
- **Description:** `ResultDispatcher.dispatch()` crashed with `AttributeError` if the preprocessor returned `None`.
- **Fix:** Added null-safe dictionary access: `structured = preprocessor.extract_structured_data(text) or {}`.
- **Evidence:** `anura/services/result_dispatcher.py` line 42.

## [NEW-010] LanguageRow: Idle Source and Memory Leak
- **Severity:** LOW
- **Status:** FIXED
- **Area:** Memory Management
- **Description:** `LanguageRow` failed to remove naturally completed idle source IDs from its tracking set, leading to a slow growth of the set over time.
- **Fix:** Implemented safe pruning in `update_progress` and `late_update` to ensure IDs are discarded from the set when the source is removed or completed.
- **Evidence:** `anura/widgets/language_row.py` lines 96, 105.

## [NEW-011] Validators: Legitimate IDN Rejection
- **Severity:** MEDIUM
- **Status:** FIXED
- **Area:** Security / Usability
- **Description:** The homograph defense blocked ANY label mixing ASCII and non-ASCII, preventing legitimate domains like `münchen.de`.
- **Fix:** Refined the validation to allow **Latin-1 Supplement** characters (0xA0-0xFF) to be mixed with ASCII, while still blocking high-risk mixed scripts (Cyrillic, Greek).
- **Evidence:** `anura/utils/validators.py` line 112.

## [NEW-012] ScreenshotService: User TESSERACT_CMD Ignored
- **Severity:** MEDIUM
- **Status:** FIXED
- **Area:** Configuration
- **Description:** `_configure_tesseract_path` unconditionally cleared `TESSERACT_CMD` in non-Flatpak environments, ignoring user overrides.
- **Fix:** Modified the logic to only clear the variable if it matches the known Flatpak path, preserving user-defined environment overrides.
- **Evidence:** `anura/services/screenshot_service.py` line 199.

## [NEW-013] ExtractedPage: Dead UI State 'cancel'
- **Severity:** LOW
- **Status:** FIXED
- **Area:** UI/UX
- **Description:** The `listen_stack` contained a "cancel" page that was never used by the Python controller.
- **Fix:** Removed the dead "cancel" page from the Blueprint UI and updated the Python class to remove the unused template child.
- **Evidence:** `data/ui/extracted_page.blp` and `anura/widgets/extracted_page.py`.

## [NEW-014] StructuralReconstructor: Incompatible Type Assignment
- **Severity:** LOW
- **Status:** FIXED
- **Area:** Stability / Lint
- **Description:** Mypy identified a type mismatch where a variable was assigned incompatible types in a loop.
- **Fix:** Corrected type hints and stabilized the assignment logic.
- **Evidence:** `anura/utils/structural_reconstructor.py` line 54.

## [NEW-015] ClipboardService: GObject Source ID Warning
- **Severity:** LOW
- **Status:** FIXED
- **Area:** Stability / Logs
- **Description:** Redundant source removal attempts caused "Source ID not found" warnings on stderr.
- **Fix:** Unified all source removals via a safe `_remove_source` helper that validates existence before removal.
- **Evidence:** `anura/services/clipboard_service.py` line 301.

## [NEW-016] LegacyX11Provider: Screenshot Timing Race (scrot)
- **Severity:** MEDIUM
- **Status:** FIXED
- **Area:** Fallback Screenshot / Reliability
- **Description:** `scrot` fallback failed on slow filesystems because the 1s polling timeout was too aggressive.
- **Fix:** Increased polling duration to **5 seconds** (50 retries) and added diagnostic logging of file status on failure.
- **Evidence:** `anura/services/screenshot/legacy_provider.py` line 28.

---

## Technical Insights
1. **GObject Property Synchronization:** Using public GObject properties for backend state (like `current_task_id`) provides a much more robust interlock for UI controllers than reaching into private attributes.
2. **Task Isolation for Pooling:** Shared directories are a liability in multi-threaded/multi-process OCR environments. Moving to UUID-based subdirectories eliminates race conditions without requiring complex IPC locking.
3. **IDN Security vs. Usability:** Whitelisting safe Unicode ranges (like Latin-1) is essential for European users. Security logic must be granular enough to distinguish between "accented Latin" and "confusable scripts" (Cyrillic/Greek).
4. **Filesystem Latency in Flatpak:** Fallback tools like `scrot` can suffer from significant disk flush delays within sandboxes. Generous polling (5s+) is required to ensure reliability across varied host hardware.

---
**Audit and Remediation by Jules (AI Engineering Lead)**
**Date:** June 3, 2026
