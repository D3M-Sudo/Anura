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

## Verified baseline (2026-11-16)

- PR #648 is open, **Draft**, unmerged and targets `feature`.
- Working branch: `fix/ui-modernization-aligned`.
- Latest verified PR head before this roadmap: `cc8aaad6601f25b9e96f3d2eb9f78bc9fb3c524d`.
- The PR snapshot reports 314 commits and 67 changed files; the branch is mergeable. The prior comparison record is 314 commits ahead and 0 behind. Re-check the compare immediately before any future integration decision.
- Latest verified CI run: [#43801048308](https://github.com/D3M-Sudo/Anura/actions/runs/43801048308), on head `cc8aaad6601f25b9e96f3d2eb9f78bc9fb3c524d`.
- CI jobs passed: Python quality, Changelog integrity, GTK Integration Tests, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture release validation. Publish-release was skipped as expected for a PR.
- GTK Integration Tests: **431 passed, 5 skipped, 632 deselected, 2 warnings**. The constrained-viewport Welcome scrolling regression passed. The run's job logs are the source of truth for detailed results.
- The latest workflow correction uses Xvfb-backed Weston X11 and verifies the Wayland seat exposes pointer and keyboard capabilities before GTK tests. The latest run passed the popup activation tests.
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

- M0-C global backlog/document reconciliation is complete. The current programme status is M0 Completed; M1–M4 Partial; M5 Not started as a complete phase; M6–M7 Partial.
- M1-02 conventions, M1-03 audit and M1-04 semantic-color/scanner/theme-test work are complete within their bounded scopes. M1 remains globally Partial pending cross-surface adoption audit.
- **M1-05 and the implementation portion of M1-06 are complete within their bounded scopes.** M1-06 closes F1 reduced-motion handling for Shortcuts and F2 production-tree color-scanner enforcement. Python/GTK regression suites and CodeQL pass on SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`; AppImage/Flatpak multi-architecture CI is still running, so phase closure remains pending.
- Earlier sections in this roadmap and older task plans may contain historical “next task” directions that predate completed work. Preserve them as historical records; where they conflict with the current snapshot, the global roadmap and this reconciliation note supersede them.
- M1-06 implementation/test SHA is `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`. CI #43974750869 has Python quality, GTK Integration and Changelog integrity green; CodeQL #43974750821 is green. AppImage/Flatpak multi-architecture jobs remain in progress. Earlier CI results are not substituted for this exact-SHA evidence.
- Manual GNOME/GTK visual, Orca/AT-SPI, manual keyboard and live multi-monitor checks remain excluded; screenshot capture remains deferred to the next release cycle.
- PR #648 remains Open/Draft/unmerged, targeting `feature`; this documentation update does not alter PR metadata or state.


## M1-05 — Cross-surface Design System audit (2026-11-16)

- **Outcome:** read-only audit completed. Detailed evidence and the surface matrix are in [M1-05 audit report](../../audit/ui-design-system-m1-05-2026-11-16.md).
- Reviewed source snapshot `fb1bcbe89f0ce982fc4adad60630a5a88496dd1`: 14 Blueprint templates, 15 Python UI modules, main window/application, reduced-motion utility, CSS, design-system guide and relevant tests/CI definitions.
- Positive baseline: shared spacing/radius conventions are statically guarded; the documented 6 px Welcome exception and 1.15em hero typography exception are explicit; native GTK4/Libadwaita patterns are used broadly.
- Findings: **F1 Medium** — separate `ShortcutsOverlay` window does not receive the main window's reduced-motion CSS class despite applying `.anura-fade-in`; **F2 Medium** — scanner fixture tests do not invoke the scanner against the production tree in CI; **F3 Low** — apparently orphaned custom CSS selectors; **F4 Low** — `title`/`h4` typography classes are not mapped in the design-system guide.
- **M1 remains Partial.** M1-06 is conditional and must be separately scoped/approved; it should address F1 and F2 only unless further evidence justifies expanding scope. F3/F4 are deferred.
- No application source, tests, workflows, CHANGELOG, dependencies, OCR behavior, architecture, PR metadata or protected branches changed. No tests or CI were run for this audit; manual GNOME/GTK visual, Orca/AT-SPI and keyboard checks remain excluded.
- PR #648 state is unchanged: Open/Draft/unmerged, base `feature`, head branch `fix/ui-modernization-aligned`.


## M1-06 — Reduced-motion and production color-scanner enforcement (2026-11-16)

- **Implementation/test head:** `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`. The work changes only `anura/widgets/shortcuts_overlay.py`, `tests/test_widgets.py` and `tests/test_ui_color_scanner.py` beyond the previously approved design/plan documents.
- **F1 implementation:** the separate Shortcuts window now reads the GTK settings associated with its display, reuses the existing accessibility helper, observes supported setting notifications and updates the reduced-motion state live. It removes root `anura-fade-in`/`anura-card` motion classes while reduced motion is active and restores them in normal mode. Settings callbacks are disconnected on close-request and in `do_destroy()`.
- **F1 tests:** GTK coverage includes initial normal/reduced states, live `gtk-interface-reduced-motion` transitions, root animation/transition class behavior, older-GTK fallback when the reduced-motion property is absent, live `gtk-enable-animations` changes and handler cleanup.
- **F2 implementation:** repository-root pytest enforcement uses the existing scanner and an exact path/value rationale map; it does not add a separate workflow or change the scanner's production-source scope.
- **Verification on the exact SHA:** Python quality 644 passed/6 skipped/277 deselected; GTK Integration 447 passed/5 skipped/650 deselected/2 warnings; Ruff, mypy, Bandit, Changelog integrity and CodeQL passed. CI [#43974750869](https://github.com/D3M-Sudo/Anura/actions/runs/43974750869), CodeQL [#43974750821](https://github.com/D3M-Sudo/Anura/actions/runs/43974750821). AppImage/Flatpak architecture and release validation are still running.
- **TDD red evidence:** test-only commits produced four expected GTK failures before the reduced-motion implementation and four expected failures before close-request cleanup; the final implementation/test SHA above is green for the complete GTK suite.
- F3/F4 remain deferred. Manual visual, Orca/AT-SPI, manual keyboard and live multi-monitor checks remain excluded; screenshots remain deferred. PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`.
