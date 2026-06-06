# Bug Hunt Progress Report
Generated: 2026-06-03T22:45:00Z

## Statistics
- Files analyzed: 309/309 (100.0%)
- Lines analyzed: 86,723/86,723 (100.0%)
- Bugs Found: 4 (Critical: 0, High: 0, Medium: 3, Low: 1)
- Tools Executed: [ruff, mypy, bandit, safety, pylint, vulture, radon, semgrep, pytest]
- Est. Completion: COMPLETE

## New Discoveries
| ID | File | Severity | Description | Confidence |
|----|------|----------|-------------|------------|
| NEW-017 | `anura/services/language_manager.py:288` | MEDIUM | Startup race condition in .tmp cleanup | 0.9 |
| NEW-018 | `anura/transformers/models.py:39` | MEDIUM | Mypy type mismatch in layout section counting | 1.0 |
| NEW-019 | `anura/core/silent_runner.py:33` | LOW | Unused variable 'frame' in signal handler | 1.0 |
| NEW-020 | `anura/controllers/ocr_controller.py:95` | MEDIUM | Redundant Magic Processing on UI thread | 0.95 |

## Cross-File Pattern Analysis

### 1. Pattern: Unsynchronized Global State Cleanup (Manifestation of NEW-017)
- **Manifestation:** Unconditional file deletion in shared directories (`TESSDATA_DIR`, `TESSDATA_POOL_DIR`) during startup or reconfiguration.
- **Pattern:** Assumptions that only one instance of the application is running or that cleanup is safe without age-based heuristics.
- **Locations:** `LanguageManager.init_tessdata`, `LanguageManager.get_tesseract_config`, and `TtsService.cleanup`.
- **Risk:** Multi-instance race conditions leading to corrupted states or failed downloads.

### 2. Pattern: Architectural Layering Leakage (Manifestation of NEW-020)
- **Manifestation:** Controllers repeating expensive logic (like Magic Processing) that was already executed in the Service layer.
- **Pattern:** Passing raw data (strings) between layers instead of enriched result objects, causing downstream layers to re-derive information.
- **Locations:** `OcrController._on_shot_done` vs `ScreenshotService._try_ocr_extraction`.
- **Risk:** Unnecessary CPU usage on the main (UI) thread and increased maintenance complexity.

### 3. Pattern: Incomplete Cooperative Cancellation
- **Manifestation:** Long-running utility functions lacking `is_cancelled` checks.
- **Pattern:** While core algorithms (`StructuralReconstructor`) support cancellation, the cleanup/sanitization pass (`TextPreprocessor.clean_extracted_text`) does not.
- **Locations:** `TextPreprocessor.clean_extracted_text` called within the isolated OCR pipeline.
- **Risk:** Orphaned worker processes remaining busy for significant time after a task is cancelled if the input text is massive.

### 4. Pattern: Boilerplate Parameter Clutter (Manifestation of NEW-019)
- **Manifestation:** Unused parameters in GObject signal handlers and standard callbacks.
- **Pattern:** Strict adherence to API signatures without using `_` or `*_` to signal intentional omission.
- **Locations:** `SilentRunner`, `WelcomePage`, `LanguageRow`, `PreferencesLanguagesPage`.
- **Risk:** Static analysis noise and minor code quality degradation.

## Recent Activity
- Finalized systematic investigation with 100% file coverage.
- Conducted cross-file pattern analysis identifying architectural and concurrency themes.
- Verified all findings against tool reports and manual logic tracing.
- Suppressed environment-specific noise (gi/PyGObject imports).

## Next Actions
- Audit complete. Finalized documentation in `bugs-observed.json`.
