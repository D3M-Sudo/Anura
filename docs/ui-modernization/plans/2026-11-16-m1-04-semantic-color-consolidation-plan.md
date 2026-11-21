# Anura M1-04 Semantic Color Consolidation and Theme Coverage Implementation Plan

**Status:** Completed — implementation, automated regression coverage and final documentation completed within the approved M1-04 scope.

**Verified implementation SHA:** `7f6a7045feefb019c869cc74aecc31a5e991a74d`

**Verification:** CI Quality Check & Release [#43951965392](https://github.com/D3M-Sudo/Anura/actions/runs/43951965392) and CodeQL [#43951968944](https://github.com/D3M-Sudo/Anura/actions/runs/43951968944) succeeded on the exact implementation SHA. Detailed test counts, job results and limitations are recorded in the implementation outcome below.

**Programme boundary:** M1-04 is complete within its approved scope. Global M1 and the overall M0–M7 modernization programme remain Partial. Native visual validation, real Orca/AT-SPI and manual keyboard checks remain excluded and are not claimed as passed.

> **For agentic workers:** Use the repository's approved Native execution process. Implement task-by-task, test each task, and stop at every review gate. Do not invoke subagents; the Anura workflow is explicitly Native because subagent-driven execution is unavailable in this environment. Steps use checkbox syntax for tracking.

**Goal:** Consolidate Anura's UI color semantics without changing its green/teal identity, and add deterministic regression coverage for unclassified UI color literals and all supported theme modes.

**Architecture:** Keep GTK 4 / Libadwaita's existing `Adw.StyleManager` integration and GSettings contract. Add a pure-Python scanner under the test support layer, use Libadwaita's native `.success` role only if the installed runtime's observable style meets the documented constraints, and extend the existing GTK integration suite rather than introducing a new test harness.

**Tech Stack:** Python 3.12+, pytest, PyGObject, GTK 4, Libadwaita, Blueprint, GTK CSS, existing GitHub Actions Weston/Wayland GTK job. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-11-16-m1-04-semantic-colors-design.md`

## Global Constraints

- Preserve palette values: `#16A36A`, `#0F7650`, `#FFFFFF`, `#21B77A` and their distinct semantic roles.
- Preserve GSettings modes `default`, `force-light`, `force-dark`, their persistence and current `Adw.StyleManager` mapping.
- Do not add dependencies, CSS preprocessors, OCR engines/models, OCR behavior changes, image-processing changes, architecture changes, portal changes or OS integration changes.
- Keep theme-managed surface, text, border and warning colors theme-managed.
- Do not conflate brand accent, suggested-action, success and focus colors.
- Do not add a new user-visible state or change language download/install behavior.
- Do not require manual GNOME/GTK visual inspection, physical-display testing, Orca/AT-SPI verification or manual keyboard navigation.
- Use the existing GitHub Actions GTK job (Weston/Wayland); no local runner is assumed.
- Do not alter protected branches `feature`, `development`, `testing` or `main`; work only on `fix/ui-modernization-aligned`.
- Keep PR #648 Open, Draft and unmerged; do not change its metadata.
- Do not claim tests or CI passed until the exact workflow run and commit SHA are verified.
- Update CHANGELOG only if the final implementation has release-relevant user-visible or maintenance impact; avoid duplicate entries.
- After implementation is complete, update both UI modernization roadmaps and `HANDOVER.md` with exact evidence. This planning task does not authorize implementation.

## Review Focus

1. **Unowned/stale downloaded-state selector:** verify that the current `.downloaded label` selector is actually attached to a live installed-language state; do not silently turn an unused selector into a new state or change download behavior.
2. **Libadwaita success style contrast:** test the computed/observable label styling in both forced schemes; if the GTK runtime cannot expose stable resolved values, do not claim runtime contrast and retain the application-owned fallback.
3. **Color scanner false positives:** comments, documentation strings, ordinary hash fragments and non-color values must not be reported as production UI color literals.
4. **Scanner coverage drift:** newly added UI source files under the declared scope must be discovered automatically, not silently omitted by a hand-maintained file list.
5. **Global theme state leakage:** GTK integration tests must restore the previous `Adw.StyleManager` color scheme even when an assertion fails.

---

### Task 1: Add deterministic production UI color-literal scanner

**Files:**
- Create: `tests/ui_color_scanner.py`
- Create: `tests/test_ui_color_scanner.py`
- Modify: `tests/test_ui_palette.py` only to invoke the scanner's production-scope check if that provides one clear existing test entry point.

**Interfaces:**
- Produce `ColorLiteral(path: str, value: str, line: int, syntax: str)`.
- Produce `scan_ui_color_literals(root: Path) -> list[ColorLiteral]`.
- Produce `find_unclassified_ui_colors(findings: Sequence[ColorLiteral], approved: Mapping[tuple[str, str], str]) -> list[ColorLiteral]`.
- The approval map key is repository-relative path plus normalized literal; each value is a short semantic rationale. Line numbers are diagnostic only and are not part of allowlist identity.

- [x] **Step 1: Write scanner unit tests first** in `tests/test_ui_color_scanner.py`:
  - `test_finds_hex_colors_in_stylesheet_and_blueprint`: recognizes 3/4/6/8-digit hexadecimal literals in CSS and Blueprint files.
  - `test_finds_rgb_and_rgba_colors_in_stylesheet`: recognizes supported `rgb()` and `rgba()` forms.
  - `test_finds_color_literals_in_python_string_constants`: recognizes color values in Python string constants in the declared application UI scope.
  - `test_ignores_comments_and_non_ui_files`: ignores CSS/Blueprint/Python comments and files outside the declared scope.
  - `test_ignores_non_color_hash_strings_and_theme_references`: does not report URL/hash fragments or semantic GTK references such as `@theme_fg_color`, `@accent_color` and `@warning_color`.
  - `test_approved_literal_requires_path_and_semantic_rationale`: an exact path/literal classification passes; the same literal in a new unclassified path does not.
  - `test_unclassified_fixture_reports_path_line_and_literal`: a temporary fixture containing a new color fails classification with actionable path, line and value.
  - `test_scanner_discovers_new_files_without_updating_a_file_list`: adding a fixture file under a scanned directory makes it part of the scan automatically.

- [x] **Step 2: Run the new tests and confirm they fail** because the scanner interface does not yet exist.

  Run: `uv run pytest tests/test_ui_color_scanner.py -q`  
  Expected: FAIL on missing scanner module/functions.

- [x] **Step 3: Implement the scanner** in `tests/ui_color_scanner.py`:
  - Discover `data/style.css`, all `data/ui/**/*.blp`, `anura/widgets/**/*.py`, `anura/window.py` and `anura/main.py` recursively/explicitly. Do not scan OCR, model, service or transformation modules that do not own UI styling.
  - Strip format-appropriate comments before scanning CSS/Blueprint.
  - Parse Python with `ast` and inspect string constants, excluding module/class/function docstrings; do not regex-scan Python comments or arbitrary source text.
  - Normalize hex literals to lowercase; retain source line and syntax kind.
  - Recognize hexadecimal and supported CSS `rgb()`/`rgba()` literals; do not treat GTK named/theme colors as hardcoded literals.
  - Return deterministic results sorted by path, line and literal.
  - Do not scan tests, generated build output, documentation, translations, screenshots or non-UI data directories.

- [x] **Step 4: Add the production classification test** in `tests/test_ui_palette.py` or `tests/test_ui_color_scanner.py` using an explicit path/literal-to-rationale map for the currently approved production literals. The test must fail on any new unclassified literal and print every finding with path and line.

- [x] **Step 5: Run scanner and existing palette tests.**

  Run: `uv run pytest tests/test_ui_color_scanner.py tests/test_ui_palette.py -q`  
  Expected: PASS; current production literals are classified, and the temporary unclassified fixture is rejected.

- [x] **Step 6: Commit the scanner task.**

  Commit message: `test(ui): guard unclassified color literals`.

### Task 2: Consolidate success semantics and repeated green roles

**Files:**
- Modify: `data/style.css`
- Modify: `anura/widgets/language_row.py` only for the existing installed-language state class, if source tracing confirms that this is the owner of the `.downloaded` selector.
- Modify: `tests/test_ui_palette.py`
- Modify: `tests/test_language_row_accessibility.py` for deterministic installed-state class toggling with the existing `headless_gi_mocks` fixture.
- Modify: `tests/test_widgets.py` for a real GTK `LanguageRow` style-class assertion under the existing GResource/Wayland test bootstrap.
- Modify: `docs/ui-design-system.md`

**Interfaces:**
- Preserve the existing `LanguageRow.update_ui()` installed-state decision; do not change its language-manager queries or button visibility/sensitivity behavior.
- The installed-state CSS class must be applied/removed idempotently from that existing state only if the selector is currently unowned and the implementation needs to connect the already-existing visual treatment.
- Do not add new public application APIs.

- [x] **Step 1: Add/adjust failing palette and state tests**:
  - Verify `LanguageRow.update_ui()` maps the existing `get_downloaded_codes()` installed state to the chosen semantic class and removes that class when the language is no longer installed.
  - Keep the existing `remove_btn` visibility, `install_btn` visibility/sensitivity and loading behavior unchanged.
  - Verify the approved palette role definitions remain exactly `#16A36A`, `#0F7650` and `#FFFFFF`.
  - Verify brand accent is not used as normal text.
  - Verify the focus and History icon treatments remain distinct from success.
  - Verify the real `LanguageRow.label` receives Libadwaita `.success` only if the GTK test can establish that the class is available and semantically suitable. If stable resolved foreground values cannot be read in CI, keep the existing app-owned light/dark CSS fallback and document that computed runtime contrast was not established.

- [x] **Step 2: Run focused tests and confirm the new assertions fail** against the current implementation.

  Run: `uv run pytest tests/test_ui_palette.py tests/test_language_row_accessibility.py -q`  
  Expected: new success-role assertions fail before implementation; unrelated existing tests remain green.

- [x] **Step 3: Evaluate the Libadwaita `.success` class** using the GTK runtime available in CI and the semantic class behavior documented in the spec.
  - Apply `.success` to `LanguageRow.label` only if runtime checks can establish suitable semantic styling and readable foreground in both forced schemes. The current `.downloaded label` selector has no `downloaded` class application in the audited `LanguageRow` implementation; connect the existing installed state to the chosen style without changing install/remove behavior.
  - If resolved foreground/background values are not available through a stable GTK API, retain the app-owned `.downloaded label` light/dark fallback, add/remove `downloaded` on the `LanguageRow` according to the existing installed state, and explicitly record that computed runtime contrast was not established.
  - Do not add an explicit error role; no existing production error-color requirement was established.

- [x] **Step 4: Consolidate only identical semantic roles** in `data/style.css`.
  - Remove duplicate standalone green declarations only where they represent the same role.
  - Keep focus, History icon, brand accent and suggested-action roles separate.
  - Keep warning and theme-managed colors expressed through GTK/Libadwaita semantic variables.
  - Do not change the four approved palette values.

- [x] **Step 5: Update semantic color documentation** in `docs/ui-design-system.md` with the success, accent, suggested-action, focus, warning and theme-managed role distinctions, plus the scanner's path scope and classification policy.

- [x] **Step 6: Run focused tests.**

  Run: `uv run pytest tests/test_ui_palette.py tests/test_ui_color_scanner.py tests/test_language_row_accessibility.py -q`  
  Expected: PASS; scanner allowlist matches the final CSS/Python state and no semantic role is conflated.

- [x] **Step 7: Commit the semantic color task.**

  Commit message: `refactor(ui): align success color semantics`.

### Task 3: Add GTK theme-mode transition integration coverage

**Files:**
- Modify: `tests/test_widgets.py` (existing GTK integration module with GResource registration and real GTK widgets).
- Modify: `tests/test_app_lifecycle.py` (existing `AnuraApplication` fixture; add focused GTK-marked tests for the existing theme mapping).
- Modify: `tests/test_ui_palette.py` only if a static contract assertion needs to remain separate from runtime behavior.
- Do not modify `anura/main.py` unless a demonstrated defect requires a minimal test seam; the current `_apply_color_scheme()` mapping is already directly testable.

**Interfaces:**
- Exercise the existing `AnuraApplication._apply_color_scheme()` mapping and `_on_color_scheme_changed()` callback.
- Use `Adw.StyleManager.get_default()` and restore its prior color scheme in a `try/finally` fixture/helper.
- Reuse the existing GTK test bootstrap and Weston/Wayland CI job.

- [x] **Step 1: Add failing GTK integration tests** in `tests/test_widgets.py`:
  - `test_application_maps_all_supported_color_scheme_settings`: `default` maps to `Adw.ColorScheme.DEFAULT`, `force-light` to `FORCE_LIGHT`, and `force-dark` to `FORCE_DARK`.
  - `test_color_scheme_changed_callback_reapplies_current_setting`: changing the mock setting and invoking the existing callback updates the StyleManager.
  - `test_theme_modes_can_be_switched_repeatedly_without_state_leakage`: exercise transitions through all three modes in one test process and restore the previous scheme.
  - `test_installed_language_success_style_tracks_theme_mode`: verify the actual installed-language widget retains its semantic success class/treatment through light/dark transitions.
  - `test_history_empty_state_and_focus_style_surfaces_survive_theme_transitions`: instantiate the real History empty state and representative Anura button, and verify their CSS classes and style contexts remain valid across the three modes.
  - `test_theme_managed_warning_and_secondary_text_are_not_overridden`: verify warning/secondary-text behavior continues to rely on GTK/Libadwaita theme semantics.

- [x] **Step 2: Run the GTK tests and confirm the new tests fail** for the missing transition/surface assertions.

  Run: `uv run pytest tests/test_widgets.py -m gtk -v --timeout=30 --override-ini "addopts=-v --tb=short"`  
  Expected: new theme-transition assertions fail before implementation; the existing GTK suite remains otherwise unchanged.

- [x] **Step 3: Implement only the minimum test helper/fixture** needed to set the application preference through the existing `_apply_color_scheme()` mapping and restore the global StyleManager state. Do not introduce a new production theme abstraction.

- [x] **Step 4: Assert observable runtime behavior**:
  - Assert StyleManager enum values after each preference transition using the existing `AnuraApplication._apply_color_scheme()` implementation and a mocked GSettings object.
  - Assert the real `LanguageRow.label` success class (or documented fallback class) persists across theme transitions, the real History StatusPage retains `history-empty-state`, and a representative button retains `anura-button`.
  - Verify the application does not add app-owned color declarations for secondary text, surfaces, borders or warning state. The stable assertion is the semantic GTK class/StyleManager state; do not infer resolved CSS colors from a style context that does not expose them.
  - Verify theme-managed warning and secondary text do not acquire application-owned hardcoded colors.

- [x] **Step 5: Run the focused GTK suite.**

  Run: `uv run pytest tests/test_widgets.py -m gtk -v --timeout=30 --override-ini "addopts=-v --tb=short"`  
  Expected: PASS under the existing Weston/Wayland CI environment; all global theme state is restored.

- [x] **Step 6: Commit the theme coverage task.**

  Commit message: `test(ui): cover runtime theme mode transitions`.

### Task 4: Final documentation, changelog and CI evidence

**Files:**
- Modify: `docs/ui-design-system.md` if final implementation behavior differs from the design decision recorded in Task 2.
- Modify: `CHANGELOG.md` only if the final change meets the repository's release-relevant entry criteria.
- Modify: `docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md`
- Modify: `docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md`
- Modify: `HANDOVER.md`

- [x] **Step 1: Review the complete diff** for accidental changes to OCR, dependencies, packaging, portals, OS integration, settings persistence or unrelated UI behavior. Expected: no such changes.

- [x] **Step 2: Update CHANGELOG if warranted** and verify there is no duplicate entry. If the implementation only adds internal regression guards without a user-visible or release-relevant maintenance change, do not add a changelog entry.

- [x] **Step 3: Run the complete CI-equivalent test set** through GitHub Actions:
  - Python quality/non-GTK test job using the existing `.github/workflows/main.yml` command.
  - GTK test job using the existing Weston/Wayland setup and `pytest tests/ -m gtk` command.
  - Full CI Quality Check & Release workflow and CodeQL on the final implementation commit.
  - Do not create temporary workflows or alter the existing workflow for this task.

- [x] **Step 4: Verify exact evidence**:
  - Record final implementation commit SHA.
  - Record Python and GTK test counts, failures, skips and warnings.
  - Record the workflow run URLs and conclusions for that exact SHA.
  - Verify CodeQL conclusion on the exact SHA.
  - Verify no result from a prior commit is represented as evidence for the final commit.

- [x] **Step 5: Update both roadmaps and `HANDOVER.md`** with completed scope, deferred limitations, exact commit and CI evidence. Keep screenshot capture and all excluded manual checks explicitly deferred/not performed.

- [x] **Step 6: Commit final documentation** with message `docs(ui): record M1-04 verification evidence`.

- [x] **Step 7: Verify repository/PR governance**:
  - Working branch remains `fix/ui-modernization-aligned`.
  - PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`.
  - No protected branch, PR metadata or merge state changed.
  - All evidence is tied to the final tested SHA.

## Completion gate — satisfied within approved scope

The M1-04 implementation and automated regression coverage were completed within the approved scope. The implementation outcome below records the exact implementation/test SHA, CI and CodeQL evidence, test counts and explicit verification limitations. The 26 task checkboxes above record completion of the planned steps; they do not imply that excluded manual/native checks were performed.

The CI and CodeQL results cited in the implementation outcome apply to the exact implementation/test SHA `7f6a7045feefb019c869cc74aecc31a5e991a74d`. They must not be attributed to later documentation-only commits. M1-04 completion does not imply application-wide M1 completion or completion of the global M0–M7 programme.


## M1-04 implementation outcome — 2026-11-16

- Retained the app-owned light/dark green success fallback (`#0F7650` / `#21B77A`); did not adopt Libadwaita `.success` because its widget-accent behavior does not provide a stable contrast guarantee for the actual application surfaces. No deprecated `Gtk.StyleContext` color getter was introduced.
- Fixed the semantic-state linkage: `LanguageRow.update_ui()` now adds/removes `downloaded` as installation state changes. No model download/install behavior changed.
- Added GTK regression coverage for the three theme modes and repeated transitions across language, History empty-state and focus styling. Added/retained scanner coverage for supported UI sources and path-specific approved exceptions.
- Exact implementation/test head: `7f6a7045feefb019c869cc74aecc31a5e991a74d`. CI Quality Check & Release [#43951965392](https://github.com/D3M-Sudo/Anura/actions/runs/43951965392) and CodeQL [#43951968944](https://github.com/D3M-Sudo/Anura/actions/runs/43951968944) both succeeded on this exact SHA. Python: 643 passed, 6 skipped, 277 deselected; GTK integration job succeeded; Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set and multi-architecture release-artifact validation succeeded. `publish-release` was skipped as expected for a PR.
- The GTK suite validates theme setting transitions and relevant CSS-class state, not screenshot/pixel-level contrast for every system theme. Manual GNOME/GTK visual review, real Orca/AT-SPI and manual keyboard checks remain excluded and are not claimed as passed.
- No OCR pipeline/model, dependencies, architecture, portal, OS integration or workflow changes.
- M1-04 implementation is complete for its approved scope; global M1 and the global M0–M7 programme remain partial.
