# Anura M1-04 Semantic Color Consolidation and Theme Coverage Implementation Plan

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

- [ ] **Step 1: Write scanner unit tests first** in `tests/test_ui_color_scanner.py`:
  - `test_finds_hex_colors_in_stylesheet_and_blueprint`: recognizes 3/4/6/8-digit hexadecimal literals in CSS and Blueprint files.
  - `test_finds_rgb_and_rgba_colors_in_stylesheet`: recognizes supported `rgb()` and `rgba()` forms.
  - `test_finds_color_literals_in_python_string_constants`: recognizes color values in Python string constants in the declared application UI scope.
  - `test_ignores_comments_and_non_ui_files`: ignores CSS/Blueprint/Python comments and files outside the declared scope.
  - `test_ignores_non_color_hash_strings_and_theme_references`: does not report URL/hash fragments or semantic GTK references such as `@theme_fg_color`, `@accent_color` and `@warning_color`.
  - `test_approved_literal_requires_path_and_semantic_rationale`: an exact path/literal classification passes; the same literal in a new unclassified path does not.
  - `test_unclassified_fixture_reports_path_line_and_literal`: a temporary fixture containing a new color fails classification with actionable path, line and value.
  - `test_scanner_discovers_new_files_without_updating_a_file_list`: adding a fixture file under a scanned directory makes it part of the scan automatically.

- [ ] **Step 2: Run the new tests and confirm they fail** because the scanner interface does not yet exist.

  Run: `uv run pytest tests/test_ui_color_scanner.py -q`  
  Expected: FAIL on missing scanner module/functions.

- [ ] **Step 3: Implement the scanner** in `tests/ui_color_scanner.py`:
  - Discover `data/style.css`, all `data/ui/**/*.blp`, and all production `anura/**/*.py` files recursively.
  - Strip format-appropriate comments before scanning CSS/Blueprint.
  - Parse Python with `ast` and inspect string constants, excluding module/class/function docstrings; do not regex-scan Python comments or arbitrary source text.
  - Normalize hex literals to lowercase; retain source line and syntax kind.
  - Recognize hexadecimal and supported CSS `rgb()`/`rgba()` literals; do not treat GTK named/theme colors as hardcoded literals.
  - Return deterministic results sorted by path, line and literal.
  - Do not scan tests, generated build output, documentation, translations, screenshots or non-UI data directories.

- [ ] **Step 4: Add the production classification test** in `tests/test_ui_palette.py` or `tests/test_ui_color_scanner.py` using an explicit path/literal-to-rationale map for the currently approved production literals. The test must fail on any new unclassified literal and print every finding with path and line.

- [ ] **Step 5: Run scanner and existing palette tests.**

  Run: `uv run pytest tests/test_ui_color_scanner.py tests/test_ui_palette.py -q`  
  Expected: PASS; current production literals are classified, and the temporary unclassified fixture is rejected.

- [ ] **Step 6: Commit the scanner task.**

  Commit message: `test(ui): guard unclassified color literals`.

### Task 2: Consolidate success semantics and repeated green roles

**Files:**
- Modify: `data/style.css`
- Modify: `anura/widgets/language_row.py` only for the existing installed-language state class, if source tracing confirms that this is the owner of the `.downloaded` selector.
- Modify: `tests/test_ui_palette.py`
- Modify: `tests/test_language_row_accessibility.py` or the existing GTK widget test module for installed-state behavior, choosing the established test location after inspecting its fixtures.
- Modify: `docs/ui-design-system.md`

**Interfaces:**
- Preserve the existing `LanguageRow.update_ui()` installed-state decision; do not change its language-manager queries or button visibility/sensitivity behavior.
- The installed-state CSS class must be applied/removed idempotently from that existing state only if the selector is currently unowned and the implementation needs to connect the already-existing visual treatment.
- Do not add new public application APIs.

- [ ] **Step 1: Add/adjust failing palette and state tests**:
  - Verify the current installed-language state maps to one semantic success treatment.
  - Verify the state class is present only when the language is installed and is removed when it is not.
  - Verify the approved palette role definitions remain exactly `#16A36A`, `#0F7650` and `#FFFFFF`.
  - Verify brand accent is not used as normal text.
  - Verify the focus and History icon treatments remain distinct from success.
  - Verify `.success` is used only if the runtime-backed test can establish the documented semantics and light/dark readability; otherwise verify the application-owned light/dark success token remains.

- [ ] **Step 2: Run focused tests and confirm the new assertions fail** against the current implementation.

  Run: `uv run pytest tests/test_ui_palette.py tests/test_language_row_accessibility.py -q`  
  Expected: new success-role assertions fail before implementation; unrelated existing tests remain green.

- [ ] **Step 3: Evaluate the Libadwaita `.success` class** using the GTK runtime available in CI and the semantic class behavior documented in the spec.
  - Apply it to the existing installed-language label/state only if the runtime test demonstrates acceptable semantics and readable foreground in both forced schemes.
  - If resolved foreground/background values are not available through a stable GTK API, do not assert an invented contrast result. Retain the explicit application-owned success token and document the limitation.
  - Do not add an explicit error role; no existing production error-color requirement was established.

- [ ] **Step 4: Consolidate only identical semantic roles** in `data/style.css`.
  - Remove duplicate standalone green declarations only where they represent the same role.
  - Keep focus, History icon, brand accent and suggested-action roles separate.
  - Keep warning and theme-managed colors expressed through GTK/Libadwaita semantic variables.
  - Do not change the four approved palette values.

- [ ] **Step 5: Update semantic color documentation** in `docs/ui-design-system.md` with the success, accent, suggested-action, focus, warning and theme-managed role distinctions, plus the scanner's path scope and classification policy.

- [ ] **Step 6: Run focused tests.**

  Run: `uv run pytest tests/test_ui_palette.py tests/test_ui_color_scanner.py tests/test_language_row_accessibility.py -q`  
  Expected: PASS; scanner allowlist matches the final CSS/Python state and no semantic role is conflated.

- [ ] **Step 7: Commit the semantic color task.**

  Commit message: `refactor(ui): align success color semantics`.

### Task 3: Add GTK theme-mode transition integration coverage

**Files:**
- Modify: `tests/test_widgets.py` (existing GTK integration module with GResource registration and real GTK widgets).
- Modify: `tests/test_ui_palette.py` only if a static contract assertion needs to remain separate from runtime behavior.
- Modify: `anura/main.py` only if a minimal test seam is proven necessary; do not rewrite the theme manager.

**Interfaces:**
- Exercise the existing `AnuraApplication._apply_color_scheme()` mapping and `_on_color_scheme_changed()` callback.
- Use `Adw.StyleManager.get_default()` and restore its prior color scheme in a `try/finally` fixture/helper.
- Reuse the existing GTK test bootstrap and Weston/Wayland CI job.

- [ ] **Step 1: Add failing GTK integration tests** in `tests/test_widgets.py`:
  - `test_application_maps_all_supported_color_scheme_settings`: `default` maps to `Adw.ColorScheme.DEFAULT`, `force-light` to `FORCE_LIGHT`, and `force-dark` to `FORCE_DARK`.
  - `test_color_scheme_changed_callback_reapplies_current_setting`: changing the mock setting and invoking the existing callback updates the StyleManager.
  - `test_theme_modes_can_be_switched_repeatedly_without_state_leakage`: exercise transitions through all three modes in one test process and restore the previous scheme.
  - `test_installed_language_success_style_tracks_theme_mode`: verify the actual installed-language widget retains its semantic success class/treatment through light/dark transitions.
  - `test_history_empty_state_and_focus_style_surfaces_survive_theme_transitions`: instantiate the real History empty state and representative Anura button, and verify their CSS classes and style contexts remain valid across the three modes.
  - `test_theme_managed_warning_and_secondary_text_are_not_overridden`: verify warning/secondary-text behavior continues to rely on GTK/Libadwaita theme semantics.

- [ ] **Step 2: Run the GTK tests and confirm the new tests fail** for the missing transition/surface assertions.

  Run: `uv run pytest tests/test_widgets.py -m gtk -v --timeout=30 --override-ini "addopts=-v --tb=short"`  
  Expected: new theme-transition assertions fail before implementation; the existing GTK suite remains otherwise unchanged.

- [ ] **Step 3: Implement only the minimum test helper/fixture** needed to set the application preference through the existing `_apply_color_scheme()` mapping and restore the global StyleManager state. Do not introduce a new production theme abstraction.

- [ ] **Step 4: Assert observable runtime behavior**:
  - Assert StyleManager enum values after each preference transition.
  - Assert widget style classes and stable GTK style-context state for the installed-language, History and focus surfaces.
  - Use resolved foreground/background contrast only when the GTK API exposes both through a stable, supported interface in this CI runtime; otherwise retain the semantic-class assertion and the existing static contrast checks, explicitly recording that pixel-level contrast was not runtime-measured.
  - Verify theme-managed warning and secondary text do not acquire application-owned hardcoded colors.

- [ ] **Step 5: Run the focused GTK suite.**

  Run: `uv run pytest tests/test_widgets.py -m gtk -v --timeout=30 --override-ini "addopts=-v --tb=short"`  
  Expected: PASS under the existing Weston/Wayland CI environment; all global theme state is restored.

- [ ] **Step 6: Commit the theme coverage task.**

  Commit message: `test(ui): cover runtime theme mode transitions`.

### Task 4: Final documentation, changelog and CI evidence

**Files:**
- Modify: `docs/ui-design-system.md` if final implementation behavior differs from the design decision recorded in Task 2.
- Modify: `CHANGELOG.md` only if the final change meets the repository's release-relevant entry criteria.
- Modify: `docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md`
- Modify: `docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md`
- Modify: `HANDOVER.md`

- [ ] **Step 1: Review the complete diff** for accidental changes to OCR, dependencies, packaging, portals, OS integration, settings persistence or unrelated UI behavior. Expected: no such changes.

- [ ] **Step 2: Update CHANGELOG if warranted** and verify there is no duplicate entry. If the implementation only adds internal regression guards without a user-visible or release-relevant maintenance change, do not add a changelog entry.

- [ ] **Step 3: Run the complete CI-equivalent test set** through GitHub Actions:
  - Python quality/non-GTK test job using the existing `.github/workflows/main.yml` command.
  - GTK test job using the existing Weston/Wayland setup and `pytest tests/ -m gtk` command.
  - Full CI Quality Check & Release workflow and CodeQL on the final implementation commit.
  - Do not create temporary workflows or alter the existing workflow for this task.

- [ ] **Step 4: Verify exact evidence**:
  - Record final implementation commit SHA.
  - Record Python and GTK test counts, failures, skips and warnings.
  - Record the workflow run URLs and conclusions for that exact SHA.
  - Verify CodeQL conclusion on the exact SHA.
  - Verify no result from a prior commit is represented as evidence for the final commit.

- [ ] **Step 5: Update both roadmaps and `HANDOVER.md`** with completed scope, deferred limitations, exact commit and CI evidence. Keep screenshot capture and all excluded manual checks explicitly deferred/not performed.

- [ ] **Step 6: Commit final documentation** with message `docs(ui): record M1-04 verification evidence`.

- [ ] **Step 7: Verify repository/PR governance**:
  - Working branch remains `fix/ui-modernization-aligned`.
  - PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`.
  - No protected branch, PR metadata or merge state changed.
  - All evidence is tied to the final tested SHA.

## Completion gate

M1-04 is ready for maintainer review only when all acceptance criteria in the design spec are supported by the implementation diff and exact-SHA CI evidence. This plan does not authorize implementation. After this plan is reviewed, obtain explicit execution approval before starting Task 1.
