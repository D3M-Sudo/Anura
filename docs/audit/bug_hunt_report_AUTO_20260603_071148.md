# Anura Bug Hunt Report - AUTO - 20260603_071148

## Overview
This report documents the findings of an automated systematic bug hunt in the Anura codebase, following the "Bug Hunter" methodology.

## Phase 1: Regression Testing (Existing Fixes BUG-1 to BUG-6)

| Bug ID | Description | Status | Evidence |
| :--- | :--- | :--- | :--- |
| **BUG-1** | TTS: play/pause button icon never updates | **FIXED** | `anura/widgets/extracted_page.py` calls `_on_paused(None, False)` in `update_tts_state` when `playing=True`. |
| **BUG-2** | DnD OCR: fails silently on first attempt | **FIXED** | `AtomicTaskManager.is_cancelled` checks `_isolated_cancellation_map` first. `DndController` calls `decode_image` directly. |
| **BUG-3a** | present() / get_active_window() timing race | **FIXED** | `OcrController._on_shot_error` uses `GLib.idle_add` for signal emission. |
| **BUG-3b** | notification_service non-dismissible | **FIXED** | `org.freedesktop.Notifications` added to Flatpak manifest finish-args. |
| **BUG-4B** | screenshot timeout implementation | **FIXED** | `AnuraWindow._on_screenshot_timeout` calls `backend.cancel()`. |
| **BUG-5** | cancelled tasks logged as ERROR | **FIXED** | `FilterChain.apply` propagates `InterruptedError` silently. |
| **BUG-6** | Source ID not found warnings | **FIXED** | `ClipboardService._remove_source` helper uses `find_source_by_id`. |

---

## Phase 2: New Discoveries

### [BUG-AUTO-01] LegacyX11Provider: Orphan processes on cancellation
- **Priority:** High
- **Reproduction:**
    1. Run Anura on X11 without a working Portal backend (so it uses `scrot`).
    2. Trigger a screenshot.
    3. Cancel the screenshot (e.g., via timeout or UI button) before selecting a region.
    4. Check running processes: `pgrep scrot`.
- **Evidence:** `anura/services/screenshot/legacy_provider.py`'s `cancel()` method cancels the `Gio.Cancellable` but does not terminate the `self._proc` (Gio.Subprocess).
- **Hypothesis:** The `scrot` process continues to run in the background, potentially holding X11 grabs or wasting resources.
- **Test dell'Ipotesi:** Spawning a dummy subprocess in a controlled environment and calling `cancellable.cancel()` without `proc.force_exit()` confirms the process survives as an orphan.
- **Root Cause:** Missing `self._proc.force_exit()` call in the cancellation logic.
- **Fix Suggerito:**
    ```python
    def cancel(self) -> None:
        with self._lock:
            if self._proc:
                self._proc.force_exit()
            if self._cancellable:
                self._cancellable.cancel()
    ```
- **Strategia di Prevenzione:** Always ensure `Gio.Subprocess` objects are explicitly terminated when their associated `Cancellable` is triggered.

### [BUG-AUTO-02] OcrController: Broken task-aware navigation
- **Priority:** Medium
- **Reproduction:**
    1. Start a long OCR task.
    2. Immediately start another one.
- **Evidence:** `anura/controllers/ocr_controller.py` line 103: `_current_id = getattr(self._window.backend, "_current_task_id", None)`. The `backend` (`ScreenshotService`) does not have a `_current_task_id` attribute.
- **Hypothesis:** Navigation occurs even for cancelled/stale tasks because `_current_id` is always `None`, bypassing the check in `_navigate_to_extracted_page`.
- **Test dell'Ipotesi:** Manually setting a task as cancelled in `AtomicTaskManager` and triggering `_navigate_to_extracted_page` shows it still navigates because it can't find the comparison ID.
- **Root Cause:** Incorrect attribute access on the wrong service object. The task ID is managed by `AtomicTaskManager`, not `ScreenshotService`.
- **Fix Suggerito:** The `decoded` signal should be updated to include the `task_id`, and `OcrController` should use that ID for validation.
- **Strategia di Prevenzione:** Use explicit signal parameters instead of attempting to read private state from other services.

### [BUG-AUTO-03] ClipboardService/LanguageRow: Raw source removal warnings
- **Priority:** Low
- **Reproduction:** Rapidly trigger clipboard pastes or download multiple languages simultaneously.
- **Evidence:**
    - `anura/services/clipboard_service.py:244` calls `GLib.source_remove(old_timeout_id)` directly.
    - `anura/widgets/language_row.py:95` calls `GLib.source_remove(self._progress_idle_id)` directly.
- **Hypothesis:** "Source ID not found" warnings appear on stderr when sources fire exactly when being removed.
- **Test dell'Ipotesi:** Forcing a source to fire immediately before calling `source_remove` in a tight loop reproduces the GLib warning.
- **Root Cause:** Regressive use of raw `GLib.source_remove()` instead of the defensive check pattern established in BUG-6.
- **Fix Suggerito:** Use a helper similar to `ClipboardService._remove_source` that checks `ctx.find_source_by_id(timeout_id)` first.
- **Strategia di Prevenzione:** Centralize GLib source management in a base class or utility.

### [BUG-AUTO-04] LanguageRow: GObject signal leak
- **Priority:** Medium
- **Reproduction:** Open and close the Preferences dialog (or wherever LanguageRow is used) many times.
- **Evidence:** `anura/widgets/language_row.py` does not inherit from `SignalManagerMixin` and manually connects to `LanguageManager` signals in `__init__`.
- **Hypothesis:** If the widget is destroyed without `do_destroy` being called by the lifecycle manager, signal connections to the `LanguageManager` singleton persist, leaking memory and potentially triggering callbacks on dead widgets.
- **Test dell'Ipotesi:** Monitoring `LanguageManager` signal handler counts after creating and destroying `LanguageRow` objects without calling `do_destroy` (or missing Mixin auto-teardown) confirms a linear increase in handlers.
- **Root Cause:** Inconsistent use of `SignalManagerMixin` for long-lived signal connections.
- **Fix Suggerito:** Refactor `LanguageRow` to use `SignalManagerMixin` and `connect_tracked`.
- **Strategia di Prevenzione:** Enforce `SignalManagerMixin` usage for all widgets connecting to singleton services.

---

## Phase 3: Environment & Manifest Audit

### Flatpak Permissions
- **Status:** PASS
- **Details:** Manifest correctly includes `--talk-name=org.freedesktop.Notifications`, `--socket=x11`, and `--socket=wayland`.

### EXDEV Handling
- **Status:** PASS
- **Details:** `LanguageManager` correctly implements `shutil.copy2` fallback when `os.link` fails due to cross-device boundaries.

---

## Conclusion
The Anura codebase remains stable with respect to previous bugs, but new architectural inconsistencies in process management and signal tracking have been identified. Priority should be given to fixing the `scrot` orphan process issue and the broken task-aware navigation.
