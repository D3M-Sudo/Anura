# Anura M4-02 — Preferences Test Coverage Design

**Date:** 2026-11-17  
**Repository:** `D3M-Sudo/Anura`  
**Working branch:** `fix/ui-modernization-aligned`  
**Workstream:** PR #648, target `feature`

## Intent

Complete the CI-testable regression coverage for the remaining M4 Preferences behaviors. The work is intended to establish reliable automated evidence for preference mapping, persistence, asynchronous disposal and the Languages page lifecycle without broadening product behavior.

## Goals

- Cover General preferences color-scheme mapping and extra-language selection/update behavior.
- Cover Editor wrap-mode mapping and GSettings persistence.
- Prove a late TTS catalog result cannot update a disposed Voice page.
- Cover Languages search/filter/empty-state behavior and model-list lifecycle.
- Exercise real GTK widget behavior where the existing GTK Integration job can provide stronger evidence than headless GI mocks.
- Apply a narrowly scoped production correction only if a new test demonstrates a real defect; follow RED → GREEN and preserve unrelated behavior.

## Non-goals

- Physical Tab/Shift+Tab navigation, real Orca or AT-SPI validation.
- Visual redesign, unrelated accessibility remediation or broad refactoring.
- New runtime/test dependencies or permanent CI workflows.
- Changes to OCR engines, model formats, download contracts or network policy.
- CHANGELOG edits unless a production behavior change is actually required.

## Existing implementation and test context

The current implementation is in:
- `anura/widgets/preferences_general_page.py`
- `anura/widgets/preferences_editor_page.py`
- `anura/widgets/preferences_voice_page.py`
- `anura/widgets/preferences_languages_page.py`

Existing headless coverage is distributed across:
- `tests/test_preferences_page_resilience.py`
- `tests/test_preferences_language_quality.py`
- `tests/test_preferences_languages_lifecycle.py`
- `tests/test_language_row_accessibility.py`

The existing real-GTK integration harness is in `tests/test_preferences_voice_integration.py`; the `gtk-tests` job in `.github/workflows/main.yml` installs GTK4/Libadwaita, compiles Blueprint resources and GSettings schemas, and runs GTK-marked tests under a virtual Wayland environment. It sets `NO_AT_BRIDGE=1` and `GTK_A11Y=none`, so it cannot establish real Orca/AT-SPI or physical keyboard accessibility.

## Approaches considered

1. **Headless only:** low-cost and deterministic for mapping and callback logic, but weak evidence for real GTK model/filter/widget interactions.
2. **Hybrid (selected):** use existing headless GI-mock tests for deterministic mappings and lifecycle guards, plus GTK integration tests for actual widget models, GSettings and Languages-page behavior. This gives the best balance without adding infrastructure.
3. **GTK-only:** stronger widget realism but slower and more brittle for narrow mapping/callback contracts; unnecessary for behavior already testable headlessly.

The maintainer selected the hybrid approach.

## Scope and acceptance criteria

### General preferences
- Verify persisted color-scheme values `default`, `force-light` and `force-dark` initialize the expected combo indices.
- Verify combo indices persist the corresponding setting; verify invalid selection fallback behavior.
- Verify extra-language selection persists the selected language code.
- Verify installation/removal signals refresh the available language model and removal of the active extra language clears the setting.
- Do not assert implementation details beyond observable settings/model behavior.

### Editor preferences
- Verify `word`, `char` and `none` initialize the expected combo indices.
- Verify selection persists the matching value.
- Verify real GSettings persistence in GTK integration using an isolated memory backend.

### Voice preferences
- Queue or directly deliver a TTS catalog completion after disposal and verify it does not mutate the combo model or selected value.
- Preserve the existing successful catalog, failure and volume behavior.

### Languages page
- Verify search matches language titles case-insensitively.
- Verify the non-search filter shows only downloaded languages.
- Verify empty and non-empty results select the corresponding stack child.
- Verify stop-search clears the query and restores the normal filter.
- Verify language-added events are idempotent and refresh the model; verify removal refreshes the visible filter.
- Use real GTK integration for the filter/model/stack interactions where supported by the existing GTK CI job.
- Preserve current model-quality cache invalidation behavior.

## Constraints and authorization

- Work only on `fix/ui-modernization-aligned`; do not modify `feature`, `development`, `testing` or `main`.
- PR #648 remains open, Draft and unmerged.
- The maintainer approved the hybrid test strategy and approved bounded production fixes only when a new test demonstrates a real defect and the fix follows RED → GREEN with no unrelated functional changes.
- No implementation starts until the implementation plan is reviewed and explicitly approved.
- GitHub Actions is the authoritative test environment; do not claim local tests were run.
- Update the subordinate and global modernization roadmaps after each completed implementation task, recording exact commit/CI evidence and exclusions.
- Keep M4 Partial until all CI-testable gaps are either covered or explicitly dispositioned. M7 native checks remain separate.

## Builder decisions

The implementer may choose exact test helper structure and fixture reuse after inspecting current tests, provided tests assert observable behavior, remain isolated, and avoid unnecessary duplication. If real GTK integration proves infeasible for a specific behavior in the existing CI environment, report the evidence and propose a bounded alternative before expanding infrastructure.
