---
auto_execution_mode: 0
description: Perform comprehensive code review of the entire Anura codebase with systematic audits
---
You are a senior software engineer performing a thorough code review to identify potential bugs and code improvements.

## General Review Principles
Focus on:
1. Logic errors and incorrect behavior
2. Edge cases that aren't handled
3. Null/undefined reference issues
4. Race conditions or concurrency issues
5. Security vulnerabilities
6. Improper resource management or resource leaks
7. API contract violations
8. Incorrect caching behavior, including cache staleness issues, cache key-related bugs, incorrect cache invalidation, and ineffective caching
9. Violations of existing code patterns or conventions

## Anura-Specific Comprehensive Audit

Perform a comprehensive code review of the entire Anura codebase.
Read every file completely before reporting. Do NOT modify anything.
Wait for my confirmation before any action.

### Review 1 — Thread Safety Audit
For every file in anura/:
- Find ALL signal emissions (self.emit, GObject.emit)
- Verify each is wrapped in GLib.idle_add() if called from a non-main thread
- Find ALL GTK/GObject widget modifications from secondary threads
- Find ALL GLib.idle_add() calls and verify the callback returns GLib.SOURCE_REMOVE or False

### Review 2 — Security Audit
- grep -rn "subprocess\|shell=True\|eval\|exec(" anura/
- grep -rn "os.system\|os.popen" anura/
- Find every place user input reaches Tesseract, GStreamer, or file paths
- Verify LANG_CODE_PATTERN is applied before EVERY Tesseract call
- Verify uri_validator() is applied before EVERY Gtk.UriLauncher call
- Find any f-string inside _() gettext calls
- Find any hardcoded paths outside config.py

### Review 3 — Resource Management
- Find every file open() without context manager (with statement)
- Find every tempfile usage — verify tempfile + shutil.move pattern
- Find every GStreamer pipeline — verify proper cleanup in finally/do_destroy
- Find every threading.Lock() — verify all acquisitions have matching releases
- Find every GLib.timeout_add() — verify SOURCE_REMOVE is returned when done
- Find every signal connection (connect()) — verify disconnect() exists in cleanup

### Review 4 — Error Handling Quality
- Find every bare except: or except Exception: — report file and line
- Find every except block with only pass or only logger — potential silent failures
- Find every broad exception that wraps a GTK or GLib operation
- Verify all network calls (requests.get) have timeout= parameter
- Verify all file operations handle PermissionError and OSError

### Review 5 — Type Safety
- Find every function missing return type annotation
- Find every parameter missing type annotation on public methods
- Find every implicit Optional (parameter with = None but no | None in type)
- Run: ruff check anura/ build-aux/ --select ANN (if available)

### Review 6 — Dead Code & Consistency
- Find every method defined but never called within the codebase
- Find every import that is used only in a comment or string
- Find every TODO/FIXME/HACK/XXX comment
- grep -rn "TODO\|FIXME\|HACK\|XXX\|NOQA\|type: ignore" anura/
- Verify all public methods have docstrings

### Review 7 — i18n Compliance
- grep -rn '_( f"' anura/ (f-strings in gettext — forbidden)
- grep -rn "_(f'" anura/
- Find any user-facing string NOT wrapped in _()
- Verify ngettext is used for all plural forms

### Review 8 — Flatpak & Build
- Read flatpak/com.github.d3msudo.anura.json completely
- Verify all sources have sha256 checksums
- Verify finish-args are minimal (no over-permissions)
- Read all meson.build files — verify all new source files are listed
- Verify GSK_RENDERER=cairo is in finish-args

### Review 9 — Test Coverage Gaps
For each public method in these files, check if a test exists:
- anura/config.py
- anura/language_manager.py
- anura/services/tts.py
- anura/services/screenshot_service.py
- anura/window.py
List untested methods with their complexity (simple/medium/complex).

### Review 10 — Performance & Memory
- Find any list comprehension inside a tight loop that could be a generator
- Find any repeated calls to get_downloaded_codes() without caching
- Find any widget that is recreated on every signal emission instead of reused
- Find any large data structure loaded entirely into memory unnecessarily

## Final Report Format
For each review provide:
- PASS / N ISSUES FOUND
- For each issue: file, line number, severity (CRITICAL/HIGH/MEDIUM/LOW), description
- Proposed fix (one line)

Priority summary table at the end:
| # | Severity | File | Line | Issue | Fix |
|---|----------|------|------|-------|-----|

If zero critical or high issues found → "CODEBASE READY FOR RELEASE"
If any critical issues → list them explicitly before anything else.

## Execution Guidelines
1. If exploring the codebase, call multiple tools in parallel for increased efficiency. Do not spend too much time exploring.
2. If you find any pre-existing bugs in the code, you should also report those since it's important for us to maintain general code quality for the user.
3. Do NOT report issues that are speculative or low-confidence. All your conclusions should be based on a complete understanding of the codebase.
4. Remember that if you were given a specific git commit, it may not be checked out and local code states may be different.
5. Do NOT modify any file. Wait for my confirmation after the full report.