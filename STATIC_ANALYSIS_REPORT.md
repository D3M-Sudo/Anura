# ANURA — Static Analysis Report

**Date:** 2026-06-05
**Branch:** jules-16576121774950604805-45df87ea
**Tools:** vulture 2.16, radon 6.0.1, bandit 1.9.4, pylint 4.0.5

## Executive Summary

- **Total confirmed issues:** 19
- **High priority:** 0
- **Medium:** 1
- **Low:** 18
- **False positives excluded:** 8 (Signal handlers, GLib/GTK callbacks)

---

## Section 1 — Dead Code (vulture)

| File | Symbol | Type | Confidence | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `anura/core/dialogs.py:18` | `release_notes` | variable | 100% | Unused parameter in `show_about` method. Callers in `main.py` provide this argument unnecessarily. |

---

## Section 2 — High Complexity Functions (radon cc)

| File | Function | Score | Grade | Reason |
| :--- | :--- | :--- | :--- | :--- |
| `anura/utils/validators.py:92` | `is_safe_url_string` | 35 | E | Contains dense nested logic for homograph detection, Unicode range validation, and mixed-script label analysis. |
| `anura/services/screenshot_service.py:48` | `run_ocr_pipeline` | 23 | D | Monolithic function managing the entire isolated OCR lifecycle: transactional I/O, image enhancement, Tesseract execution, and structural reconstruction. |
| `anura/utils/structural_reconstructor.py:26` | `StructuralReconstructor.reconstruct` | 18 | C | Implements spatial analysis for grouping words into lines and paragraphs with cooperative cancellation support. |
| `anura/services/language_manager.py:637` | `get_tesseract_config` | 17 | C | Manages complex environment configuration and symbolic pooling for multi-language Tesseract support. |
| `anura/services/language_manager.py:322` | `LanguageManager.get_downloaded_codes` | 15 | C | Complex filtering and validation of local model files across multiple directories. |
| `anura/services/language_manager.py:444` | `LanguageManager.download_begin` | 15 | C | Coordinates download lifecycle, session management, and state transitions. |
| `anura/services/screenshot/legacy_provider.py:146` | `LegacyX11Provider._on_finish` | 15 | C | Post-capture logic for `scrot` including error handling, signal emission, and file cleanup. |
| `anura/services/screenshot_service.py:503` | `ScreenshotService._try_ocr_extraction` | 14 | C | Orchestrates multi-stage extraction with fallback mechanisms. |
| `anura/utils/image_filters.py:191` | `FilterChain.apply` | 13 | C | Iterative application of the filter chain with mode-specific handling. |
| `anura/widgets/extracted_page.py:231` | `ExtractedPage.update_tts_state` | 13 | C | Handles complex UI state transitions for the integrated TTS player. |
| `anura/transformers/models.py:62` | `OcrResult.add_linebreaks` | 12 | C | Geometric logic for inserting artificial linebreaks based on layout analysis. |
| `anura/utils/image_filters.py:131` | `AdaptiveThresholdFilter.apply` | 12 | C | Core mathematical logic for image thresholding using Pillow. |
| `anura/services/clipboard_service.py:462` | `ClipboardService._on_uri_list_bytes` | 11 | C | Decodes and parses RFC 2483 URI list payloads from the clipboard. |
| `anura/services/tts.py:579` | `TTSService.cleanup` | 11 | C | Thread-safe cleanup of GStreamer resources and temporary files. |
| `anura/services/language_manager.py:260` | `LanguageManager.init_tessdata` | 11 | C | Directory initialization, cleanup of stale artifacts, and path auditing. |
| `anura/utils/portal_advice.py:61` | `detect_portal_advice` | 11 | C | Set of heuristics for detecting desktop environments and recommending specific portal backends. |
| `anura/utils/validators.py:209` | `validate_image_resource` | 11 | C | Validates image existence, dimensions, and file size against security constraints. |

---

## Section 3 — Low Maintainability Modules (radon mi)

*No modules found with Maintainability Index grade C or worse (MI < 65).*

---

## Section 4 — Security Issues (bandit)

*No Medium or High severity security issues identified.*

---

## Section 5 — Duplicate Code (pylint)

*No duplicate code blocks of 8 lines or more identified.*

---

## Section 6 — High Priority Cross-References

*None. No issues met the cross-reference criteria (e.g., Bandit finding in a Radon high-complexity function).*

---

## Section 7 — False Positives Excluded

| File | Symbol | Type | Reason |
| :--- | :--- | :--- | :--- |
| `anura/core/silent_runner.py:33` | `frame` | variable | Unused parameter in standard signal handler `on_signal(signum, frame)`. |
| `anura/widgets/language_row.py:90` | `sender` | variable | Unused parameter in GObject signal callback (required by signature). |
| `anura/widgets/language_row.py:147` | `sender` | variable | Unused parameter in GObject signal callback (required by signature). |
| `anura/widgets/preferences_languages_page.py:92` | `factory` | variable | Unused parameter in `Gtk.SignalListItemFactory` callback. |
| `anura/widgets/preferences_languages_page.py:96` | `factory` | variable | Unused parameter in `Gtk.SignalListItemFactory` callback. |
| `anura/widgets/preferences_languages_page.py:102` | `sender` | variable | Unused parameter in GTK widget signal handler. |
| `anura/widgets/welcome_page.py:97` | `y` | variable | Unused parameter in `Gtk.DropTargetAsync` callback. |
| `anura/widgets/welcome_page.py:118` | `y` | variable | Unused parameter in `Gtk.DropTargetAsync` callback. |

---

## Section 8 — Recommended Action Order

1. **Refactor `is_safe_url_string` (`anura/utils/validators.py`)**: Split the homograph and script detection logic into private helper functions (e.g., `_verify_homographs`, `_verify_scripts`). This will significantly reduce the cyclomatic complexity of this security-critical function.
2. **Refactor `run_ocr_pipeline` (`anura/services/screenshot_service.py`)**: Decompose the 200-line isolated pipeline into a dedicated `OcrPipeline` class or multiple helper functions for each stage (Enhancement, OCR, Reconstruction, Magic Processing).
3. **Refactor `StructuralReconstructor.reconstruct`**: Extract the paragraph merging logic (`_should_merge` is already separate, but the loop logic is dense) into smaller units.
4. **Clean up Dead Code**: Remove the unused `release_notes` parameter from `DialogManager.show_about` in `anura/core/dialogs.py` and update the call site in `anura/main.py`.
5. **Simplify `LanguageManager`**: Methods like `get_downloaded_codes` and `download_begin` should delegate more responsibility to smaller private methods to handle the directory traversal and session state management respectively.
