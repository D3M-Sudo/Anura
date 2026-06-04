# ANURA — Static Analysis Report
Date: 2026-06-04
Branch: jules-17758675021464600266-4e3b1606
Tools: vulture 2.16, radon 6.0.1, bandit 1.9.4, pylint 4.0.5

## Executive Summary
- Total confirmed issues: 19
- High priority: 2 | Medium: 16 | Low: 1
- False positives excluded: ~100 (GObject overrides, Signal handlers, Magic methods, UI bindings)

## Section 1 — Dead Code (vulture)
| File | Symbol | Type | Confidence | Notes |
| :--- | :--- | :--- | :--- | :--- |
| anura/core/dialogs.py:18 | `release_notes` | variable | 100% | Function argument in `show_about` is never used. |

## Section 2 — High Complexity Functions (radon cc)
| File | Function | Score | Grade | Reason |
| :--- | :--- | :--- | :--- | :--- |
| anura/utils/validators.py | `is_safe_url_string` | 35 | E | Monolithic homograph detection logic with nested loops and script-specific checks. |
| anura/services/screenshot_service.py | `run_ocr_pipeline` | 23 | D | Large pipeline handling env setup, transactional I/O, and service orchestration. |
| anura/utils/structural_reconstructor.py | `reconstruct` | 18 | C | Spatial analysis for paragraph reconstruction based on word coordinates. |
| anura/services/language_manager.py | `get_tesseract_config` | 17 | C | Multi-language pooling and directory validation logic. |
| anura/services/screenshot/legacy_provider.py | `_on_finish` | 15 | C | Complex process exit handling with polling for filesystem flush. |
| anura/services/language_manager.py | `get_downloaded_codes` | 15 | C | Filtering and validating local traineddata files. |
| anura/services/language_manager.py | `download_begin` | 15 | C | Locking and task initialization for downloads. |
| anura/services/screenshot_service.py | `_try_ocr_extraction` | 14 | C | Retry logic and exception handling for OCR engine calls. |
| anura/utils/image_filters.py | `FilterChain.apply` | 13 | C | Execution pipeline for modular image filters. |
| anura/utils/image_filters.py | `AdaptiveThresholdFilter.apply` | 12 | C | Mathematical logic for adaptive thresholding via PIL. |
| anura/widgets/extracted_page.py | `update_tts_state` | 13 | C | UI state management for multiple playback control widgets. |
| anura/transformers/models.py | `OcrResult.add_linebreaks` | 12 | C | Geometric coordinate logic for semantic layout reconstruction. |
| anura/services/clipboard_service.py | `_on_uri_list_bytes` | 11 | C | Parsing URI lists and GFile conversion logic. |
| anura/services/tts.py | `cleanup` | 11 | C | Disposal logic for GStreamer buses and signal connections. |
| anura/services/language_manager.py | `init_tessdata` | 11 | C | Initial directory setup and system model discovery. |
| anura/utils/portal_advice.py | `detect_portal_advice` | 11 | C | Heuristics for providing desktop-specific installation advice. |
| anura/utils/validators.py | `validate_image_resource` | 11 | C | Security checks for file accessibility and MIME types. |

## Section 3 — Low Maintainability Modules (radon mi)
*No modules found with MI Grade C or worse (all modules scored Grade A).*

## Section 4 — Security Issues (bandit)
*No security issues with Medium/High severity and confidence identified in the source tree.*

## Section 5 — Duplicate Code (pylint)
*No duplicated blocks exceeding the 8-line similarity threshold identified within `anura/`.*

## Section 6 — High Priority Cross-References
*No intersections found between Dead Code, Complexity, and Security analysis (i.e., no dead code in complex modules).*

## Section 7 — False Positives Excluded
- **GObject Virtual Overrides**: ~12 methods (e.g., `do_destroy`, `do_activate`, `do_startup`) excluded as they are invoked by the GTK runtime.
- **Signal Infrastructure**: ~26 symbols from `__gsignals__` definitions and their associated handlers.
- **UI Bindings**: ~60 symbols representing `Gtk.Template.Child` widget IDs and callback handlers (e.g., `_on_download`) referenced in `.blp`/`.ui` files.
- **Python Magic Methods**: Standard methods like `__init__`, `__repr__` were automatically excluded.

## Section 8 — Recommended Action Order
1. **Refactor `is_safe_url_string` (High Impact)**: Decompose the monolithic homograph detection logic into smaller, script-specific validator functions (e.g., `_is_latin_supplement_safe`, `_is_pure_idn`).
2. **Refactor `run_ocr_pipeline` (High Impact)**: Extract the environment variable management (TMPDIR/TEMP/TMP) and the transactional temporary directory cleanup into a dedicated context manager.
3. **Dead Code Cleanup (Low Impact)**: Remove the unused `release_notes` argument from `DialogManager.show_about` in `anura/core/dialogs.py`.
4. **Monitor Geometric Logic**: Complexity in `StructuralReconstructor` and `OcrResult.add_linebreaks` is inherent to spatial analysis, but should be monitored for further growth to prevent maintainability degradation.

## Section 9 — Appendix: Findings in Tests
- **tests/test_extracted_page_reflow.py:13**: `test_extracted_page_ui_reflow_properties` (Grade D, Score 28). This test contains extensive XML parsing and assertions to verify UI reflow properties. High complexity is acceptable for exhaustive verification.
- **tests/test_language_row_logic.py:77**: `_collect_add_pattern_nodes` (Grade C, Score 17). AST walking logic for finding pattern nodes within the test suite.
