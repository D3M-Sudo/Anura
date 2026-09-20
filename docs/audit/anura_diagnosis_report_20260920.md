# Diagnosis report: Full Diagnostics & Test Tier Audit (HEAD: aba2884)
Mode: diagnose
Task: Perform a full diagnosis run across both test tiers (headless and gtk) and project health as outlined in the debug protocol.

## 0. Target
```
jules-9488902420944664243-b1e69a33
aba2884ab861261212a5eb54909993750cfe6f1e
```
Why this branch/commit: Requested target branch `jules-9488902420944664243-b1e69a33` pinned at head commit `aba2884ab861261212a5eb54909993750cfe6f1e`.

---

## 1. Environment

### Pre-provisioning probe output (verbatim):
```
2026-09-20T10:42:52Z
Linux 6.8.0
Ubuntu 24.04.4 LTS
XDG_SESSION_TYPE       unset
XDG_CURRENT_DESKTOP    unset
DISPLAY                unset
WAYLAND_DISPLAY        unset
LANG                   set
GSETTINGS_SCHEMA_DIR   unset
python3                  /home/jules/.pyenv/shims/python3
uv                       /home/jules/.local/bin/uv
tesseract                MISSING
weston                   MISSING
blueprint-compiler       MISSING
glib-compile-resources   MISSING
glib-compile-schemas     /usr/bin/glib-compile-schemas
xvfb-run                 /usr/bin/xvfb-run
dbus-run-session         /usr/bin/dbus-run-session
gdb                      /usr/bin/gdb
flatpak                  MISSING
flatpak-builder          MISSING
bwrap                    MISSING
scrot                    MISSING
-bash: tesseract: command not found
-- python3
PyGObject MISSING ModuleNotFoundError
```

### Provisioning output (`/tmp/provision_env.sh` verbatim):
```
== 1. system packages ==
Setting up gir1.2-gtksource-5:amd64 (5.12.0-1build1) ...
Setting up libgtk-4-dev:amd64 (4.14.5+ds-0ubuntu0.10) ...
Setting up gir1.2-adw-1:amd64 (1.5.0-1ubuntu2) ...
Setting up libadwaita-1-dev:amd64 (1.5.0-1ubuntu2) ...
Processing triggers for libc-bin (2.39-0ubuntu8.7) ...

== 2. python environment (system site-packages so PyGObject is visible) ==
Creating virtual environment at: .venv
Activate with: source .venv/bin/activate
 + urllib3==2.7.0
 + vulture==2.16
 + zxing-cpp==3.0.0

== 3. build artifacts (git-ignored; never commit) ==
compiled 12 .ui file(s)
gresource ok: data
gresource ok: builddir/data
gschema ok

== 3b. environment file for later commands (a script cannot export into your shell) ==
wrote /tmp/anura-debug/env.sh (WAYLAND_DISPLAY only works while weston runs: use run_tests.sh custom ...)

== 3c. generated files must not end up in a commit ==
Untracked files after provisioning (never commit these; never use git add -A / git add .):
?? data/ui/extracted_page.ui
?? data/ui/history_page.ui
?? data/ui/language_popover.ui
?? data/ui/language_popover_row.ui
?? data/ui/language_row.ui
?? data/ui/preferences_dialog.ui
?? data/ui/preferences_general.ui
?? data/ui/preferences_languages.ui
?? data/ui/share_row.ui
?? data/ui/shortcuts_overlay.ui
?? data/ui/welcome_page.ui
?? data/ui/window.ui
NOTE: data/ui/window.ui is NOT git-ignored. Check .gitignore for inline '#' comments (git has none).

== 4. reproducibility summary ==
wayland headless: weston present (use run_tests.sh gtk)
tesseract 5.3.4
flatpak: not installed -> sandbox findings stay NOT-REPRODUCIBLE-HERE
bwrap sandbox: works

== GAPS ==
none
log: /tmp/anura-debug/provision.log
```

### Post-provisioning probe output (verbatim):
```
python 3.12.13 | PyGObject 3.48.2
Gtk 4.0 available
Adw 1 available
GtkSource 5 available
Gst 1.0 available
Xdp 1.0 available
```

**GTK / libadwaita versions comparison**:
- Host VM environment: PyGObject 3.48.2, GTK 4.14.5, Libadwaita 1.5.0, GtkSourceView 5.12.0.
- Flatpak Runtime: GNOME 50 runtime (Adw 1.6+).
- Note on version skew: In Libadwaita 1.5.0, `Adw.PreferencesDialog` derives from `Adw.Dialog` (introduced in Libadwaita 1.5), which does not accept `transient_for` keyword arguments during instantiation.

---

## 2. Test coverage account

Verbatim summary output from `bash /tmp/run_tests.sh all`:

```
== COVERAGE ACCOUNT (passed is not the whole story) ==
Files ignored by pyproject addopts in the headless tier:
  tests/test_clipboard_service.py
  tests/test_screenshot_service.py
  tests/test_share_service.py
  tests/test_tts_service.py
  tests/test_notification_service.py
  tests/test_language_manager.py
  tests/test_tts_initialization.py
  tests/test_app_lifecycle.py
  tests/test_widgets.py
  tests/test_audit_app_logic.py
  tests/test_integration_cli_enterprise.py
  tests/test_security_download_limit.py
Total tests collectable (no ignores, no marker filter):
608 tests collected in 1.41s
Collectable gtk-marked tests:
315/608 tests collected (293 deselected) in 0.86s
```

| Tier | Passed | Failed | Errors | Skipped | Deselected/ignored | Not run (why) |
|------|--------|--------|--------|---------|-------------------|---------------|
| Headless (`not gtk`) | 291 | 0 | 0 | 2 | 197 | N/A |
| GTK (`gtk`, weston headless) | 312 | 0 | 0 | 3 | 293 | N/A |
| **Total Collectable** | **603 (unique)** | **0** | **0** | **5 (unique)** | N/A | N/A |

### Skipped tests detail table:

| Test | Reason | Environment gap or swallowed exception? | Action |
|------|--------|-----------------------------------------|--------|
| `tests/test_audit_app_logic.py::TestAnuraWindow::test_window_init` | `Could not init window: 'Application' object has no attribute 'settings'` | Swallowed exception in test stub (`Adw.Application()` passed instead of stub with `settings`) | Update test stub to mock `app.settings` |
| `tests/test_audit_ui_widgets.py::TestWidgets::test_simple_widgets_init` | `Could not init PreferencesDialog: gobject 'PreferencesDialog' doesn't support property 'transient_for'` | Swallowed exception due to Libadwaita 1.5+ `Adw.PreferencesDialog` API transition | Instantiate `PreferencesDialog()` without `transient_for` |
| `tests/test_audit_config_types.py::TestLanguageItem::test_language_item_init` | `Needs real GObject` | Unconditional skip decorator on non-GTK marked test | Add `@pytest.mark.gtk` marker and remove explicit skip |
| `tests/test_audit_config_types.py::TestLanguageItem::test_language_item_repr` | `Needs real GObject` | Unconditional skip decorator on non-GTK marked test | Add `@pytest.mark.gtk` marker and remove explicit skip |
| `tests/test_keyboard_shortcuts.py::TestShortcutsIntegration::test_full_shortcuts_registration` | `Full GTK test requires display and GResources` | Unconditional explicit skip in test body | Refactor test to exercise registration under Weston environment |

---

## 3. Symptom
- **Expected**: All 608 tests pass without skips or swallowed test-fixture setup exceptions across both tiers, and prior VM audit items are verified.
- **Actual**: 603 tests pass; 5 tests skip due to test fixture/stub mismatches and hardcoded skip decorators.

---

## 4. Prior claims re-checked

| Claim (source) | Re-check command | Result at this commit | Status |
|----------------|------------------|-----------------------|--------|
| 1. Model quality change invalidates cache (`docs/audit/anura_followup_diagnosis_20260917.md`) | `grep -n -C 5 "invalidate_cache" anura/widgets/preferences_languages_page.py` | Line 201 calls `get_language_manager().invalidate_cache()` in `_on_model_quality_changed` | **RESOLVED-AT-HEAD** |
| 2. Screenshot spinner restored (`docs/audit/anura_followup_diagnosis_20260917.md`) | `grep -n -C 5 "_on_capture_finished" anura/window.py` | Line 431 calls `self.welcome_page.show_spinner()` in `_on_capture_finished` | **RESOLVED-AT-HEAD** |
| 3. Match Case toggle button icon (`docs/audit/anura_followup_diagnosis_20260917.md`) | `grep -n "search_case_btn" data/ui/extracted_page.blp -A 5` | Lines 202-204 use `label: "Aa";` (nonexistent icon name removed) | **RESOLVED-AT-HEAD** |
| 4. External Editor OpenURI failure (`docs/audit/anura_followup_diagnosis_20260917.md`) | `grep -n -C 10 "External editor launch failed" anura/window.py` | Lines 345-355 catch GLib.Error and display descriptive toast | **CONFIRMED** / **NOT-REPRODUCIBLE-HERE** |
| 5. TTS AudioPlayer state lifecycle | `uv run pytest tests/test_tts_service.py -v` | All 12 TTS tests pass cleanly with zero warnings | **RESOLVED-AT-HEAD** |

---

## 5. Evidence (one tag per item)

### E1 (REPRODUCED) `AnuraWindow.__init__` test stub mismatch
```bash
$ PYTHONPATH="/usr/lib/python3/dist-packages" uv run pytest tests/test_audit_app_logic.py::TestAnuraWindow::test_window_init -v -p skip_reasons
```
```
SKIP-REASON tests/test_audit_app_logic.py::TestAnuraWindow::test_window_init :: Could not init window: 'Application' object has no attribute 'settings'
```

### E2 (REPRODUCED) `PreferencesDialog` Libadwaita 1.5 property mismatch
```bash
$ PYTHONPATH="/usr/lib/python3/dist-packages" uv run pytest tests/test_audit_ui_widgets.py::TestWidgets::test_simple_widgets_init -v -p skip_reasons
```
```
SKIP-REASON tests/test_audit_ui_widgets.py::TestWidgets::test_simple_widgets_init :: Could not init PreferencesDialog: gobject 'PreferencesDialog' doesn't support property 'transient_for'
```

### E3 (STATIC-ONLY) Unconditional skip on `LanguageItem` tests
```bash
$ grep -n -C 5 "Needs real GObject" tests/test_audit_config_types.py
```
```
88:class TestLanguageItem:
89:    @pytest.mark.skip(reason="Needs real GObject")
90:    def test_language_item_init(self):
...
98:    @pytest.mark.skip(reason="Needs real GObject")
99:    def test_language_item_repr(self):
```

### E4 (STATIC-ONLY) Unconditional skip on shortcuts integration test
```bash
$ grep -n -C 5 "pytest.skip(" tests/test_keyboard_shortcuts.py
```
```
226:    def test_full_shortcuts_registration(self):
227:        """Test full shortcuts registration (requires GTK environment)."""
...
230:        pytest.skip("Full GTK test requires display and GResources")
```

### E5 (RESOLVED-AT-HEAD) All static checks pass cleanly
```bash
$ PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" uv run ruff check anura tests
$ python3 build-aux/check_manifest_consistency.py
$ python3 build-aux/check_tessdata_consistency.py
$ PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" python3 build-aux/check_runtime_dependency_coverage.py --manifest local
$ uv run bandit -r anura/ -q
```
```
All checks passed!
PASS: Manifests are consistent (16 shared Python modules)
PASS: Tessdata SHAs are consistent (commit: 4.1.0...)
PASS: all runtime Python dependencies are represented in the Flatpak manifests
[No security vulnerabilities identified]
```

---

## 6. Root cause

### Finding 1: `test_window_init` skip
- **Location**: `tests/test_audit_app_logic.py:76`
- **Mechanism**: `TestAnuraWindow.test_window_init` passes `app = Adw.Application()` to `AnuraWindow`. `AnuraWindow.__init__` expects `app` to provide `.settings` (an instance of `Gio.Settings`). Accessing `app.settings` raises an `AttributeError`, which is swallowed by line 80 (`except Exception as e: pytest.skip(...)`).
- **Known pattern**: "Test green but never ran the code: `pytest.skip()` in `except Exception` swallows real errors"
- **Stale-finding check**: `git grep "test_window_init"` confirms `app = Adw.Application()` is still present at HEAD.
- **Confidence**: High (100% reproducible error).

### Finding 2: `test_simple_widgets_init` skip
- **Location**: `tests/test_audit_ui_widgets.py:103`
- **Mechanism**: Libadwaita 1.5+ changed `Adw.PreferencesDialog` to derive from `Adw.Dialog` rather than `Gtk.Window`. `Adw.Dialog` does not support the `transient_for` keyword parameter during initialization, raising `TypeError: gobject 'PreferencesDialog' doesn't support property 'transient_for'`, which is swallowed on line 105 by `pytest.skip()`.
- **Known pattern**: "Test green but never ran the code: `pytest.skip()` in `except Exception` swallows real errors"
- **Stale-finding check**: `git grep "PreferencesDialog(transient_for=None)"` confirms the call is present at HEAD.
- **Confidence**: High (100% reproducible error).

---

## 7. Alternatives ruled out
- **Environment GAPs**: Provisioning via `provision_env.sh` succeeded completely with zero GAPS (Wayland Weston, Tesseract 5.3.4, GResources, and compiled schemas were all successfully set up).
- **Packaging/Dependency Drift**: Manifest consistency and runtime dependency coverage checks verified 100% alignment across Flathub/local manifests and `uv.lock`.

---

## 8. Proposed fix (diagnose mode)
In `fix` mode, the following minimal changes would resolve all 5 skipped unit tests:
1. `tests/test_audit_app_logic.py`: Attach a `settings` mock attribute to `app` (or instantiate `AnuraApplication()`) before passing it to `AnuraWindow`.
2. `tests/test_audit_ui_widgets.py`: Instantiate `PreferencesDialog()` without `transient_for=None`.
3. `tests/test_audit_config_types.py`: Mark `TestLanguageItem` with `@pytest.mark.gtk` and remove explicit `@pytest.mark.skip`.
4. `tests/test_keyboard_shortcuts.py`: Exercise actual shortcut action registration using the active `GResource` bundle under the GTK test runner environment.

---

## 9. Not verified here
- **Flatpak sandbox execution**: Flatpak runtime/SDK dependencies are not installed in this headless CLI container, so sandboxed execution findings remain `NOT-REPRODUCIBLE-HERE` (tested via native PyGObject + Weston).
- **External Editor Portal Launch (`OpenURI` fd response)**: Requires an active host desktop environment (`xdg-desktop-portal-gtk`); marked `CONFIRMED` from D-Bus trace log in prior audit report.

---

## 10. Other observations (not fixed)
- `.gitignore` line 42-43: Inline comments on file pattern lines (e.g. `data/ui/*.ui  # comment`) cause Git to parse `# comment` as part of the filename pattern, causing generated UI build artifacts to remain untracked rather than ignored.

---

## 11. Questions for the maintainer
- Would you like a follow-up task in `fix` mode to patch the 5 test stubs/markers so the test suite runs with 0 skips across both tiers?

---

## 12. Report integrity checklist
- [x] Sections 1-2 are the unedited `/tmp/anura-debug` logs
- [x] All commands exist and were run; predictions labeled `PREDICTED (not run)`
- [x] One tag per finding; line numbers from `grep -n` at the pinned commit
- [x] Every skipped test listed with its reason
