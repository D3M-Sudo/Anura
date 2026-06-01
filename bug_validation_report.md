# Bug Validation Report: Branch `testing`

## BUG-1 — TTS: play/pause button icon never updates

### Hypothesis
`update_tts_state(playing=True)` is called by `TtsController` on resume. It calls `swap_controls("playing")` which sets `listen_stack` to the `"pause"` child — correct. However, it does **not** reset the icon of `listen_pause_btn` back to `media-playback-pause-symbolic`. The button retains `media-playback-start-symbolic` (▶) set during the previous pause, so the icon is permanently wrong after the first pause/resume cycle.

The `_on_paused(None, False)` path (which would reset the icon) is never called for the resume case. It is only called explicitly when `paused=True`.

### Verdict
CONFIRMED

### Evidence
- File: `anura/widgets/extracted_page.py`, lines 416-430
  ```python
    def update_tts_state(self, playing: bool = False, paused: bool = False) -> None:
        """Update the TTS UI state (called from TtsController).

        States:
          playing=True  → stack="pause", controls locked (playback active or resumed)
          paused=True   → stack stays on "pause", icon changes to ▶ (ready to resume)
          (default)     → stack="button" (idle), controls unlocked (stopped/finished)
        """
        if playing:
            # Active playback (initial play OR resume after pause).
            # swap_controls("playing") sets listen_stack → "pause" child.
            self.swap_controls("playing")
        elif paused:
  ```
- File: `anura/widgets/extracted_page.py`, lines 462-474
  ```python
    def swap_controls(self, state: bool | str = False) -> None:
        """Enable or disable interactive controls during TTS playback."""
        # Handle both legacy boolean state and new descriptive string states
        is_playing = state is True or state == "playing"

        if self.grab_btn:
            self.grab_btn.set_sensitive(not is_playing)
        if self.text_copy_btn:
            self.text_copy_btn.set_sensitive(not is_playing)
        if self.listen_stack:
            # Unified stack management: handle both pause/play and spinner states
            if is_playing:
                self.listen_stack.set_visible_child_name("pause")
  ```

### Root Cause (confirmed wording)
When `update_tts_state(playing=True)` is invoked during resume, it calls `swap_controls("playing")`, which correctly switches the `listen_stack` to the `"pause"` child but lacks any logic to reset the icon of `listen_pause_btn`. Since the icon was set to `media-playback-start-symbolic` during the previous pause event, it remains stuck in that state despite playback being active.

### Fix Scope
MINIMAL
Explicitly call `self._on_paused(None, False)` inside the `if playing:` block of `update_tts_state`.

---

## BUG-2 — DnD OCR: always fails silently on first attempt

### Hypothesis
`AtomicTaskManager.is_cancelled()` returns `True` immediately in the **spawned child process**, causing `image_filters.py` to raise `InterruptedError` before any processing begins.

The child process is created via `multiprocessing` with `spawn` context. It gets a fresh `AtomicTaskManager` singleton where `_current_task_id = None`. The `is_cancelled(task_id)` method falls through to the check `task_id != self._current_task_id` → `task_id != None` → always `True` → immediate cancellation.

The `_isolated_cancellation_map` is set correctly via `set_isolated_cancellation_map(shared_map)` and contains `{task_id: False}` — but the code never short-circuits on this before reaching the `_current_task_id` comparison.

### Verdict
CONFIRMED

### Evidence
- File: `anura/core/atomic_task_manager.py`, lines 214-230
  ```python
    def is_cancelled(self, task_id: str) -> bool:
        """Check if a specific task ID has been cancelled or invalidated."""
        # 1. Check shared map for isolated processes
        if (
            hasattr(self, "_isolated_cancellation_map")
            and self._isolated_cancellation_map is not None
            and self._isolated_cancellation_map.get(task_id, False)
        ):
            return True

        # 2. Check local state for threads
        with self._state_lock:
            # If the task_id is not the current one, it's considered cancelled/obsolete
            if task_id != self._current_task_id:
                return True
            # If it is the current one, check the GIO cancellable
            return self._cancellable.is_cancelled() if self._cancellable else True
```
- File: `anura/controllers/dnd_controller.py`, line 48
  ```python
            get_atomic_manager().execute(self._window.backend.decode_image, (lang, file_path))
  ```

### Root Cause (confirmed wording)
The `is_cancelled()` method logic is flawed: it returns `True` (cancelled) if the `task_id` is found in the `_isolated_cancellation_map` with a `True` value, but then proceeds to check `task_id != self._current_task_id`. In spawned worker processes, `_current_task_id` is always `None`, so any valid `task_id` fails this check and returns `True` (cancelled). Additionally, `DndController` wraps a call to `execute_isolated` (inside `decode_image`) within a standard `execute` task; the inner call cancels the outer task immediately.

### Fix Scope
MODERATE
Update `is_cancelled` to return `False` if the ID is found in the shared map with value `False`, and ensure `DndController` uses the backend synchronously or bypasses the nested task.

---

## BUG-3 — Screenshot error: notification stuck, not closeable, semi-freezes DE

### BUG-3a — `present()` / `get_active_window()` timing race

### Hypothesis
In `OcrController._on_shot_error()` (called via `GLib.idle_add`), `self._window.present()` is called immediately followed by a **synchronous** `self.emit("error-occurred", message)`. The `emit()` call reaches `main._on_error_occurred()` in the same GTK main loop frame, before the window manager (LXQt/Openbox) has processed the `present()` and granted keyboard focus. Therefore `get_active_window()` returns `None`, and the code falls into the `notification_service.show_notification()` branch instead of `win.show_toast()`.

### Verdict
CONFIRMED

### Evidence
- File: `anura/controllers/ocr_controller.py`, lines 133-145
  ```python
    def _on_shot_error(self, _sender: GObject.GObject, message: str) -> None:
        """Handle screenshot capture errors."""
...
        if was_screenshot:
            self._window.present()
        self._window.welcome_page.reset_drop_area_state()
        if message:
            self.emit("error-occurred", message)
  ```
- File: `anura/main.py`, line 231
  ```python
    def _on_error_occurred(self, _controller, message: str) -> None:
        win = self.get_active_window()
  ```

### Root Cause (confirmed wording)
`OcrController` emits `error-occurred` synchronously immediately after calling `window.present()`. Because window managers process focus changes asynchronously, `Gtk.Application.get_active_window()` returns `None` during the signal emission, forcing `main.py` to use system notifications instead of in-app toasts.

### Fix Scope
MINIMAL
Wrap the `self.emit("error-occurred", message)` call in `GLib.idle_add` to allow the window manager to process the focus change.

---

### BUG-3b — `notification_service` sends OS notification that cannot be dismissed

### Hypothesis
When `show_notification()` is called, it attempts `Xdp.Portal.add_notification()` first. In LXQt, this call either:
- Succeeds at the D-Bus level but `remove_notification()` (called after `_DISMISS_SECONDS`) fails silently because `lxqt-notificationd` does not implement `org.freedesktop.portal.Notification` fully, OR
- Fails silently and falls through to `libnotify`, which is blocked by the Flatpak sandbox because `--talk-name=org.freedesktop.Notifications` is absent from `finish-args`

In both cases the notification is shown but never dismissed — it outlives the app process.

### Verdict
CONFIRMED

### Evidence
- File: `flatpak/io.github.d3msudo.anura.json`, lines 11-26
  ```json
    "finish-args": [
        "--share=network",
        "--share=ipc",
        "--socket=x11",
        "--socket=wayland",
        "--socket=pulseaudio",
        "--device=dri",
        "--filesystem=xdg-pictures:ro",
        "--filesystem=xdg-download:ro",
        "--filesystem=xdg-desktop:ro",
        "--filesystem=xdg-documents:ro",
        "--talk-name=org.a11y.Bus",
        "--talk-name=org.freedesktop.portal.Desktop",
        "--env=TESSDATA_PREFIX=/app/share/tessdata"
    ],
  ```
- File: `anura/services/notification_service.py`, lines 215-223
  ```python
    def _dismiss_portal_notification(self, notification_id: str) -> bool:
        """Auto-dismiss a portal notification by removing it via the portal API."""
        try:
            if self._portal is not None:
                self._portal.remove_notification(notification_id, None, None, None)
                logger.debug(f"NotificationService: Dismissed portal notification: {notification_id}")
        except (AttributeError, RuntimeError, TypeError, GLib.Error) as e:
            logger.debug(f"NotificationService: Failed to dismiss portal notification: {e}")
  ```

### Root Cause (confirmed wording)
The Flatpak manifest lacks the `org.freedesktop.Notifications` permission, making `libnotify` non-functional inside the sandbox. Simultaneously, the portal-based `remove_notification` call is wrapped in a `try/except` block that silently logs failures at `debug` level, effectively swallowing errors when the desktop environment's portal implementation fails to dismiss the notification.

### Fix Scope
MINIMAL
Add `org.freedesktop.Notifications` to the Flatpak manifest and investigate why `Gio.Application.send_notification` is not used as the primary path.

---

### BUG-3c — `_on_error_occurred` check for `fallback_provider` is always wrong

### Hypothesis
In `main.py`, `_on_error_occurred()` checks:
```python
not getattr(self.backend, "fallback_provider", None)
```
to decide whether to show a fatal dialog vs. a toast. But `ScreenshotService` has **no attribute** named `fallback_provider` on the instance. `getattr` returns `None` (the default), making the condition `not None` → `True`. This means the fatal dialog (`DialogManager.show_fatal_error`) fires for **all** screenshot failures where the message contains `"Screenshot failed"`, even when the fallback scrot was attempted and also failed.

### Verdict
REFUTED

### Evidence
- File: `anura/services/screenshot_service.py`, line 339
  ```python
        self.fallback_provider = ScreenshotProviderFactory.get_fallback_provider()
  ```
- File: `anura/main.py`, line 234
  ```python
            if "Screenshot failed" in message.lower() and not getattr(self.backend, "fallback_provider", None):
  ```

### Root Cause (confirmed wording)
The attribute `fallback_provider` **is** correctly assigned in `ScreenshotService.__init__`. The condition in `main.py` is logically sound: it only shows the fatal dialog if the error message indicates a screenshot failure and no fallback provider was even available (e.g., on Wayland where scrot is not supported). The observed behavior of the fatal dialog showing must be due to `self.fallback_provider` being `None` at runtime, which is expected on non-X11 sessions.

### Fix Scope
MINIMAL
The logic is correct, but the error message checking could be more robust than simple string matching.

---

## BUG-4 — scrot fallback: exits 0 but produces no output

### BUG-4A — Architecture: orphan provider code never integrated

### Hypothesis
The `testing` branch contains a full provider subsystem (`anura/services/screenshot/portal_provider.py`, `legacy_provider.py`, `factory.py`) that was written but **never integrated into `ScreenshotService`**. `ScreenshotService` still uses the old monolithic approach.

The provider classes are orphan code. `ScreenshotProviderFactory` is never called. `LegacyX11Provider` is never instantiated by the service.

### Verdict
REFUTED

### Evidence
- File: `anura/services/screenshot_service.py`, lines 338-339
  ```python
        self.provider = ScreenshotProviderFactory.get_provider()
        self.fallback_provider = ScreenshotProviderFactory.get_fallback_provider()
  ```
- File: `anura/services/screenshot_service.py`, lines 371-374
  ```python
                if is_generic and self.fallback_provider:
                    logger.info("Anura Screenshot: Attempting fallback capture...")
                    self.fallback_provider.capture(lang, copy, _on_capture_result)
  ```

### Root Cause (confirmed wording)
The provider subsystem is fully integrated into `ScreenshotService`. The service uses `ScreenshotProviderFactory` to instantiate both primary and fallback providers and delegates capture requests to them.

### Fix Scope
NONE
No fix required for integration; the code is correctly wired.

---

### BUG-4B — `_on_screenshot_timeout` now implemented, breaks scrot -s

### Hypothesis
In `testing`, `_on_screenshot_timeout` **is fully implemented**: it calls `self.present()` after 30s, restoring the window. Scrot is still running when the 30s timeout fires. The window reappears on top of scrot's crosshair cursor, interfering with X11 area selection.

Additionally, `_on_screenshot_timeout` does **not** cancel the in-progress scrot process, leaving `_is_capturing = True`.

### Verdict
CONFIRMED

### Evidence
- File: `anura/window.py`, lines 122-128
  ```python
    def _on_screenshot_timeout(self) -> bool:
        """Restore window if portal screenshot doesn't respond within 30s."""
        self._screenshot_timeout_id = None
        self.present()
        self.show_toast(_("Screenshot timed out. Please try again."))
        logger.warning("Anura: Screenshot portal timeout — restoring window.")
        return GLib.SOURCE_REMOVE
  ```

### Root Cause (confirmed wording)
The `_on_screenshot_timeout` handler restores the window UI but fails to signal the `ScreenshotService` or its providers to cancel the active capture operation. On X11, the restored window interferes with `scrot`'s mouse grab, preventing the user from completing the selection.

### Fix Scope
MODERATE
Update `_on_screenshot_timeout` to call `self.backend.provider.cancel()` and `self.backend.fallback_provider.cancel()` (if active) to ensure the subprocess is killed and state is reset.

---

## BUG-5 — `image_filters.py`: cancelled tasks logged as ERROR

### Hypothesis
In `anura/utils/image_filters.py` around line 221, intentionally cancelled tasks (cancelled via `AtomicTaskManager` when a newer task supersedes them) are logged with `logger.error()`. This produces misleading `ERROR` entries in the log for normal, expected behaviour.

### Verdict
CONFIRMED

### Evidence
- File: `anura/utils/image_filters.py`, lines 219-222
  ```python
        except (AttributeError, RuntimeError, TypeError, ValueError, OSError) as e:
            # If the pipeline fails, ensure all successfully created intermediates are closed
            logger.error(f"Filter chain failed: {e}")
  ```

### Root Cause (confirmed wording)
The generic exception handler in `FilterChain.apply` catches `InterruptedError` (which inherits from `OSError`) and logs it at the `ERROR` level. Since `InterruptedError` is the standard mechanism for cooperative cancellation in Anura, normal task supersession results in misleading error logs.

### Fix Scope
MINIMAL
Add an explicit `except InterruptedError: raise` block before the generic catch-all to allow cancellations to propagate silently.

---

## BUG-6 — `clipboard_service.py`: `Warning: Source ID not found` on stderr

### Hypothesis
`GLib.source_remove()` emits a C-level `g_warning()` to stderr **before** raising a Python exception. The existing `try/except Exception` blocks suppress the Python exception but cannot intercept the C-level warning. The stale source ID originates from a race window: GLib auto-removes a one-shot timeout source when it fires, but `_clipboard_timeout_id` still holds the old ID.

A secondary leak: `_fallback_to_texture_read()` and `_fallback_to_uri_list_read()` overwrite `_clipboard_timeout_id` with a new `GLib.timeout_add_seconds()` return value without first calling `_clear_active_timeout()`.

### Verdict
CONFIRMED

### Evidence
- File: `anura/services/clipboard_service.py`, lines 112-123
  ```python
    def set(self, value: str) -> None:
...
        if old_timeout_id and old_timeout_id > 0:
            try:
                GLib.source_remove(old_timeout_id)
            except Exception:
                pass  # Source already fired or removed — safe to ignore.
  ```
- File: `anura/services/clipboard_service.py`, lines 298-301
  ```python
            self._clipboard_timeout_id = GLib.timeout_add_seconds(
                self.CLIPBOARD_TIMEOUT_SECONDS,
                self._on_clipboard_timeout,
                cancellable,
            )
  ```

### Root Cause (confirmed wording)
The `set()` method attempts to remove the previous timeout using `GLib.source_remove`, which triggers a GLib console warning if the source has already fired. Furthermore, fallback methods overwrite `_clipboard_timeout_id` without clearing the previous source, leading to orphaned GLib timers.

### Fix Scope
MODERATE
Implement a robust `_clear_active_timeout` pattern that resets the ID to 0/None and uses `GLib.MainContext.default().find_source_by_id()` before attempting removal.

---

## Priority Matrix

| Bug | Verdict | Fix Scope | Suggested Fix File(s) |
|-----|---------|-----------|----------------------|
| BUG-1 | CONFIRMED | MINIMAL | `anura/widgets/extracted_page.py` |
| BUG-2 | CONFIRMED | MODERATE | `anura/core/atomic_task_manager.py`, `anura/controllers/dnd_controller.py` |
| BUG-3a | CONFIRMED | MINIMAL | `anura/controllers/ocr_controller.py` |
| BUG-3b | CONFIRMED | MINIMAL | `flatpak/io.github.d3msudo.anura.json` |
| BUG-3c | REFUTED | MINIMAL | `anura/main.py` |
| BUG-4A | REFUTED | NONE | - |
| BUG-4B | CONFIRMED | MODERATE | `anura/window.py` |
| BUG-5 | CONFIRMED | MINIMAL | `anura/utils/image_filters.py` |
| BUG-6 | CONFIRMED | MODERATE | `anura/services/clipboard_service.py` |

## Fix Order Recommendation

1. **BUG-2 (DnD Failure)**: High impact (DnD broken), moderate complexity.
2. **BUG-4B (Screenshot Timeout/Interference)**: High impact (UI freeze/broken capture), moderate complexity.
3. **BUG-1 (TTS Icon)**: High visibility, trivial fix.
4. **BUG-3a (Notification Race)**: High visibility, trivial fix.
5. **BUG-6 (Clipboard Warnings)**: High noise in logs, moderate complexity.
6. **BUG-5 (Logging Level)**: Low impact, trivial fix.
7. **BUG-3b (Flatpak Permissions)**: Medium impact (notifications broken), trivial fix.

---

## Additional Investigation

### Q1 — Python version mismatch
`pyproject.toml` declares `requires-python = ">=3.12"`. The runtime environment uses Python 3.13. There is no mismatch; the requirement is satisfied.

### Q2 — `_on_screenshot_timeout` in development vs testing
Git history confirms that `_on_screenshot_timeout` was introduced in the `testing` branch (Commit `f8b2bcf`). It was absent in the `development` branch, which explains why the timeout-driven interference was not observed there.

### Q3 — `fallback_provider` attribute presence
The `fallback_provider` attribute is explicitly assigned in `anura/services/screenshot_service.py` at line 339:
```python
self.fallback_provider = ScreenshotProviderFactory.get_fallback_provider()
```
The check in `main.py` is correct, but it may evaluate to `True` (showing the fatal dialog) if `get_fallback_provider()` returns `None` (which it does on Wayland or if `scrot` is missing).

### Q4 — Orphan code confirmation
Files under `anura/services/screenshot/` (`portal_provider.py`, `legacy_provider.py`, `factory.py`) are **not** orphan code. They are imported and instantiated by `ScreenshotService` via the `ScreenshotProviderFactory`.

### Q5 — `tts_controller.py` signal connection
In `TtsController`, the `"paused"` signal is connected in `_setup_connections()`:
```python
self.connect_tracked(self._tts_service, "paused", self._on_tts_paused)
```
The handler `_on_tts_paused` then dispatches to the window:
```python
    def _on_tts_paused(self, _service, is_paused):
        if is_paused:
            self._window.extracted_page.update_tts_state(paused=True)
        else:
            self._window.extracted_page.update_tts_state(playing=True)
```
