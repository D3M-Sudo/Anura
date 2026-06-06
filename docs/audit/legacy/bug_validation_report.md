# Bug Validation Report — Current Code State

> **Last verified:** 2026-03-06 — All fixes confirmed present in the current codebase.

## Executive Summary

| Bug | Verdict (Report) | Current Code Status | Found in Source |
|-----|------------------|--------------------|-----------------|
| BUG-1  TTS Icon never updates | CONFIRMED | **FIXED** ✅ | `extracted_page.py:231-258` |
| BUG-2  DnD OCR always fails first attempt | CONFIRMED | **FIXED** ✅ | `atomic_task_manager.py:285-304` |
| BUG-3a Notification race (present/get_active_window) | CONFIRMED | **FIXED** ✅ | `ocr_controller.py:140-146` |
| BUG-3b Notification stuck (Flatpak permissions) | CONFIRMED | **FIXED** ✅ | `io.github.d3msudo.anura.json:20` |
| BUG-3c fallback_provider check always wrong | REFUTED | — | Logic was correct |
| BUG-4A Orphan provider code never integrated | REFUTED | — | Providers are integrated |
| BUG-4B Screenshot timeout interferes with scrot | CONFIRMED | **FIXED** ✅ | `window.py:164-173` |
| BUG-5 Cancelled tasks logged as ERROR | CONFIRMED | **FIXED** ✅ | `image_filters.py:220-225` |
| BUG-6 Clipboard Source ID not found warning | CONFIRMED | **FIXED** ✅ | `clipboard_service.py:300-331` |

---

## BUG-1 — TTS: play/pause button icon never updates

### Hypothesis
`update_tts_state(playing=True)` is called by `TtsController` on resume. It calls `swap_controls("playing")` which sets `listen_stack` to the `"pause"` child — correct. However, it does **not** reset the icon of `listen_pause_btn` back to `media-playback-pause-symbolic`. The button retains `media-playback-start-symbolic` (▶) set during the previous pause, so the icon is permanently wrong after the first pause/resume cycle.

### Verdict
CONFIRMED

### Current Code State — **FIXED** ✅

The `update_tts_state()` method was refactored to use a string-based `state` parameter instead of separate booleans. The `"playing"` state (line 239-246) now **explicitly sets the icon** to `"media-playback-pause-symbolic"`:

```python
# anura/widgets/extracted_page.py, lines 239-246
elif state == "playing":
    self.swap_controls(True)
    if self.listen_stack:
        self.listen_stack.set_visible_child_name("pause")
    if self.listen_spinner:
        self.listen_spinner.stop()
    if self.listen_pause_btn:
        self.listen_pause_btn.set_icon_name("media-playback-pause-symbolic")
```

### Fix Scope
MINIMAL — Icon reset added to the `"playing"` state branch.

---

## BUG-2 — DnD OCR: always fails silently on first attempt

### Hypothesis
`AtomicTaskManager.is_cancelled()` returns `True` immediately in the **spawned child process**, causing `image_filters.py` to raise `InterruptedError` before any processing begins.

The child process is created via `multiprocessing` with `spawn` context. It gets a fresh `AtomicTaskManager` singleton where `_current_task_id = None`. The `is_cancelled(task_id)` method falls through to the check `task_id != self._current_task_id` → `task_id != None` → always `True` → immediate cancellation.

### Verdict
CONFIRMED

### Current Code State — **FIXED** ✅

`is_cancelled()` was updated (lines 285-304) to check the `_isolated_cancellation_map` **first**. If the task ID is present in the shared map, its value directly determines the cancellation state, short-circuiting before the `_current_task_id` comparison:

```python
# anura/core/atomic_task_manager.py, lines 289-296
if (
    hasattr(self, "_isolated_cancellation_map")
    and self._isolated_cancellation_map is not None
    and task_id in self._isolated_cancellation_map
):
    return self._isolated_cancellation_map.get(task_id, False)
```

### Fix Scope
MODERATE — Logic restructured to prefer shared map over local state in worker processes.

---

## BUG-3 — Screenshot error: notification stuck, not closeable, semi-freezes DE

### BUG-3a — `present()` / `get_active_window()` timing race

### Hypothesis
In `OcrController._on_shot_error()` (called via `GLib.idle_add`), `self._window.present()` is called immediately followed by a **synchronous** `self.emit("error-occurred", message)`. The `emit()` call reaches `main._on_error_occurred()` in the same GTK main loop frame, before the window manager (LXQt/Openbox) has processed the `present()` and granted keyboard focus. Therefore `get_active_window()` returns `None`, and the code falls into the `notification_service.show_notification()` branch instead of `win.show_toast()`.

### Verdict
CONFIRMED

### Current Code State — **FIXED** ✅

The `_on_shot_error` method (lines 140-146) now wraps the signal emission in `GLib.idle_add`, deferring it to allow the window manager to process the focus change:

```python
# anura/controllers/ocr_controller.py, lines 140-146
def _on_shot_error(self, _sender: GObject.GObject, message: str) -> None:
    """Handle screenshot capture errors."""
    if message:
        GLib.idle_add(self.emit, "error-occurred", message)
```

### Fix Scope
MINIMAL — `GLib.idle_add` wrapper added.

---

### BUG-3b — `notification_service` sends OS notification that cannot be dismissed

### Hypothesis
When `show_notification()` is called, it attempts `Xdp.Portal.add_notification()` first. In LXQt, this call either:
- Succeeds at the D-Bus level but `remove_notification()` fails silently because `lxqt-notificationd` does not fully implement `org.freedesktop.portal.Notification`, OR
- Fails silently and falls through to `libnotify`, which is blocked by the Flatpak sandbox because `--talk-name=org.freedesktop.Notifications` is absent from `finish-args`.

### Verdict
CONFIRMED

### Current Code State — **FIXED** ✅

The Flatpak manifest (line 20) now includes the required D-Bus permission:

```json
"--talk-name=org.freedesktop.Notifications",
```

### Fix Scope
MINIMAL — One-line addition to Flatpak `finish-args`.

---

### BUG-3c — `_on_error_occurred` check for `fallback_provider` is always wrong

### Hypothesis
In `main.py`, `_on_error_occurred()` checks:
```python
not getattr(self.backend, "fallback_provider", None)
```
But `ScreenshotService` has **no attribute** named `fallback_provider` on the instance.

### Verdict
**REFUTED**

### Evidence
The attribute `fallback_provider` **is** correctly assigned in `ScreenshotService.__init__` at line 339:
```python
self.fallback_provider = ScreenshotProviderFactory.get_fallback_provider()
```
The condition in `main.py` is logically sound. The observed fatal dialog behaviour is due to `get_fallback_provider()` returning `None` on Wayland (where scrot is not supported), which is expected.

### Fix Scope
MINIMAL — Error message matching could be more robust, but the logic is correct.

---

## BUG-4 — scrot fallback: exits 0 but produces no output

### BUG-4A — Architecture: orphan provider code never integrated

### Hypothesis
The `testing` branch contains a full provider subsystem (`anura/services/screenshot/portal_provider.py`, `legacy_provider.py`, `factory.py`) that was written but **never integrated into `ScreenshotService`**.

### Verdict
**REFUTED**

### Evidence
`ScreenshotService` explicitly imports and instantiates the factory:
```python
# anura/services/screenshot_service.py, lines 338-339
self.provider = ScreenshotProviderFactory.get_provider()
self.fallback_provider = ScreenshotProviderFactory.get_fallback_provider()
```

### Fix Scope
NONE — No fix required.

---

### BUG-4B — `_on_screenshot_timeout` now implemented, breaks scrot -s

### Hypothesis
In `testing`, `_on_screenshot_timeout` **is fully implemented**: it calls `self.present()` after 30s, restoring the window. Scrot is still running when the 30s timeout fires. The window reappears on top of scrot's crosshair cursor, interfering with X11 area selection. Additionally, it does **not** cancel the in-progress scrot process, leaving `_is_capturing = True`.

### Verdict
CONFIRMED

### Current Code State — **FIXED** ✅

`_on_screenshot_timeout` (lines 164-173) now calls `self.backend.cancel()` to terminate the active capture and reset state before restoring the window:

```python
# anura/window.py, lines 164-173
def _on_screenshot_timeout(self) -> bool:
    """Restore window if portal screenshot doesn't respond within 30s."""
    self._screenshot_timeout_id = None
    # Cancel active capture to prevent UI interference and reset state
    if self.backend:
        self.backend.cancel()
    self.present()
    self.show_toast(_("Screenshot timed out. Please try again."))
    logger.warning("Anura: Screenshot portal timeout — restoring window.")
    return GLib.SOURCE_REMOVE
```

### Fix Scope
MODERATE — Added `self.backend.cancel()` call before window restoration.

---

## BUG-5 — `image_filters.py`: cancelled tasks logged as ERROR

### Hypothesis
In `anura/utils/image_filters.py` around line 221, intentionally cancelled tasks (cancelled via `AtomicTaskManager` when a newer task supersedes them) are logged with `logger.error()`. This produces misleading `ERROR` entries in the log for normal, expected behaviour.

### Verdict
CONFIRMED

### Current Code State — **FIXED** ✅

An explicit `except InterruptedError` handler (lines 220-225) was added **before** the generic catch-all, allowing cancellations to propagate silently:

```python
# anura/utils/image_filters.py, lines 220-225
except InterruptedError:
    # Silently propagate cancellation
    for img in intermediates:
        with contextlib.suppress(AttributeError, RuntimeError):
            img.close()
    raise
except (AttributeError, RuntimeError, TypeError, ValueError, OSError) as e:
    logger.error(f"Filter chain failed: {e}")
```

### Fix Scope
MINIMAL — Single `except InterruptedError: raise` block added.

---

## BUG-6 — `clipboard_service.py`: `Warning: Source ID not found` on stderr

### Hypothesis
`GLib.source_remove()` emits a C-level `g_warning()` to stderr **before** raising a Python exception. The existing `try/except Exception` blocks suppress the Python exception but cannot intercept the C-level warning. The stale source ID originates from a race window: GLib auto-removes a one-shot timeout source when it fires, but `_clipboard_timeout_id` still holds the old ID.

A secondary leak: `_fallback_to_texture_read()` and `_fallback_to_uri_list_read()` overwrite `_clipboard_timeout_id` with a new `GLib.timeout_add_seconds()` return value without first calling `_clear_active_timeout()`.

### Verdict
CONFIRMED

### Current Code State — **FIXED** ✅

Two fixes applied:

1. **`_remove_source()`** (lines 300-311) — Checks `ctx.find_source_by_id()` before calling `GLib.source_remove()`, preventing the C-level warning:
```python
def _remove_source(self, timeout_id: int | None) -> None:
    if timeout_id is not None and timeout_id > 0:
        ctx = GLib.MainContext.default()
        if ctx and ctx.find_source_by_id(timeout_id):
            try:
                GLib.source_remove(timeout_id)
            except (AttributeError, RuntimeError, TypeError, GLib.Error):
                pass
```

2. **`_clear_active_timeout()`** (lines 313-331) — Centralised, lock-safe pattern that atomically captures the timeout ID under `_state_lock` and calls `_remove_source()` **outside** the lock to prevent deadlock with GLib's main-loop lock.

### Fix Scope
MODERATE — New `_remove_source` and `_clear_active_timeout` helper methods implemented.

---

## Summary

All **7 confirmed bugs** from the validation report are now **fixed** in the current codebase. Both **refuted** claims (BUG-3c, BUG-4A) required no changes. No remaining actionable items from the report.