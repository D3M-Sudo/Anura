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
| UI-07 | Reconcile handover, subordinate plans and PR description with current state | **Next** | Correct stale status/evidence and contradictions without changing application code or PR state. |
| UI-08 | Audit original modernization requirements against the final PR diff | **Pending** | Trace every accepted original requirement to implementation/test/evidence or an explicit rejection/deferment. |
| UI-09 | Define the next development task and obtain maintainer approval | **Blocked pending UI-08** | Do not invent a feature or infer authorization from this roadmap. |
| UI-10 | Implement the next explicitly approved task | **Not started** | Must use an approved execution approach and task-level acceptance criteria. |
| UI-11 | Review, run CI and validate delivery evidence | **Not started** | Run after UI-10 or any later implementation task; record exact results and limitations. |
| UI-12 | Update this roadmap after every completed task | **Mandatory recurring control** | Execute after each task, before starting another. This is not a one-time final task. |

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
