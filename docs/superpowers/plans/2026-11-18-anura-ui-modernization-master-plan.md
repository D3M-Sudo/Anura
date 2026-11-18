# Anura UI Modernization — Master Plan

> **For agentic workers:** This is a phase-gated programme plan, not blanket implementation authorization. Execute only the phase explicitly approved by the maintainer. For each phase, use the approved native workflow; do not assume subagent execution is available. Steps use checkbox syntax for tracking.

**Goal:** Complete the remaining cross-window UI modernization work through evidence-backed automated coverage, programme traceability, and separately validated native desktop checks.

**Architecture:** Preserve the current GTK 4 / Libadwaita implementation and existing pytest, GTK Integration, and GitHub Actions infrastructure. Treat the M6-02 automated-test plan as the detailed child plan for the CI-testable P1/P2 work; keep native M7 validation separate from CI and from automated test claims.

**Tech Stack:** Python, GTK 4, Libadwaita, PyGObject, Blueprint, pytest, existing GTK Integration workflow, GitHub Actions, Orca/AT-SPI for explicitly native validation.

**Source documents:**
- M6-01 audit: `docs/audit/ui-cross-window-m6-01-2026-11-18.md`
- M6-02 child plan: `docs/superpowers/plans/2026-11-18-anura-m6-02-automated-test-coverage-plan.md`
- Global roadmap: `docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md`
- Workstream roadmap: `docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md`

## Global constraints and governance

- Work only on `fix/ui-modernization-aligned`.
- PR #648 remains Open, Draft, unmerged, with base `feature`; do not change its state, base, or merge status.
- Do not modify `feature`, `development`, `testing`, or `main`.
- No commit, PR transition, merge, release publication, or protected-branch write is authorized by this plan.
- Each phase is a separate authorization gate. Approval of this master plan does not approve implementation of any phase.
- Default implementation scope is test-only. If a test demonstrates a product defect, stop at the failing regression and request a separate, explicit production-fix authorization. A production fix requires a valid RED result attributable to the product behavior, a minimal correction, and GREEN verification.
- Do not add dependencies, permanent or temporary workflows, or broaden test infrastructure unless a separately approved phase requires them.
- Reuse existing test suites and CI jobs. Avoid duplicate assertions and do not represent proposed tests as existing tests.
- Do not change CHANGELOG for documentation-only or test-only work. Update it only when product behavior changes and repository policy requires an entry.
- After each approved implementation task, run focused checks, then the full required CI and CodeQL on the exact resulting SHA. Do not start the next task or update roadmap status until all required checks for that SHA are green.
- Update the global and workstream roadmaps only after the corresponding task's exact-head CI succeeds. Record commit SHA, workflow/run IDs, test outcomes, skips, limitations, and next authorized step.
- No local-host test execution is claimed unless the maintainer explicitly authorizes it and supplies the required host evidence.

## Baseline and current disposition

**Baseline branch head at master-plan preparation:** `e3621ffef73ba153331e9a07642354fcec633bfe`.

The exact-head CI gate for that baseline is complete:
- CI Quality & Release run `44412014880`: success.
- CodeQL run `44412015137`: success.
- Python Quality, GTK Integration, Changelog Integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, and artifact validation: success.
- `publish-release`: skipped as expected; no release was published.

PR #648 was verified Open, Draft, unmerged, base `feature`, head branch `fix/ui-modernization-aligned`, at the baseline SHA above. Its descriptive body may contain historical milestone text; this plan and the roadmap are the programme-status records to update after future task gates.

### Existing milestone disposition

| Milestone | Current status | Master-plan treatment |
|---|---|---|
| M0 — Full audit | Complete | Baseline; no repeat audit unless scope changes. |
| M1 — Design System | Complete operationally | Preserve; remaining native visual checks belong to P9. |
| M2 — Welcome/navigation | Complete operationally | Preserve current automated evidence; native checks belong to P9. |
| M3 — Extracted/History | Complete within approved remediation scope | Do not reopen completed scope by default; P1 covers only the M6-01 residual responsive/overflow gaps. |
| M4 — Preferences/languages | Partial globally; M4-01, M4-02 and M4-RR complete within approved CI-testable scope | P2 addresses remaining cross-page responsive/focus gaps; native checks remain P9. |
| M5 — Other windows/components | Complete within agreed scope | P7 remains deferred and separately gated; no implied completion of toast/dialog lifecycle. |
| M6 — Responsive/accessibility | Partial | P1–P6 cover the planned P1/P2 automated residuals, subject to separate phase approvals. |
| M7 — Integration/consolidation | Partial | P8 traceability/consolidation, then P9 native validation. |

## Programme sequence

The sequence below is dependency ordered. P1–P6 are the implementation-oriented decomposition of the existing M6-02 child plan, not a second copy of its detailed test cases. P7 is explicitly deferred. P8 and P9 complete the wider M7 programme.

| Phase | Priority / status | Depends on | Objective and bounded deliverable | Main candidate files / sources | Completion gate |
|---|---|---|---|---|---|
| P0 — Baseline and execution control | Required; planning baseline established | Master-plan approval | Freeze baseline evidence, confirm exact branch/PR invariants, map each phase to the M6-01 gap register and M6-02 requirements, and maintain a per-task evidence ledger. No product/test changes. | This plan; M6-01 report; M6-02 child plan; global/workstream roadmaps | All source references and constraints reconciled; each phase has a named acceptance/evidence gate; no implementation claims. |
| P1 — Extracted and History responsive/overflow | P1; not started | P0; explicit phase approval | Test real GTK allocation, scrolling, long-result/long-history behavior, and reachability of essential actions at the applicable reference viewports. Tests only by default. | New `tests/test_m6_02_extracted_history_responsive.py`; `anura/widgets/extracted_page.py`, `history_page.py`; `data/ui/extracted_page.blp`, `history_page.blp` | M6-R01/R02 acceptance in child plan; focused tests and GTK Integration pass; full exact-SHA CI + CodeQL green. Any product defect stops for separate authorization. |
| P2 — Preferences responsive geometry and focus | P1; not started | P1 complete; explicit phase approval | Cover General, Languages, Editor and Voice page geometry, content reachability, and supported programmatic focus entry/exit on page switching. Preserve existing settings/lifecycle tests. | New `tests/test_m6_02_preferences_responsive.py`; `anura/widgets/preferences_dialog.py`, `preferences_general_page.py`, `preferences_languages_page.py`, `preferences_editor_page.py`, `preferences_voice_page.py`; related `data/ui/preferences_*.blp` | M6-R03/R04 acceptance; focused tests and GTK Integration pass; full exact-SHA CI + CodeQL green. |
| P3 — Shortcuts and Language Selector compact geometry/focus | P1; not started | P2 complete; explicit phase approval | Cover compact overlay/popover geometry, search/empty states, scrolling, and supported focus lifecycle. Handler tests must not be described as physical keyboard traversal. | New `tests/test_m6_02_shortcuts_popover_focus.py`; `anura/widgets/shortcuts_overlay.py`, `language_popover.py`, `language_popover_row.py`; corresponding Blueprint templates | M6-R05/R06 acceptance; focused tests and GTK Integration pass; full exact-SHA CI + CodeQL green. |
| P4 — Cross-window focus routes | P1; not started | P1–P3 complete; explicit phase approval | Define and test supported programmatic navigation routes and destination focus fallback without duplicating existing History→Welcome coverage. | New `tests/test_m6_02_navigation_focus_routes.py`; `anura/window.py`; `data/ui/window.blp`, `welcome_page.blp`, `extracted_page.blp`, `history_page.blp`; existing `tests/test_history_navigation_focus.py` | M6-R07 acceptance; route matrix reconciled with existing tests; GTK Integration pass; full exact-SHA CI + CodeQL green. |
| P5 — Accessible names, roles, states and announcements | P2; not started | P4 complete; explicit phase approval | Establish a finite inventory of high-value controls and meaningful dynamic states; assert GTK-exposed properties and concise announcement transitions. Do not infer screen-reader output. | New `tests/test_m6_02_accessible_control_contracts.py`; extend only as needed `tests/test_accessible_status_announcements.py`, `tests/test_language_row_accessibility.py`; relevant widget/templates from M6-01 | M6-R08/R09 acceptance; tests cover the approved inventory without duplicate assertions; relevant Python/GTK jobs and full exact-SHA CI + CodeQL green. |
| P6 — Theme/contrast and reduced motion | P2; not started | P5 complete; explicit phase approval | Reconcile semantic color roles across audited surfaces and trace remaining application-controlled animation consumers; add assertions only for uncovered combinations/consumers. | Extend `tests/test_ui_palette.py`, `tests/test_ui_color_scanner.py`, `tests/test_reduced_motion.py`; shared CSS and the 14 audited Blueprint templates | M6-R10/R11 acceptance; inventory has no unexplained application-authored semantic color or animation gaps; focused checks and full exact-SHA CI + CodeQL green. |
| P7 — Dialogs and transient lifecycle | P3 deferred; not approved | Separate proposal and explicit approval required | Potential future scope: About/fatal dialogs, Portal timeout/shutdown, toast dismissal/lifecycle, and unverified banner/template signal paths. Not part of P1–P6 acceptance and not authorized by this master plan. | Existing M5 audit/tests; candidate files must be scoped only after a new read-only audit | No work until separate scope approval. If approved later, create a dedicated design/test plan and independent CI gate. |
| P8 — M7 integration, traceability and consolidation | Required M7 work; not started | P1–P6 dispositions complete; P7 remains deferred unless separately approved | Reconcile original approved requirements and current PR delivery evidence; classify verified, partially evidenced, deferred and unresolved items; review translations; prepare approved next-release screenshots and a final readiness report. No release/merge action. | Global/workstream roadmaps; `HANDOVER.md`; translation resources and relevant docs; existing M0–M6 audit/spec/plan records; screenshot artifacts only if separately authorized | Every in-scope requirement has a traceable disposition and evidence reference; translation review records what was actually checked; screenshots are current and authorized; unresolved items have owners/disposition; exact-head CI + CodeQL green for any repository changes. |
| P9 — Native desktop validation | Required M7 native gate; not started | P8 evidence inventory; maintainer host/session available; explicit approval and scheduling | Validate rendered GTK/Libadwaita behavior, physical keyboard traversal, Orca/AT-SPI with bridge enabled, live window-manager/multi-monitor geometry, real pointer/template interactions, and installed-package smoke on the maintainer's host. | Native installed application and host environment; issue #655 for History row physical traversal; evidence log and approved screenshots | Each native check records environment, application/package build, exact commit/artifact, procedure, observed result and limitations. Failed checks return to a separately approved bounded remediation task. CI cannot satisfy this phase. |

## M6-02 child-plan mapping

The existing child plan remains authoritative for detailed test names, exact source/template targets, viewport protocol, harness constraints and requirement acceptance. Do not duplicate or rewrite those detailed specifications here.

| Master phase | Child requirements | Child-plan details |
|---|---|---|
| P1 | M6-R01, M6-R02 | Extracted/History responsive geometry, scrolling, long content and essential-action reachability. |
| P2 | M6-R03, M6-R04 | Four Preferences pages, geometry and programmatic focus on page switching. |
| P3 | M6-R05, M6-R06 | Shortcuts overlay and language popover compact geometry, search, empty state and focus lifecycle. |
| P4 | M6-R07 | Supported cross-window routes and destination focus. |
| P5 | M6-R08, M6-R09 | High-value control names/roles/states and meaningful announcement transitions. |
| P6 | M6-R10, M6-R11 | Semantic color/contrast inventory and application-controlled reduced-motion consumers. |
| P7 | M6-R12 | Explicitly deferred; no M6-02 acceptance claim. |

**Reference viewports:** 360×600, 640×480, 900×600 and 1280×800. Apply them according to each surface's sizing contract; do not imply every surface must be forced into every viewport.

**Test layers:** headless contracts in Python Quality; real GTK widget/allocation/focus/accessibility-property assertions in the existing virtual-Wayland GTK Integration job; static/source contracts only where a stable runtime seam is unavailable. Do not create a new compositor or CI workflow.

## Cross-cutting acceptance and evidence protocol

For every approved phase:

1. Read current repository instructions and the relevant source/template/test files; confirm the target branch and PR invariants before editing.
2. Write the phase-specific acceptance criteria and candidate file list before implementation. Reuse the M6-02 child plan for P1–P6.
3. Add or extend the smallest cohesive regression tests. For test-only work, no product source changes.
4. If a regression exposes a product defect, stop and request separate explicit production-fix authorization. Do not bundle a fix into the test phase.
5. Run focused tests and inspect their complete results.
6. Review the diff for scope, duplicate assertions, test quality and unintended changes.
7. Run the complete required CI and CodeQL on the exact resulting SHA. Required CI includes Python Quality, GTK Integration, Changelog Integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation, multi-architecture artifact validation and CodeQL where configured. Record intentionally skipped jobs such as `publish-release`; a skipped release job is not a release.
8. Only after all required checks are green, update roadmap status and evidence ledger in a separate bounded documentation task (or a clearly isolated final documentation step). Run CI again on the resulting exact SHA.
9. Stop and report any failed, cancelled, missing or inconclusive required job. Do not advance based on partial success.

### CI evidence is not native validation

The existing GTK CI configuration uses `NO_AT_BRIDGE=1` and `GTK_A11Y=none`. It can validate selected GTK widget contracts in the configured virtual environment, but it cannot establish:
- rendered native GTK/Libadwaita visual correctness, density, clipping or reflow;
- physical Tab/Shift+Tab traversal;
- Orca output, AT-SPI exposure or behavior with an enabled accessibility bridge;
- live window-manager, work-area or multi-monitor geometry;
- physical pointer activation or Gtk.Template signal wiring when tests invoke controller/handler methods directly;
- installed AppImage/Flatpak runtime behavior on the maintainer's host.

These remain P9 native obligations. History row physical keyboard traversal remains separately tracked by issue #655.

## Deferred scope and non-goals

- P7 is not approved and must remain deferred until a separate scope decision.
- No new UI features, redesign, broad refactor or dependency introduction is implied.
- No pixel snapshots, screenshot-diff thresholds or color sampling are part of P1–P6; native rendered inspection is P9.
- No claims of complete application-wide accessibility or WCAG conformance are permitted from the planned GTK property assertions alone.
- No physical keyboard, Orca/AT-SPI, native visual, live multi-monitor or installed-host validation may be reported as passed from CI.
- No automatic fix of production defects; a separate authorization and RED→GREEN evidence are mandatory.
- No release publication, PR readiness transition, PR retargeting, branch promotion or merge.

## Programme completion criteria

The remaining UI modernization programme can be considered complete only when:
- P1–P6 have each been explicitly approved, implemented within their bounded scopes, reviewed, and passed exact-head CI/CodeQL; or any residual is explicitly dispositioned with evidence and maintainer acceptance.
- P7 remains explicitly deferred or is completed under its own separate approval and acceptance plan.
- P8 has a requirement-to-delivery traceability disposition, translation review evidence, and approved screenshot/readiness artifacts, with all unresolved items visible.
- P9 native checks have been performed and recorded on the maintainer's supported desktop/package environment; CI-only evidence is not a substitute.
- Global and workstream roadmaps accurately reflect the final status, exact SHAs, CI run IDs, residual limitations and deferred items.
- PR #648 remains Open/Draft/unmerged/base `feature` unless the maintainer separately authorizes a future state change.

## Planning status

- Master plan: created in commit `db71476932bc89c84bb69bc1adc018abc61966d7`; exact-head CI Quality & Release `44414583151` and CodeQL `44414583117` passed. Documentation-only; no tests or product changes.
- M6-01: complete within documentation-only scope.
- M6-02: detailed automated-test plan complete; implementation not started.
- M6 global: Partial.
- M7: Partial; P8/P9 remain.
- Next candidate: P1 — Extracted and History responsive/overflow test phase. Not started; requires separate explicit approval before implementation.
