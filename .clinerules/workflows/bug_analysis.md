# Static Bug Analysis — Full Codebase Review

## Role

You are performing a **static bug analysis** of this codebase. Your goal is to find real bugs: issues that cause incorrect behavior, crashes, silent exceptions, or broken functionality at runtime.

Do NOT report:
- Style issues or formatting preferences
- Theoretical concerns without a concrete failure path
- "Could be improved" observations
- Anything you cannot trace to an actual broken behavior

---

## Process

Work through the codebase **file by file**, in this order:

1. **Entry point / application class** (main.py, app.py, or equivalent)
2. **Core business logic** (services, managers, controllers)
3. **UI layer** (windows, views, dialogs, widgets)
4. **Utilities and helpers**
5. **UI definition files** (.blp, .xml, .ui, .qml, or equivalent)
6. **Build scripts** that generate code or resources
7. **Tests** — verify they match the actual current code

Read each file fully before moving to the next. Do not skim.

---

## What to look for

For every file, check each of the following categories. Skip categories that are not relevant to the language/framework in use.

---

### A. Attributes and methods

- **Attribute declared but never initialized:** if a class declares a slot, field, or property that is never set in the constructor, accessing it before assignment raises an error.
- **Method called but never defined:** search for `self._method()`, callbacks passed to async APIs, or deferred calls (e.g. `idle_add`, `setTimeout`, `dispatch`) — verify the method actually exists in the class body.
- **Wrong attribute name:** compare every `self.attr` access against declarations in `__init__` / the constructor. A misplaced underscore prefix/suffix means the access always fails silently.
- **Module-level function called as instance method:** if a function is imported at module level (`from x import func`) and then called as `self.func()`, it will raise `AttributeError` because `func` is not a method of the instance.

---

### B. Callback and handler signatures

- **Event/action handler wrong arity:** frameworks typically call handlers with a fixed signature. If the registered callback has fewer parameters than the framework passes, it raises `TypeError`. Check every `connect()`, `addEventListener()`, `bind()`, or equivalent registration.
- **Return value ignored by caller:** some frameworks require callbacks to return a specific sentinel (e.g. `True`/`False`, `SOURCE_REMOVE`, `EVENT_STOP`). Missing return values cause the callback to fire repeatedly or propagation to behave incorrectly.
- **Async callback called with wrong arguments:** verify that callbacks passed to async APIs match the signature those APIs expect when they resolve.

---

### C. Signal / event lifecycle

- **Connect without disconnect:** every signal/event connection that is not disconnected before the object is destroyed is a memory leak. Verify that `do_destroy`, `componentWillUnmount`, `dispose`, or equivalent lifecycle methods disconnect all handlers registered in the constructor or setup methods.
- **Signal connected inside a conditional block:** if `connect()` is placed after an early `return` (a guard clause), certain execution paths will never connect the handler — the user changes the widget but nothing responds.
- **Signal connected multiple times:** if a setup function is called repeatedly (e.g. on dialog open, on model refresh) without disconnecting the previous handler first, the callback fires N times per event.

---

### D. Error handling

- **Broad `except` that silences real bugs:** `except Exception`, `except AttributeError`, `catch (e) {}` applied to a large block hides failures from downstream code. Identify every catch that logs-and-continues, and verify each reachable exception in that block is genuinely recoverable.
- **Exception caught but return value not checked:** if a function returns a success/failure indicator and the caller ignores it, the program continues in an invalid state.
- **Silent fallback on wrong type:** `if x is None: return` or `x or default` patterns can mask bugs where `x` should never be None/falsy in the first place.

---

### E. Async and threading

- **UI access from background thread:** any framework object (widget, view, model) must be accessed only from the thread it was created on. Background threads must marshal results back to the main thread (via `idle_add`, `runOnMainThread`, `dispatch_async(main_queue)`, etc.).
- **Deferred call with wrong argument:** `idle_add(func, arg)` is correct; `idle_add(func(arg))` calls `func` immediately and passes its return value — a common mistake. Check all deferred/scheduled call sites.
- **Shared mutable state without synchronization:** variables accessed from multiple threads without a lock are a data race. Class-level mutable variables (dicts, lists, counters) are especially risky.
- **Resource not released on all code paths:** if a lock is acquired, a file opened, or a connection established inside a try block, verify there is a corresponding `finally` or context manager that releases it even when exceptions occur.

---

### F. Application flow

- **Action that sets state but never updates UI:** after an async operation completes (network request, file read, background computation), verify that the UI is actually updated. It is common to set a model value but forget to trigger the navigation or redraw.
- **Window/screen that hides and may never return:** if the UI hides itself to perform an action (e.g. hide a window to take a screenshot), verify that every code path — success, error, timeout — restores the visible state.
- **Guard clause that returns `None` implicitly:** a function with a declared return type of `str` (or any non-optional) that hits an early `return` without a value silently returns `None`, which breaks callers that do not expect it.

---

### G. UI definition files

- **Widget declared in UI file but missing from code:** if a UI file references a widget by ID and the code never retrieves or uses it, either the UI or the code is out of sync.
- **Action or shortcut defined in UI but not registered in code:** a button bound to `app.some_action` will silently do nothing if `some_action` is never added to the application's action group.
- **Keyboard shortcut that depends on keyboard layout:** accelerators using named special characters (`question`, `slash`, `comma`, etc.) may not resolve on non-default keyboard layouts. Always provide a layout-agnostic fallback (function keys, etc.).
- **Modal dialog that blocks global shortcuts:** a modal window captures all keyboard input. Application-level shortcuts do not fire while it is open. Verify that modal dialogs are modal intentionally and that reference/help windows (e.g. shortcuts windows) are non-modal.
- **Rich text field with unescaped special characters:** text rendered as markup (Pango, HTML, XML) requires that `&`, `<`, `>` in literal strings are escaped as `&amp;`, `&lt;`, `&gt;`. Raw `&` in a markup field causes a parse error.

---

### H. Code generation and build scripts

- **Generated file format that violates the consuming API:** scripts that generate XML, JSON, or other structured content must produce output that matches exactly what the consuming library expects. Check the schema or API docs for the target format.
- **Generated file that can be None or empty:** if the script can produce an empty or null value for a required field, the consuming code will fail at runtime.

---

### I. Tests

- **Test that asserts the wrong behavior:** after a bug fix, the corresponding test may still assert the old (broken) behavior. This causes the test to fail on the fixed code, hiding the regression safety net.
- **Test that always skips:** `skip` / `pytest.skip` / `xit` in conditions that are always true means the test never actually runs.
- **Test that tests structure instead of behavior:** a test that checks "method exists" or "class has attribute" without verifying what the method does provides false confidence.

---

## Output format

For every bug found:

```
### BUG-N — Short title
Severity: CRITICAL / HIGH / MEDIUM / LOW

File: path/to/file.py  Line: N

Root cause:
Precise technical explanation of what is wrong and why.

Broken code:
[exact snippet]

Runtime impact:
What the user sees (or does not see). Which exception is raised. Whether it is silenced.

Fix:
[corrected snippet]
```

---

## Final summary

After individual bug entries, provide a table:

| # | Severity | File | One-line description | Fix in one line |
|---|----------|------|----------------------|-----------------|

Sort by severity descending. Include only confirmed bugs, not suspicions.