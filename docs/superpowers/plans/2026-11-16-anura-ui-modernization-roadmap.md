# Anura UI Modernization Roadmap — PR #648 Workstream

> **Roadmap hierarchy:** the [Global Anura UI/UX Modernization Roadmap](2026-11-16-anura-ui-modernization-global-roadmap.md) is primary and covers all application windows and components. This file is subordinate and records the PR #648 workstream only. Completing tasks here does not, by itself, complete a global M0–M7 phase.

> **Scope:** subordinate execution and evidence register for the PR #648 workstream only. The authoritative application-wide scope, phase plan M0–M7, progress status and requirement traceability live in the [Global Anura UI/UX Modernization Roadmap](2026-11-16-anura-ui-modernization-global-roadmap.md). This document preserves the detailed PR #648 implementation history and must not be interpreted as the complete modernization plan.

**Repository:** `D3M-Sudo/Anura`  
**Working branch:** `fix/ui-modernization-aligned`  
**PR:** [#648 — UI modernization aligned](https://github.com/D3M-Sudo/Anura/pull/648)  
**Target:** `feature`  
**Roadmap created:** 2026-11-16

## Operating rules

1. Work only on `fix/ui-modernization-aligned` unless the maintainer explicitly authorizes a different branch.
2. Keep `feature`, `development`, `testing` and `main` untouched. Do not merge, publish a release, or change PR #648 out of Draft without explicit authorization.
3. Do not begin a development task until its scope and acceptance criteria have been reviewed and explicitly approved by the maintainer.
4. **Mandatory progress update:** immediately after each task is completed, update this roadmap before starting the next task. Record the task ID, outcome, files changed, commit/head, test results, CI run URL, limitations and next permitted task. A task is not complete merely because implementation was reported; record verifiable evidence.
5. Distinguish implementation, automated verification and manual verification. Never label a check as passed if it was not run.
6. Manual GNOME/GTK visual checks, Orca/AT-SPI checks and manual keyboard-navigation checks are excluded by the maintainer's current decision. They are **excluded**, not passed, and must not be used as blocking gates unless the maintainer changes that decision.
7. Use GitHub Actions as the test execution environment; this working environment does not provide the local project test runner. Do not claim local tests were run.
8. Keep CHANGELOG and technical documentation accurate when a task changes user-visible behavior or project contracts.

## Verified baseline (2026-11-17)

- PR #648 is Open, Draft, unmerged and mergeable; base `feature`; working branch `fix/ui-modernization-aligned`.
- Audited head before M5 closure documentation: `ee81c01c47b49ebe53b5c36797eb54f18e6d8469`.
- GitHub PR metadata at that snapshot: 576 commits, 96 changed files, 8,661 additions and 986 deletions. Live comparison with `feature`: 576 ahead / 0 behind; merge base `cb079b0b55e252a7ac054fe1b6f57030ddc7b1f9`. Ahead count is Git ancestry, not a count of distinct UI features.
- Latest complete code/test-head CI: [#44142298765](https://github.com/D3M-Sudo/Anura/actions/runs/44142298765) and CodeQL [#44142298673](https://github.com/D3M-Sudo/Anura/actions/runs/44142298673) passed on exact head `74f6a4ef98392f80c0ca1e95ed987d2c1d48749c`. Python quality, Changelog integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture artifact validation passed; publish-release was skipped as expected for a PR.
- Documentation-inclusive head observed during the audit: CodeQL [#44145092317](https://github.com/D3M-Sudo/Anura/actions/runs/44145092317) passed on `ee81c01c47b49ebe53b5c36797eb54f18e6d8469`. CI [#44145092344](https://github.com/D3M-Sudo/Anura/actions/runs/44145092344) was still in progress: Python quality, Changelog integrity, GTK Integration, AppImage x86_64/aarch64 and AppImage release-set validation had passed; Flatpak x86_64/aarch64 were still running. This run does not cover later documentation commits.
- M5 banner regressions: temporary run [#44141439001](https://github.com/D3M-Sudo/Anura/actions/runs/44141439001), 2 passed, 1 warning. Final code/test head and CI evidence are recorded in M5-03 below.
- No merge, release publication or protected-branch update is authorized.

## Relationship to the global M0–M7 plan

This workstream contributes implementation/evidence to global M1 (Design System), M2 (Welcome/navigation), M3 (Extracted/History), M4 (Preferences/languages), and M6 (responsive/accessibility), with CI evidence contributing to M7. Contributions are partial at application-wide level unless the global roadmap explicitly records the corresponding requirement as satisfied. In particular, this workstream does not establish completion of History, language selector, About, dialogs, popovers, menus, banners/toasts or notifications.

The global roadmap owns phase status and app-wide prioritization. This document owns detailed PR #648 task records, commits, CI evidence and workstream-specific follow-ups. When a task changes a global requirement status, update both documents before starting the next task.

## Progress overview

| ID | Task | Status | Notes |
|---|---|---|---|
| UI-00 | Reconstruct current state and reconcile available evidence | **Completed** | Read-only audit completed; this roadmap records the verified baseline and known documentation drift. |
| UI-01 | M1 Preferences and asynchronous lifecycle corrections | **Completed** | Preferences pages and TTS/OCR lifecycle work are present in the PR branch; covered by the current PR CI run. |
| UI-02 | M2 Extracted header and lower action bar | **Completed** | Extracted layout work is present; existing text scrolling is preserved and covered by regression tests. |
| UI-03 | M2-B T1 Welcome responsive actions, focus and scrolling | **Completed** | Automated responsive/focus coverage and the constrained-viewport scrolling regression pass in CI. |
| UI-04 | M2-B T2 green Design System palette and stylesheet loading | **Implemented; evidence recorded** | Implementation and palette tests exist. The palette plan's checkboxes are stale (all unchecked); reconcile its execution record rather than treating the checkboxes as proof of unfinished code. |
| UI-05 | M2-B T3 shell geometry and resizability | **Completed** | Monitor-aware sizing, normal-state size persistence and resizable Preferences/Shortcuts behavior have implementation and regression evidence. |
| UI-06 | M2-B T4 accessibility A1–A5 | **Completed** | Accessibility implementation and tests are recorded; manual assistive-technology checks remain excluded. |
| UI-07 | Reconcile handover, subordinate plans and PR description with current state | **Partial / approval-limited** | Global and subordinate roadmaps plus HANDOVER are being reconciled; the PR description remains unchanged because PR metadata changes require separate explicit approval. |
| UI-08 | Audit original modernization requirements against the final PR diff | **Pending** | Trace every accepted original requirement to implementation/test/evidence or an explicit rejection/deferment. |
| UI-09 | Define the next development task and obtain maintainer approval | **Blocked pending UI-08** | Do not invent a feature or infer authorization from this roadmap. |
| UI-10 | Implement the next explicitly approved task | **Not started** | Must use an approved execution approach and task-level acceptance criteria. |
| UI-11 | Review, run CI and validate delivery evidence | **Not started** | Run after UI-10 or any later implementation task; record exact results and limitations. |
| UI-12 | Update this roadmap after every completed task | **Mandatory recurring control** | Execute after each task, before starting another. This is not a one-time final task. |
| UI-13 | M1-02 GTK4/Libadwaita typography, spacing and radius conventions | **Completed** | Design conventions documented, Blueprint/CSS spacing normalized, four static regression tests added; exact-head CI and CodeQL passed. See the M1-02 record below. |
| UI-14 | M3-01 Extracted/History audit and F-301/F-302 test remediation | **Completed within bounded scope** | Read-only audit completed; History refresh contract test reconciled; Extracted search-announcement edge cases covered; exact-head CI and CodeQL passed. M3 was Partial at that historical point; its subsequent operational closure is recorded below. |
| UI-15 | F-303-01 History TTS action-label semantics and state tests | **Completed** | State-specific tooltip and accessible labels implemented; four-state assertions and CHANGELOG entry added. Exact-head CI #44027455501 and CodeQL #44027455444 passed on `2d503db3b98383ab0b293f7e7752b583826a40c9`. F-303-02 was subsequently deferred to native M7 validation; F-303-03 assertions were later added and M3 closed operationally within agreed scope. |
| UI-16 | M5-02 approved automated UI contract tests | **Completed within approved scope** | Shortcuts search/Escape, static menu action/scope contract and toast delegation/title/priority tests. Banner dismissal and toast lifecycle excluded. Exact-head CI #44135571249 and CodeQL #44135571322 passed. |
| UI-17 | M5-03 portal-banner Dismiss correction | **Completed** | Connected `Adw.Banner::button-clicked` to the hide handler; two GTK regression tests passed in temporary run #44141439001. Exact code/test head `74f6a4ef` passed CI #44142298765 and CodeQL #44142298673. CHANGELOG records the user-visible fix. |
| UI-18 | M5 agreed-scope closure and global documentation reconciliation | **Completed by maintainer decision** | P3 candidates are deferred/non-blocking; native visual, Orca/AT-SPI and physical keyboard checks belong to M7; toast lifecycle remains excluded. Global roadmap, workstream roadmap and HANDOVER record M5 Completed within agreed scope. |

## Completed work — scope and evidence

### UI-01 — M1 Preferences and lifecycle

- Preferences are separated into General, Editor, Voice and Languages pages.
- TTS catalog initialization is asynchronous and cached-first.
- OCR request ownership follows latest-operation-started-wins; stale callbacks and obsolete work cannot take ownership of the active spinner or publish stale results.
- The current PR CI run is the latest aggregate automated verification for the branch baseline. Detailed historical implementation records remain in `HANDOVER.md`.

### UI-02 — M2 Extracted

- Compact header and lower action bar are in place.
- Existing SearchBar and text-scroller behavior are retained; regression tests protect the scroller.
- Do not describe this as a new implementation task unless the requirement audit finds a concrete uncovered acceptance criterion.

### UI-03 — M2-B T1 Welcome

- Screenshot remains the primary action.
- Open Image, Paste Image and Drop Image remain the same secondary controls, reparented between the row and More options layout rather than duplicated.
- The page retains its asynchronous drop target and uses constrained content with vertical scrolling.
- Automated focus restoration and responsive layout tests are present.
- The latest CI explicitly passed `test_welcome_page_scrolls_when_vertical_viewport_is_constrained`; the test exercises a mapped GTK scroller with actual overflow and reaches the lower scroll bound.
- No manual desktop interaction is claimed.

### UI-04 — M2-B T2 palette and runtime CSS

- Approved green roles are implemented: `#16A36A` accent, `#0F7650` suggested-action background/light-surface accent text and `#21B77A` dark-surface accent text; suggested-action foreground is white.
- Runtime CSS loading is implemented through the GResource-backed provider and application startup lifecycle.
- Palette, contrast and stylesheet-provider regression tests exist.
- **Documentation discrepancy:** `docs/superpowers/plans/2026-11-15-anura-m2b-palette.md` still has every task checkbox unchecked, despite the implementation and tests being present. UI-07 must reconcile the plan with verified delivery evidence; do not infer that the implementation is absent from the stale checkboxes.

### UI-05 — M2-B T3 shell geometry

- Initial window dimensions are clamped to monitor geometry; actual monitor selection is resolved after realization and monitor changes trigger re-clamping.
- Only normal-state window dimensions are persisted.
- Preferences minimum-size constraints and Shortcuts resizability were addressed.
- GTK exposes monitor geometry but no universal panel/dock-excluded work-area API; no dock-aware sizing guarantee is made.

### UI-06 — M2-B T4 accessibility

- A1: accessible language-download labels and semantic start/completion/failure announcements.
- A2: deduplicated/debounced OCR, TTS and search status announcements with lifecycle cleanup.
- A3: automated focus traversal and responsive focus-restoration tests.
- A4: reduced-motion preference support with compatibility fallback; application does not write desktop-wide settings.
- A5: contrast and theme-role tests for application-controlled colors.
- The accessibility implementation plan records completed A1–A5 work and its earlier CI evidence. The current aggregate CI run provides a newer branch-level verification point.
- Real Orca/AT-SPI and manual keyboard checks are excluded by the maintainer's current decision; automated GTK focus tests do not establish screen-reader runtime conformance.

## Next tasks — detailed acceptance criteria

### UI-07 — Reconcile delivery documentation

**Allowed scope:** documentation only; no application source changes, no branch rebase, no merge, and no PR state transition.

1. Update `HANDOVER.md` so it links to this roadmap as the authoritative progress register and clearly identifies older entries as historical evidence where their head/run/status is superseded.
2. Update the palette implementation plan checkboxes and completion/evidence notes to reflect the actual implementation and CI evidence. Do not fabricate historical test commands or commits.
3. Review the accessibility plan and other relevant plan records for stale head SHAs, CI counts, obsolete manual-validation gates or contradictory completion claims. Preserve historical records but label them as historical; add a current pointer to this roadmap where appropriate.
4. Inspect PR #648's current body. Replace outdated statements that treat excluded manual GNOME/Orca/keyboard checks as pending merge gates with an accurate statement that they were explicitly excluded by maintainer decision. Keep Draft and unmerged. Update the latest CI/head evidence only if the PR body can be safely edited without altering its review state.
5. Verify links and consistency among roadmap, HANDOVER, plans, CHANGELOG and PR body.
6. Record changed paths, commit SHA and any CI result in this roadmap before proceeding to UI-08.

**Completion evidence:** GitHub file contents at the resulting branch head, PR #648 still Draft/open/unmerged, and a clear diff of documentation-only changes. A documentation-only commit is not by itself proof that application CI was rerun.

### UI-08 — Requirement-to-delivery traceability audit

1. Use the original PR #448 description and exact original changed-file inventory as historical source material, plus the approved M2-B palette/accessibility specifications and the current PR #648 diff.
2. Build a requirement matrix with one row per accepted requirement: source, intended behavior, current implementation path, regression test, current CI evidence and status.
3. Classify each requirement as **implemented and verified**, **implemented but evidence incomplete**, **deferred by decision**, or **not transferred / unresolved**.
4. Do not treat a historical PR description as authority to reintroduce a change if it conflicts with later maintainer decisions or current architecture.
5. Do not create a new implementation task until every requirement has a disposition and the evidence gaps are explicit.

**Completion evidence:** reviewed traceability matrix in the roadmap or a linked plan, with each unresolved item explained and no inferred feature scope.

### UI-09 — Next task definition and approval

- Convert only a concrete UI-08 unresolved requirement into a bounded task with files, expected behavior, regression tests and CI acceptance criteria.
- If no unresolved implementation requirement remains, recommend closure/readiness review rather than inventing more UI work.
- Present the task and wait for explicit maintainer approval before implementation.

### UI-10 and UI-11 — Future implementation and verification

- Implementation is not authorized by the creation of this roadmap.
- Follow the maintainer-approved execution approach. Keep changes on the authorized working branch.
- Add regression tests and update CHANGELOG/documentation when relevant.
- Run the existing GitHub Actions CI matrix and inspect the actual job conclusions and logs.
- Use the AI Delivery Evidence Checker only as a secondary evidence assessment; it does not replace CI execution or source inspection.
- Report failures, skipped jobs, warnings and environment limitations accurately.

## Progress update template (mandatory after each completed task)

Append or update the relevant task record before starting the next task:

- **Task ID / title:**
- **Outcome:** completed / partial / blocked
- **Files changed:**
- **Branch and resulting head commit:**
- **Tests:** exact command or CI job, counts and result
- **CI run:** URL and conclusion; identify skipped jobs
- **Limitations / exclusions:**
- **Next permitted task:**
- **Roadmap updated:** yes (must be yes before proceeding)

## Change log

### 2026-11-16 — Initial roadmap and evidence reconciliation

- Created after a read-only audit of PR #648, its current head and CI run, HANDOVER, and the M2-B palette/accessibility plans.
- Confirmed completed M1/M2/M2-B implementation areas and identified stale plan/handover/PR evidence as a documentation task, not a reason to invent another feature.
- Next task is UI-07, documentation reconciliation only.


### 2026-11-16 — UI-00 completion and roadmap publication

- UI-00 is complete: the read-only audit has been converted into this authoritative progress register.
- Created this roadmap and linked it from `HANDOVER.md` in documentation-only commit `95fb1ed70ea4dc05a7a2bd273d9ff08772198b93` (the roadmap file itself was introduced immediately before that link commit).
- Current PR head after the documentation commits: `95fb1ed70ea4dc05a7a2bd273d9ff08772198b93`.
- Re-checked PR #648: open, Draft, unmerged, target `feature`. No protected branch was modified.
- The latest full application CI evidence remains run [#43801048308](https://github.com/D3M-Sudo/Anura/actions/runs/43801048308) on the prior application/workflow head `cc8aaad6601f25b9e96f3d2eb9f78bc9fb3c524d`. The two commits in this roadmap-publication step are documentation-only; no claim is made that CI ran on the new documentation head.
- UI-07 remains the next task. Only the HANDOVER roadmap link is complete; palette/accessibility plan reconciliation and PR description correction remain outstanding.
- **Roadmap updated before proceeding:** yes. No subsequent task has started.


### 2026-11-16 — Roadmap hierarchy aligned with global plan

- Reframed this document as the subordinate PR #648 implementation/evidence register.
- Linked the primary [Global Anura UI/UX Modernization Roadmap](2026-11-16-anura-ui-modernization-global-roadmap.md), which restores the full approved M0–M7 scope across all application windows and components.
- Clarified that PR #648 contributions are partial at global phase level unless the global traceability matrix explicitly marks a requirement satisfied.
- No application source, CI workflow, PR state or protected branch was changed by this documentation update.
- Global roadmap creation commit: `7683f8ea733f8218eb223b2f710291a87592a514`.
- This workstream document is updated before proceeding; UI-07 remains the next detailed workstream task (documentation reconciliation), and global M0-A remains the next application-wide audit task after explicit approval.


## UI-12 — M2-D Extracted and History navigation-state implementation

**Authorization:** maintainer approved complete M2-D implementation on 2026-11-16 after reviewing the bounded file/test/CI plan.

### Approved behavior

- **Extracted (decision 1C):** preserve the current OCR result when navigating away; replace it only when the next extraction completes.
- **History (decision 2C):** preserve the expanded entry and vertical scroll position across refresh/navigation in the current application session; do not persist this transient view state across process restarts.

### Implementation and regression coverage

- `anura/widgets/extracted_page.py`: `do_hiding()` no longer clears the text buffer; it continues emitting the existing `go-back` signal.
- `anura/widgets/history_page.py`: capture the expanded entry's stable ID and the containing scroller's vertical adjustment before rebuilding; map rebuilt rows by entry ID; restore expansion and scroll through a generation-guarded GLib idle callback. A removed entry is not re-expanded. No new GSettings key, disk persistence, service change or data-model change.
- `tests/test_widgets.py`: GTK tests verify retention/replacement, navigation round-trip, focus acquisition on Extracted navigation and TTS stop when returning to Welcome.
- `tests/test_history_ui.py`: headless regression tests cover refresh snapshot, matching-row expansion, scroll restoration, stale refresh/removed-entry safety and default state on a newly constructed page.
- `CHANGELOG.md`: existing `[Unreleased]` entries record the user-visible behavior and session-only scope; no duplicate entry was necessary.

### Final validation evidence

- **CI Quality Check & Release:** [run #43885843452](https://github.com/D3M-Sudo/Anura/actions/runs/43885843452), workflow run 2397, completed/success on exact implementation head `bb316f94d37629cc7566b24330a87b6e86029db3`.
- **Python Quality:** success — 630 passed, 6 skipped, 277 deselected.
- **Changelog integrity:** success.
- **GTK Integration Tests:** success — 436 passed, 5 skipped, 636 deselected, 2 warnings. The five M2-D GTK regression cases (Extracted retention/replacement, navigation round-trip, History state restoration, Extracted text-view focus, and TTS stop on return to Welcome) passed.
- **AppImage:** x86_64 and aarch64 builds succeeded; complete AppImage release-set validation succeeded.
- **Flatpak:** x86_64 and aarch64 builds succeeded; multi-architecture release-artifact validation succeeded.
- **CodeQL:** [run #43885843419](https://github.com/D3M-Sudo/Anura/actions/runs/43885843419), completed/success on the same exact commit.
- **publish-release:** skipped as expected for a pull-request run; no release was published.
- The History unit tests for snapshot/restore, stale refresh callbacks, removed entries and default state on a new page passed in Python Quality. Current-head Python Quality also completed successfully.
- These are automated CI results only. Manual GNOME/GTK visual checks, real Orca/AT-SPI checks and manual keyboard-navigation checks remain **excluded**, not passed. CI's `NO_AT_BRIDGE=1` and `GTK_A11Y=none` settings do not validate real assistive-technology behavior.
- Warnings were non-fatal; all executable jobs concluded successfully.

### Disposition and limitations

- **UI-12 / M2-D bounded task:** implementation, automated regression coverage, CHANGELOG record and exact-head CI/CodeQL verification complete.
- **Global M2 phase:** remains Partial. This workstream does not complete broader Welcome/main-shell requirements or the full M0–M7 modernization.
- **Manual checks:** GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard-navigation checks remain explicitly excluded, not passed or pending blockers.
- **PR:** [#648](https://github.com/D3M-Sudo/Anura/pull/648) remains Open, Draft, unmerged, targeting `feature`. No protected branch was modified.


## UI-13 — M2-E Welcome and main-shell residual-gap audit (2026-11-16)

**Status:** Completed — read-only audit and documentation record only.

### Welcome disposition

- Screenshot remains the primary action; Open Image, Paste Image and Drop Image remain the same secondary controls, reparented according to measured preferred widths.
- Existing implementation/test coverage addresses 360×600, 640×480, 900×600 and 1280×800; constrained-height scrolling; responsive focus preservation; drag/drop; and language-selector accessible naming/state updates.
- No broad Welcome rewrite or additional feature is justified by this audit.

### Main-shell findings

1. **High — History TTS lifecycle:** History row playback starts through `HistoryPage._on_tts_clicked()`. The explicit stop is in `AnuraWindow.show_welcome_page()`; standard `Adw.NavigationView` back navigation from History does not necessarily call that method. Playback can continue after returning to Welcome. This is the primary M2-F functional correction candidate.
2. **Medium — route integration:** no end-to-end test was found for the actual `AnuraWindow` History-open/back route.
3. **Medium — focus:** focus restoration across the actual History → Welcome route is not covered end-to-end.
4. **Geometry:** helper/policy tests exist for sizing, monitor selection and persistence. The maintainer explicitly declined live multi-monitor geometry verification; no such test is planned or required.

### Evidence and limits

- Inspected `AnuraWindow`, `WelcomePage`, `HistoryPage`, `TtsController`, Blueprint templates and related Welcome/navigation/geometry test sources on pre-recording head `97a42a0c17252cc2a36be563e87255cb2d306e63`.
- No source, test, workflow or CHANGELOG file was modified. No tests or CI were run for this audit.
- Manual GNOME/GTK visual, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed or blockers.
- Context7 Libadwaita navigation documentation was consulted. AI Delivery Evidence Checker structured the criteria; its combined verdict call returned `out_of_scope`, so no combined checker verdict is claimed.
- PR #648 was verified Open/Draft/unmerged, base `feature`; no protected branch or PR metadata was changed.

**Next permitted task:** define the bounded M2-F implementation/test plan and request explicit approval before implementation. Do not add live multi-monitor verification.

## M2-F — History TTS navigation lifecycle (2026-11-16)

### Implemented

- `AnuraWindow` centrally observes `Adw.NavigationView:visible-page` using a tracked signal connection.
- When the previous visible page is History and the new visible page is different, the handler stops TTS. This covers native back navigation, gestures and transitions to any destination without wiring individual navigation controls.
- The explicit `show_welcome_page()` route already stops TTS; the lifecycle handler avoids a duplicate stop for that same transition.
- Added five real GTK integration tests around the actual `AnuraWindow` and `Adw.NavigationView`: native History → Welcome, explicit History → Welcome, History → Extracted, entering/remaining in History, and History exit with TTS already idle. All five passed.
- Changed files: `anura/window.py`, `tests/test_widgets.py`, `CHANGELOG.md`. No dependencies, OCR pipeline, Welcome redesign, manifests, workflows or live multi-monitor tests were added.

### Exact-head validation

- Final code/CHANGELOG head: `acd1f03e3dee92173af98b4afe7f712806747afe`.
- CI Quality Check & Release [#43897822566](https://github.com/D3M-Sudo/Anura/actions/runs/43897822566): **success** on the exact head. Python Quality: **630 passed, 6 skipped, 277 deselected**. GTK Integration: **441 passed, 5 skipped, 636 deselected, 2 warnings**; all five M2-F tests passed. Changelog integrity passed.
- AppImage x86_64 and aarch64 builds passed; Flatpak x86_64 and aarch64 builds passed; complete AppImage release-set validation and multi-architecture release-artifact validation passed. `publish-release` was skipped as expected for a PR.
- CodeQL [#43897822286](https://github.com/D3M-Sudo/Anura/actions/runs/43897822286) passed on the same code head.
- The subsequent roadmap/HANDOVER commits are documentation-only; the CI run above is not represented as having tested those later documentation commits.
- Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed. Live multi-monitor verification remains out of scope.

### PR state

PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`. No protected branch, PR metadata or release state was changed.


## M1-02 — GTK4/Libadwaita design conventions (2026-11-16)

- **Outcome:** completed for the M1-02 scope. This is a contribution to global M1, not closure of the whole Design System phase.
- **Changed files:** `docs/ui-design-system.md`, `data/style.css`, `data/ui/extracted_page.blp`, `data/ui/language_popover.blp`, `data/ui/language_popover_row.blp`, `data/ui/language_row.blp`, `data/ui/share_row.blp`, `data/ui/welcome_page.blp`, `tests/test_ui_palette.py`, `CHANGELOG.md`.
- The design document specifies Libadwaita semantic typography, spacing values 4/8/12/16/24 px, custom radius roles, native control hierarchy and theme compatibility, including GTK CSS numeric-token limitations.
- Four static regression tests cover Blueprint spacing, GTK stylesheet spacing, custom corner radii and the semantic typography exception.
- The Welcome compact screenshot action retains a documented 6 px spacing exception: 8 px caused three responsive GTK test failures by increasing the compact action width. The regression test enforces that this exception remains documented.
- **Implementation range:** `b4f8c0798933fb410dd4bf24cb808e183aba932a` → `6dece44cd3deb57fc43cb276db4a291a771e9584` (8 commits).
- **CI:** [#43907544843](https://github.com/D3M-Sudo/Anura/actions/runs/43907544843) success on exact head. Python: 634 passed, 6 skipped, 277 deselected. GTK: 441 passed, 5 skipped, 640 deselected, 2 warnings. Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and release-artifact validations passed; publish-release skipped as expected.
- **CodeQL:** [#43907544861](https://github.com/D3M-Sudo/Anura/actions/runs/43907544861) success on the same SHA.
- No manual visual, Orca/AT-SPI or manual keyboard verification is claimed. No OCR/pipeline/model, architecture, dependency, portal or OS integration changes were made.
- PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`.

**Next:** prepare a bounded M1-03 semantic-color role audit plan for review. The PR description remains unchanged pending separate approval for PR metadata edits.

## M1-03 — Semantic color-role audit (2026-11-16)

- **Outcome:** read-only audit completed. No source, test, CHANGELOG, workflow or PR metadata changes were made.
- **Inspected:** `data/style.css`, all 14 Blueprint UI files, relevant Python widget/application modules, `anura/main.py`, `docs/ui-design-system.md` and `tests/test_ui_palette.py`. This was a scoped inspection, not an exhaustive repository-wide color scan.
- **Role mapping:** `#16A36A` brand/graphical accent; `#0F7650` + white suggested-action pair and light-scheme standalone green; `#21B77A` dark-scheme standalone green; `@warning_color` warning; `@popover_bg_color`, `@theme_base_color`, `@theme_fg_color` and `@borders` theme-managed surfaces/text/borders; translucent black shadows decorative.
- **Contrast samples:** white on `#0F7650` 5.63:1; `#0F7650` on `#F6F5F4` 5.17:1; `#21B77A` on `#242424` 6.00:1 and on `#353535` 4.74:1. Brand accent `#16A36A` is 3.24:1 on white and should remain graphical rather than general normal text. These are calculated representative pairs, not runtime measurements.
- **Findings:** no Critical/High issue demonstrated. Medium: downloaded-language success uses explicit light/dark green values instead of a semantic Libadwaita success class. Low: repeated standalone green literals and missing repository-wide color-literal guard. Informational: no explicit error color role found in audited CSS; no missing user-facing error state is inferred.
- **Theme review:** existing `default`, `force-light` and `force-dark` mapping through `Adw.StyleManager` is present. Custom green states have dark overrides; surfaces and warning use theme-managed colors.
- **Test gaps:** no runtime cross-surface test across all three theme modes; no repository-wide scanner for unclassified hardcoded colors; no explicit test for semantic success/error style-role mapping. Existing contrast tests use fixed representative surfaces.
- **Context7 Libadwaita:** confirms `.accent`, `.success`, `.warning`, `.error` classes and recommends theme-aware colors for custom styling. This is a future evaluation point, not approval to change the palette.
- **AI Delivery Evidence Checker:** 10 criteria; delivery partially supported (5 supported, 5 partial); test evidence partially supported; verdict `needs_more_evidence` (level 3). No tests were run during this audit. Historical CI #43907544843 applies to SHA `6dece44cd3deb57fc43cb276db4a291a771e9584`, not audit head `f5225e2e82973db63822ca8b3b26cf13619b907a`.
- Manual GNOME/GTK visual, Orca/AT-SPI and manual keyboard checks remain excluded, not passed. PR #648 remains Open/Draft/unmerged, base `feature`; no protected branch or PR metadata was changed.

**M1-04 design proposal (2026-11-16):** approach B selected by the maintainer. Design: [`docs/superpowers/specs/2026-11-16-m1-04-semantic-colors-design.md`](../specs/2026-11-16-m1-04-semantic-colors-design.md), commit `b724f2688475bfd94e03c6e085863bfbc066c80c`. The proposal covers conditional `.success` adoption, role-safe green consolidation, classified color-literal scanning and automated theme-mode transitions. Design only; no source/test implementation is authorized.

**M1-04 implementation update (2026-11-16):** the approved plan has been started. The scanner portion is implemented and its eight unit tests pass. Exact-SHA CI [#43928078842](https://github.com/D3M-Sudo/Anura/actions/runs/43928078842) and CodeQL [#43928078536](https://github.com/D3M-Sudo/Anura/actions/runs/43928078536) passed on `f300740f2691c0a122ea4b067b607a41cef51273`. Python: 642 passed, 6 skipped, 277 deselected; GTK: 441 passed, 5 skipped, 648 deselected, 2 warnings; formatting reported 232 files already formatted. AppImage/Flatpak x86_64/aarch64 and release artifact validations passed. `publish-release` skipped as expected.

**Important status correction:** M1-04 is **Partial**, not complete. The successful run verifies the scanner and the existing suites, but does not establish the planned semantic success-style consolidation or new GTK theme-transition integration tests. The `.downloaded label` CSS fallback remains and `LanguageRow.update_ui()` does not currently apply a corresponding style class. These remaining plan items require a separate bounded continuation and verification.

**Historical next-step note — superseded by M0-C (2026-11-16):** continue M1-04 with semantic success styling and GTK theme-transition coverage. The approved M1-04 work was subsequently completed within scope; see the completion record and global roadmap.


## M1-04 — semantic color implementation completed (2026-11-16)

- **Outcome:** M1-04 implementation complete for approved scope; M1 remains Partial.
- Added a repository-discovering scanner and eight tests for unclassified hardcoded UI colors. Intentional colors require path-specific rationale.
- Linked the installed-language state to the existing `downloaded` CSS class in `LanguageRow.update_ui()`; the class is added/removed with installation state. No download/install behavior changed.
- Retained application-owned light/dark green values. Libadwaita `.success` was not adopted because it modifies widget accent and does not ensure contrast against the actual resolved surfaces. Repeated values remain where roles differ.
- Added automated theme-transition coverage for `default`, `force-light` and `force-dark`, including downloaded language, History empty-state and focus classes. This does not claim pixel-level contrast across arbitrary desktop themes.
- Exact code/test SHA: `7f6a7045feefb019c869cc74aecc31a5e991a74d`. CI #43951965392 and CodeQL #43951968944 passed on this SHA. Python 643 passed, 6 skipped, 277 deselected; GTK Integration, Changelog integrity, AppImage and Flatpak x86_64/aarch64 builds and release-set validators passed. `publish-release` skipped as expected for a PR.
- Manual GNOME/GTK visual, Orca/AT-SPI and manual keyboard checks remain excluded, not passed. No OCR, dependency, architecture, portal or OS integration changes.


## M0-C reconciliation — current workstream boundary (2026-11-16)

The [global roadmap](2026-11-16-anura-ui-modernization-global-roadmap.md) is the sole authority for current M0–M7 phase status, global priorities, dependencies and application-wide requirement disposition. This file remains the detailed PR #648 workstream/evidence register; completion of a PR task does not complete a global phase.

- M0-C global backlog/document reconciliation is complete. Its phase snapshot was recorded on 2026-11-16 as M0 Completed; M1–M4 Partial; M5 Not started as a complete phase; M6–M7 Partial. This is a historical snapshot, superseded for M1 by the 2026-11-17 operational closure decision recorded below and by the current status table in the global roadmap.
- M1-02 conventions, M1-03 audit, M1-04 semantic-color/scanner/theme-test work, and M1-05 through M1-07 are complete within their approved scopes. The maintainer subsequently closed M1 as Completed (operationally) on 2026-11-17; the remaining manual rendered-UI, keyboard, Orca/AT-SPI and live multi-monitor checks are explicitly deferred to M7 and are not claimed as passed.
- **M1-05 and M1-06 are complete within their bounded scopes.** M1-06 closes F1 reduced-motion handling for Shortcuts and F2 production-tree color-scanner enforcement. CI #43974750869 completed with conclusion `success` on the exact source/test SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`. All 9 executable jobs passed: Python quality (644 passed, 6 skipped, 277 deselected); GTK Integration (447 passed, 5 skipped, 650 deselected, 2 warnings); Changelog integrity; AppImage x86_64 and aarch64 builds, architecture/update-metadata verification, clean-host smoke tests and artifact uploads; Flatpak x86_64 and aarch64 builds/runtime checks; multi-architecture Flatpak artifact validation; and complete AppImage release-set validation. The `publish-release` job was skipped as expected for a pull request. CodeQL #43974750821 also passed on the same source/test SHA.
- Earlier sections in this roadmap and older task plans may contain historical “next task” directions that predate completed work. Preserve them as historical records; where they conflict with the current snapshot, the global roadmap and this reconciliation note supersede them.
- M1-06 implementation/test SHA is `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`. CI #43974750869 and CodeQL #43974750821 completed successfully; all applicable jobs passed, with `publish-release` skipped as expected for a PR.
- Manual GNOME/GTK visual, Orca/AT-SPI, manual keyboard and live multi-monitor checks remain excluded; screenshot capture remains deferred to the next release cycle.
- PR #648 remains Open/Draft/unmerged, targeting `feature`; this documentation update does not alter PR metadata or state.


## M1-05 — Cross-surface Design System audit (2026-11-16)

- **Outcome:** read-only audit completed. Detailed evidence and the surface matrix are in [M1-05 audit report](../../audit/ui-design-system-m1-05-2026-11-16.md).
- Reviewed source snapshot `fb1bcbe89f0ce982fc4adad60630a5a88496dd1`: 14 Blueprint templates, 15 Python UI modules, main window/application, reduced-motion utility, CSS, design-system guide and relevant tests/CI definitions.
- Positive baseline: shared spacing/radius conventions are statically guarded; the documented 6 px Welcome exception and 1.15em hero typography exception are explicit; native GTK4/Libadwaita patterns are used broadly.
- Findings: **F1 Medium** — separate `ShortcutsOverlay` window does not receive the main window's reduced-motion CSS class despite applying `.anura-fade-in`; **F2 Medium** — scanner fixture tests do not invoke the scanner against the production tree in CI; **F3 Low** — apparently orphaned custom CSS selectors; **F4 Low** — `title`/`h4` typography classes are not mapped in the design-system guide.
- **Historical note:** at the time of M1-05, M1-06 required separate scope and approval. That approval was subsequently received and the bounded F1/F2 implementation is recorded in the M1-06 section above. F3/F4 remain deferred.
- No application source, tests, workflows, CHANGELOG, dependencies, OCR behavior, architecture, PR metadata or protected branches changed. No tests or CI were run for this audit; manual GNOME/GTK visual, Orca/AT-SPI and keyboard checks remain excluded.
- PR #648 state is unchanged: Open/Draft/unmerged, base `feature`, head branch `fix/ui-modernization-aligned`.


## M1-06 — Reduced-motion and production color-scanner enforcement (2026-11-16)

- **Implementation/test head:** `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`. The source/test diff changes only `anura/widgets/shortcuts_overlay.py`, `tests/test_widgets.py` and `tests/test_ui_color_scanner.py` beyond the approved design/plan documents.
- **F1 implementation:** the separate Shortcuts window reads GTK settings associated with its display, reuses the existing accessibility helper, observes supported setting notifications and updates the reduced-motion state live. It removes root `anura-fade-in`/`anura-card` motion classes while reduced motion is active and restores them in normal mode. Settings callbacks are disconnected on close-request and in `do_destroy()`.
- **F1 tests:** GTK coverage includes initial normal/reduced states, live `gtk-interface-reduced-motion` transitions, root animation/transition class behavior, older-GTK fallback when the reduced-motion property is absent, live `gtk-enable-animations` changes and handler cleanup.
- **F2 implementation:** repository-root pytest enforcement uses the existing scanner and an exact path/value rationale map; it does not add a separate workflow or change the scanner's production-source scope.
- **Final verification on the exact SHA:** CI #43974750869 completed with conclusion `success` on the exact source/test SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`. All 9 executable jobs passed: Python quality (644 passed, 6 skipped, 277 deselected); GTK Integration (447 passed, 5 skipped, 650 deselected, 2 warnings); Changelog integrity; AppImage x86_64 and aarch64 builds, architecture/update-metadata verification, clean-host smoke tests and artifact uploads; Flatpak x86_64 and aarch64 builds/runtime checks; multi-architecture Flatpak artifact validation; and complete AppImage release-set validation. The `publish-release` job was skipped as expected for a pull request. CodeQL #43974750821 also passed on the same source/test SHA. Ruff, mypy and Bandit passed within Python quality.
- **TDD red evidence:** test-only commits produced expected GTK failures before the reduced-motion implementation and before close-request cleanup; the final implementation/test SHA above is green for the complete GTK suite.
- F3/F4 follow-up is recorded in M1-07 below. Manual visual, Orca/AT-SPI, manual keyboard and live multi-monitor checks remain excluded; screenshots remain deferred. PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`.


## M1-07 — F3 CSS selector cleanup and F4 typography documentation (2026-11-17)

- **Outcome:** M1-07 completed within the approved follow-up scope. The maintainer subsequently closed the global M1 cycle as **Completed (operationally)**; manual visual/accessibility verification is deferred to M7.
- **F3 audit:** temporary workflow [#43981815120](https://github.com/D3M-Sudo/Anura/actions/runs/43981815120) succeeded on audit commit `498f8de52cff7c4ea9d12f0ea9a9b19e913d81ce`. No direct consumers were found in tracked Python/Blueprint application sources. The uploaded [audit artifact](https://github.com/D3M-Sudo/Anura/actions/runs/43981815120/artifacts/14283985075) and job log record the search.
- **F3 cleanup:** removed unused custom selector groups and their dedicated keyframes from `data/style.css`; removed stale reduced-motion references to `.share-row` and `.welcome-card`. No speculative future selectors were retained. The temporary workflow was removed after collecting evidence.
- **F4 documentation:** the design-system guide now distinguishes supported `.heading` from arbitrary/unverified `.title` and `.h4` classes. Existing Blueprint assignments remain unchanged.
- **Limitations:** the consumer audit searches literal strings in tracked files and cannot rule out dynamically synthesized names or external integrations. No manual rendered UI or assistive-technology test is claimed.
- **Files updated:** `data/style.css`, `docs/ui-design-system.md`, M1-05 audit report, global roadmap, HANDOVER, CHANGELOG and M1-06 execution ledger.
- **Final CI/CodeQL:** verified on final head `443fd6085dfa14ef9941015e688760ff5874ec4f`: [CI #43982790571](https://github.com/D3M-Sudo/Anura/actions/runs/43982790571) and [CodeQL #43982790585](https://github.com/D3M-Sudo/Anura/actions/runs/43982790585) both completed with conclusion `success`. Python quality, GTK Integration, Changelog integrity, AppImage/Flatpak x86_64+aarch64 builds and release-artifact validators passed; `publish-release` was skipped as expected for a PR.
- PR #648 remains Open/Draft/unmerged, base `feature`; protected branches and PR metadata remain unchanged.


## M1 — operational closure (2026-11-17)

- The maintainer selected **A — operationally completed**, with the remaining manual verification deferred to M7. The global roadmap is authoritative for phase status; this subordinate workstream records the final evidence and disposition.
- M1-02 through M1-07 are complete within their approved scopes. Final validation was performed against branch head `443fd6085dfa14ef9941015e688760ff5874ec4f`.
- [CI #43982790571](https://github.com/D3M-Sudo/Anura/actions/runs/43982790571) and [CodeQL #43982790585](https://github.com/D3M-Sudo/Anura/actions/runs/43982790585) both succeeded on that exact head. The CI build/test and packaging matrix passed; `publish-release` was skipped as expected for a PR.
- Not performed: manual GNOME/GTK rendered-UI review, manual keyboard navigation, real Orca/AT-SPI verification and live multi-monitor checks. These are deferred to M7 and must not be represented as passed. Screenshot capture remains deferred to the agreed later release stage.
- PR #648 remains Open, Draft and unmerged, targeting `feature`. This documentation update does not change PR metadata, merge state or any protected branch.


## M2 — operational closure (2026-11-17)

- **Outcome:** the maintainer selected option A. M2 is **Completed (operationally)** for this work cycle; the global roadmap remains authoritative for phase status and global scope.
- **M2-G01:** History → Welcome focus behavior implemented and exact-head CI passed on `7d34cf8f92435c85d9ba3537ead42c7bb98519a4`.
- **M2-G02:** asynchronous Welcome drag-and-drop implementation and eight regression tests completed on `f52e437d9bdfdf6200d26449152e3ffeeacc14be`. CI [#43995410588](https://github.com/D3M-Sudo/Anura/actions/runs/43995410588) and CodeQL [#43995410567](https://github.com/D3M-Sudo/Anura/actions/runs/43995410567) both passed on that exact head. Python quality: 652 passed, 6 skipped, 279 deselected; GTK Integration, Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and release artifact validators passed. Release publication was skipped as expected for a PR.
- **Deferred to M7:** manual GNOME/GTK visual checks, manual keyboard navigation and real Orca/AT-SPI verification. They were not performed and are not claimed as passed or as M2 blockers. Live multi-monitor verification remains excluded.
- **Deferred to M5:** app-wide menu consistency and review of intentional menu differences.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`. No merge, protected-branch update or PR metadata change was made.
- **Next:** M3-01 read-only audit, separately scoped; no M3 implementation is authorized by this closure.


## M3-01 — Extracted and History audit; F-301/F-302 remediation (2026-11-17)

### Audit disposition

- Extracted baseline includes header/actions, editable text and scrolling, search navigation/wrap, undo/redo, TTS/share/statistics and OCR-result focus. Existing accessible-search announcement behavior was found in `tests/test_accessible_status_announcements.py`; F-302 was therefore refined from “missing tests” to a limited edge-case coverage gap.
- History baseline includes entry list/empty/disabled states, expandable details, copy/editor/TTS actions, clear confirmation, refresh/navigation and in-session expansion/scroll restoration.
- No production bug was established by the read-only audit. F-301 was a contradictory test expectation; F-302/F-303 are test-coverage gaps. Visual/viewport evidence is not exhaustive.

### F-301 — History refresh contract

- Maintainer decision: **A1 — `HistoryPage.refresh()` preserves view state**. Preserve the expanded entry if it remains, preserve scroll, clear expansion if the entry disappears, and maintain the contract across navigation.
- Updated `tests/test_history_expansion_real.py` so the former “every row collapsed” test now verifies restoration of the same expanded entry and that no more than one row remains expanded.
- Commits: `e7ee3032bc375ea953c18a809b2ccd42a9397aad` (test contract), `0988708e88a162417a9622500c813ae3c1a98dac` (Ruff formatting only).

### F-302 — Extracted search announcements

- Added focused coverage for the visible/accessibility “Searching…” state, one-result announcement after the 400 ms debounce with LOW priority, zero-result “No matches”, and clearing search/restoring the accessible label while cancelling a pending announcement.
- A CI failure exposed unstable independent MagicMock values for `Gtk.AccessibleAnnouncementPriority.LOW`; the test now uses a stable sentinel via `SimpleNamespace`. No production code was changed.
- Final test commit: `56d794502d84c0dfc392230867b4c90b6d08ee91`, file `tests/test_accessible_status_announcements.py`.

### Exact-head verification

- CI [#2497](https://github.com/D3M-Sudo/Anura/actions/runs/44006990401) and CodeQL [#699](https://github.com/D3M-Sudo/Anura/actions/runs/44006990338) both completed successfully on exact head `56d794502d84c0dfc392230867b4c90b6d08ee91`.
- Passed: Ruff lint/format, Mypy, Bandit, Vulture, Python tests with coverage, Flatpak runtime dependency coverage, Changelog integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture release-artifact validation.
- `publish-release` was skipped as expected for a pull request.
- No local test execution or TDD red→green demonstration is claimed; CI is the verification source. The evidence does not establish real Orca/AT-SPI or manual keyboard behavior.

### Boundaries and next task

- No production source, permanent/temporary workflow, CHANGELOG, protected branch or PR metadata was changed for F-301/F-302 remediation.
- PR #648 remains Open/Draft/unmerged, base `feature`, head `56d794502d84c0dfc392230867b4c90b6d08ee91`.
- M3 status at the time of this record was Partial; this interim status is superseded by the operational-closure record below.
- **Historical next-step note:** F-303-02 CI input experiments were later stopped and moved to M7-03/#655; F-303-03 initial accessible-label assertions were subsequently added. The next current task is M4-02 planning.


## F-303-01 — History TTS action-label semantics (2026-11-17)

### Implementation

- Updated the History TTS button's visible tooltip and `Gtk.AccessibleProperty.LABEL` to describe the current action:
  - `generating`: “Stop listening”
  - `playing`: “Pause listening”
  - `paused`: “Resume listening”
  - `idle` or inactive: “Listen to text”
- TTS execution and lifecycle logic were left unchanged.
- Added `test_tts_button_labels_describe_the_current_action` in `tests/test_history_ui.py`; it verifies both tooltip and accessible label for all four states.
- Added the corresponding user-visible accessibility change to `CHANGELOG.md`.
- Changed paths: `anura/widgets/history_page.py`, `tests/test_history_ui.py`, `CHANGELOG.md`.

### Exact-head validation

- Implementation/test/CHANGELOG SHA: `2d503db3b98383ab0b293f7e7752b583826a40c9`.
- CI [#44027455501](https://github.com/D3M-Sudo/Anura/actions/runs/44027455501): completed `success` on the exact SHA. Python quality, Changelog integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture release-artifact validation all passed. `publish-release` was skipped as expected for a PR.
- CodeQL [#44027455444](https://github.com/D3M-Sudo/Anura/actions/runs/44027455444): completed `success` on the same SHA.
- No local tests or TDD red→green sequence are claimed. The CI validates the code/test/CHANGELOG SHA above; subsequent documentation-only commits are not covered by those runs.
- Real Orca/AT-SPI and manual keyboard traversal were not performed; they remain excluded/deferred. The new automated test does not substitute for those checks.

### Boundaries and next task

- No workflow, dependency, protected branch or PR metadata was changed.
- PR #648 remains Open/Draft/unmerged, base `feature`.
- M3 status at the time of this record was Partial. The subsequent CI keyboard-traversal experiment was stopped and assigned to M7-03/#655; F-303-03 assertions were later added in `tests/test_history_ui.py`. See the M3 operational-closure record below.


## F-303-02 — suspended due to CI virtual-input limitation (2026-11-17)

- **Outcome:** suspended. The current XTest → Weston → Wayland → GTK CI path did not reliably deliver keyboard events to GTK; no application defect was established.
- **Evidence:** test commit `84ff4d50a3291b4328d28e657b251144d979e9c6`; CI [#44040005554](https://github.com/D3M-Sudo/Anura/actions/runs/44040005554) failed in GTK Integration (4 failed, 449 passed, 5 skipped, 663 deselected); CodeQL [#44040005537](https://github.com/D3M-Sudo/Anura/actions/runs/44040005537) passed on the same commit.
- **Diagnostics:** three failures were at the input-delivery boundary (Weston/XTest request not observed by GTK); one delivered Tab event did not move focus from the collapsed TextView. The latter is not classified as an app defect because the test route is not yet reliable.
- **Decision:** stop further F-303-02 CI input experiments. F-303-02 is suspended; F-303-03 remains deferred pending later disposition. No further workflow, test, production or dependency changes were made.

## M4-01 — Preferences and language selector audit + remediation (2026-11-17)

- **Outcome:** completed within approved scope: read-only audit followed by remediation of all four findings M4-F01–F04. Report: [M4-01 audit](../../audit/preferences-languages-m4-01-2026-11-17.md).
- **M4-F01:** network reachability now probes the hostname from `TESSDATA_URL` over HTTPS instead of `google.com`.
- **M4-F02:** PreferencesLanguagesPage owns a cancellable, cancels superseded checks and cancels on destruction; late or stale callbacks are ignored before touching widgets.
- **M4-F03:** LanguageRow now tracks one-shot idle refreshes through `_schedule_idle_update()` and prunes each source ID when its callback starts.
- **M4-F04:** the Preferences OCR model ListView has the localized accessible label “Available OCR models”; the gettext POT template includes the new message.
- **Regression tests:** added `tests/test_preferences_languages_lifecycle.py` with four focused tests covering configured source host, cancellation/late callback after disposal, completed idle-source cleanup and the accessible ListView name.
- **Changed files:** `anura/widgets/preferences_languages_page.py`, `anura/widgets/language_row.py`, `tests/test_preferences_languages_lifecycle.py`, `CHANGELOG.md`, `po/io.github.d3m_sudo.anura.pot`, and the M4-01 audit report.
- **Exact final-head evidence:** documentation-inclusive head `c0eaa426e2fa2c37eeb43c7e04200fe67848bb37`; CI [#44109820125](https://github.com/D3M-Sudo/Anura/actions/runs/44109820125), CodeQL [#44109819932](https://github.com/D3M-Sudo/Anura/actions/runs/44109819932).
  - Python quality — passed, including Ruff lint/format, Mypy, Bandit, Vulture, tests and Flatpak runtime dependency coverage. Coverage run: **661 passed, 6 skipped, 283 deselected**.
  - Changelog integrity — passed.
  - CodeQL — passed on the exact head.
  - GTK Integration — failed with **4 failed, 449 passed, 5 skipped, 667 deselected**. All four failures are the previously suspended F-303-02 XTest/Weston keyboard-traversal tests: three input events not observed by GTK and one focus-retention case after GTK received Tab. This is the already documented CI input-harness limitation, not a new M4 regression. No further F-303-02 changes are authorized in this work cycle.
  - AppImage x86_64/aarch64 — still in progress at the last check. Flatpak and downstream artifact-validation jobs were skipped because GTK Integration failed.
  - No local tests or manual GNOME/GTK, Orca/AT-SPI or keyboard checks are claimed.
- **Limits:** no local tests were run. No manual GNOME/GTK visual, real Orca/AT-SPI or keyboard checks are claimed; those remain excluded/deferred. No workflow, dependency, OCR engine/pipeline, protected branch or PR state changed.
- **Global status at the time of this record:** M4 remained Partial because other Preferences mapping, secondary-language refresh/removal and Voice lifecycle coverage gaps remained. M4-01's four audited findings are remediated; current gap disposition is recorded in M4-02 below.
- **Next:** M5-01 — read-only audit of Shortcuts, About, dialogs, popovers, menus, banners, toasts and notifications.


## 2026-11-17 — F-303-02 experimental GTK keyboard lane / CI unblocking

- **Decision:** retain the four F-303-02 keyboard traversal tests, but mark them `keyboard_traversal` and separate them from the required GTK Integration suite. This records a CI harness limitation, not a confirmed production accessibility defect.
- **Required GTK suite:** runs with `-m "gtk and not keyboard_traversal"`; the four experimental cases are excluded from this blocking job only.
- **Experimental lane:** `GTK Keyboard Traversal (experimental)` runs the four marked tests on its own GTK/Wayland/XTest environment. The job depends only on `python-quality`, has job-level `continue-on-error: true`, and remains visible in Actions without gating release builds.
- **Build graph correction:** `flatpak-builder` now depends on `python-quality` only, not the required GTK suite. `validate-release-artifacts` continues to depend on Flatpak builds. AppImage builds and AppImage artifact validation retain their existing independent dependency chain.
- **Debt tracking:** GitHub issue [#655 — Replace the F-303-02 GTK keyboard traversal CI input harness](https://github.com/D3M-Sudo/Anura/issues/655) records the evidence, constraints and acceptance criteria. The four tests must return to the required GTK suite only after the harness reliably observes real Tab/Shift+Tab at the GTK client boundary and passes repeated CI runs.
- **Last pre-change evidence:** CI [#44110517818](https://github.com/D3M-Sudo/Anura/actions/runs/44110517818) on `24c9f99f683de1ee26eb33e53678998326fc5ce9`: Python Quality, Changelog integrity, AppImage x86_64/aarch64 and complete AppImage release-set validation passed; GTK failed on the four F-303-02 tests; Flatpak builds and multi-architecture release-artifact validation were skipped. CodeQL [#44110517974](https://github.com/D3M-Sudo/Anura/actions/runs/44110517974) passed.
- **Validation status:** workflow/test-marker changes are committed; the new graph and exact-SHA CI results remain pending. No local tests or YAML validation are claimed. No production code, dependency, OCR behavior, CHANGELOG, protected branch, PR metadata, merge or release was changed.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`.


## F-303-02 — final disposition: defer physical keyboard validation to M7 (2026-11-17)

### Decision and evidence

The maintainer selected the cleanup fallback: stop CI input-harness experiments, remove the four CI-specific keyboard traversal tests and their synthetic input helpers, restore the ordinary GTK CI gate, and retain a tracked native-host validation obligation. This formally closes the *CI experimentation phase* only; it does not mark keyboard traversal as passed or F-303-02 fully validated.

- **Weston/XTest:** prior CI runs repeatedly failed to establish reliable Tab/Shift+Tab delivery at GTK's `EventControllerKey` boundary. One case received Tab but focus remained on a collapsed `Gtk.TextView`; this was not classified as a product defect because the harness was unreliable.
- **Sway/wtype:** [CI run #44120435948](https://github.com/D3M-Sudo/Anura/actions/runs/44120435948), tested head `bff387fcf5a07c6b580f47d60f98f9ff6966e319`. Sway, Wayland socket, `wl_seat` and `zwp_virtual_keyboard_manager_v1` were available; Sway reported the GTK test window focused. GTK did not receive the injected Tab event and reported `active=False`. The shell stopped on the first failure, so three-run repeatability was not tested. The evidence shows this harness was unsuccessful, not that CI virtual input is categorically impossible.

### CI and test cleanup

- Removed the experimental Sway job and its Sway/wtype/wayland-utils packages.
- Removed xdotool, Weston X11 host-window lookup and `WESTON_HOST_DISPLAY`, which existed only for XTest injection.
- Retained Xvfb + Weston X11 and the `wl_seat` pointer/keyboard preflight for ordinary GTK integration tests.
- Restored the regular GTK test selection and restored `flatpak-builder` to `needs: [python-quality, gtk-tests]`.
- Removed the four experimental tests and Sway/XTest helpers; retained unrelated History tests.
- No application source or runtime dependency changes. CHANGELOG was not changed because this is test infrastructure and validation disposition, not a product behavior change.

### Residual debt and acceptance

Issue [#655 — F-303-02 native-host keyboard traversal validation](https://github.com/D3M-Sudo/Anura/issues/655) remains open. M7-03 must validate on a native desktop session:

1. Tab and Shift+Tab reach the enabled History row suffix actions in forward and reverse order.
2. Expanded rows preserve keyboard reachability of suffix actions.
3. Collapsing a row while its text view has focus leaves keyboard navigation usable.
4. Expanding another row preserves the single-open-row behavior and traversal.
5. Record host/session details, exact tested commit, procedure, results and any remaining defect. Reintroduce automated blocking tests only if a reliable harness is separately established.

M5-01 can proceed after this formal disposition; F-303-02 remains deferred until M7-03 is completed. Manual keyboard validation is not claimed as passed.


## M5-01 — Other windows and shared UI components audit (2026-11-17)

- **Outcome:** read-only source/Blueprint/test-definition audit completed on source snapshot `0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a`. Global report: [M5-01 audit](../../audit/ui-other-surfaces-m5-01-2026-11-17.md).
- **Surfaces:** Shortcuts; About and fatal-error dialogs; Clear History confirmation; language/share popovers; Welcome/Extracted menus; banner; toast overlay; XDG Portal/libnotify notifications.
- **Disposition:** no confirmed product defect. Keep existing Libadwaita/native components; no broad restyle or behavior change justified. Existing test coverage is meaningful for Clear History response wiring, language search/accessibility state, share-row accessibility/icon resources, notification backend fallback/markup escaping and OCR-notification privacy.
- **P2 test proposal (not implemented):** M5-P2-01 Shortcuts search/match/empty/reset/Escape; M5-P2-02 menu action resolution and action scope across Welcome/Extracted/screenshot menus; M5-P2-03 banner dismissal and deterministic toast lifecycle. Each requires a separate implementation approval.
- **P3 deferred:** About/fatal-dialog configuration assertions, Portal cleanup/error-path tests and any additional popover focus tests after duplicate-coverage review.
- **Validation boundary:** no tests or build were run for this audit; no live GTK, visual, Orca/AT-SPI, keyboard, notification daemon or multi-monitor behavior is claimed. CodeQL #44128147802 passed on the audited head; CI #44128148026 was still in progress when checked.
- **CHANGELOG:** unchanged; no product behavior changed.
- **PR state:** Open/Draft/unmerged, base `feature`. No protected branch or PR metadata changed.
- **Next:** M5-02 test implementation only after separate explicit approval; F-303-03 remains a separate History workstream and is not pulled into M5-01.


## M5-02 — Approved automated UI contract tests (2026-11-17)

- **Outcome:** completed within the approved test-only scope on `fix/ui-modernization-aligned`; global M5 remains Partial.
- **Implemented tests:** `tests/test_m5_02_ui_contracts.py` contains five GTK tests for Shortcuts search matching, no-results state, clearing/resetting, Escape semantics and toast delegation/title/priority. `tests/test_m5_02_menu_actions.py` contains one headless/static test validating Blueprint `app.*`/`win.*` action references against the action registry/declarations.
- **Toast lifecycle exclusion:** no test asserts dismissal or `dismissed` signal timing. The initial assertion invoked `Adw.Toast.dismiss()` before the toast had been registered with an `Adw.ToastOverlay`; that call is a documented no-op. The lifecycle test was removed instead of adding fragile event-loop timing. The task therefore makes no claim about dismissal lifecycle.
- **Banner exclusion:** banner dismissal was not included in the approved implementation subset; the suspected signal-wiring question remains separate and no production fix was made.
- **Temporary CI:** [run #44134120773](https://github.com/D3M-Sudo/Anura/actions/runs/44134120773) passed the dedicated GTK and action-contract test job. The temporary workflow was removed after evidence collection; no permanent workflow or dependency was added.
- **Exact-head CI:** `ae048880f46162f1f11892a06b27fa420c39430c`; [CI #44135571249](https://github.com/D3M-Sudo/Anura/actions/runs/44135571249) passed Python quality, Changelog integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, complete AppImage release-set validation and multi-architecture artifact validation. `publish-release` was skipped as expected for a PR. [CodeQL #44135571322](https://github.com/D3M-Sudo/Anura/actions/runs/44135571322) passed on the same head.
- **CHANGELOG:** unchanged; the work adds test coverage only and does not change user-visible behavior.
- **Validation boundary:** no local test run, live visual inspection, physical keyboard traversal, Orca/AT-SPI or live notification-daemon validation is claimed. F-303-02 remains deferred to M7-03/#655.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`; no protected branch or PR metadata changed.


## M5-03 — Portal-missing banner dismissal correction (2026-11-17)

- **Finding and correction:** the portal-missing Adw.Banner displayed a “Dismiss” button but had no button-clicked handler. AnuraWindow._setup_controller_signals() now connects the signal to _on_portal_banner_dismissed(), which sets revealed=False. The existing _on_portal_missing() reveal behavior is preserved.
- **Tests:** two GTK regressions in tests/test_m5_02_ui_contracts.py verify the signal connection and the hide behavior.
- **Test evidence:** the temporary M5-03 workflow [#44141439001](https://github.com/D3M-Sudo/Anura/actions/runs/44141439001) passed both tests (2 passed, 1 warning). The red phase had demonstrated both failures before the production fix. The temporary workflow was removed after evidence collection.
- **Final formatting and CI head:** formatting-only commit 74f6a4ef98392f80c0ca1e95ed987d2c1d48749c. Exact-head CI [#44142298765](https://github.com/D3M-Sudo/Anura/actions/runs/44142298765) and CodeQL [#44142298673](https://github.com/D3M-Sudo/Anura/actions/runs/44142298673) both succeeded. Python quality, Changelog Integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and both release-artifact validation jobs passed; publish-release was skipped as expected for a PR.
- **CHANGELOG:** added an [Unreleased] / Fixed entry for the user-visible correction.
- **Boundaries:** no local tests, manual visual inspection, physical keyboard traversal, Orca/AT-SPI or live portal/notification-daemon verification are claimed. F-303-02 remains deferred to M7-03/#655. M5-02 toast lifecycle and P3 About/fatal-dialog, Portal cleanup/error-path and popover-focus tests remain deferred.
- **Status:** M5 remains Partial; M5-03 is complete only within this correction and regression-test scope.
- **PR state:** #648 remains Open/Draft/unmerged, base feature. No protected branch, merge or release was changed.


## M5 — agreed-scope closure (2026-11-17)

- **Status:** Completed within the scope explicitly agreed with the maintainer. This is a phase-level disposition, not a claim that every conceivable test or manual check was performed.
- **M5-01:** read-only audit completed for Shortcuts, About/fatal/Clear History dialogs, language/share popovers, Welcome/Extracted menus, banner, toast overlay and desktop notifications. Report: [M5-01 audit](../../audit/ui-other-surfaces-m5-01-2026-11-17.md).
- **M5-02:** five GTK tests cover Shortcuts search/match/empty/reset/Escape and toast delegation/title/priority; one headless/static test checks Blueprint `app.*`/`win.*` action resolution/scope. Toast dismissal/lifecycle is deliberately excluded and is not claimed as tested.
- **M5-03:** portal-unavailable banner Dismiss is wired to hide the banner. Two GTK regressions verify signal wiring and handler behavior; temporary run [#44141439001](https://github.com/D3M-Sudo/Anura/actions/runs/44141439001) passed both (2 passed, 1 warning). Final code/test head `74f6a4ef` passed CI [#44142298765](https://github.com/D3M-Sudo/Anura/actions/runs/44142298765) and CodeQL [#44142298673](https://github.com/D3M-Sudo/Anura/actions/runs/44142298673).
- **P3 disposition:** About/fatal-dialog construction/presentation tests, Portal timeout/shutdown cleanup and error-path tests, and additional popover-focus assertions are deferred and do not block M5 closure.
- **Manual verification disposition:** native GNOME/GTK visual inspection, real Orca/AT-SPI and physical keyboard traversal are allocated to M7. F-303-02 is tracked by [issue #655](https://github.com/D3M-Sudo/Anura/issues/655) for M7-03; it is deferred, not passed.
- **Historical global programme status at M5 closure:** M0 Completed; M1 Completed (operationally); M2 Completed (operationally); M3 Partial at that time (subsequently closed operationally within agreed scope); M4 Partial; M5 Completed within agreed scope; M6 Partial; M7 Partial.
- **CHANGELOG:** the existing `[Unreleased] / Fixed` entry already records the banner Dismiss correction; no additional changelog entry was needed for the phase-status decision.


## M3 — operational closure within agreed scope (2026-11-17)

- **Status:** Completed operationally within the bounded M3 remediation scope; this is not a claim that all future visual refinements or native accessibility checks are complete.
- **Automated contracts:** Extracted selection/labels, OCR asynchronous lifecycle and announcements, History initial action accessible labels (Copy, Editor, TTS), History state semantics and GNOME 51 icon compatibility are covered by the audited test/code sequence.
- **F-303-03:** no longer outstanding. `tests/test_history_ui.py` includes `test_history_row_actions_have_initial_accessible_labels`, covering the initial labels.
- **F-303-02:** not passed; physical Tab/Shift+Tab traversal remains deferred to M7-03 under [#655](https://github.com/D3M-Sudo/Anura/issues/655).
- **Native visual and real Orca/AT-SPI checks:** not performed; assigned to M7.
- **Pre-merge note:** the M3 commit sequence contained a transient large deletion/restoration anomaly; the net audited delta is limited to five M3-related files. Review the history before merge.

## M4-02 — remaining CI coverage gaps (initial disposition, 2026-11-17; execution status updated below)

- M4-01 and M4-F01–F04 remain complete. Global M4 stays **Partial**.
- CI-testable candidates: General color-scheme and secondary-language selection/refresh/removal mapping; Editor `word`/`char`/`none` mapping and persistence; Voice late-result-after-disposal; Preferences Languages page search/empty/install/remove/progress/cancellation/disposal lifecycle.
- Native-only residual: actual physical keyboard traversal in the language selector and real Orca/AT-SPI verification remain M7 work. Existing direct handler invocation is not physical keyboard evidence.
- M4-02 must add deterministic regression tests only where the CI environment can exercise the contract. A test gap alone does not justify production changes; a fix requires a reproduced defect and explicit bounded approval.
- **Next permitted task:** prepare the M4-02 test plan for maintainer review. No M4-02 code/test implementation is authorized by this update.


## M4-02 Task 1 — General Preferences mapping and extra-language behavior (2026-11-17)

- **Outcome:** Completed — headless coverage for General Preferences color-scheme initialization/persistence, extra-language mapping/persistence, and active-language removal/reset with model refresh.
- **Files changed for implementation:** `tests/test_preferences_page_resilience.py` only; no production files changed.
- **Commits:** `fbbbf00d063ed7638aca488d99aae0d98d1603ef` (tests), `b8af80b3931957f4eeae7ea39e77431fec2e5d24` (formatting), `c5f820aac1a722c42bb79f5ebcbbf6fea17a0c7a` (assert final selected value).
- **CI:** [Quality/build run #44188821619](https://github.com/D3M-Sudo/Anura/actions/runs/44188821619) passed. Python Quality: Ruff, formatting, mypy, Bandit, pytest and F-005 all passed; pytest reported **682 passed, 6 skipped, 287 deselected**. GTK Integration passed. Changelog Integrity passed. AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set and multi-architecture artifact validation passed; publish-release was skipped as expected for a PR. [CodeQL #44188821605](https://github.com/D3M-Sudo/Anura/actions/runs/44188821605) passed.
- **Test correction:** the first test run exposed four assertion failures caused by checking mock invocation count across parametrized initialization cases. The assertion now checks the final selected value; the next full CI passed. This was a test assertion correction, not a production defect; no RED→GREEN production fix was needed.
- **Limitations:** CI ran against the PR merge ref; no local tests are claimed. The 6 skipped and 287 deselected tests remain outside this run's executed pytest set. No native keyboard, Orca/AT-SPI or manual visual result is claimed.
- **Next permitted task:** Task 2 — Editor wrap-mode mapping and persistence, under the already approved M4-02 plan. M4 remains Partial.
- **Governance:** PR #648 remains Open/Draft/unmerged, target `feature`; no protected branch was changed.


## M4-02 Task 2 — Editor wrap-mode mapping and GSettings persistence (2026-11-18)

- **Outcome:** Completed — headless mapping/persistence coverage and real GTK/GSettings integration coverage passed on the exact implementation head.
- **Files changed:** `tests/test_preferences_page_resilience.py` and new `tests/test_preferences_editor_integration.py`. No production files, dependencies or workflows changed.
- **Coverage:** headless initialization mappings `word → 0`, `char → 1`, `none → 2`, unknown-value fallback; persistence mappings `0 → word`, `1 → char`, `2 → none`, invalid-index fallback to `word`. GTK integration instantiated the real Editor Preferences page with an isolated Gio memory settings backend and verified read/write persistence for all three modes (3 parametrized cases passed).
- **Exact implementation head:** `cae8b8c27114daf59fab96ebefdd377b3efb76ae` — `style: fix remaining Ruff formatting violation`. The preceding CI run failed only because one test declaration still differed from Ruff's formatter output; this formatting-only correction resolved it.
- **CI evidence:** [CI Quality Check & Release #44195812990](https://github.com/D3M-Sudo/Anura/actions/runs/44195812990) passed. Python Quality: Ruff, formatting, mypy, Bandit, pytest and F-005 passed; pytest **690 passed, 6 skipped, 290 deselected**. GTK Integration passed (**460 passed, 6 skipped, 696 deselected**), including all three Editor/GSettings integration cases. Changelog Integrity passed. AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set and multi-architecture artifact validation passed. [CodeQL #44195813017](https://github.com/D3M-Sudo/Anura/actions/runs/44195813017) passed; publish-release was skipped as expected for a PR.
- **Limitations:** no local test execution is claimed. The six skipped and deselected tests are not represented as executed. Physical keyboard traversal, native GNOME visual inspection and real Orca/AT-SPI remain M7 work; GTK CI's virtual-input harness does not substitute for those checks.
- **Next permitted task:** Task 3 — Voice late-result-after-disposal coverage. Do not start it without maintainer authorization.
- **Governance:** PR #648 remains Open/Draft/unmerged and targets `feature`; no protected branch was modified.


## M4-02 Task 3 — Voice late-result-after-disposal coverage (2026-11-18)

- **Outcome:** Completed within the approved Task 3 scope. Headless regression coverage now exercises both a TTS catalog result delivered after Voice page disposal and the complementary live-page update path.
- **Files changed for implementation:** `tests/test_preferences_page_resilience.py` only. No production files, dependencies or workflows changed; the existing `_disposed` guard was sufficient.
- **Coverage:** the disposed-page test captures the callback scheduled through `GLib.idle_add`, calls `page.do_destroy()`, then delivers the result and asserts `GLib.SOURCE_REMOVE`, no combo-model replacement/selection mutation, and loading-state cleanup. The live-page test asserts the valid catalog result updates the model/selection and clears loading state.
- **Test-development history:** initial failures were test-fixture/mock-base issues, not observed production regressions; these were corrected. No mutation run removing the production guard was performed, so do not claim an experimentally observed RED from guard removal. The final assertions are specifically directed at preventing post-disposal widget mutation.
- **Exact implementation head:** `8a70fa257375f5da060b30568a6eeacd50b2f820`.
- **CI evidence:** [CI Quality Check & Release #44199827587](https://github.com/D3M-Sudo/Anura/actions/runs/44199827587) completed successfully. Python Quality: **692 passed, 6 skipped, 290 deselected**; GTK Integration, Changelog Integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture artifact validation all passed. [CodeQL #44199827449](https://github.com/D3M-Sudo/Anura/actions/runs/44199827449) passed. `publish-release` was skipped as expected for a PR.
- **Limitations:** no local test execution is claimed. No native GNOME visual inspection, physical keyboard traversal or real Orca/AT-SPI verification is claimed; these remain deferred to M7. CI GTK configuration does not establish native AT-SPI behavior.
- **CHANGELOG:** no entry added; this task adds tests only and changes no product behavior.
- **Next:** M4-02 Task 4 — Languages search/filter and lifecycle coverage. Task 4 has not started and requires its own explicit authorization.
- **Governance:** PR #648 remains Open/Draft/unmerged, target `feature`; no protected branch was modified.


## M4-02 Task 3 — Voice late-result-after-disposal coverage (2026-11-18)

- **Outcome:** Completed within the approved Task 3 scope. Headless regression tests cover a TTS catalog result delivered after Voice page disposal and the complementary live-page update path.
- **Files changed:** `tests/test_preferences_page_resilience.py` only. No production files, dependencies or workflows changed; the existing `_disposed` guard was sufficient.
- **Coverage:** the disposal test captures the callback scheduled through `GLib.idle_add`, calls `page.do_destroy()`, then delivers the result and asserts `GLib.SOURCE_REMOVE`, no combo-model replacement/selection mutation, and loading-state cleanup. The live-page test asserts the valid result updates the model/selection and clears loading state.
- **Test-development history:** initial failures were test-fixture/mock-base issues, not observed production regressions; these were corrected. No mutation run removing the production guard was performed, so no experimentally observed RED from guard removal is claimed.
- **Exact implementation head:** `8a70fa257375f5da060b30568a6eeacd50b2f820`.
- **CI:** [#44199827587](https://github.com/D3M-Sudo/Anura/actions/runs/44199827587) passed: Python Quality **692 passed, 6 skipped, 290 deselected**; GTK Integration; Changelog Integrity; AppImage and Flatpak x86_64/aarch64; AppImage release-set and multi-architecture artifact validation. [CodeQL #44199827449](https://github.com/D3M-Sudo/Anura/actions/runs/44199827449) passed. `publish-release` skipped as expected for a PR.
- **Limitations:** no local tests, native GNOME visual inspection, physical keyboard traversal or real Orca/AT-SPI verification are claimed; native checks remain assigned to M7.
- **CHANGELOG:** not changed because this is test-only work with no product behavior change.
- **Next:** M4-02 Task 4 — Languages search/filter/lifecycle coverage; not started and requires explicit authorization.
- **Governance:** PR #648 remains Open/Draft/unmerged, target `feature`; no protected branch was modified.


## M4-02 Task 4 — Languages search/filter and list lifecycle (2026-11-18)

- **Status:** Completed within the bounded Task 4 scope; global M4 remains **Partial** pending Task 5 disposition and native M7 checks.
- **Headless coverage:** ten new tests in `tests/test_preferences_languages_lifecycle.py` passed. They cover configured tessdata-host reachability, cancellation and suppression of a late network callback after disposal, pruning completed LanguageRow idle sources, accessible list naming, case-insensitive title search, downloaded-only default filtering, empty/non-empty stack selection, stop-search reset, idempotent add events and filter refresh after removal.
- **GTK integration:** new `tests/test_preferences_languages_integration.py` instantiated the real Languages Preferences page with controlled GObject language-manager signals, real LanguageItem objects, a GResource bundle and isolated Gio memory GSettings. The test verified downloaded-only filtering, case-insensitive search including a non-downloaded language, empty state, stop-search reset, idempotent addition and removal refresh. The exact test `test_languages_page_search_empty_reset_and_model_lifecycle` passed in GTK Integration.
- **Production changes for this task:** none. The Task 4 additions are test-only; no dependencies or permanent workflows were added. No CHANGELOG entry was warranted. No production RED/GREEN correction is claimed; no mutation test was performed.
- **Exact implementation head:** `8e2a2f5d7ca3b8ec3b6f8ae478ecc0c94bc7c3bd`.
- **CI evidence:** [CI Quality Check & Release #44205336611](https://github.com/D3M-Sudo/Anura/actions/runs/44205336611) completed successfully after rerunning the initially cancelled GTK Integration job. Python Quality: **698 passed, 6 skipped, 291 deselected**. GTK Integration: **461 passed, 6 skipped, 704 deselected**, including the new Languages GTK integration test. Changelog Integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture artifact validation passed. [CodeQL #44205336610](https://github.com/D3M-Sudo/Anura/actions/runs/44205336610) passed.
- **Review qualification:** the test diff was inspected in-session; an independent code-review subagent was unavailable, so no independent review is claimed.
- **Limitations / residuals:** the new GTK test validates filtering, search, empty/reset state and add/remove model signals; it does not claim a full real download-progress UI transition test. Native visual inspection, physical Tab/Shift+Tab traversal and real Orca/AT-SPI remain M7 work. GTK CI's virtual input is not equivalent to native accessibility verification.
- **Governance:** PR #648 verified Open, Draft, unmerged, base `feature`, head branch `fix/ui-modernization-aligned` at the exact SHA above. No protected branch was modified.
- **Next:** Task 5 — full M4-02 acceptance-criteria disposition and roadmap closure review. Requires separate maintainer authorization.


## 2026-11-18 — M4-02 Task 5: acceptance-criteria disposition

- **Outcome:** M4-02 CI-testable acceptance criteria are covered or explicitly dispositioned; this closes the bounded M4-02 test-coverage workstream, not the wider M4 phase.
- **General:** color-scheme initialization/persistence and extra-language selection, persistence and active-model removal/reset are covered by `tests/test_preferences_page_resilience.py`.
- **Editor:** `word`/`char`/`none` initialization and persistence are covered headlessly; real GSettings persistence is covered by `tests/test_preferences_editor_integration.py`.
- **Voice:** late catalog completion after disposal and the live-page success path are covered headlessly. Existing catalog failure/loading-state and volume persistence/binding behavior remain covered by the existing resilience and GTK integration tests.
- **Languages:** case-insensitive title search, downloaded-only default filtering, empty/non-empty stack selection, stop-search reset, idempotent add and removal/filter refresh are covered headlessly and by the real GTK integration test. Existing model-quality mapping and cache invalidation remain covered by `tests/test_preferences_language_quality.py`.
- **Explicit scope disposition:** download-progress UI transition coverage was mentioned as a possible residual in the implementation plan, but it is not an acceptance criterion in the maintainer-approved M4-02 design. It was not implemented or verified here and is not claimed. Any additional progress-announcement or download-progress lifecycle coverage requires a separately approved scope. Network reachability/cancellation and row idle-source cleanup tests add lifecycle coverage but do not substitute for a progress UI transition test.
- **Native residuals:** physical Tab/Shift+Tab traversal, real Orca/AT-SPI and native visual verification remain M7 work. GTK CI uses virtual Wayland input and disables the accessibility bridge; it is not native accessibility evidence.
- **Exact-head verification:** `8e2a2f5d7ca3b8ec3b6f8ae478ecc0c94bc7c3bd`; CI [#44205336611](https://github.com/D3M-Sudo/Anura/actions/runs/44205336611) and CodeQL [#44205336610](https://github.com/D3M-Sudo/Anura/actions/runs/44205336610) passed. Python Quality **698 passed, 6 skipped, 291 deselected**; GTK Integration **461 passed, 6 skipped, 704 deselected**, including the Languages GTK integration test; AppImage and Flatpak x86_64/aarch64, Changelog Integrity and artifact validations passed.
- **Review qualification:** test diff inspected in-session; no independent review subagent was available, so independent review is not claimed.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`. No protected branch was modified; no CHANGELOG entry was warranted because Task 4 added tests only.
- **Global status:** M4 remains **Partial**; this Task 5 disposition does not complete M4 native validation or M7.


## 2026-11-18 — M4 residual review (M4-RR)

- **Outcome:** M4-RR-01 evidence inventory, M4-RR-02 residual-gap analysis and M4-RR-03 test/fix verification are complete. The CI-testable M4 residual review is closed on this branch; global M4 remains **Partial** because native visual/responsive and accessibility validation remains assigned to M7.
- **Finding 1 — stale idle source on LanguageRow failure path:** `on_download_failed()` previously registered `_idle_update_ui` directly with `GLib.idle_add()` and retained the source ID after the callback completed. The new regression test demonstrated the stale-ID bookkeeping defect; the minimal production correction routes the callback through `_schedule_idle_update()` so its ID is pruned consistently. The test `test_language_row_prunes_failed_download_refresh_idle_id` passes.
- **Finding 2 — download progress UI coverage:** added `test_download_progress_reveals_updates_and_hides_progress_bar`, asserting fractions `0.35` and `1.0` and reveal transitions `[True, False]`. This closes the specific progress UI transition gap identified by the broader M4-01/residual audit; it does not claim native visual correctness or assistive-technology announcements.
- **Finding 3 — network retry/recovery coverage:** added `test_network_banner_retry_hides_warning_after_recovery`, proving initial unreachable state reveals the banner, a direct `check_connection()` retry launches a second probe, and successful recovery hides the banner. **Limit:** the test does not invoke the GTK template button callback and does not prove physical click/signal wiring.
- **Finding 4 — Preferences visual/layout:** four pages (General, Languages, Editor, Voice) and the 640×480 default content geometry were confirmed from source/templates. Actual rendered layout, density, responsive behavior and navigation appearance require native-host inspection and remain M7.
- **Finding 5 — language selector keyboard/accessibility:** existing selector signal, selected-state, down-arrow handler and search-label tests remain automated evidence. Handler-level tests are not proof of physical Tab/Shift+Tab traversal or Orca/AT-SPI; those remain M7.
- **Changed files:** `anura/widgets/language_row.py`, `tests/test_language_row_accessibility.py`, `tests/test_preferences_languages_lifecycle.py`; no dependency, workflow or CHANGELOG change.
- **RED→GREEN:** stale idle-source regression was observed failing before the bounded production fix and passed afterward. Progress and retry tests are additive test-only coverage; no production change was justified by those findings.
- **Exact-head evidence:** branch HEAD `cc4267083af30c006251e290d78cd2a7e5d6ecf2`; [CI Quality & Release #44325172798](https://github.com/D3M-Sudo/Anura/actions/runs/44325172798) and [CodeQL #44325172840](https://github.com/D3M-Sudo/Anura/actions/runs/44325172840) passed. Python Quality: **701 passed, 6 skipped, 291 deselected**. GTK Integration: **461 passed, 6 skipped, 707 deselected**. The two additive progress/retry tests and the idle-source regression test were each explicitly observed as PASSED in the Python Quality log. Changelog Integrity, AppImage x86_64/aarch64 builds and smoke tests, Flatpak x86_64/aarch64 builds and functional checks, AppImage/Flatpak multi-architecture artifact validation and CodeQL passed. `publish-release` was skipped as expected; no release was published.
- **Review qualification:** no independent review subagent was available; the in-session evidence and test changes were inspected. Do not represent this as an independent Goldfish review.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`, head branch `fix/ui-modernization-aligned`; no protected branch was modified.
- **Deferred:** rendered native GTK/Libadwaita review, actual banner-button signal/physical interaction, physical Tab/Shift+Tab, Orca/AT-SPI and installed-package host smoke checks remain M7 obligations.
- **Next:** M6-01 cross-window responsive/accessibility matrix; no implementation authorization is implied by this roadmap entry.
