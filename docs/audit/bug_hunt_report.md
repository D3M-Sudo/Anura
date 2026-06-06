# Anura Bug Hunt Report - June 2026

## Overview
This report documents the findings of a systematic bug hunt in the Anura codebase, following the "Bug Hunter" methodology from the Antigravity Awesome Skills library.

## Phase 1: Regression Testing (Existing Fixes BUG-1 to BUG-6)

### [BUG-1] TTS: play/pause button icon never updates
- **Status:** FIXED
- **Evidence:** `anura/widgets/extracted_page.py` lines 416-430. The `update_tts_state` method now explicitly calls `self._on_paused(None, False)` when `playing=True`, which resets the icon to "pause" symbolic.
- **Verdict:** Fix verified in source code.

### [BUG-2] DnD OCR: always fails silently on first attempt
- **Status:** FIXED
- **Evidence:**
    1. `anura/core/atomic_task_manager.py` lines 275-285: `is_cancelled` now prioritizes checking `_isolated_cancellation_map` before checking `_current_task_id`. This prevents child processes (where `_current_task_id` is None) from self-cancelling.
    2. `anura/controllers/dnd_controller.py` line 48: `process_dnd_file_sync` now calls `self._window.backend.decode_image` directly instead of wrapping it in `execute()`, avoiding nested task cancellation.
- **Verdict:** Fix verified in source code.

### [BUG-3a] present() / get_active_window() timing race
- **Status:** FIXED
- **Evidence:** `anura/controllers/ocr_controller.py` line 144: `self.emit("error-occurred", message)` is now wrapped in `GLib.idle_add`.
- **Verdict:** Fix verified in source code.

### [BUG-3b] notification_service sends OS notification that cannot be dismissed
- **Status:** FIXED
- **Evidence:** `flatpak/io.github.d3msudo.anura.json` line 18: `--talk-name=org.freedesktop.Notifications` has been added to `finish-args`.
- **Verdict:** Fix verified in manifest.

### [BUG-3c] _on_error_occurred check for fallback_provider is always wrong
- **Status:** REFUTED (No bug exists)
- **Evidence:** `anura/services/screenshot_service.py` line 339 correctly assigns `self.fallback_provider`. The check in `main.py` line 234 correctly uses `getattr` to check for this attribute.
- **Verdict:** Confirmed behavior is correct.

### [BUG-4B] _on_screenshot_timeout now implemented, breaks scrot -s
- **Status:** FIXED
- **Evidence:** `anura/window.py` line 125: `_on_screenshot_timeout` now calls `self.backend.cancel()` before presenting the window. `ScreenshotService.cancel()` in `anura/services/screenshot_service.py` line 351 correctly calls `cancel()` on providers.
- **Verdict:** Fix verified in source code.

### [BUG-5] image_filters.py: cancelled tasks logged as ERROR
- **Status:** FIXED
- **Evidence:** `anura/utils/image_filters.py` lines 214-218: An explicit `except InterruptedError: raise` block has been added to `FilterChain.apply` to prevent cancellations from being logged as errors.
- **Verdict:** Fix verified in source code.

### [BUG-6] clipboard_service.py: Warning: Source ID not found on stderr
- **Status:** FIXED
- **Evidence:** `anura/services/clipboard_service.py` lines 205-214: `_remove_source` now uses `GLib.MainContext.default().find_source_by_id(timeout_id)` to verify the source exists before attempting to remove it.
- **Verdict:** Fix verified in source code.

---

## Phase 2: New Undiscovered Bugs

### [NEW-001] AtomicTaskManager: Thread executor memory leak on repeated shutdown/init
- **Status:** FIXED
- **Evidence:** `anura/core/atomic_task_manager.py` line 380. `shutdown(wait=True)` is now used for the thread executor.
- **Verdict:** Fix verified in source code.

### [NEW-002] ExtractedPage: UI State inconsistency on generation error
- **Status:** FIXED
- **Evidence:** `anura/widgets/extracted_page.py` line 503. `swap_controls` now unconditionally sets the stack child to "button" on stop.
- **Verdict:** Fix verified in source code.

### [NEW-003] OcrController: Race condition in `_on_shot_done` navigation
- **Status:** FIXED
- **Evidence:** `anura/controllers/ocr_controller.py` lines 112, 177. Navigation now passes and validates the `task_id` against the backend's current task.
- **Verdict:** Fix verified in source code.

### [NEW-004] LanguageManager: Link failure on cross-device partitions
- **Status:** FIXED
- **Evidence:** `anura/services/language_manager.py` line 700. Explicit check for `errno.EXDEV` added to hard-link logic with silent fallback.
- **Verdict:** Fix verified in source code.

### [NEW-005] ExtractedPage: Architectural inconsistency and manual cleanup
- **Status:** FIXED
- **Evidence:** `anura/widgets/extracted_page.py`. Class now inherits from `SignalManagerMixin` and uses `connect_tracked` for all signals. Manual cleanup removed from `do_dispose`.
- **Verdict:** Fix verified in source code.

### [NEW-006] LanguageRow: Potential flooding of main loop in `update_progress`
- **Status:** FIXED
- **Evidence:** `anura/widgets/language_row.py` lines 95-98. Implemented `_progress_idle_id` tracking to throttle redundant UI updates.
- **Verdict:** Fix verified in source code.
