# M1-06 Reduced-Motion Coverage and UI Color Scanner Enforcement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close M1-05 findings F1 and F2 by making the Shortcuts window honor GTK reduced-motion preferences and enforcing repository-wide UI color classification in pytest.

**Architecture:** Reuse the existing accessibility helpers and GTK settings pattern from `AnuraWindow`; keep signal ownership local to `ShortcutsOverlay` and disconnect it at destruction. Extend the existing scanner test module with one repository-root test and a path/value rationale map; rely on the existing Python CI pytest job.

**Tech Stack:** Python 3.12+, GTK4/PyGObject, pytest, existing UI color scanner.

**Spec:** `docs/superpowers/specs/2026-11-16-m1-06-reduced-motion-color-scanner-design.md`

## Global Constraints

- Work only on `fix/ui-modernization-aligned`; do not modify `feature`, `development`, `testing`, or `main`.
- PR #648 remains Open, Draft, unmerged, base `feature`, head `fix/ui-modernization-aligned`.
- No new dependencies, OCR changes, palette changes, architecture changes, portal changes, or OS changes.
- Do not expand scope to M1-05 findings F3 or F4.
- No manual visual, Orca/AT-SPI, manual keyboard, or live multi-monitor checks; do not claim these passed.
- Tie every CI/test result to the exact commit SHA tested.
- Update the global roadmap, PR roadmap, and `HANDOVER.md` after implementation; update CHANGELOG only if the change merits a user-facing entry.

## Review Focus

- GTK builds without `gtk-interface-reduced-motion`: the overlay must still honor `gtk-enable-animations` and avoid connecting to a nonexistent property.
- GTK setting changes while the overlay is open: both enabling and disabling reduced motion must update the root CSS class.
- Overlay destruction: settings signal handlers must be disconnected exactly once and must not retain the window.
- A new color literal in any scanner-covered production UI source: pytest must fail with actionable location details.
- A color approved in one source path but appearing in another path, or an approval with a blank rationale: it must remain unclassified.

---

### Task 1: Apply GTK reduced-motion policy to ShortcutsOverlay

**Files:**
- Modify: `anura/widgets/shortcuts_overlay.py`
- Test: `tests/test_widgets.py`

**Interfaces:**
- Reuse: `anura.utils.accessibility.sync_reduced_motion_class(widget: Gtk.Widget, settings: Gtk.Settings) -> bool`.
- Follow the established pattern in `anura/window.py`: `Gtk.Settings.get_for_display(self.get_display())`, optional-property detection with `find_property()`, and `notify::<property>` observers.
- Add overlay-local callback and sync method; do not introduce a new shared abstraction.

- [x] **Step 1: Add GTK regression tests for initial state and live preference transitions**

  Add focused tests for `ShortcutsOverlay` in `tests/test_widgets.py`. Verify the `reduced-motion` CSS class is present when `is_reduced_motion_enabled()` resolves true and absent when it resolves false. Exercise both directions by changing the settings state and invoking the connected notification path. Preserve and restore any GTK settings changed by the test in a `try/finally` block.

- [x] **Step 2: Run the focused GTK tests and confirm the expected failure**

  Run: `pytest tests/test_widgets.py -k shortcuts_overlay_reduced_motion -v`
  Expected: FAIL before implementation because `ShortcutsOverlay` does not yet synchronize reduced-motion state.

- [x] **Step 3: Add initial reduced-motion synchronization**

  In `ShortcutsOverlay.__init__`, obtain `Gtk.Settings` for `self.get_display()`, store it as `self._motion_settings`, and call a private `_sync_reduced_motion_class()` after window initialization. Import and reuse `sync_reduced_motion_class` from `anura.utils.accessibility`.

- [x] **Step 4: Observe supported GTK motion properties**

  For `gtk-enable-animations` and `gtk-interface-reduced-motion`, connect `notify::<name>` only when `self._motion_settings.find_property(name)` is not `None`. Store each returned handler ID. Add `_on_motion_settings_changed(settings, pspec)` to reapply the class and a private sync method matching the main-window policy.

- [x] **Step 5: Disconnect motion-setting handlers during destruction**

  Extend `do_destroy()` to disconnect every stored handler from `self._motion_settings`, using the same defensive handling already used for the overlay's other signal handlers. Clear the stored IDs and references before delegating to `super().do_destroy()`.

- [x] **Step 6: Run the focused GTK tests and verify they pass**

  Run: `pytest tests/test_widgets.py -k shortcuts_overlay_reduced_motion -v`
  Expected: PASS for initial reduced-motion, initial normal-motion, both live transitions, and handler cleanup.

- [x] **Step 7: Run the complete GTK integration test module**

  Run: `pytest tests/test_widgets.py -m gtk -v`
  Expected: PASS; no regressions in existing widget tests.

### Task 2: Enforce the production UI color scanner in pytest

**Files:**
- Modify: `tests/test_ui_color_scanner.py`
- Reuse unchanged: `tests/ui_color_scanner.py`
- CI integration: existing `.github/workflows/main.yml` `python-quality` pytest invocation; no workflow edit expected.

**Interfaces:**
- `scan_ui_color_literals(root: Path) -> list[ColorLiteral]`
- `find_unclassified_ui_colors(findings, approved) -> list[ColorLiteral]`
- Repository root: `Path(__file__).resolve().parents[1]`.

- [x] **Step 1: Add a repository-root enforcement test**

  Add a test that scans the real repository root and checks that `find_unclassified_ui_colors()` returns no findings. Define a module-level approval map keyed by `(relative_path, normalized_value)`, with a non-empty semantic rationale for every approved literal.

- [x] **Step 2: Confirm the allowlist against actual scanner output**

  Run: `pytest tests/test_ui_color_scanner.py -k repository_ui_colors_are_classified -v`
  Expected: initially FAIL if the inventory is incomplete. Inspect every finding and add only the exact path/value pair with a defensible rationale. Do not approve by value alone or add wildcard paths.

  Initial expected `data/style.css` values to verify:
  - `#16a36a`, `#0f7650`, `#ffffff`, `#21b77a`
  - `rgba(0, 0, 0, 0.15)`, `rgba(0, 0, 0, 0.1)`, `rgba(0, 0, 0, 0.12)`

- [x] **Step 3: Make failures actionable**

  Format each unclassified result with `path:line`, literal value, and syntax. Include the full list in the assertion message so a future contributor can classify or remove each new literal.

- [x] **Step 4: Verify fixture-level and repository-level scanner tests**

  Run: `pytest tests/test_ui_color_scanner.py -v`
  Expected: all existing fixture tests and the new repository-root enforcement test PASS.

- [x] **Step 5: Verify the normal non-GTK pytest tier**

  Run: `pytest tests/ -m "not gtk"`
  Expected: PASS. This is the same test tier invoked by `python-quality`; no standalone workflow step is necessary.

### Task 3: Documentation, traceability, and final verification

**Files:**
- Modify: `docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md`
- Modify: `docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md`
- Modify: `HANDOVER.md`
- Modify: `CHANGELOG.md` only if a user-facing entry is warranted.

- [x] **Step 1: Record F1 and F2 completion evidence**

  Update both roadmaps and `HANDOVER.md` with the implemented behavior, tests, and exact verification status. Mark M1-06 complete only after required evidence is available. Keep F3 and F4 explicitly deferred.

- [x] **Step 2: Review CHANGELOG relevance**

  Check existing `[Unreleased]` entries. Add one concise entry only if the behavior change is user-visible and not already represented; do not duplicate an existing entry.

- [x] **Step 3: Run static checks**

  Run: `ruff check anura/widgets/shortcuts_overlay.py tests/test_widgets.py tests/test_ui_color_scanner.py`
  Run: `ruff format --check anura/widgets/shortcuts_overlay.py tests/test_widgets.py tests/test_ui_color_scanner.py`
  Expected: both commands pass.

- [x] **Step 4: Run full CI and CodeQL on the final implementation SHA**

  Confirm all applicable jobs on the exact final SHA, including Python quality, GTK integration, changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, release artifact validation, and CodeQL. Record skipped jobs with their reasons; do not interpret expected PR-only skips as failures.

- [x] **Step 5: Verify PR invariants**

  Re-fetch PR #648 and confirm it remains Open, Draft, unmerged, base `feature`, head `fix/ui-modernization-aligned`. Do not alter PR metadata or merge it.

## Execution Notes

- Execution used the native in-session method; no subagent-driven execution was claimed.
- The root `.anura-fade-in` and `.anura-card` classes are removed while reduced motion is active because `.reduced-motion *` does not match the root widget. They are restored in normal-motion mode; no CSS change is needed.
- Settings handlers are disconnected in both `_on_close_request()` and `do_destroy()`. GTK CI demonstrated that the tested `destroy()` call did not exercise the existing `do_destroy()` path, so close-request cleanup is also required; the destroy hook remains an idempotent fallback.
- On implementation/test SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`, CI #43974750869 completed with overall `success`; all 9 executable jobs passed, including AppImage x86_64/aarch64 builds, metadata checks, clean-host smoke tests and artifact uploads, Flatpak x86_64/aarch64 builds/runtime checks, and both release-set validators. Python quality: 644 passed, 6 skipped, 277 deselected; GTK Integration: 447 passed, 5 skipped, 650 deselected, 2 warnings. Ruff, mypy, Bandit and Changelog integrity passed. CodeQL #43974750821 passed on the same SHA. `publish-release` was skipped as expected for a PR.
