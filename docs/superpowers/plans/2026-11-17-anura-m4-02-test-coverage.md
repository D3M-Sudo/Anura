# Anura M4-02 — Preferences Test Coverage Implementation Plan

**Date:** 2026-11-17  
**Design:** [M4-02 test coverage design](../specs/2026-11-17-anura-m4-02-test-coverage-design.md)  
**Repository:** `D3M-Sudo/Anura`  
**Branch:** `fix/ui-modernization-aligned`  
**PR:** #648 (keep Open/Draft/unmerged; base `feature`)

## Execution contract

- Use the hybrid strategy: headless tests for deterministic contracts and the existing GTK Integration job for real widget/GSettings behavior.
- Follow strict TDD for every production correction: add one focused failing test, observe the expected failure in CI, make the smallest correction, then observe it pass.
- Test-only changes do not authorize broad production refactors.
- Bounded production fixes are permitted only for defects demonstrated by a new test, as explicitly approved by the maintainer.
- Do not add dependencies or permanent workflows. Do not claim local tests were run.
- After each task, update both modernization roadmaps with changed files, exact HEAD, CI run/job evidence, limitations and the next permitted task before starting the next task.

## File map

### Existing production files (read/modify only if a test proves a defect)
- `anura/widgets/preferences_general_page.py`: color scheme and extra-language settings.
- `anura/widgets/preferences_editor_page.py`: editor wrap-mode setting.
- `anura/widgets/preferences_voice_page.py`: asynchronous TTS catalog and disposal guard.
- `anura/widgets/preferences_languages_page.py`: search, filtering, stack state and language events.

### Existing test files
- `tests/test_preferences_page_resilience.py`: headless General/Editor/Voice preference contracts.
- `tests/test_preferences_languages_lifecycle.py`: headless Languages lifecycle and callback contracts.
- `tests/test_preferences_voice_integration.py`: existing real GTK + memory GSettings integration harness; extend only if it remains cohesive.
- `tests/test_preferences_language_quality.py`: existing model-quality mapping/cache invalidation; retain as regression coverage.

### Documentation
- `docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md`: subordinate PR #648 workstream evidence/status.
- `docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md`: authoritative global M0–M7 status and traceability.

No production file is presumed to require modification.

## Task 1 — General preferences mapping and extra-language behavior

**Files**
- Test/modify: `tests/test_preferences_page_resilience.py`
- Conditional production fix: `anura/widgets/preferences_general_page.py`

- [ ] Add headless tests for all three color-scheme initialization mappings: `default → 0`, `force-light → 1`, `force-dark → 2`.
- [ ] Add headless tests for combo selection persistence: `0 → default`, `1 → force-light`, `2 → force-dark`; pin invalid-index fallback to `default`.
- [ ] Add tests for extra-language selected-item persistence using the language manager's name/code mapping.
- [ ] Add tests for language install/removal refresh, including clearing `extra-language` when its active model is removed.
- [ ] Run the focused headless tests in the existing Python Quality workflow and confirm each new contract fails for the intended reason before any production fix.
- [ ] If a production defect is proven, apply the smallest fix and rerun the focused tests plus the complete Python-quality suite.

## Task 2 — Editor wrap-mode mapping and persistence

**Files**
- Test/modify: `tests/test_preferences_page_resilience.py`
- GTK integration: create `tests/test_preferences_editor_integration.py` for real Editor/GSettings coverage; leave the existing Voice integration module focused on Voice.
- Conditional production fix: `anura/widgets/preferences_editor_page.py`

- [ ] Add headless tests for initialization mappings: `word → 0`, `char → 1`, `none → 2`.
- [ ] Add headless tests for selection persistence: `0 → word`, `1 → char`, `2 → none`; pin invalid-index fallback to `word`.
- [ ] Extend the existing GTK integration harness to instantiate the real Editor page with an isolated GSettings memory backend and verify the selected value is persisted and reflected by the setting.
- [ ] Observe the intended RED result for each new contract before any production correction.
- [ ] Apply only a demonstrated, bounded production fix; rerun focused tests and full Python-quality checks.

## Task 3 — Voice late-result disposal guard

**Files**
- Test/modify: `tests/test_preferences_page_resilience.py`
- Conditional production fix: `anura/widgets/preferences_voice_page.py`

- [ ] Add a headless test that captures the callback passed to `GLib.idle_add`, disposes the page, then delivers the catalog result.
- [ ] Assert the disposed page's combo model is not replaced and its selection is not changed; assert the callback returns `GLib.SOURCE_REMOVE`.
- [ ] Add the complementary live-page assertion that a valid result is applied, if not already covered by existing tests.
- [ ] Confirm the disposal test fails if the disposal guard is absent, then verify the current implementation passes.
- [ ] Do not alter production code if the current guard is sufficient.

## Task 4 — Languages search, filtering and list lifecycle

**Files**
- Test/modify: `tests/test_preferences_languages_lifecycle.py`
- GTK integration: create `tests/test_preferences_languages_integration.py` so the real Languages widget tests remain isolated from Voice integration.
- Conditional production fix: `anura/widgets/preferences_languages_page.py`

- [ ] Add headless tests for case-insensitive title search and the default downloaded-only filter.
- [ ] Add headless tests for empty/non-empty stack state and stop-search reset behavior.
- [ ] Add headless tests for idempotent language-added events and filter refresh on removal.
- [ ] Keep the Languages GTK tests in the dedicated integration module; do not expand the Voice integration module.
- [ ] In real GTK, instantiate the Languages page with controlled language-manager data and a stubbed network probe; verify search model contents, empty-state stack selection and reset behavior.
- [ ] Confirm each new test detects its intended regression before any production fix.
- [ ] Fix only demonstrated defects; preserve existing model-quality/cache invalidation behavior.

## Task 5 — Full verification and M4 disposition

**Files**
- Update: both modernization roadmap files listed above.
- Update PR #648 description only if its M4 status/remaining-gap summary becomes inaccurate.
- No CHANGELOG change unless product behavior changed.

- [ ] Run the full existing CI workflow on the exact resulting branch HEAD.
- [ ] Record the Python Quality test count/pass/skip/deselection output.
- [ ] Record GTK Integration results, including any skipped integration tests and their reasons.
- [ ] Record CodeQL and all required build/package jobs; do not infer success from an earlier SHA.
- [ ] Map every M4-02 acceptance criterion to a test or an explicit disposition.
- [ ] Keep M4 Partial if any CI-testable requirement remains unverified; do not conflate CI coverage with native M7 checks.
- [ ] Verify PR #648 remains Open/Draft/unmerged and targets `feature`.

## Verification commands (run by CI)

Headless tests are run through the existing Python Quality workflow, which invokes pytest for `tests/` excluding GTK-marked tests and configured integration exclusions.

GTK integration tests are run through the existing `gtk-tests` job after GTK4/Libadwaita, Blueprint resources, GResource bundle and GSettings schema are prepared. Do not add a second workflow unless the existing job is proven unable to execute a required test and the maintainer separately approves the temporary workflow.

## Review focus

- Empty downloaded-language set and missing/unknown `extra-language` values.
- Invalid combo indices and unknown setting values.
- Repeated install/download events and removal of the currently selected extra language.
- TTS callback delivered after disposal versus while the page is still alive.
- GTK filter model behavior when search text is cleared and when the underlying language store changes.
- Integration test isolation: restore module globals/settings and avoid network access.

## Completion criteria

M4-02 is complete only when all CI-testable acceptance criteria are either supported by fresh exact-HEAD CI evidence or explicitly dispositioned with the maintainer. Physical keyboard navigation and real Orca/AT-SPI remain deferred to M7 and are not part of this completion claim.


## Execution record — Task 1 (2026-11-17)

- [x] Color-scheme initialization mappings: `default → 0`, `force-light → 1`, `force-dark → 2`.
- [x] Selection persistence mappings and invalid-index fallback.
- [x] Extra-language selection persistence through language-manager name/code mapping.
- [x] Active extra-language removal clears the setting and refreshes the model.
- [x] Full CI verification completed successfully.

**Evidence:** implementation/test head `c5f820aac1a722c42bb79f5ebcbbf6fea17a0c7a`; [CI #44188821619](https://github.com/D3M-Sudo/Anura/actions/runs/44188821619) passed with Python Quality pytest **682 passed, 6 skipped, 287 deselected**, GTK Integration, Changelog Integrity, AppImage/Flatpak builds for both architectures and release-artifact validation; [CodeQL #44188821605](https://github.com/D3M-Sudo/Anura/actions/runs/44188821605) passed. No production files changed. Initial pytest failures were confined to an over-strict mock call-count assertion, corrected in the test; final CI passed. Next task: Task 2 — Editor wrap-mode mapping and persistence.
