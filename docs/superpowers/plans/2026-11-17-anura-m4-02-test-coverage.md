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

- [x] Add headless tests for initialization mappings: `word → 0`, `char → 1`, `none → 2`.
- [x] Add headless tests for selection persistence: `0 → word`, `1 → char`, `2 → none`; pin invalid-index fallback to `word`.
- [x] Extend the existing GTK integration harness to instantiate the real Editor page with an isolated GSettings memory backend and verify the selected value is persisted and reflected by the setting.
- [ ] Observe the intended RED result for each new contract before any production correction.
- [ ] Apply only a demonstrated, bounded production fix; rerun focused tests and full Python-quality checks.

## Task 3 — Voice late-result disposal guard

**Files**
- Test/modify: `tests/test_preferences_page_resilience.py`
- Conditional production fix: `anura/widgets/preferences_voice_page.py`

- [x] Add a headless test that captures the callback passed to `GLib.idle_add`, disposes the page, then delivers the catalog result.
- [x] Assert the disposed page's combo model is not replaced and its selection is not changed; assert the callback returns `GLib.SOURCE_REMOVE`.
- [x] Add the complementary live-page assertion that a valid result is applied.
- [ ] Confirm the disposal test fails if the disposal guard is absent, then verify the current implementation passes. No mutation run removing the guard was performed; do not claim an observed RED from guard removal.
- [x] Do not alter production code; the existing guard is sufficient.

## Task 4 — Languages search, filtering and list lifecycle

**Files**
- `tests/test_preferences_languages_lifecycle.py`
- `tests/test_preferences_languages_integration.py`

- [x] Headless tests for case-insensitive title search and the default downloaded-only filter.
- [x] Headless tests for empty/non-empty stack state and stop-search reset behavior.
- [x] Headless tests for idempotent language-added events and filter refresh on removal.
- [x] Dedicated GTK integration module kept separate from Voice integration.
- [x] Real GTK test instantiates the Languages page with controlled manager data and a stubbed network probe; verifies search model contents, empty-state stack selection, reset, add and remove signals.
- [x] Exact-head Python Quality and GTK Integration CI passed; the new GTK integration test was executed, not skipped.
- [x] No production defect/fix was claimed; no production code, dependencies or permanent workflow changed.
- [x] Task 4 bounded acceptance criteria above completed. Download-progress UI transition coverage is explicitly left for Task 5 disposition if still required; it is not claimed by this task.

**Execution evidence (2026-11-18):** exact head `8e2a2f5d7ca3b8ec3b6f8ae478ecc0c94bc7c3bd`; [CI #44205336611](https://github.com/D3M-Sudo/Anura/actions/runs/44205336611) passed — Python Quality **698 passed, 6 skipped, 291 deselected**; GTK Integration **461 passed, 6 skipped, 704 deselected**, including `test_languages_page_search_empty_reset_and_model_lifecycle`; Changelog Integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set and multi-architecture artifact validation passed. [CodeQL #44205336610](https://github.com/D3M-Sudo/Anura/actions/runs/44205336610) passed. The GTK job was rerun after an initial cancellation; final run succeeded on the same SHA. No CHANGELOG entry was warranted. Native physical keyboard and Orca/AT-SPI remain M7 work. Independent reviewer subagent unavailable; in-session test-diff inspection only.

## Task 5 — Full verification and M4 disposition

**Files**
- Update: both modernization roadmap files listed above.
- Update PR #648 description only if its M4 status/remaining-gap summary becomes inaccurate.
- No CHANGELOG change unless product behavior changed.

- [x] Run the full existing CI workflow on the exact resulting branch HEAD.
- [x] Record the Python Quality test count/pass/skip/deselection output.
- [x] Record GTK Integration results, including the new Languages integration test execution.
- [x] Record CodeQL and all required build/package jobs on the exact SHA.
- [ ] Map every M4-02 acceptance criterion to a test or an explicit disposition.
- [ ] Keep M4 Partial if any CI-testable requirement remains unverified; do not conflate CI coverage with native M7 checks.
- [x] Verify PR #648 remains Open/Draft/unmerged and targets `feature`.

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

 
## Execution record — Task 2: Editor wrap-mode mapping and GSettings persistence (2026-11-18)

- [x] Headless initialization mapping: `word → 0`, `char → 1`, `none → 2`, with unknown-value fallback.
- [x] Headless selection persistence: `0 → word`, `1 → char`, `2 → none`, with invalid-index fallback.
- [x] Dedicated GTK integration module uses the real Editor Preferences page and isolated Gio memory GSettings backend; all three stored-mode/persisted-mode cases passed.
- [x] Full exact-head CI verification completed successfully.
- [ ] Production correction: not applicable; the tests did not demonstrate a production defect, so no production code was changed.
 
**Evidence:** exact implementation head `cae8b8c27114daf59fab96ebefdd377b3efb76ae`; [CI #44195812990](https://github.com/D3M-Sudo/Anura/actions/runs/44195812990) passed with Python Quality **690 passed, 6 skipped, 290 deselected**, GTK Integration **460 passed, 6 skipped, 696 deselected** (including all three Editor integration cases), Changelog Integrity, AppImage/Flatpak builds for x86_64/aarch64 and artifact validation; [CodeQL #44195813017](https://github.com/D3M-Sudo/Anura/actions/runs/44195813017) passed. No production files changed. Next task: Task 3 — Voice late-result-after-disposal; maintainer authorization required.


## Execution record — Task 3: Voice late-result-after-disposal (2026-11-18)

- [x] Headless test captures the `GLib.idle_add` callback, disposes the page and then delivers the catalog result.
- [x] Disposed-page callback returns `GLib.SOURCE_REMOVE`; combo model and selection are not mutated; loading state is cleared.
- [x] Complementary live-page test confirms a valid result updates model/selection and clears loading state.
- [ ] Mutation verification by removing the disposal guard was not performed. Initial failed runs were test-fixture/mock-base failures, not production RED evidence.
- [x] No production correction was needed; the existing `_disposed` guard is sufficient.
- [x] Full exact-head CI and CodeQL verification completed successfully.

**Evidence:** exact implementation head `8a70fa257375f5da060b30568a6eeacd50b2f820`; [CI #44199827587](https://github.com/D3M-Sudo/Anura/actions/runs/44199827587) passed with Python Quality **692 passed, 6 skipped, 290 deselected**, GTK Integration, Changelog Integrity, AppImage/Flatpak builds for x86_64/aarch64, AppImage release-set and multi-architecture artifact validation; [CodeQL #44199827449](https://github.com/D3M-Sudo/Anura/actions/runs/44199827449) passed. `publish-release` was skipped as expected for a PR. No production files, dependencies, workflows or CHANGELOG entries changed. Native visual, physical keyboard and Orca/AT-SPI checks remain deferred to M7. Next task: Task 4 — Languages search/filter/lifecycle; separate maintainer authorization required.
