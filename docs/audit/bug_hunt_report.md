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
#### 1. Reproduce the Bug
- Call `AtomicTaskManager.shutdown()` then later call `execute()`.
#### 2. Gather Evidence
- `shutdown()` sets `self._executor = None` and calls `shutdown(wait=False)`.
- `_get_executor()` lazily recreates it if called again.
- If tasks are active during shutdown, the manager thread for the old executor persists until the task finishes, but since the reference is lost, repeated cycles could accumulate "zombie" manager threads.
#### 3. Form a Hypothesis
- Repeatedly triggering OCR and shutting down the app/service might leave orphaned `AnuraAtomicWorker` threads.
#### 4. Test the Hypothesis
- Log thread count during repeated shutdown/init cycles.
#### 5. Find Root Cause
- `ThreadPoolExecutor.shutdown(wait=False)` allows the executor to close, but doesn't wait for threads to finish.
#### 6. Suggested Fix
- Use a more robust lifecycle for the singleton or ensure threads are reaped.
#### 7. Prevention Strategy
- Monitor thread count in integration tests.

### [NEW-002] ExtractedPage: UI State inconsistency on generation error
#### 1. Reproduce the Bug
- Trigger TTS generation and induce an error (e.g., disconnect network).
#### 2. Gather Evidence
- `_on_generate_error` calls `_set_spinner_active(False)` then `swap_controls(False)`.
- `_set_spinner_active(False)` stops the spinner but leaves the stack child as "spinner".
- `swap_controls(False)` has a guard: `if current_child != "spinner": self.listen_stack.set_visible_child_name("button")`.
#### 3. Form a Hypothesis
- The stack will remain stuck on the "spinner" child (now stopped) even after an error, because `swap_controls` refuses to switch away from it.
#### 4. Test the Hypothesis
- Inspect code in `anura/widgets/extracted_page.py` lines 320, 360, 473.
#### 5. Find Root Cause
- Circular logic guard in `swap_controls` prevents resetting the stack from "spinner" to "button" when called with `state=False`.
#### 6. Suggested Fix
- `_on_generate_error` should use a more forceful reset or `swap_controls` should allow "spinner" -> "button" transitions on stop.
#### 7. Prevention Strategy
- Add a test case for TTS error UI state.

### [NEW-003] OcrController: Race condition in `_on_shot_done` navigation
#### 1. Reproduce the Bug
- Take two screenshots in rapid succession.
#### 2. Gather Evidence
- `_on_shot_done` unconditionally calls `GLib.idle_add(self._navigate_to_extracted_page)`.
#### 3. Form a Hypothesis
- If a second screenshot is initiated while the first is still navigating, the UI might flicker or focus might jump unexpectedly.
#### 4. Test the Hypothesis
- Stress test the capture button.
#### 5. Find Root Cause
- Lack of task ID validation in the navigation callback.
#### 6. Suggested Fix
- Verify that the task ID being navigated for is still the current active task.
#### 7. Prevention Strategy
- UI state locking during transitions.

### [NEW-004] LanguageManager: Link failure on cross-device partitions
#### 1. Reproduce the Bug
- Run Anura with `XDG_CACHE_HOME` and `XDG_DATA_HOME` on different filesystems.
#### 2. Gather Evidence
- `get_tesseract_config` uses `os.link` which fails with `EXDEV` across partitions.
#### 3. Form a Hypothesis
- While there is a fallback to `shutil.copy2`, trying `os.link` every time is inefficient and noisy.
#### 4. Test the Hypothesis
- Simulate `OSError: [Errno 18] Invalid cross-device link`.
#### 5. Find Root Cause
- Hard links cannot cross filesystem boundaries.
#### 6. Suggested Fix
- Cache the failure or use `shutil.copy2` directly if partitions differ.
#### 7. Prevention Strategy
- Cross-partition test environment.

### [NEW-005] ExtractedPage: Architectural inconsistency and manual cleanup
#### 1. Reproduce the Bug
- Audit `anura/widgets/extracted_page.py`.
#### 2. Gather Evidence
- Unlike `WelcomePage` and `AnuraWindow`, `ExtractedPage` does NOT inherit from `SignalManagerMixin`.
- It performs manual signal disconnection in `do_dispose`.
#### 3. Form a Hypothesis
- It might miss some signal disconnections if they are added using `connect_tracked` (which it doesn't use yet, but might if refactored).
#### 4. Test the Hypothesis
- Check for leaked signal handlers after multiple page navigations.
#### 5. Find Root Cause
- Partial adoption of the new `SignalManagerMixin` architecture.
#### 6. Suggested Fix
- Refactor `ExtractedPage` to use `SignalManagerMixin` and `connect_tracked`.
#### 7. Prevention Strategy
- Linter rule or base class enforcement for UI components.

### [NEW-006] LanguageRow: Potential flooding of main loop in `update_progress`
#### 1. Reproduce the Bug
- Download a large language model.
#### 2. Gather Evidence
- `update_progress` (line 92) calls `GLib.idle_add(self.late_update, ...)` for every progress update emitted by `LanguageManager`.
- `LanguageManager.download_begin` throttles updates to 10/sec, but if multiple rows are active, this still adds up.
#### 3. Form a Hypothesis
- While throttled, the unconditional `idle_add` might lead to many pending callbacks if the main loop is busy.
#### 4. Test the Hypothesis
- Monitor idle queue size during multiple downloads.
#### 5. Find Root Cause
- No check if an idle update is already pending for that row.
#### 6. Suggested Fix
- Use a single tracked idle ID per row for progress updates.
#### 7. Prevention Strategy
- Use `Debouncer` or `Throttler` utilities for UI updates.
