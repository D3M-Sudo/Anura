# Anura — Global UI/UX Modernization Roadmap

> **Primary roadmap:** this document governs the complete, application-wide UI/UX modernization approved as Anura UI/UX Modernization v1.0 on 2026-11-08. Its scope includes every application window, page, dialog, popover, menu, notification and relevant UI state—not only the work contained in PR #648.
>
> **Execution detail:** [PR #648 workstream roadmap](2026-11-16-anura-ui-modernization-roadmap.md) remains a subordinate register for implementation and evidence already accumulated on `fix/ui-modernization-aligned`. It does not define or reduce the global scope.

**Repository:** `D3M-Sudo/Anura`  
**Working branch for the current workstream:** `fix/ui-modernization-aligned`  
**Active implementation PR:** [#648 — UI modernization aligned](https://github.com/D3M-Sudo/Anura/pull/648)  
**Target branch:** `feature`  
**Plan version:** 1.0 (approved 2026-11-08; consolidated 2026-11-16)

## 1. Governance and execution rules

1. This is the **single authoritative roadmap for scope, phase order, application-wide progress and requirement disposition**. The PR #648 roadmap is subordinate and must link back here.
2. Work only on the currently authorized working branch, `fix/ui-modernization-aligned`, unless the maintainer explicitly authorizes another branch. Do not modify protected branches `feature`, `development`, `testing` or `main`.
3. PR #648 must remain open and Draft until explicitly authorized otherwise. No merge, release publication, protected-branch update or PR state transition is authorized by this roadmap.
4. A roadmap entry is not authorization to implement. Before each implementation task, present its bounded scope, affected files/windows, acceptance criteria and test plan; wait for explicit approval.
5. **Mandatory roadmap invariant:** after every completed task, update this global roadmap with its outcome and evidence before starting the next task. Update the subordinate PR #648 roadmap as well when its workstream changes.
6. Preserve existing functionality. Distinguish restyling from behavioral changes; do not silently add mockup-only features or alter product behavior.
7. Do not introduce new OCR engines, OCR/model/pipeline changes, image-processing changes, unnecessary architecture changes, dependencies, portal changes or operating-system changes as part of visual modernization. Such work requires a separate proposal and approval.
8. Keep the green/teal brand direction. The blue palette proposal is rejected. Preserve automatic, light and dark theme behavior, including `default`, `force-light` and `force-dark`; theme consistency is an acceptance criterion.
9. Manual GNOME/GTK visual checks and real Orca/AT-SPI checks remain excluded unless separately authorized. F-303-02 keyboard traversal is not considered validated: CI input injection was unreliable, so physical Tab/Shift+Tab validation is deferred to M7 on a native host and tracked as residual debt (#655). Never report excluded or deferred checks as passed.
10. Use GitHub Actions as the test execution environment; do not claim local project tests were run. Record exact CI run, commit, job conclusions, counts, skipped jobs and limitations.
11. Update CHANGELOG, technical documentation, screenshots and internal links when relevant to an approved task. Screenshot capture remains deferred to the next release cycle as previously agreed; do not treat it as an immediate implementation gate.
12. Existing windows/components that are already coherent may remain unchanged after audit. Modernization is not a mandate for gratuitous redesign.

## 2. Product scope

The audit and modernization cover the complete UI surface:

| Area | Included surfaces and states |
|---|---|
| Welcome and main shell | Welcome page, main window geometry, navigation, header/action areas, primary and secondary actions, responsive behavior, focus and drop targets |
| Extracted / OCR | Extracted page, text presentation and scrolling, search, selection, copy/share/listen/undo/redo actions, processing and result states |
| History | History window/page, entry list, expansion/details, empty state, clear-history flow and related confirmation |
| Preferences | General, Languages, Editor and Voice pages; navigation between pages; controls, loading, failure and persistence states |
| Language selection | Language selector, installed/downloadable states, progress, success/failure announcements and badges |
| Keyboard Shortcuts | Shortcuts window/overlay, list presentation, resizing, scrolling and focus behavior |
| About and application information | About window/dialog, version and links |
| Dialogs and transient UI | Fatal-error, clear-history and other dialogs; popovers, menus, share/language menus, banners, toasts and notifications |
| Cross-cutting states | Loading, error, empty, disabled, hover, focus, active, confirmation, drag/drop, progress and reduced-motion behavior |

The inventory must be reconciled against the actual current application tree during M0. The table is the accepted scope baseline, not a claim that every listed surface has already been audited or implemented.

## 3. Global design and engineering acceptance criteria

### 3.1 Visual system

- Unified GTK4 / Libadwaita / Blueprint visual language.
- Consistent green brand palette, typography hierarchy, spacing, radii, iconography and component states.
- Shared visual patterns for buttons, rows, cards/boxed lists, headers, navigation, status indicators and empty states where appropriate.
- Correct contrast for application-controlled text, focus indicators, icons and controls in light and dark themes.
- Preserve theme-managed colors where appropriate; do not replace system theme behavior with hard-coded colors unnecessarily.
- Preserve automatic theme selection and explicit `default`, `force-light`, `force-dark` modes.

### 3.2 Responsive behavior and geometry

- Initial window target: **900×600**.
- Reference viewports: **360×600**, **640×480** and **1280×800**.
- No clipped essential controls or inaccessible actions at supported sizes; content must scroll or reflow intentionally.
- Main and secondary windows must respect monitor geometry and resize constraints without assuming a universal panel/dock-excluded work area.
- Responsive behavior must preserve control identity and semantics; do not duplicate interactive controls solely to support alternate layouts.

### 3.3 Interaction, accessibility and motion

- Predictable focus order, focus restoration after responsive reparenting, keyboard-operable controls and meaningful accessible names/roles.
- Status and progress announcements must be useful, deduplicated and appropriately prioritized.
- Reduced-motion preference must be respected without writing desktop-wide settings.
- Preserve existing drag/drop, clipboard, extraction, OCR, TTS, search and history behavior.
- Automated GTK accessibility/focus tests are required where behavior can be exercised in CI. Real assistive-technology verification remains excluded by current decision.

### 3.4 Architecture, performance and Linux compatibility

- Prefer reuse of existing GTK/Libadwaita components and project patterns.
- Avoid unnecessary dependencies and broad architectural refactors.
- Avoid regressions in startup, responsiveness, memory use and asynchronous lifecycle behavior.
- Keep Linux desktop integration and existing packaging contracts intact.
- Do not change OCR engines, models, processing pipeline, portals or OS-level configuration under this UI-only plan.

## 4. Phase plan M0–M7

Status values are evidence-based: **Not started**, **In progress**, **Partial**, **Completed**, **Blocked**. A phase is not complete merely because one window or one PR is complete.

| Phase | Scope | Exit condition | Current status |
|---|---|---|---|
| M0 | Full application audit | Complete inventory of windows/components/states/functions; current behavior, visual/functional/accessibility/architecture/performance/Linux-compatibility findings; prioritized requirements and traceability baseline | **Completed — M0-A inventory, M0-B traceability/evidence reconciliation and M0-C prioritized backlog/document reconciliation are complete. The programme proceeds to M1-05; this does not imply that all M0 findings are implemented.** |
| M1 | Design System and themes | Approved shared palette/tokens and reusable patterns; typography/spacing/component rules; automatic/light/dark and force-light/force-dark behavior verified | **Completed (operationally) — M1-02 through M1-07 are complete within their approved scopes. The automated design-system, palette/theme, reduced-motion, production color-scanner, CSS-consumer and typography-documentation work is recorded; final PR CI #43982790571 and CodeQL #43982790585 passed on head `443fd6085dfa14ef9941015e688760ff5874ec4f`. Manual rendered-UI, keyboard, Orca/AT-SPI and live multi-monitor checks were not performed and are explicitly deferred to M7; they are not represented as passed or as blockers to M2.** |
| M2 | Welcome and main navigation | Welcome and main-shell/navigation experience meet responsive, visual, interaction and focus criteria | **Completed (operationally) — M2-G01 and M2-G02 completed within their approved scopes; exact-head CI and CodeQL passed for M2-G02. All M2 requirements selected for automated verification are complete. Manual GNOME/GTK visual, keyboard and real Orca/AT-SPI checks remain deferred to M7 and are not claimed as passed; live multi-monitor verification remains excluded. Menu consistency and intentional menu differences are deferred to M5.** |
| M3 | Extracted and History | Extracted/OCR and History surfaces consistently modernized without functional regressions | **Completed operationally within the agreed M3 remediation scope (2026-11-17).** F-301/F-302, F-303-01 and F-303-03 accessible-label assertions are covered; the M3 CI remediation sequence is complete. F-303-02 physical Tab/Shift+Tab traversal remains explicitly deferred to native-host validation in M7-03/#655. No real Orca/AT-SPI or manual visual verification is claimed. Further visual refinements outside the agreed M3 scope remain backlog work, not an implicit reopening criterion.** |
| M4 | Preferences and languages | General, Languages, Editor, Voice and language selector meet shared visual, responsive, lifecycle and accessibility criteria | **Partial — M4-01 and M4-02 Tasks 1–4 are complete within their bounded scopes. Task 4 adds headless Languages search/filter/list-lifecycle coverage and real GTK integration for search, empty/reset state and add/remove signals. Task 5 must still disposition the remaining acceptance criteria, including download-progress UI coverage. Native physical keyboard traversal and real Orca/AT-SPI remain M7 validation, not CI claims.** |
| M5 | Other windows and components | Shortcuts, About, dialogs, popovers, menus, notifications, banners and toasts audited and addressed where justified | **Completed within the agreed M5 scope (2026-11-17).** M5-01 surface audit, M5-02 approved automated contracts and M5-03 portal-banner Dismiss correction are complete. P3 About/fatal-dialog, Portal cleanup/error-path and extra popover-focus tests are explicitly deferred and are not M5 exit criteria. Toast lifecycle/dismissal was explicitly excluded from the approved M5-02 test scope. Native visual, Orca/AT-SPI and physical-keyboard checks are assigned to M7, not M5. These exclusions are recorded as deferred, never as passed. |
| M6 | Responsive behavior and accessibility | Cross-window responsive, focus, contrast, accessible naming/announcements and reduced-motion requirements tested consistently | **Partial — selected automated accessibility and responsive work exists in PR #648; cross-window coverage remains** |
| M7 | Integration and consolidation | Integrated regression suite, documentation/CHANGELOG, translations review, screenshots at agreed timing, and distribution/build validation complete | **Partial — PR #648 has strong branch-level CI evidence; full app-wide phase exit criteria remain** |

## 4.1 Current prioritized backlog (M0-C, 2026-11-16)

M0-C consolidated the operational backlog. The task list is a planning baseline, not blanket implementation authorization. Every implementation requires a separate bounded proposal and explicit approval.

| ID | Priority | Task / boundary | Dependencies | Exit criteria |
|---|---|---|---|---|
| M1-05 | P1 | **Completed** — read-only cross-surface audit; report: [M1-05 audit](../../audit/ui-design-system-m1-05-2026-11-16.md). | M1-04 | 14 Blueprint templates, 15 Python UI modules and related styles/docs/tests inventoried; findings F1–F4 recorded with priorities and evidence limits. |
| M1-06 | P1 | **Completed within approved scope.** F1 reduced-motion handling in Shortcuts; F2 production-tree color-scanner enforcement in pytest. Exact-SHA CI and CodeQL passed; F3/F4 were subsequently addressed by the M1-07 follow-up recorded below. | M1-05; explicit approval received | Initial/live motion preferences, older-GTK fallback, close/dispose cleanup, root motion suppression, production-tree scanner and path/value rationale allowlist covered by tests; final AppImage aarch64 build, metadata verification, clean-host smoke test and artifact upload passed. F3/F4 were subsequently addressed by the M1-07 follow-up recorded below. |
| M2-01 | P1 | Complete the residual Welcome/main-shell audit, including navigation, states and focus affordances. | M2-E, M2-F | Requirement-to-surface matrix, findings and test gaps; separate automated evidence from excluded manual checks. |
| M3-01 | P1 | Full Extracted and History audit: states, actions, scrolling, list/row/empty/confirmation behavior. | M1-05 | Surface/state inventory, behavior-preservation map, findings and test gaps; no OCR internals or mockup-only features. |
| M4-01 | P1 | **Completed — audit and approved remediation of M4-F01–F04**; report: [M4-01 audit](../../audit/preferences-languages-m4-01-2026-11-17.md). | M1-05 | Configured model-source reachability, cancellable/disposal-safe network callback, LanguageRow idle-source cleanup and localized accessible model-list name implemented with four regression tests. Exact-head final CI evidence is recorded in the subordinate roadmap; global M4 remains Partial because other mapping and lifecycle coverage gaps remain. |
| M5-01 | P2 | **Completed — read-only audit and P2 test proposal**; report: [M5-01 audit](../../audit/ui-other-surfaces-m5-01-2026-11-17.md). | M1-05 | Component/state inventory, evidence-backed disposition and prioritized test gaps; coherent surfaces remain unchanged. |
| M5-02 | P2 | **Completed within approved automated-test scope (2026-11-17).** | M5-01; explicit approval received | Shortcuts search/empty/reset/Escape; static menu action resolution/scope; toast overlay delegation/title/priority. Toast lifecycle/dismissal remains explicitly excluded. Exact-head CI and CodeQL passed. No production behavior change in this task. |
| M5-03 | P2 | **Completed — portal-banner Dismiss correction (2026-11-17).** | M5-01 audit; separate approval received | Connect `Adw.Banner::button-clicked` to a handler that hides the portal-unavailable banner; preserve existing reveal behavior; two GTK regressions pass in the dedicated temporary run and final exact-code-head CI/CodeQL pass. CHANGELOG `[Unreleased]` records the user-visible fix. |
| M5-EXIT | — | **Completed by maintainer decision (2026-11-17).** | M5-01, M5-02, M5-03 | Close M5 within the agreed bounded scope. P3 test candidates are deferred/non-blocking; native visual, Orca/AT-SPI and physical keyboard verification are assigned to M7. Toast lifecycle is excluded, not silently marked tested. |
| M3-EXIT | P1 | **Completed operationally within agreed scope (2026-11-17).** Reconcile M3 implementation/test evidence and formally disposition residual native checks. | M3-01; F-301/F-302; F-303-01; F-303-02 disposition; F-303-03 assertions | M3 remediation sequence closed; F-303-02 remains deferred to M7-03/#655 and is not marked passed. No broader redesign or manual AT verification is implied. |
| M4-02 | P1 | **In progress.** Tasks 1–4 complete within approved bounded scopes; Task 5 (full acceptance-criteria disposition and closure review) remains. | M4-01; approved M4-02 plan and task-level maintainer approvals | General, Editor, Voice and Languages search/filter/list-lifecycle coverage completed. Task 5 must map every acceptance criterion, explicitly disposition download-progress/UI residuals and retain native keyboard/AT-SPI checks for M7. |
| M6-01 | P2 | Cross-window responsive/accessibility coverage matrix and approved automated-test gap closure. | M2-01, M3-EXIT, M4-02, M5-01 | Reference viewport matrix plus focus, naming, announcements, contrast and reduced-motion evidence; exclusions explicit. |
| M7-01 | P2 | Define the global integration and final validation plan. | M1-05 through M6-01; M1-06 disposition | Traceability/validation plan, exact evidence requirements, translation review and deferred screenshot timing. |
| M7-02 | P3 | Execute approved global integration, documentation and distribution validation. | M7-01 and explicit approval | Regression/packaging evidence, relevant docs/CHANGELOG, translation review and final requirement dispositions. |
| M7-03 | P2 | Perform native-host F-303-02 History keyboard traversal validation (Tab/Shift+Tab, forward/reverse suffix-action reachability, expanded/collapsed rows and focus recovery). | #655; supported native desktop session and explicit test authorization | Record host/session details, exact commit, test procedure/results and residual findings; only then decide whether automated tests can be restored to blocking CI. |

P1 establishes foundational audits and justified gap closure; P2 completes cross-surface validation and integration planning; P3 executes final integration. M1-06 is complete within its approved scope with exact-SHA CI and CodeQL success. No task authorizes implementation merely by appearing in this table.

### M0 — Full audit

1. Enumerate every window, page, dialog, popover, menu, reusable component and transient state in the current source tree.
2. Record each surface's purpose, current behavior, entry/exit paths, dependencies, asynchronous operations and existing tests.
3. Assess visual consistency, functional usability, accessibility, architecture, performance and Linux desktop compatibility.
4. Compare the current implementation with the accepted product scope and original modernization records, including PR #448 as historical input.
5. Classify findings as required correction, optional improvement, already acceptable, regression risk or out of scope.
6. Build the requirement-to-surface traceability matrix before proposing implementation tasks.

**M0 deliverables:** UI inventory, findings register, requirement matrix, baseline screenshots only if already available (new screenshot capture remains deferred), and prioritized phase backlog.

### M1 — Design System and themes

1. Audit actual style tokens, CSS/GResource loading, shared components and theme overrides.
2. Consolidate the approved green palette and semantic color roles.
3. Define consistent typography, spacing, radii, iconography, button hierarchy, list/card patterns and focus/disabled/hover states.
4. Check every surface for hard-coded colors and theme-role misuse.
5. Preserve automatic theme selection and the `default`, `force-light` and `force-dark` modes.
6. Add automated palette, contrast and theme-role regression coverage.

**M1 deliverables:** design-system specification, shared style implementation where justified, component usage rules and automated theme/palette tests.

**M1-02 completed:** the GTK4/Libadwaita-first typography, spacing and custom-radius conventions are documented in `docs/ui-design-system.md`; Blueprint/GTK CSS spacing is normalized and statically guarded. The shared numeric spacing scale is documented rather than expressed as CSS custom properties because GTK CSS does not support arbitrary numeric custom properties. One 6 px Welcome compact-action spacing exception is retained to preserve responsive geometry and is explicitly guarded by a regression test. Historical status note: at the time of this M1-02 entry, the broader M1 phase remained Partial; the later M1-07 closure decision below supersedes that interim status.

### M2 — Welcome and navigation

1. Review Welcome hierarchy, primary action, secondary actions, drag/drop, empty/loading/error states and constrained layouts.
2. Review main-shell navigation, header/action areas, page transitions and navigation focus.
3. Validate reference viewports and minimum practical geometry through automated tests.
4. Preserve existing action semantics and avoid duplicate controls during responsive layout changes.

**M2 deliverables:** consistent Welcome/shell navigation, responsive/focus regression tests and updated behavior documentation.

### M3 — Extracted and History

1. Audit Extracted content hierarchy, text scroller, search, selection and action placement.
2. Audit OCR processing, success, empty and failure states without changing OCR internals.
3. Audit History list, row expansion/details, empty state and clear-history confirmation.
4. Preserve existing list/row behavior and ensure long content remains reachable.
5. Do not introduce mockup-only History search, photo previews, Save or formatting tools without separate approval.

**M3 deliverables:** consistent Extracted and History presentation, preserved interactions and automated regression coverage.

### M4 — Preferences and languages

1. Audit General, Languages, Editor and Voice pages for grouping, labels, control hierarchy, sizing and navigation.
2. Audit language selector and installed/downloadable language states, badges, progress and failure/retry behavior.
3. Verify asynchronous TTS/catalog and OCR-related UI lifecycle behavior without expanding into engine/pipeline work.
4. Preserve settings persistence and existing semantics.

**M4 deliverables:** coherent Preferences and language-selection experience, lifecycle/accessibility regression tests and documentation.

### M5 — Other windows and shared components

1. Audit Keyboard Shortcuts presentation, sizing, scrolling and focus.
2. Audit About and fatal-error/application-information surfaces.
3. Audit clear-history and other confirmation dialogs.
4. Audit share/language popovers, menus, banners, toasts and notifications.
5. Review all transient states for consistency, focus handling, dismissal behavior and accessible labels.
6. Leave already coherent surfaces unchanged unless M0 identifies a concrete issue.

**M5 deliverables:** justified corrections across remaining windows/components and focused regression tests.

**M5 closure (2026-11-17):** the maintainer approved closure after confirming that P3 candidates were never part of the agreed M5 exit criteria and that native/manual verification had already been moved to M7. M5 is complete for its agreed scope: M5-01 audit, M5-02 selected automated contracts, and M5-03 banner dismissal correction. P3 dialog/Portal/popover test candidates remain deferred; toast dismissal/lifecycle remains outside the approved M5-02 test scope. No manual GNOME/GTK, Orca/AT-SPI or physical-keyboard check is claimed as passed.

### M6 — Responsive behavior and accessibility

1. Verify responsive behavior across all applicable windows at the reference viewports.
2. Verify automated focus traversal/restoration, accessible names/roles, status announcements, contrast and reduced-motion behavior.
3. Ensure scrolling and resizing preserve access to all essential controls.
4. Test light/dark and theme-mode behavior through automated coverage where possible.
5. Keep manual GNOME/GTK visual, Orca/AT-SPI and manual keyboard checks explicitly excluded unless the maintainer changes that decision.

**M6 deliverables:** cross-window responsive/accessibility matrix, automated tests and a clear record of excluded manual verification.

### M7 — Integration and consolidation

1. Run the complete automated test suite and packaging/build matrix through GitHub Actions.
2. Review regressions across all modernized and intentionally unchanged surfaces.
3. Update CHANGELOG and technical/user documentation; validate links and cross-references.
4. Review translation impact and avoid introducing untranslated user-facing strings.
5. Capture/update screenshots only at the previously agreed next-release stage.
6. Record distribution validation, CI evidence, known limitations and final requirement dispositions.
7. Recommend readiness only when all accepted requirements are either verified or explicitly deferred/rejected by maintainer decision.

**M7 deliverables:** integration evidence, documentation/CHANGELOG, translation review, distribution validation and final traceability report.

## 5. Requirement-to-surface traceability baseline

This table maps the global requirements to the current known PR #648 contribution. It is intentionally conservative: **partial** means there is implementation evidence for part of the requirement, not that the whole surface or phase is complete.

| Global requirement / surface | PR #648 contribution known today | Remaining global work / disposition |
|---|---|---|
| Green palette and runtime stylesheet | Green semantic palette, GResource CSS provider registration, palette/contrast tests; M1-05 cross-surface audit recorded targeted gaps | M1-06 implementation/test coverage closes reduced-motion handling in Shortcuts and production-tree color-scanner enforcement; all automated CI and CodeQL checks passed; manual/pixel validation remains excluded |
| Welcome primary/secondary actions | Screenshot primary; Open/Paste/Drop responsive grouping | Complete remaining M2 audit of navigation and all states |
| Welcome responsiveness and scrolling | Adaptive actions, scroll container, focus restoration; constrained-viewport test passed in recorded CI | Extend M6 coverage only where M0 identifies gaps in other windows |
| Main window geometry | Monitor-aware clamp, monitor-change handling, normal-size persistence | M2/M6 audit other windows and geometry constraints; no universal dock-aware guarantee |
| Extracted | Compact header/action bar and existing scroller regression protection | M3 audit full Extracted/OCR states and action behavior |
| History | Selected theme/contrast and scroller protections are recorded | M3 automated remediation is operationally closed within agreed scope; native keyboard/Orca/AT-SPI validation is deferred to M7; broader visual refinements remain backlog work |
| Preferences | General/Editor/Voice/Languages split and selected async lifecycle protections | M4-01 audit/remediations complete; M4-02 closes CI-testable mapping and lifecycle gaps; native keyboard/AT validation remains M7 |
| Keyboard Shortcuts | Resizability and existing scroll behavior | M5 full visual, interaction and accessibility audit |
| About, dialogs, popovers, menus, banners, toasts, notifications | M5-01 audit completed; M5-02 Shortcuts/menu/toast contracts added; M5-03 banner dismissal corrected and covered by two GTK regressions | M5 complete within agreed scope. P3 About/fatal-dialog, Portal cleanup/error-path and extra popover-focus tests are deferred/non-blocking; toast lifecycle excluded. Native visual/AT-SPI/keyboard checks belong to M7. |
| Accessibility A1–A5 | Download labels/announcements, status announcements, automated focus tests, reduced motion, contrast roles | M6 extend traceability to all relevant windows; real assistive-technology checks excluded |
| Cross-window responsive behavior | Welcome and selected window geometry/preferences/shortcuts changes | M0/M6 determine remaining surfaces and test coverage |
| Integration/build validation | PR #648 has a successful recorded multi-job CI run on its prior application/workflow head | M7 requires final CI on the eventual integrated head and complete regression review |

### PR #648 evidence boundary

- PR #648 is one implementation workstream, not the global modernization itself.
- The subordinate roadmap records M1 Preferences/lifecycle, M2 Extracted, M2-B Welcome, palette, shell geometry and accessibility A1–A5 implementation/evidence.
- Its recorded complete CI run [#43801048308](https://github.com/D3M-Sudo/Anura/actions/runs/43801048308) ran on application/workflow head `cc8aaad6601f25b9e96f3d2eb9f78bc9fb3c524d`; later documentation-only commits must not be represented as having that exact CI run.
- Recorded GTK result: 431 passed, 5 skipped, 632 deselected, 2 warnings. Packaging and validation jobs recorded in the subordinate roadmap passed; release publication was skipped as expected for a PR.
- Manual GNOME/GTK visual checks, Orca/AT-SPI and manual keyboard checks are excluded, not passed.
- PR #648 remains Draft/open/unmerged. Its current state must be rechecked before any future integration decision.

## 6. Relationship to the PR #648 workstream roadmap

The subordinate document [2026-11-16-anura-ui-modernization-roadmap.md](2026-11-16-anura-ui-modernization-roadmap.md) remains the detailed execution/evidence log for PR #648.

- It owns the detailed UI-00…UI-12 task history, implementation descriptions, commit/head references, CI run records and documentation-reconciliation tasks specific to PR #648.
- This global roadmap owns the full M0–M7 scope, phase status, application-wide requirement matrix and prioritization.
- A task marked complete in the subordinate roadmap may satisfy one contribution to a global requirement, but does not automatically complete the corresponding global phase.
- When a PR #648 task changes the global status, update both documents. Update this global roadmap before beginning the next task.
- New work outside PR #648 must receive its own approved task/branch/PR plan; do not silently expand PR #648 or alter protected branches.

## 7. Next execution sequence

1. **GLOBAL-00 — Establish the roadmap hierarchy and reconcile references.** This task creates this global document, identifies the PR #648 roadmap as subordinate and updates the handover links. Documentation-only; no application code or PR state changes.
2. **M0-A — Complete the current-tree UI inventory.** **Completed 2026-11-16** in read-only mode; details and limitations are recorded below.
3. **M0-B — Requirement and evidence reconciliation.** **Completed 2026-11-16** in read-only mode; details and limitations are recorded below.
4. **M0-C — Prioritize the phase backlog.** The bounded, dependency-ordered M1–M7 audit/implementation backlog was synthesized and reviewed in chat on 2026-11-16. Its roadmap record remains separate from this M1 audit update; no implementation was authorized by backlog review.
5. **M1-A/M1-B — Design-system and theme audit.** **Completed 2026-11-16** in read-only mode. The historical audit snapshot initially described M1 as Partial; that interim status was superseded by the M1 operational closure decision recorded below and in the current phase table.
6. **M2-A — Welcome and main-navigation read-only audit. Completed 2026-11-16**; findings and evidence limits are recorded below. No code changes were made.
7. **M2-B — focused read-only verification of complete NavigationView transition paths and state restoration. Completed 2026-11-16**; findings and evidence limits are recorded below. No code changes were made.
8. **M2-C — bounded automated integration-test proposal. Completed 2026-11-16 (planning only).** The two navigation paths, focus/side-effect assertions and maintainer-approved state-retention policies are specified in the task record below. No implementation was authorized.
9. **M2-D — implement the approved Extracted and History navigation-state policies, add automated regression tests, update CHANGELOG and record exact CI evidence. Completed 2026-11-16 on `bb316f94d37629cc7566b24330a87b6e86029db3`.** The contemporaneous note that M2 remained Partial was an interim status, superseded by the M2 operational closure decision recorded below and in the current phase table.
10. **M5-01 — read-only audit of Shortcuts, About, dialogs, popovers, menus, banners, toasts and notifications. Completed 2026-11-17**; audit and original test-gap proposal are recorded in [M5-01 audit](../../audit/ui-other-surfaces-m5-01-2026-11-17.md).
11. **M5-02 — approved automated contracts. Completed 2026-11-17**: Shortcuts search/Escape, menu action/scope and toast delegation/title/priority tests; toast lifecycle deliberately excluded.
12. **M5-03 — portal-banner Dismiss correction. Completed 2026-11-17**: signal wiring and handler fix with two GTK regression tests; temporary regression run and exact-code-head CI/CodeQL passed.
13. **M5-EXIT — phase closure. Completed 2026-11-17 by maintainer decision**: P3 candidates are deferred/non-blocking; native visual/accessibility/keyboard validation is allocated to M7. This closes M5 only within the agreed scope, not the global modernization. 
14. **M3-EXIT — operational closure. Completed 2026-11-17**: F-303-03 accessible-label assertions are present; F-303-02 physical keyboard traversal remains deferred to M7-03/#655.
15. **M4-02 — prepare and execute the bounded CI coverage-gap closure plan. Next, after separate maintainer approval.** M6-01 remains sequenced after M4-02 so that the Preferences/language coverage gaps are not silently carried forward.

No application-code task is authorized by GLOBAL-00 or by the existence of this roadmap.

## 8. Mandatory task update record

After every completed task, append/update the relevant phase and record:

- **Task ID / title:**
- **Outcome:** completed / partial / blocked
- **Scope and affected surfaces:**
- **Files changed:**
- **Branch and resulting head commit:**
- **Tests:** exact command or CI job, counts and result
- **CI run:** URL and conclusion; identify skipped jobs
- **Limitations / exclusions:**
- **Requirement matrix changes:**
- **Next permitted task:**
- **Global roadmap updated before next task:** yes


### 2026-11-16 — M0-A: current-tree UI inventory completed

- **Outcome:** completed as a structural/read-only inventory. No repository files, application code, workflows, tests, PR metadata or protected branches were changed.
- **Audited snapshot:** branch `fix/ui-modernization-aligned`, HEAD `066c698ea9d039985e79e09776268d5d4a96414f`.
- **Repository inventory:** 416 tracked files; 89 under `anura/`; 14 Python widget files; 14 Blueprint (`.blp`) templates; 125 test files.
- **Surface map:** main shell/navigation (`anura/window.py`, `data/ui/window.blp`); Welcome; Extracted/OCR; History; Preferences General/Editor/Voice/Languages; Welcome language popover and rows; Keyboard Shortcuts; Share; About and dialogs; notification services; banners/toasts; contextual menus, screenshot menu and provider/language popovers.
- **State inventory:** OCR processing/results/errors; drag/drop; clipboard; text empty/selection/search-no-results; TTS generation/playback/pause; History empty/disabled/populated/expanded and deletion confirmation; model download progress/failure/network states; asynchronous Voice catalog; toasts, banners and desktop notifications.
- **Representative existing test modules identified:** `test_ui_palette.py`, `test_reduced_motion.py`, `test_accessible_status_announcements.py`, `test_window_geometry.py`, `test_history_ui.py`, `test_keyboard_shortcuts.py`, Preferences resilience/Voice/idle/language tests, `test_language_row_accessibility.py`, notification/privacy tests, file-dialog regressions, search navigation, widget/share tests, Extracted reflow, UI widget audit, Welcome accessibility and shortcut consistency.
- **Preliminary findings:** contextual menu contents differ by page and require intentionality review rather than assuming parity; About/menu/some dialogs have less dedicated UI coverage than Welcome/History; responsive evidence is concentrated on Welcome and window geometry; Preferences Languages and the Welcome language selector need a consistency review; toast/banner/desktop notification implementations need a cross-surface consistency review; shared CSS/component patterns need systematic audit.
- **Limitations:** this was a structural source/test inventory, not a complete runtime visual audit, manual desktop verification, test execution or proof that every behavior is correct. Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain excluded by maintainer decision.

### 2026-11-16 — M0-B: requirement traceability and evidence reconciliation completed

- **Outcome:** completed as a read-only reconciliation of the approved global requirements against the M0-A inventory, inspected source/test modules and available PR #648 CI evidence. No repository files or tests were changed or run.
- **Requirement disposition:** R01–R11 and R16 remain **partial** at application-wide scope; R12 (no OCR/model/pipeline/image-processing/portal/OS expansion) and R13 (no unapproved mockup-only features) remain explicit scope constraints; R14 manual verification remains **excluded**, not passed; R15 CI evidence-recording requirement has a recorded baseline; R17 remains a governance constraint.
- **Priority findings:**
  - **High — M0-B01:** verify automatic/light/dark theme behavior and `default`, `force-light`, `force-dark` across all relevant surfaces.
  - **High — M0-B02:** extend responsive test coverage beyond Welcome and main-window geometry to applicable secondary surfaces and reference viewports.
  - **High — M0-B03:** extend cross-window focus, accessible-name/role and announcement coverage.
  - **Medium — M0-B04:** add focused UI coverage for About, contextual menus and dialogs where tests are practical.
  - **Medium — M0-B05:** reconcile behavior and presentation across toast, banner and desktop notification channels.
  - **Medium — M0-B06:** review translation impact and user-facing strings as part of implementation/integration.
- **Evidence boundary for CI:** run [#43801048308](https://github.com/D3M-Sudo/Anura/actions/runs/43801048308) succeeded on tested application/workflow head `cc8aaad6601f25b9e96f3d2eb9f78bc9fb3c524d`: Python quality, changelog integrity, GTK integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set and multi-architecture validation succeeded; publish release was skipped as expected for a PR. GTK reported 431 passed, 5 skipped, 632 deselected and 2 warnings. This is aggregate run evidence, not an individual pass/fail result for every named test module and not evidence for later documentation-only commits.
- **AI Delivery Evidence Checker limitation:** the checker was supplied with criteria and evidence snippets; its verdict was `not_supported` at Level 1 because the supplied material did not establish each criterion. It does not inspect the full live repository, execute tests or authenticate CI evidence. Its result is an evidence-sufficiency warning, not a finding that the implementation is defective. Individual test outcomes not independently supplied remain unknown; they must not be described as failed or skipped on that basis.
- **Graphify limitation:** its repository graph indexed `development`, not the audited `fix/ui-modernization-aligned` branch. Graph output was used only as discovery context, not as branch-specific implementation proof.
- **Context7:** official Libadwaita and Blueprint documentation was used to clarify component responsibilities and template/widget relationships; it does not prove Anura-specific behavior.
- **Superpowers:** no executable Superpowers tool was available in this session; no subagents were run.
- **M0 status:** remains **Partial** until M0-C produces the prioritized, bounded backlog and remaining audit synthesis. M0-A and M0-B are complete; no implementation task is authorized by their completion.
- **Next permitted task:** M0-C planning only; no application-code changes are authorized by this record.

### 2026-11-16 — M1-A/M1-B: design-system and theme audit completed

- **Outcome:** completed as a read-only source/test audit on `fix/ui-modernization-aligned`. No application code, tests, workflows, PR metadata, protected branches or packaging files were changed; no tests or CI were run.
- **Audited source:** `data/style.css`, `anura/main.py`, `data/io.github.d3m_sudo.anura.gschema.xml`, `data/ui/preferences_general.blp`, and `tests/test_ui_palette.py`; existing roadmap and PR #648 metadata were also checked for context.
- **M1-A — Design system:** the application has a GResource-loaded GTK stylesheet and an existing green palette. The inspected primary accent tokens are `accent_color: #16A36A`, `accent_bg_color: #0F7650` and `accent_fg_color: #FFFFFF`. Existing CSS also uses GTK/Libadwaita semantic colors and component-specific selectors. This is a useful foundation, but not evidence of a fully centralized design-token system.
- **M1-A findings:** (1) shared token coverage appears partial; (2) component-specific color declarations/selectors need a complete usage audit; (3) typography, spacing and radii consistency has not yet been established; (4) CSS class usage and possible dead/duplicated rules need source-to-template tracing. These are audit findings/open questions, not confirmed defects.
- **M1-B — Theme handling:** GSettings defines `default`, `force-light` and `force-dark`; Preferences General exposes the color-scheme choice. Application startup applies the configured scheme and connects to `changed::color-scheme` for subsequent updates. The inspected code therefore establishes the preference mapping and runtime update path.
- **M1-B findings:** `tests/test_ui_palette.py` provides static palette/contrast assertions for selected UI elements. The inspected evidence does not establish an automated runtime test that switches the actual Libadwaita color scheme and verifies all relevant application surfaces. Cross-window theme coverage remains unproven.
- **Recommended direction (not implementation authorization):** retain the approved green/teal identity and existing semantic GTK colors; centralize only genuinely shared values; avoid replacing theme-managed colors with unnecessary hardcoded values; trace CSS selectors to their consumers before cleanup; add automated runtime theme coverage for `default`, `force-light` and `force-dark` across applicable surfaces.
- **Evidence limits:** this was a source/test inspection, not a runtime visual audit. No contrast recalculation beyond the existing test source, GTK rendering, test execution or CI result is claimed. Manual GNOME/GTK visual checks, Orca/AT-SPI and manual keyboard checks remain excluded, not passed.
- **M1 disposition:** M1-A and M1-B audit activities are complete; the M1 phase remains **Partial** pending design-system decisions/implementation, broader token and component coverage, and automated cross-surface theme verification.
- **Next permitted task:** M2-A Welcome and main-navigation read-only audit. Implementation still requires a separate explicit approval.


### 2026-11-16 — M2-A: Welcome and main-navigation audit completed

- **Outcome:** completed as a grouped, read-only source/test audit on `fix/ui-modernization-aligned`, commit `25016746177a2a6a6588cd22cb02cec0b96be03c`. No repository files, application code, tests, workflows, PR metadata, protected branches or merge state were changed; no tests or CI were run.
- **Audited source and tests:** `anura/widgets/welcome_page.py`, `anura/window.py`, `anura/main.py`, `anura/core/action_registry.py`, `data/ui/welcome_page.blp`, `data/ui/window.blp`, `data/ui/extracted_page.blp`, `data/ui/history_page.blp`, `tests/test_widgets.py`, `tests/test_audit_ui_widgets.py`, `tests/test_keyboard_shortcuts.py` and `tests/test_app_lifecycle.py`.
- **Welcome structure and behavior:** Welcome is an `Adw.NavigationPage` using an `Adw.StatusPage`, a primary screenshot action, language selector, secondary open/paste/drop actions and an expandable drop area. The secondary actions are reparented between wide and compact layouts; the compact layout exposes a More Options menu. The drop area supports Escape collapse and updates its accessible expanded/label state. The code also handles OCR capability absence by disabling the screenshot action and providing an explanatory tooltip.
- **Responsive/focus evidence:** existing tests cover 360×600, 640×480, 900×600 and 1280×800 viewports; measured-width breakpoints; compact/wide action visibility and parentage; vertical scrolling; compact popover opening; Tab focus order; focus restoration after responsive reparenting; and focus movement from More Options to the primary action. This is substantial existing Welcome coverage and should be preserved; the audit found no evidence-based reason for a wholesale rewrite of its responsive system.
- **Main-shell/navigation structure:** `Adw.NavigationView` hosts Welcome, Extracted and History pages. The inspected handlers push Extracted after OCR navigation requests and focus the extracted text view; return-to-Welcome pops to the `welcome` tag and stops TTS; opening History refreshes it before pushing the `history` tag. Application actions and keyboard accelerators are registered through `ActionRegistry`. The Welcome menu includes History, Preferences, Shortcuts, About, issue reporting and GitHub actions; Extracted has its own header actions.
- **Findings / follow-up:** the inspected test evidence is strong for Welcome widget behavior but does not establish a dedicated end-to-end integration suite for complete Welcome → Extracted → Welcome and Welcome → History → return navigation paths, including state restoration and relevant side effects. This is an evidence gap, not a confirmed navigation defect. Headerbar/back affordances and state preservation should be examined in the focused follow-up before proposing any implementation.
- **Prioritized follow-up candidates:** high — preserve existing responsive/focus tests and establish complete navigation transition coverage; medium — verify headerbar/back affordances and state preservation across transitions; low — review consistency of primary-menu action hierarchy where a concrete usability issue is evidenced.
- **Evidence limits:** source/test inspection only. No runtime behavior, test pass/fail outcome or CI result is claimed. Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed.
- **M2 disposition:** M2 remains **Partial**. M2-A audit is complete; Welcome's responsive/focus implementation has substantial test coverage, while end-to-end navigation transitions/state restoration and remaining shell acceptance criteria are not yet established.
- **Next permitted task:** M2-B, focused read-only verification of complete `Adw.NavigationView` transition paths and state restoration. Implementation requires separate explicit approval.


### 2026-11-16 — M2-B: NavigationView transition and state-restoration audit completed

- **Outcome:** completed as a read-only source/test audit on `fix/ui-modernization-aligned`, audited against commit `bf39a91454ff2665cb881454363126f0b72e0ea5`. No application code, tests, workflows, PR metadata, protected branches or merge state were changed; no tests or CI were run.
- **Audited source and tests:** `anura/window.py`, `anura/main.py`, `anura/core/action_registry.py`, `anura/widgets/welcome_page.py`, `anura/widgets/extracted_page.py`, `anura/widgets/history_page.py`, `anura/controllers/ocr_controller.py`, `data/ui/window.blp`, `data/ui/welcome_page.blp`, `data/ui/extracted_page.blp`, `data/ui/history_page.blp`, `tests/test_app_lifecycle.py`, `tests/test_keyboard_shortcuts.py`, `tests/test_widgets.py`, `tests/test_audit_ui_widgets.py` and `tests/test_history_controller.py`.
- **Welcome → Extracted:** OCR navigation is mediated by `OcrController`, which emits `navigation-requested("extracted")`; the window pushes the Extracted page and requests focus on `text_view`. On return, the window pops to the `welcome` tag and stops TTS. `ExtractedPage.do_hiding()` clears its buffer and emits `go-back`; the inspected implementation therefore does not preserve extracted text across this return path. This is an observed behavior, not a defect determination; whether it is intended product behavior remains a state-policy question.
- **Welcome → History:** the Welcome menu exposes `win.show-history`; the registered action invokes the window handler, which calls `history_page.refresh()` before pushing the `history` page. The History page uses an `Adw.HeaderBar`. The inspected implementation rebuilds History rows during refresh; persistence of expanded-row state and scroll position across reopening was not established.
- **Navigation affordances and focus:** the inspected page templates use Libadwaita header-bar/navigation structures, but no dedicated test was found proving the rendered back affordance and complete return path. OCR focus is requested after navigation push, but the inspected tests do not establish that focus is actually acquired once the destination page is mapped and visible.
- **Test coverage:** `tests/test_widgets.py` and `tests/test_audit_ui_widgets.py` cover Welcome responsive layout and focus behavior; `tests/test_history_controller.py` covers History controller operations, not navigation; `tests/test_app_lifecycle.py` and `tests/test_keyboard_shortcuts.py` do not establish complete page-transition integration coverage. No test was identified that exercises the complete Welcome → Extracted → Welcome or Welcome → History → Welcome path with state and side-effect assertions.
- **Findings:** no confirmed navigation defect was established by static inspection. The primary gap is missing end-to-end evidence for transitions, return affordances, focus acquisition/restoration, TTS stop behavior in the full flow, History refresh and any required state preservation.
- **Recommended next step (not implementation authorization):** define a bounded automated integration-test proposal for both navigation paths. Decide explicitly whether Extracted text should be discarded on return and whether History expansion/scroll state should persist. Assert actual focus only where the GTK test environment can reliably observe it; otherwise document the limitation rather than claiming success.
- **Evidence limits:** source/test inspection only; no runtime GTK execution, test pass/fail result or CI result is claimed. Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed.
- **M2 disposition:** remains **Partial**. M2-A and M2-B audits are complete, but integration tests and remaining shell acceptance evidence are not established.
- **Next permitted task:** M2-C, planning a bounded automated integration-test proposal. No code changes are authorized.


### 2026-11-16 — M2-C: navigation integration-test proposal

- **Outcome:** completed as a planning-only task. The proposal defines bounded automated integration coverage for Welcome → Extracted → Welcome and Welcome → History → Welcome. No source code, tests or workflows were changed.
- **Maintainer-approved state policies:**
  - **Extracted (choice 1C):** retain the extracted text when returning to Welcome; retain it only until the next extraction, which replaces the prior content.
  - **History (choice 2C):** retain expanded-row state and scroll position across navigation/reopening within the current application session; do not persist either state across application restarts.
- **Proposed Extracted scenarios:** verify destination visibility and focus where observable; text survives return to Welcome; a subsequent extraction replaces the previous text; returning while TTS is active stops playback; re-entering Extracted shows the current result.
- **Proposed History scenarios:** verify refresh before display; expansion and scroll survive leaving/reopening History within one session; a fresh application session starts with default expansion/scroll state. The restart case must distinguish in-memory session state from persisted state and must not introduce new GSettings keys or disk persistence for these transient preferences.
- **Cross-cutting test design:** reuse existing GTK integration fixtures/helpers and deterministic OCR/History data; assert observable navigation, focus, signals and side effects rather than implementation details. Assert actual focus only where the CI GTK environment can reliably observe it; otherwise record the limitation.
- **Test proposal identifiers:** M2-C01–M2-C05 (Extracted lifecycle/navigation/TTS); M2-C06–M2-C10 (History refresh, session-state retention and restart reset).
- **Evidence limits:** this is a test design, not execution evidence. No tests were run and no CI result is claimed. Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed.
- **Requirement disposition:** the user decisions for Extracted text lifetime and History session-only state are now explicit acceptance constraints for any subsequent implementation.
- **Next permitted task:** M2-D, present a bounded implementation scope with affected files, acceptance criteria and CI plan; obtain separate explicit approval before modifying source, tests or workflows.
- **Roadmap update:** this record is being committed to the global roadmap on fix/ui-modernization-aligned; no protected branch, PR metadata or merge state is to be changed.

## 9. Change log

### 2026-11-16 — GLOBAL-00: global roadmap consolidated

- Recovered the previously approved Anura UI/UX Modernization v1.0 M0–M7 scope and made this the primary application-wide roadmap.
- Preserved the detailed PR #648 roadmap as a subordinate implementation/evidence register rather than replacing or discarding its history.
- Established conservative phase statuses: PR #648 contains substantial contributions, but no evidence supports claiming the full application-wide M0–M7 modernization is complete.
- Recorded the full application surface inventory baseline, design/engineering acceptance criteria, phase exit conditions and requirement-to-surface matrix.
- Manual visual/Orca/AT-SPI/manual keyboard checks remain excluded by maintainer decision; automated GTK tests remain in scope.
- GLOBAL-00 is documentation-only. No application code, protected branch, PR state or merge state is changed.
- Next task: M0-A, read-only full current-tree UI inventory, subject to task-level approval.


### 2026-11-16 — GLOBAL-00 publication and hierarchy verification

- Global roadmap created in commit `7683f8ea733f8218eb223b2f710291a87592a514`.
- PR #648 subordinate roadmap reframed and linked to the global plan in commit `ed676556a56cb541e458dfe302f6ec65ae83200f`.
- `HANDOVER.md` updated to identify the global M0–M7 roadmap as primary and PR #648 plan as subordinate in commit `549208d2a0c53585bc0986d7d698ed0a2b0329ff`.
- Verified all three files are readable on `fix/ui-modernization-aligned`, the branch exists, and the PR remains open. No PR state transition, merge, application-code edit or protected-branch update was performed.
- Branch comparison against `feature` reports 320 commits ahead and 0 behind, with `feature` at `cb079b0b55e252a7ac054fe1b6f57030ddc7b1f9`. This is a fresh comparison snapshot, not a merge/readiness recommendation.
- This task changed documentation only; no new CI run is claimed. The latest recorded application CI evidence remains the run cited in the subordinate roadmap and must be re-evaluated when implementation changes are proposed.
- **GLOBAL-00 completed.** Next global task: M0-A, read-only full current-tree UI inventory, pending explicit task approval. Mandatory roadmap update completed before any next task.


### 2026-11-16 — M0-A/M0-B audit record

- Recorded the completed structural UI inventory (M0-A), requirement/evidence reconciliation (M0-B), priority findings, CI evidence boundary and tool limitations.
- Updated the M0 status and execution sequence: M0 remains partial; M0-C backlog prioritization is next.
- Documentation-only roadmap update on `fix/ui-modernization-aligned`; no application code, workflows, tests, protected branches, PR state or merge state changed. No CI run is claimed.

### 2026-11-16 — M1-A/M1-B audit record

- Recorded the read-only design-system/CSS and theme-mode audit, including existing green tokens, GSettings mode mapping, runtime update path, test coverage boundary and unresolved app-wide coverage.
- M1 remains Partial: audit activities are complete, but design-system consolidation and automated cross-surface runtime theme verification remain.
- Updated the next permitted task to M2-A, read-only Welcome and main-navigation audit.
- Documentation-only update on `fix/ui-modernization-aligned`; no application code, tests, workflows, protected branches or PR metadata changed. No CI run is claimed.


### 2026-11-16 — M2-A audit record

- Recorded the read-only Welcome/main-navigation audit, including existing responsive/focus test coverage, NavigationView structure, evidence gaps and follow-up priorities.
- M2 remains Partial; the next permitted task is M2-B, a focused read-only verification of complete navigation transition paths and state restoration.
- Documentation-only update on `fix/ui-modernization-aligned`; no application code, tests, workflows, protected branches, PR metadata or merge state changed. No CI run is claimed.


### 2026-11-16 — M2-B audit record

- Recorded the read-only NavigationView transition/state-restoration audit, including OCR and History paths, current side effects, existing test coverage and missing end-to-end evidence.
- M2 remains Partial. Next permitted task is M2-C, a planning-only proposal for bounded automated integration tests; implementation still requires separate explicit approval.
- Documentation-only update on `fix/ui-modernization-aligned`; no application code, tests, workflows, protected branches, PR metadata or merge state changed. No CI run is claimed.


### 2026-11-16 — M2-D implementation and verification record

- **Outcome:** completed for the bounded Extracted/History navigation-state scope. The implementation preserves Extracted text across navigation until the next OCR result replaces it, and preserves History expanded-row identity plus vertical scroll across refresh/navigation within the current process. History view state is not persisted across process restarts.
- **Implementation:** `anura/widgets/extracted_page.py` no longer clears the text buffer in `do_hiding()`; `anura/widgets/history_page.py` snapshots the expanded entry ID and scroll adjustment, maps rebuilt rows by ID and restores state through a generation-guarded GLib idle callback. Removed entries and stale callbacks are handled safely.
- **Regression coverage:** `tests/test_widgets.py` covers Extracted hide/replace, navigation round-trip, focus acquisition when navigating to Extracted, and stopping active TTS when returning to Welcome. `tests/test_history_ui.py` covers state snapshot/restore, removed entries, stale refresh callbacks and default transient state on a newly constructed page.
- **CHANGELOG:** existing `[Unreleased]` entries accurately document Extracted retention/replacement and History session-only expansion/scroll restoration; no duplicate entry was added.
- **Exact implementation-head CI:** - **CI Quality Check & Release:** [run #43885843452](https://github.com/D3M-Sudo/Anura/actions/runs/43885843452), workflow run 2397, completed/success on exact implementation head `bb316f94d37629cc7566b24330a87b6e86029db3`.
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
- **Branch / PR:** implementation and tests are on `fix/ui-modernization-aligned`; PR [#648](https://github.com/D3M-Sudo/Anura/pull/648) remains Open, Draft, unmerged, base `feature`. No protected branch was modified and no merge/release was performed.
- **Scope boundary:** M2-D's bounded behavior and automated checks are complete; this does not complete the full global M2 phase or M0–M7 programme. Broader Welcome/main-shell, cross-window and application-wide criteria remain tracked above.
- **Next permitted activity:** proceed to the next separately scoped M2/global roadmap task only after this evidence record is committed. Manual GNOME/GTK visual, Orca/AT-SPI and manual keyboard checks remain excluded by maintainer decision.


### M2-E — Welcome and main-shell residual-gap audit (2026-11-16; read-only)

**Outcome:** audit completed; no source, test, workflow, CHANGELOG or PR metadata changes. The audit was performed against branch `fix/ui-modernization-aligned` at the pre-recording head `97a42a0c17252cc2a36be563e87255cb2d306e63`.

**Welcome — substantially covered; no redesign justified by this audit**

- Screenshot remains the primary action; Open Image, Paste Image and Drop Image are the same secondary actions reparented between the homogeneous row and More options according to measured preferred widths.
- Existing implementation and automated tests cover the four reference viewports (360×600, 640×480, 900×600, 1280×800), constrained-height scrolling, responsive focus preservation, drop-target behavior and language-selector accessible naming/state updates.
- Existing loading/status and error feedback paths were inspected. No concrete Welcome-page defect justifying a broad rewrite was established.

**Main shell — findings**

- **M2-E-01 / High — History TTS lifecycle:** History rows can start TTS through `HistoryPage._on_tts_clicked()`. The explicit stop is currently performed by `AnuraWindow.show_welcome_page()`, but the standard `Adw.NavigationView` back path from History does not necessarily invoke that application method. Returning to Welcome from History can therefore leave playback active. This is a functional gap requiring a bounded follow-up.
- **M2-E-02 / Medium — actual navigation integration coverage:** no end-to-end test was found for the real `AnuraWindow` History-open/back route. Existing tests cover synthetic NavigationView paths or mocked window interactions, not the complete route.
- **M2-E-03 / Medium — focus restoration:** focus across the actual History → Welcome route is not covered end-to-end. Existing focused tests cover Welcome responsive reparenting and Extracted focus behavior, not this route.
- **Geometry coverage:** existing tests exercise sizing/monitor-selection helpers and persistence policy. A live multi-monitor geometry test is explicitly **not requested and will not be added**, by maintainer decision. This is not an open task or blocker.

**Verification boundaries**

- This was a source/test audit only. No new tests were run and no CI was triggered; prior CI results remain tied to their recorded commits.
- Manual GNOME/GTK visual checks, real Orca/AT-SPI checks and manual keyboard-navigation checks remain **excluded**, neither passed nor blockers.
- Context7 documentation was consulted for Libadwaita navigation behavior; it confirms the standard back action/gesture is part of `Adw.NavigationView` navigation. This supports the distinction between framework back navigation and the application's explicit `show_welcome_page()` method.
- AI Delivery Evidence Checker was used to structure the audit requirements. Its evidence checks are secondary and do not replace source inspection; its combined verdict endpoint returned `out_of_scope`, so no combined verdict is claimed.

**Disposition:** Welcome remains substantially covered. The next justified work is a bounded M2-F plan for History → Welcome TTS stop and real `AnuraWindow` navigation/focus integration tests. No live multi-monitor verification is in scope.

**Repository governance:** PR [#648](https://github.com/D3M-Sudo/Anura/pull/648) was verified Open, Draft, unmerged, base `feature`; no protected branch was modified. The PR must remain Draft/open/unmerged.

## M2-F — History TTS navigation lifecycle (2026-11-16)

- Implemented centralized navigation lifecycle handling in `AnuraWindow`: the window tracks `Adw.NavigationView:visible-page` transitions through `connect_tracked` and stops History TTS whenever the visible page leaves History, regardless of destination.
- The handler avoids a duplicate stop when the explicit `show_welcome_page()` path already stops TTS. Entering History and History-local operations do not trigger the History-exit stop.
- Added five GTK integration regressions using the real `AnuraWindow` and `Adw.NavigationView`: History → Welcome via native back navigation; explicit History → Welcome; History → Extracted; entering/remaining in History; and leaving History while TTS is already idle. All five passed.
- Source/test/CHANGELOG final code head: `acd1f03e3dee92173af98b4afe7f712806747afe`.
- CI Quality Check & Release [#43897822566](https://github.com/D3M-Sudo/Anura/actions/runs/43897822566): **success** on that exact SHA. Python Quality: **630 passed, 6 skipped, 277 deselected**. GTK Integration: **441 passed, 5 skipped, 636 deselected, 2 warnings**. Changelog integrity passed. AppImage x86_64/aarch64, Flatpak x86_64/aarch64, complete AppImage release-set validation and multi-architecture release-artifact validation all passed. `publish-release` was skipped as expected for a pull request; no release was published.
- CodeQL [#43897822286](https://github.com/D3M-Sudo/Anura/actions/runs/43897822286) passed on the same code head.
- No dependencies, OCR pipeline, Welcome redesign, manifests, workflows or live multi-monitor tests were changed. CHANGELOG was updated without duplicating prior entries.
- Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain explicitly excluded, not passed.
- Documentation follow-up commits update this roadmap, the subordinate PR #648 roadmap and `HANDOVER.md`; CI evidence above is attributed to the exact code/CHANGELOG SHA, not to those later documentation commits.
- PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`. No protected branch, PR metadata or release state was changed.

**Next:** continue with the next approved roadmap task only after presenting its bounded plan and receiving explicit approval.


## M1-02 — GTK4/Libadwaita design conventions (2026-11-16)

### Outcome and implementation

- **Outcome:** completed for the bounded M1-02 scope; global M1 remains **Partial**.
- **Approach:** approved hybrid GTK4/Libadwaita-first conventions. Native semantic typography and native widget geometry remain defaults; application-authored conventions cover typography exceptions, spacing and custom radii.
- Added `docs/ui-design-system.md` with semantic typography roles; spacing scale `4/8/12/16/24 px`; custom radius roles `6/12/9999 px`; native control hierarchy; theme compatibility; and GTK CSS limitations.
- Normalized application-authored spacing in `data/ui/*.blp` and `data/style.css`; updated `CHANGELOG.md`.
- Added four static regression tests in `tests/test_ui_palette.py` for Blueprint spacing, GTK CSS spacing, custom radii and semantic typography.
- **Responsive exception:** an initial 8 px normalization of the Welcome compact screenshot action changed its measured width and caused three narrow-viewport GTK integration regressions. Restored that one gap to 6 px, documented the exception immediately above the Blueprint property, and added a test that requires the documented exception. The remaining selector CSS padding was normalized to 8 px.
- No OCR engines/pipelines/models, architecture, dependencies, portal or OS integration were changed. No manual visual, Orca/AT-SPI or manual keyboard verification is claimed.

### Validation evidence

- M1-02 implementation range: `b4f8c0798933fb410dd4bf24cb808e183aba932a` → `6dece44cd3deb57fc43cb276db4a291a771e9584` (8 commits).
- GitHub Actions [run #43907544843](https://github.com/D3M-Sudo/Anura/actions/runs/43907544843): **completed/success** on exact head `6dece44cd3deb57fc43cb276db4a291a771e9584`.
  - Python quality: **634 passed, 6 skipped, 277 deselected**.
  - GTK Integration: **441 passed, 5 skipped, 640 deselected, 2 warnings**.
  - Changelog integrity passed.
  - AppImage x86_64/aarch64 and Flatpak x86_64/aarch64 builds passed.
  - Complete AppImage release-set and multi-architecture artifact validations passed.
  - `publish-release` skipped as expected for a PR; no release was published.
- CodeQL [run #43907544861](https://github.com/D3M-Sudo/Anura/actions/runs/43907544861): **completed/success** on the same SHA.
- The AI Delivery Evidence Checker supported all eight supplied delivery criteria. Its test-evidence sub-check was only partially supported and its combined verdict was `needs_more_evidence`, primarily because it treated documentation/CHANGELOG delivery criterion C7 as a runtime-test criterion and does not inspect source or execute CI. Actual CI and source/diff evidence are recorded above; the checker result is not represented as an independent code audit.
- Manual visual, Orca/AT-SPI and manual keyboard checks remain excluded, not passed or blockers.

**Next permitted task:** prepare a bounded M1-03 semantic-color role audit plan for review. No M1-03 implementation is authorized by this record.

## M1-03 — Semantic color-role audit (2026-11-16)

- **Outcome:** read-only audit completed; global M1 remains **Partial**. No implementation, tests, CHANGELOG, branch metadata or PR metadata were changed during the audit.
- **Inspected scope:** `data/style.css`; all 14 `data/ui/*.blp` files; relevant application Python widget modules and `anura/main.py`; `docs/ui-design-system.md`; and `tests/test_ui_palette.py`. The search did not constitute an exhaustive repository-wide static scan.
- **Palette inventory:** `#16A36A` is the green brand accent used for graphical borders/tints and interaction surfaces; `#0F7650` with `#FFFFFF` is the suggested-action background/foreground pair; `#0F7650` (light) and `#21B77A` (dark) are used for downloaded-language text and the History empty-state icon/focus treatment. Warning and surface roles use theme-managed GTK/Libadwaita colors (`@warning_color`, `@popover_bg_color`, `@theme_base_color`, `@theme_fg_color`, `@borders`). Translucent black shadows are decorative.
- **Contrast calculations:** representative WCAG ratios include 5.63:1 for white on `#0F7650`; 5.17:1 for `#0F7650` on `#F6F5F4`; 6.00:1 for `#21B77A` on `#242424`; and 4.74:1 for `#21B77A` on `#353535`. `#16A36A` reaches 3.24:1 on white, 4.79:1 on `#242424` and 3.79:1 on `#353535`: suitable for the audited graphical treatment on those samples, but not a general normal-text color on white. These are calculated representative pairs, not runtime theme measurements.
- **Theme handling:** `anura/main.py` maps `default`, `force-light` and `force-dark` to the corresponding `Adw.StyleManager` schemes and listens for preference changes. Custom downloaded text, History icon and focus rules use dark-scheme overrides; surfaces and warning colors remain theme-managed.
- **Findings:** no Critical or High issue demonstrated. Medium: downloaded-language success state uses hardcoded light/dark green variants rather than a Libadwaita semantic success class. Low: standalone green literals recur in multiple CSS rules; no exhaustive hardcoded-color scanner exists. Informational: no explicit error color role was found in the audited CSS; this is not evidence of a missing user-facing error state.
- **Test coverage:** existing static tests cover palette/contrast samples, downloaded text, focus, History empty-state icon, theme-managed secondary/disabled text, warning semantics and M1-02 layout conventions. Gaps include runtime switching across all three scheme modes and relevant surfaces, repository-wide detection of unclassified color literals, and explicit semantic success/error style-role coverage. Existing fixed-surface contrast tests do not query colors resolved by the running theme.
- **Context7:** Libadwaita documentation confirms `.accent`, `.success`, `.warning` and `.error` style classes and recommends theme-aware CSS variables for custom styling. This supports evaluating semantic classes in a future implementation proposal, not changing the approved palette automatically.
- **AI Delivery Evidence Checker:** 10 criteria extracted; delivery evidence partially supported (5 supported, 5 partial); test evidence partially supported; final verdict `needs_more_evidence` (level 3). The checker does not inspect the complete codebase or execute tests. Its result is recorded as an evidence limitation, not a software failure.
- **Execution boundary:** no tests were run during this audit. Historical CI #43907544843 passed on implementation SHA `6dece44cd3deb57fc43cb276db4a291a771e9584`; it is not a new run on audit head `f5225e2e82973db63822ca8b3b26cf13619b907a`. Manual GNOME/GTK visual, Orca/AT-SPI and manual keyboard checks remain excluded, not passed or blockers.
- **Repository state:** PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`. No protected branch or PR metadata was modified.

**M1-04 design proposal (2026-11-16):** approach B selected by the maintainer. Design document created at [`docs/superpowers/specs/2026-11-16-m1-04-semantic-colors-design.md`](../specs/2026-11-16-m1-04-semantic-colors-design.md), commit `b724f2688475bfd94e03c6e085863bfbc066c80c`. It defines conditional adoption of Libadwaita `.success`, semantic color consolidation, a classified hardcoded-color scanner and automated transitions across `default`, `force-light` and `force-dark`. This is design-only; implementation and test changes remain unauthorized pending design approval and a separately reviewed implementation plan.

**M1-04 design approval and implementation plan (2026-11-16):** maintainer approved approach B and the design document. The detailed implementation plan is [`2026-11-16-m1-04-semantic-color-consolidation-plan.md`](2026-11-16-m1-04-semantic-color-consolidation-plan.md). It decomposes the work into scanner, semantic success/color consolidation, GTK theme-transition coverage and exact-SHA CI/documentation evidence. The plan is ready for maintainer review; implementation remains unauthorized until the plan is reviewed and explicitly approved for execution.

**Next:** obtain approval of the implementation plan and explicit execution authorization. No source or test implementation has started.

## M1-04 — Semantic color consolidation and theme coverage (2026-11-16)

- **Status: Partial, not complete.** The implementation branch contains the deterministic production UI color scanner (`tests/ui_color_scanner.py`) and its eight unit tests (`tests/test_ui_color_scanner.py`). The scanner discovers the declared CSS, Blueprint and Python UI source scope, ignores supported comments/docstrings and non-UI paths, and reports unclassified literals by path, line and value.
- **Verified implementation evidence:** final tested implementation SHA `f300740f2691c0a122ea4b067b607a41cef51273`. CI Quality Check & Release [#43928078842](https://github.com/D3M-Sudo/Anura/actions/runs/43928078842) and CodeQL [#43928078536](https://github.com/D3M-Sudo/Anura/actions/runs/43928078536) both completed successfully on that exact SHA.
- **Python quality:** Ruff lint, Ruff formatting (232 files), Mypy and Python tests passed; Python result **642 passed, 6 skipped, 277 deselected**.
- **GTK integration:** **441 passed, 5 skipped, 648 deselected, 2 warnings**. This run does not demonstrate newly added runtime theme-transition tests; the GTK test count is unchanged from the preceding M1-02 evidence.
- **Packaging/release validation:** Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, multi-architecture artifact validation and complete AppImage release-set validation passed. `publish-release` was skipped as expected for a PR. CodeQL passed.
- **Scope not yet demonstrated as implemented:** semantic success-class evaluation/installed-language styling consolidation, duplicate-role consolidation and GTK integration tests exercising repeated `default`, `force-light` and `force-dark` transitions across affected surfaces. The current source still contains the `.downloaded label` CSS fallback and the audited `LanguageRow.update_ui()` does not attach a `downloaded` style class. Do not infer these plan items are complete from the green CI.
- **No CHANGELOG entry was added:** the delivered change is an internal test-support scanner and regression guard, with no user-visible behavior change or release-relevant maintenance change established.
- Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed. No OCR, dependency, architecture, portal or OS integration changes were made.
- PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`. No protected branch or PR metadata was changed.

**Historical next-step note — superseded by M0-C (2026-11-16):** prepare a bounded continuation for the remaining M1-04 semantic-style and runtime theme-transition work. M1-04 was subsequently completed within its approved scope; see the M1-04 completion record and current backlog above.

## M1-04 semantic color consolidation — implementation outcome (2026-11-16)

**Status: implementation complete for approved scope; global M1 remains Partial.**

- Color scanner implemented with TDD and eight unit tests. It covers CSS/Blueprint literals and selected Python UI string constants, ignores comments/docstrings/non-UI paths, reports file/line/value and requires path-specific rationale for approved exceptions.
- Downloaded-language semantic state now correctly applies/removes `downloaded` on installation-state changes. Existing light/dark green values remain; Libadwaita `.success` was not adopted because its widget-accent effect does not guarantee contrast on resolved application surfaces. No deprecated style-context color getter was introduced.
- GTK tests cover `default`, `force-light`, `force-dark` transitions and continuity of language, History empty-state and focus CSS classes. This is automated state/theme integration coverage, not pixel-level verification of all desktop themes.
- Exact code/test SHA `7f6a7045feefb019c869cc74aecc31a5e991a74d`: CI #43951965392 and CodeQL #43951968944 succeeded. Python 643 passed, 6 skipped, 277 deselected; GTK Integration Tests passed; Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and both release-artifact validation jobs passed. PR publication job skipped as expected.
- Manual visual, Orca/AT-SPI and manual keyboard checks remain excluded, not passed. No OCR/dependency/architecture/portal/OS changes. PR #648 remains Open/Draft/unmerged, base `feature`.


## M0-C — Global backlog and document consolidation (2026-11-16)

- **Status: Completed.** M0-C formalized the prioritized, dependency-ordered M1–M7 backlog and reconciled the global roadmap, subordinate PR #648 roadmap and `HANDOVER.md`.
- The global roadmap is authoritative for scope, phase status, global priorities and requirement disposition. The PR #648 roadmap remains a subordinate workstream evidence register. `HANDOVER.md` is the concise operational handover and historical technical record.
- Current phase snapshot: M0 Completed; M1 Partial; M2 Partial; M3 Partial; M4 Partial; M5 Not started as a complete phase; M6 Partial; M7 Partial.
- M1-02, M1-03 and M1-04 are complete only within their recorded bounded scopes. M1 remains Partial pending cross-surface Design System coverage. M1-04 includes the scanner, downloaded-language `.downloaded` class linkage and automated GTK theme-transition coverage; these are not pending implementation items.
- **Next recommended task: M1-05 — read-only audit of cross-surface Design System adoption.** It is a candidate for a separate bounded proposal and approval, not pre-authorized implementation.
- Historical task records and CI evidence are retained. CI results remain attributable only to their exact recorded SHAs; the latest previously verified documentation-head CI was run #43956668829 on `37b00668452272e993eb5fd1723402362da8c7e7`, with CodeQL #43956668787 on the same SHA. These results do not automatically validate subsequent M0-C documentation commits.
- Manual GNOME/GTK visual checks, real Orca/AT-SPI, manual keyboard checks and live multi-monitor geometry verification remain excluded. Screenshots remain deferred to the next release cycle.
- No application source, tests, workflows, CHANGELOG, PR metadata, protected branches, OCR behavior, dependencies or architecture were changed by M0-C.
- PR #648 was rechecked during this task: Open, Draft, unmerged, base `feature`, head branch `fix/ui-modernization-aligned`. No PR state transition or merge was performed.


## M1-05 — Cross-surface Design System audit (2026-11-16)

- **Status: Completed — read-only audit.** Report: [M1-05 cross-surface Design System audit](../../audit/ui-design-system-m1-05-2026-11-16.md).
- Source snapshot inspected: `fb1bcbe89f0ce982fc4adad60630a5a88496dd1`. Coverage: 14 Blueprint templates, 15 Python UI modules, main window/application, reduced-motion utility, stylesheet, Design System guide and relevant test/CI definitions.
- **Pass / acceptable:** documented spacing scale is statically checked across all 14 Blueprint templates and CSS; custom radii remain within the documented scale; the 1.15em Welcome hero typography exception is documented; the 6 px compact-action spacing exception is documented and guarded; native Libadwaita controls are used consistently across Preferences and most surfaces.
- **F1 — Medium:** reduced-motion CSS class is applied to the main `AnuraWindow`, but the separate `ShortcutsOverlay(Adw.Window)` receives app-authored `.anura-fade-in` and `.anura-card` classes without the reduced-motion class. Recommend a targeted fix and regression test.
- **F2 — Medium:** scanner unit tests exercise temporary fixtures, but no inspected test or CI command invokes the scanner against the production repository tree and fails on unclassified color literals. Recommend a production-tree CI gate with a reviewed path/value rationale map.
- **F3 — Low:** apparently unreferenced CSS selectors recorded in the report; defer cleanup pending confirmation that no dynamic consumer exists.
- **F4 — Low:** `title` and `h4` typography classes are not mapped in the design-system guide; their use is not classified as a defect without checking toolkit semantics.
- **Historical note:** at the time of the M1-05 audit, M1-06 was the next conditional candidate. The later approved F1/F2 implementation and test evidence are recorded in the M1-06 section below. F3/F4 were subsequently addressed by the M1-07 follow-up recorded below.
- No tests or workflows were run for M1-05; this is static source/test-definition inspection only. No runtime rendering, manual GNOME/GTK visual, Orca/AT-SPI or manual keyboard checks are claimed. Live multi-monitor checks remain excluded; screenshots remain deferred.
- No application source, tests, workflows, CHANGELOG, dependencies, OCR behavior, architecture, protected branches or PR metadata were modified. PR #648 remains Open/Draft/unmerged, base `feature`, head branch `fix/ui-modernization-aligned`.


## M1-06 — Reduced-motion and production UI color scanner (2026-11-16)

- **Status: Completed within approved scope.** Work is isolated to `fix/ui-modernization-aligned`; all automated CI and CodeQL checks passed on the exact source/test SHA; no protected branch or PR metadata was changed.
- **F1:** `ShortcutsOverlay` reuses `sync_reduced_motion_class()`, observes only GTK settings properties exposed by the current runtime, updates on live preference changes, and disconnects handlers on close-request and destruction. While reduced motion is active it removes the root `anura-fade-in` and `anura-card` classes because the shared `.reduced-motion *` selector does not match the root widget itself; those classes are restored in normal-motion mode. No CSS palette or desktop-wide settings were changed.
- **F2:** `tests/test_ui_color_scanner.py` now scans the actual repository root and approves only exact `(relative_path, normalized_value)` pairs with non-empty semantic rationales. The test reports path, line, literal and syntax for any unclassified finding. Existing fixture tests and the scanner implementation remain unchanged.
- **TDD evidence:** test-only GTK run #43973177077 on `2a937aca9e196973dfa6646c986fe84909fb8dad` produced four expected failures before F1 implementation; test-only run #43973548114 on `f7f03be1f5eddecf9257d6cc75e52cb0c0ddee4f` remained red before implementation; run #43974133349 on `08870472896167b7321e9aa71b557ebdd8f93b3b` reproduced missing close-path cleanup. Final implementation/test SHA: `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`.
- **Final verification on SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`:** CI #43974750869 completed with conclusion `success` on the exact source/test SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`. All 9 executable jobs passed: Python quality (644 passed, 6 skipped, 277 deselected); GTK Integration (447 passed, 5 skipped, 650 deselected, 2 warnings); Changelog integrity; AppImage x86_64 and aarch64 builds, architecture/update-metadata verification, clean-host smoke tests and artifact uploads; Flatpak x86_64 and aarch64 builds/runtime checks; multi-architecture Flatpak artifact validation; and complete AppImage release-set validation. The `publish-release` job was skipped as expected for a pull request. CodeQL #43974750821 also passed on the same source/test SHA. Ruff lint/format, mypy and Bandit passed within Python quality.
- **Exclusions:** no manual visual, Orca/AT-SPI, manual keyboard or live multi-monitor validation is claimed. Screenshots remain deferred. M1-05 findings F3 and F4 remain deferred.


## M1-07 — F3 CSS selector cleanup and F4 typography documentation (2026-11-17)

- **Outcome:** completed within the approved low-priority follow-up scope; global M1 remains Partial.
- **F3:** temporary audit [#43981815120](https://github.com/D3M-Sudo/Anura/actions/runs/43981815120) succeeded on exact audit SHA `498f8de52cff7c4ea9d12f0ea9a9b19e913d81ce`; no direct consumers were found in tracked Python/Blueprint sources. Removed the nine orphaned selector groups, their five dedicated keyframes, and obsolete reduced-motion selector references. The temporary workflow was removed after evidence collection.
- **F4:** documented `.heading` as supported Libadwaita typography and `.title`/`.h4` as arbitrary/legacy styling hooks not included in the documented Adwaita typography utility set. No Blueprint class assignment or visual styling was changed.
- **Files:** `data/style.css`, `docs/ui-design-system.md`, M1-05 audit report, CHANGELOG, HANDOVER, PR workstream roadmap and M1-06 execution ledger.
- **Validation boundary:** the audit is a literal tracked-file search; synthesized runtime class names and external integrations cannot be ruled out. Full PR CI/CodeQL for the final resulting head is recorded in the execution ledger. Manual visual, Orca/AT-SPI, keyboard and live multi-monitor checks remain excluded; screenshots remain deferred.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`; no protected branch or PR metadata was changed.


## M1 — operational closure decision (2026-11-17)

- **Status: Completed (operationally).** The maintainer selected option A: close the M1 work cycle on the basis of the completed bounded tasks, static audits, automated regression coverage and exact-head CI/CodeQL evidence.
- **Final validation head:** `443fd6085dfa14ef9941015e688760ff5874ec4f` on `fix/ui-modernization-aligned`.
- **GitHub Actions:** [CI #43982790571](https://github.com/D3M-Sudo/Anura/actions/runs/43982790571) completed with conclusion `success`; Python quality, Changelog integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and both release-artifact validators succeeded. `publish-release` was skipped as expected for a PR.
- **CodeQL:** [#43982790585](https://github.com/D3M-Sudo/Anura/actions/runs/43982790585) completed with conclusion `success` on the same head.
- **Deferred verification:** manual GNOME/GTK rendered-UI review, manual keyboard navigation, real Orca/AT-SPI verification and live multi-monitor checks were not performed. They are carried forward to M7 as explicit verification items, not M1 blockers and not passed checks. Screenshot capture remains deferred as previously agreed.
- This operational closure does not claim that every application surface has completed global Design System adoption; the remaining cross-surface modernization work continues in M2–M6, followed by M7 integration and final validation.


## M2 — operational closure (2026-11-17)

- **Decision:** the maintainer selected **A — operational closure**. M2 is **Completed (operationally)** for the current work cycle; this is a bounded phase disposition, not a claim that every global UI surface or every manual verification has been completed.
- **Completed automated work:** M2-G01 (History → Welcome focus behavior) and M2-G02 (asynchronous Welcome drag-and-drop) are implemented and validated. M2-G01 passed its exact-head CI on `7d34cf8f92435c85d9ba3537ead42c7bb98519a4`. M2-G02 passed CI [#43995410588](https://github.com/D3M-Sudo/Anura/actions/runs/43995410588) and CodeQL [#43995410567](https://github.com/D3M-Sudo/Anura/actions/runs/43995410567) on exact head `f52e437d9bdfdf6200d26449152e3ffeeacc14be`.
- **M2-G02 test evidence:** Python quality reported 652 passed, 6 skipped and 279 deselected; GTK Integration, Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture release validation passed. The release-publication job was skipped as expected for a PR. CodeQL passed.
- **Deferred to M7:** manual GNOME/GTK rendered-UI checks, manual keyboard navigation and real Orca/AT-SPI verification. These checks were not performed and are not represented as passed or as blockers to operational M2 closure. Live multi-monitor verification remains excluded by the existing decision.
- **Deferred to M5:** app-wide menu consistency review and disposition of intentional menu differences. These are outside the operational M2 closure and must be handled in M5.
- **PR governance:** PR #648 remains Open, Draft and unmerged, targeting `feature`, with head branch `fix/ui-modernization-aligned`. No protected branch, PR metadata or merge state was changed.
- **Next global task:** M3-01, the read-only Extracted and History audit, subject to its separately agreed scope. This M2 closure does not authorize implementation work in M3.


## M3-01 — Extracted and History audit; F-301/F-302 test remediation (2026-11-17)

- **Audit outcome:** the read-only Extracted/History baseline audit is complete. Extracted coverage includes search navigation/wrap, text reflow, undo/redo, OCR-result focus and debounced accessible search-result announcements. History coverage includes list/empty states, row expansion, clear confirmation, TTS behavior, navigation and in-session scroll/expanded-row restoration.
- **F-301 — resolved test-contract inconsistency:** the previous test expected every History row to collapse after `refresh()`, conflicting with the implemented and separately tested preservation contract. The maintainer selected A1: preserve the expanded entry when it still exists, preserve scroll, clear stale expansion if the entry disappears, and maintain behavior across navigation. The contradictory test was renamed and updated to assert restoration of the same expanded entry and single-row expansion. Test-only commit: `e7ee3032bc375ea953c18a809b2ccd42a9397aad`; formatting-only follow-up: `0988708e88a162417a9622500c813ae3c1a98dac`.
- **F-302 — resolved targeted coverage gaps:** audit confirmed an existing debounced plural-result announcement test; the gap was incomplete edge-case coverage, not absence of implementation or all tests. Added tests for the visible/accessibility “Searching…” state, singular result announcement after the 400 ms debounce at LOW priority, zero-result “No matches”, and clearing search/restoring the accessible label while cancelling a pending announcement. Test file: `tests/test_accessible_status_announcements.py`. Final test-fix commit: `56d794502d84c0dfc392230867b4c90b6d08ee91`.
- **Exact-head validation:** CI [#2497](https://github.com/D3M-Sudo/Anura/actions/runs/44006990401) and CodeQL [#699](https://github.com/D3M-Sudo/Anura/actions/runs/44006990338) both completed successfully on `56d794502d84c0dfc392230867b4c90b6d08ee91`. Python quality, Changelog integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture release-artifact validation all passed. The release-publication job was skipped as expected for a PR.
- **Evidence limits:** no local test execution or TDD red→green demonstration is claimed; GitHub Actions is the verification source. CI does not establish real Orca/AT-SPI or manual keyboard behavior. Those manual checks remain excluded/deferred according to the existing decision. F-303 History accessible-action-label/keyboard-traversal coverage remains a separate gap for audit; do not infer that it is fixed.
- **Files changed for remediation:** `tests/test_history_expansion_real.py` and `tests/test_accessible_status_announcements.py`; no production code, workflow, CHANGELOG, protected branch or PR metadata was changed in these remediation commits.
- **M3 status:** remains **Partial**. The audit and these two test remediations do not establish full Extracted/History modernization or close M3.
- **Governance:** PR #648 remains Open, Draft and unmerged, targeting `feature`; head is `56d794502d84c0dfc392230867b4c90b6d08ee91`. No merge or protected-branch modification occurred.
- **Next permitted task:** prepare the bounded F-303-02 automated keyboard-traversal test plan. F-303-01 is complete; F-303-03 direct accessible-label assertions follow F-303-02. Each implementation remains subject to separate explicit approval.


## F-303-01 — History TTS action-label semantics (2026-11-17)

- **Outcome:** implemented the approved state-specific TTS action labels and automated transition assertions on `fix/ui-modernization-aligned`. The production change is limited to the History TTS button's label/tooltip semantics; TTS execution logic is unchanged.
- **Approved state contract:** `generating` → “Stop listening”; `playing` → “Pause listening”; `paused` → “Resume listening”; `idle` or inactive → “Listen to text”.
- **Files changed:** `anura/widgets/history_page.py`, `tests/test_history_ui.py` and `CHANGELOG.md`. The test asserts both tooltip text and `Gtk.AccessibleProperty.LABEL` for all four states. The CHANGELOG records the user-visible accessibility improvement.
- **Implementation/test/CHANGELOG head:** `2d503db3b98383ab0b293f7e7752b583826a40c9`.
- **Exact-head CI:** [CI Quality Check & Release #44027455501](https://github.com/D3M-Sudo/Anura/actions/runs/44027455501) completed with conclusion `success` on that exact SHA. Python quality (Ruff lint/format, Mypy, Bandit, Vulture, coverage tests and Flatpak runtime dependency coverage), Changelog integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture release-artifact validation all passed. `publish-release` was skipped as expected for a PR.
- **CodeQL:** [#44027455444](https://github.com/D3M-Sudo/Anura/actions/runs/44027455444) completed successfully on the same SHA.
- **Evidence limits:** no local test execution or TDD red→green demonstration is claimed. Automated tests verify label/tooltip state transitions; they do not establish real Orca/AT-SPI behavior or manual keyboard traversal. Those checks remain excluded/deferred under the existing decision.
- **Governance:** PR #648 remains Open, Draft and unmerged, base `feature`. No protected branch, workflow or PR metadata was changed. The implementation/test SHA above is the exact SHA validated by CI; subsequent documentation-only commits are not covered by those runs.
- **M3 status:** remains **Partial**. F-303-01 is complete; F-303-02 automated keyboard traversal tests are next, followed by F-303-03 direct accessible-label assertions. Broader Extracted/History modernization remains open.


## F-303-02 — CI keyboard-input limitation and suspension (2026-11-17)

- **Disposition:** suspended as an automated real-keyboard traversal test task; no further changes to the test harness are authorized or planned in this work cycle.
- **Evidence commit:** `84ff4d50a3291b4328d28e657b251144d979e9c6`.
- **CI:** [Quality & Release #44040005554](https://github.com/D3M-Sudo/Anura/actions/runs/44040005554) failed in GTK Integration Tests; [CodeQL #44040005537](https://github.com/D3M-Sudo/Anura/actions/runs/44040005537) succeeded on the same source/test commit.
- **Observed result:** GTK Integration reported 4 failed, 449 passed, 5 skipped and 663 deselected. Three tests received no key event at GTK's toplevel `EventControllerKey` after the test helper invoked `xdotool` against the Weston X11 host window. One test did observe Tab at GTK but focus remained on the collapsed `Gtk.TextView`.
- **Diagnostic boundary:** Xvfb :99, Weston X11 backend, Wayland socket and a keyboard-capable `wl_seat` were available. The current XTest → Weston → Wayland → GTK route nevertheless did not reliably deliver key events to the GTK client. The logs do not prove that every possible CI input mechanism is impossible; they establish that the currently configured route is not a reliable verification mechanism.
- **Conclusion:** do not classify these failures as a confirmed Anura application defect. The one focus-retention case remains unproven because the full keyboard traversal environment is not reliable. Do not claim keyboard traversal passed.
- **Next:** suspend F-303-02 and defer F-303-03 until its dependency/order is reconsidered. Continue with the next global audit M4-01. No production code, workflow or dependency changes were made after this diagnostic commit.

## M4-01 — Preferences and language selector audit (2026-11-17)

- **Status:** Completed — read-only audit. Report: [M4-01 Preferences and language selector audit](../../audit/preferences-languages-m4-01-2026-11-17.md).
- **Scope:** General, Editor, Voice and Languages Preferences pages; main language selector/popover; language rows; GSettings schema; LanguageManager signal contract; related test coverage.
- **Findings:** M4-F01 P2 (network probe checks `google.com`, while OCR model downloads use GitHub); M4-F02 P2 (OCR reachability callback has no cancellation/disposal guard); M4-F03 P3 (LanguageRow retains completed idle source IDs); M4-F04 P2 coverage/accessibility gap (Preferences language ListView has no explicit accessible name).
- **Evidence:** source/template/schema/test-definition inspection only; no runtime tests or manual AT-SPI/keyboard verification were run for this audit.
- **Disposition:** global M4 remains Partial. Findings and test gaps require separate maintainer disposition; this audit does not authorize implementation.


## 2026-11-17 — F-303-02 experimental GTK keyboard lane / CI unblocking

- **Decision:** retain the four F-303-02 keyboard traversal tests, but mark them `keyboard_traversal` and separate them from the required GTK Integration suite. This records a CI harness limitation, not a confirmed production accessibility defect.
- **Required GTK suite:** runs with `-m "gtk and not keyboard_traversal"`; the four experimental cases are excluded from this blocking job only.
- **Experimental lane:** `GTK Keyboard Traversal (experimental)` runs the four marked tests on its own GTK/Wayland/XTest environment. The job depends only on `python-quality`, has job-level `continue-on-error: true`, and remains visible in Actions without gating release builds.
- **Build graph correction:** `flatpak-builder` now depends on `python-quality` only, not the required GTK suite. `validate-release-artifacts` continues to depend on Flatpak builds. AppImage builds and AppImage artifact validation retain their existing independent dependency chain.
- **Debt tracking:** GitHub issue [#655 — Replace the F-303-02 GTK keyboard traversal CI input harness](https://github.com/D3M-Sudo/Anura/issues/655) records the evidence, constraints and acceptance criteria. The four tests must return to the required GTK suite only after the harness reliably observes real Tab/Shift+Tab at the GTK client boundary and passes repeated CI runs.
- **Last pre-change evidence:** CI [#44110517818](https://github.com/D3M-Sudo/Anura/actions/runs/44110517818) on `24c9f99f683de1ee26eb33e53678998326fc5ce9`: Python Quality, Changelog integrity, AppImage x86_64/aarch64 and complete AppImage release-set validation passed; GTK failed on the four F-303-02 tests; Flatpak builds and multi-architecture release-artifact validation were skipped. CodeQL [#44110517974](https://github.com/D3M-Sudo/Anura/actions/runs/44110517974) passed.
- **Validation status:** workflow/test-marker changes are committed; the new graph and exact-SHA CI results remain pending. No local tests or YAML validation are claimed. No production code, dependency, OCR behavior, CHANGELOG, protected branch, PR metadata, merge or release was changed.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`.


## F-303-02 — CI testing phase closed; native-host validation deferred (2026-11-17)

- **Disposition:** stop CI input-harness experimentation and remove the four CI-specific keyboard tests/helpers. This is a process disposition, not a claim that keyboard traversal passed or that the application has an accessibility defect.
- **Weston/XTest evidence:** earlier CI attempts failed to deliver injected Tab/Shift+Tab reliably to GTK; one case observed Tab but retained focus on a collapsed TextView.
- **Sway/wtype evidence:** CI run [#44120435948](https://github.com/D3M-Sudo/Anura/actions/runs/44120435948), head `bff387fcf5a07c6b580f47d60f98f9ff6966e319`. Sway started, a Wayland socket and `wl_seat`/`zwp_virtual_keyboard_manager_v1` were available, and Sway reported the GTK test window focused. GTK did not observe the injected Tab events; diagnostics reported `active=False`. The job aborted on its first failing attempt, so the configured three repetitions were not evaluated. This does not prove virtual input is impossible in GitHub Actions; it establishes that the current harness did not provide reliable GTK-boundary evidence.
- **CI cleanup:** remove the experimental Sway job and Sway/wtype/wayland-utils dependencies; remove XTest-only xdotool installation, Weston host-window discovery and `WESTON_HOST_DISPLAY`; retain Xvfb + Weston X11 and the `wl_seat` preflight for ordinary GTK integration; restore the normal `-m "gtk"` selection; restore `flatpak-builder` dependency on both `python-quality` and `gtk-tests`.
- **Test disposition:** remove the four experimental keyboard-traversal tests and their Sway injection/probe helpers. Preserve unrelated History expansion, persistence and UI tests. No application source or runtime dependency changes.
- **Residual debt:** issue [#655 — F-303-02 native-host keyboard traversal validation](https://github.com/D3M-Sudo/Anura/issues/655) remains open. M7-03 requires real Tab/Shift+Tab validation on a native desktop, including forward/reverse suffix-action traversal, expanded/collapsed rows and focus recovery. Until then F-303-02 is deferred, not passed.
- **Gate:** M5-01 may proceed after this disposition is committed and the issue/docs are reconciled; the outstanding physical keyboard check remains scheduled for M7 and must not be represented as complete.


## M5-01 — Other windows and shared UI components audit (2026-11-17)

- **Outcome:** read-only audit completed on `fix/ui-modernization-aligned`, source snapshot `0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a`. Full report and P2 test proposal: [M5-01 audit](../../audit/ui-other-surfaces-m5-01-2026-11-17.md).
- **Scope:** Shortcuts, About, fatal-error and Clear History dialogs, language/share popovers, Welcome/Extracted menus, banner, toast overlay and desktop notifications.
- **Disposition:** no confirmed product defect and no reason for gratuitous redesign. Native Libadwaita surfaces are retained. Clear History, language popover, share-row and notification behavior already have meaningful focused coverage in the inspected tests.
- **P2 plan:** (M5-P2-01) Shortcuts search/match/empty/reset/Escape; (M5-P2-02) Welcome/Extracted/screenshot menu action resolution and scope; (M5-P2-03) banner dismissal and deterministic toast lifecycle. This is a proposal only; no tests or application code were implemented.
- **P3 deferred:** direct About/fatal-dialog configuration tests, Portal timeout/shutdown cleanup edge cases, and additional popover focus tests only if duplicate coverage is ruled out.
- **Evidence boundary:** source, Blueprint and test-definition inspection only. No test/build/CI command was run as part of the audit. CodeQL #44128147802 passed on the audited PR head; CI #44128148026 was still in progress at the last check. No runtime, visual, Orca/AT-SPI or physical keyboard result is claimed.
- **Global status:** M5 is Partial, not complete. M5-02 is the next proposed task and requires separate explicit implementation approval.
- **CHANGELOG:** unchanged because no product behavior changed.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`; protected branches and PR metadata remain untouched.


## M5-02 — Approved automated UI contract tests (2026-11-17)

- **Status:** Completed within the explicitly approved test-only scope. This closes M5-02's selected automated-test subset; global M5 remains **Partial**.
- **Shortcuts:** added GTK coverage for search matching, empty results, clearing/resetting the search and the two-level Escape behavior (clear a non-empty search first; close the overlay when the search is empty).
- **Menus:** added a headless/static contract test that checks Blueprint `app.*` and `win.*` action references against the registered application/window action declarations. This verifies action resolution/scope contracts without claiming that physical menu interaction was exercised.
- **Toasts:** GTK tests verify `AnuraWindow.show_toast()` delegation to the existing `Adw.ToastOverlay`, including title and priority. **Toast lifecycle/dismissal is deliberately excluded.** The attempted lifecycle assertion called `Adw.Toast.dismiss()` on a toast that had not been added to an `Adw.ToastOverlay`; Libadwaita specifies that dismiss is a no-op before overlay registration. The test was removed rather than introducing timing-sensitive behavior or misrepresenting the API contract. No lifecycle guarantee is claimed by M5-02.
- **Banner:** dismissal testing remains excluded and requires a separately scoped diagnosis; no banner behavior was changed or certified by this task.
- **Test files:** `tests/test_m5_02_menu_actions.py` (1 static test) and `tests/test_m5_02_ui_contracts.py` (5 GTK tests). The dedicated temporary CI run [#44134120773](https://github.com/D3M-Sudo/Anura/actions/runs/44134120773) passed; its job ran the selected GTK and action-contract tests. The temporary workflow was removed after evidence collection.
- **Exact-head validation:** PR head `ae048880f46162f1f11892a06b27fa420c39430c`. CI [#44135571249](https://github.com/D3M-Sudo/Anura/actions/runs/44135571249) completed successfully: Python quality, Changelog integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, complete AppImage release-set validation and multi-architecture artifact validation all passed. `publish-release` was skipped as expected for a PR. CodeQL [#44135571322](https://github.com/D3M-Sudo/Anura/actions/runs/44135571322) also passed on the same head.
- **Changes and limits:** test-only changes; no application source/runtime behavior or dependency changes. `CHANGELOG.md` remains unchanged because no user-visible behavior changed. No local test execution, rendered-UI inspection, native keyboard traversal, Orca/AT-SPI or live notification-daemon verification is claimed. F-303-02 physical keyboard traversal remains deferred to M7-03/#655.
- **Governance:** PR #648 remains Open/Draft/unmerged, targeting `feature`; no protected branch, PR metadata or merge state was changed.


## M5-03 — Portal-missing banner dismissal (2026-11-17)

- **Finding:** the Adw.Banner exposed a “Dismiss” button, but the window did not connect button-clicked to a handler. Showing the banner on portal-missing state worked; dismissing it had no application-side effect.
- **Approved correction:** AnuraWindow._setup_controller_signals() now connects the banner signal to _on_portal_banner_dismissed(); the handler sets revealed=False. The existing portal-missing path still reveals the banner. No portal behavior, permissions, screenshot fallback or other application flow was changed.
- **Regression tests:** tests/test_m5_02_ui_contracts.py adds two GTK tests: one verifies the signal is connected to the window handler, and one verifies the handler hides the banner.
- **Red/green evidence:** temporary M5-03 workflow run [#44141439001](https://github.com/D3M-Sudo/Anura/actions/runs/44141439001) collected both regression tests and passed them (**2 passed, 1 warning**) on the tested pre-formatting head. The earlier red phase showed both tests failing before the production fix. The temporary workflow was removed after evidence collection.
- **Formatting follow-up:** commit 74f6a4ef98392f80c0ca1e95ed987d2c1d48749c changes test-file spacing only; no behavior or assertions changed.
- **Final exact-head validation:** CI [#44142298765](https://github.com/D3M-Sudo/Anura/actions/runs/44142298765) and CodeQL [#44142298673](https://github.com/D3M-Sudo/Anura/actions/runs/44142298673) both completed successfully on exact head 74f6a4ef98392f80c0ca1e95ed987d2c1d48749c. Python quality, Changelog Integrity, GTK Integration, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set validation and multi-architecture artifact validation passed. publish-release was skipped as expected for a PR.
- **Evidence limits:** no local test execution, rendered GNOME/GTK visual inspection, physical keyboard traversal, real Orca/AT-SPI or live desktop-notification/portal verification is claimed. F-303-02 physical keyboard traversal remains deferred to M7-03/#655. M5-02 toast lifecycle remains excluded; P3 About/fatal-dialog, Portal cleanup/error-path and popover-focus gaps remain deferred.
- **CHANGELOG:** updated under [Unreleased] / Fixed to record the user-visible dismissal correction.
- **Programme status:** M5 remains **Partial**. M5-01 audit, M5-02 selected automated contracts and M5-03 banner correction are complete within their bounded scopes; they do not close the complete M5 phase.
- **Governance:** PR #648 remains Open/Draft/unmerged, base feature, head fix/ui-modernization-aligned. No protected branch was modified; no merge or release was performed.


## M5 — agreed-scope closure (2026-11-17)

- **Maintainer decision:** close M5 within the scope agreed for this phase. P3 test candidates were not part of the exit criteria; native/manual verification had already been moved to M7 alongside the other phases.
- **Completed work:** M5-01 read-only audit of Shortcuts, About/fatal/Clear History dialogs, language/share popovers, Welcome/Extracted menus, banner, toast overlay and desktop notifications; M5-02 selected GTK/headless contracts for Shortcuts search/Escape, Blueprint action resolution/scope and toast delegation/title/priority; M5-03 portal-banner Dismiss wiring/handler correction with two GTK regressions.
- **P3 disposition:** About/fatal-dialog construction/presentation tests, Portal timeout/shutdown cleanup and failure-path tests, and any additional popover-focus tests remain deferred. They are not M5 blockers.
- **Explicit exclusions:** toast dismissal/lifecycle was not included in the approved M5-02 implementation; no dismissal lifecycle guarantee is claimed. Native GNOME/GTK visual checks, real Orca/AT-SPI and physical keyboard traversal are deferred to M7; issue [#655](https://github.com/D3M-Sudo/Anura/issues/655) tracks the M7-03 History keyboard validation.
- **Validation:** the two banner GTK regressions passed in temporary run [#44141439001](https://github.com/D3M-Sudo/Anura/actions/runs/44141439001). Final code/test head `74f6a4ef98392f80c0ca1e95ed987d2c1d48749c` passed CI [#44142298765](https://github.com/D3M-Sudo/Anura/actions/runs/44142298765) and CodeQL [#44142298673](https://github.com/D3M-Sudo/Anura/actions/runs/44142298673). Later documentation commits are not covered by that exact-head run; the current documentation-head CI/CodeQL status is recorded in the PR and subordinate roadmap.
- **CHANGELOG:** already contains the `[Unreleased] / Fixed` entry for the user-visible banner Dismiss correction; no additional changelog change is needed for a phase-status decision.
- **Historical global status at the time of the M5 closure record:** M5 **Completed within agreed scope**. M3 was subsequently closed operationally within agreed scope; M4, M6 and M7 remain Partial.


## 2026-11-17 — M3 operational closure and M4 coverage-gap disposition

### M3 — Completed operationally within the agreed scope

- The M3 commit audit confirmed the approved automated remediation sequence is present: Extracted state/selection contracts, OCR asynchronous lifecycle/announcement contracts, History action-label semantics, and GNOME 51 icon compatibility.
- F-303-03 is no longer an open gap: `tests/test_history_ui.py` now asserts the initial accessible labels for the History row actions (Copy, Editor and TTS).
- F-303-02 is **not passed**. CI input-harness experiments were stopped; native Tab/Shift+Tab traversal remains tracked by [#655](https://github.com/D3M-Sudo/Anura/issues/655) for M7-03.
- Real GNOME/GTK visual inspection and Orca/AT-SPI remain unperformed and assigned to M7. These limitations do not reopen the bounded M3 automated remediation scope.
- The audit observed a temporary commit-history anomaly in the M3 sequence (large transient deletion followed by restoration); the net source delta is limited to the five M3-related files already reviewed. Record this for pre-merge review; it is not a current-tree integrity finding.

### M4 — remains Partial; M4-02 execution status (updated 2026-11-18)

M4-01 and remediations M4-F01–F04 are complete. The following coverage gaps remain from the M4-01 audit:

| Area | CI-testable gap candidate | Native/manual residual |
|---|---|---|
| General | Color-scheme mapping; secondary-language selection, refresh and removal/reset mapping | None identified beyond general UI verification |
| Editor | `word` / `char` / `none` wrap-mode mapping and persistence | None identified beyond general UI verification |
| Voice | Worker result arriving after page disposal, with no stale widget mutation | None identified beyond general UI verification |
| Languages | Page-level search/empty state, install/remove/progress transitions, cancellation and disposal lifecycle | Full keyboard traversal and real screen-reader behavior |
| Main language selector | Existing direct handler test is not a real key-input traversal test | Native keyboard traversal and Orca/AT-SPI in M7 |

M4-02 must first inspect existing tests and public GTK/Gio seams, then add only deterministic tests that can run in the existing GitHub Actions environment. A missing test is not evidence of a production defect: production changes require a reproduced failing behavior and a separate, narrowly justified fix. Any CI-unreliable keyboard traversal remains explicitly deferred to M7. M4 must not be marked complete until the approved CI-testable gaps have been addressed or explicitly dispositioned with evidence.

Historical note (2026-11-17): M4-02 implementation had not yet been authorized at that point in the record. Subsequent approved Task 1–4 execution is documented below. M6-01 remains sequenced after M4-02.


## M4-02 Task 1 — General Preferences automated coverage (2026-11-17)

- **Status:** Completed within the approved M4-02 scope; global M4 remains Partial.
- **Coverage:** General Preferences color-scheme initialization and persistence mappings, extra-language selection/persistence, and active-language removal/reset plus model refresh are now covered by headless regression tests in `tests/test_preferences_page_resilience.py`.
- **Production changes:** none. A test assertion was corrected after the first pytest run; the final full CI passed.
- **Exact implementation head:** `c5f820aac1a722c42bb79f5ebcbbf6fea17a0c7a`.
- **Evidence:** CI [#44188821619](https://github.com/D3M-Sudo/Anura/actions/runs/44188821619) passed, including Python Quality (**682 passed, 6 skipped, 287 deselected**), GTK Integration, Changelog Integrity, AppImage and Flatpak builds for x86_64/aarch64, and release-artifact validation. CodeQL [#44188821605](https://github.com/D3M-Sudo/Anura/actions/runs/44188821605) passed.
- **Limitations:** no native/manual GNOME, physical keyboard, Orca or AT-SPI verification is claimed; those remain in M7. No CHANGELOG entry was warranted because this task adds tests only and changes no product behavior.
- **Next:** M4-02 Task 2 — Editor wrap-mode mapping and persistence.


## 2026-11-18 — M4-02 Task 2: Editor Preferences coverage

- **Status:** Task 2 Completed within the approved scope; global M4 remains **Partial**.
- **Coverage:** headless tests now cover Editor wrap-mode initialization and persistence for `word`, `char` and `none`, including unknown-value and invalid-index fallbacks. A dedicated GTK integration module verifies the real Editor Preferences page against an isolated Gio memory GSettings backend; all three parametrized integration cases passed.
- **Production changes:** none. Only `tests/test_preferences_page_resilience.py` and `tests/test_preferences_editor_integration.py` changed for this task. No new dependency or workflow was added.
- **Exact implementation head:** `cae8b8c27114daf59fab96ebefdd377b3efb76ae`.
- **Evidence:** [CI #44195812990](https://github.com/D3M-Sudo/Anura/actions/runs/44195812990) passed: Python Quality **690 passed, 6 skipped, 290 deselected**; GTK Integration **460 passed, 6 skipped, 696 deselected**, including all three Editor/GSettings cases; Changelog Integrity, AppImage and Flatpak builds for x86_64/aarch64, AppImage release-set and multi-architecture artifact validation passed. [CodeQL #44195813017](https://github.com/D3M-Sudo/Anura/actions/runs/44195813017) passed.
- **Limitations:** skipped/deselected tests are not claimed as executed. No local tests, native visual inspection, physical keyboard traversal or real Orca/AT-SPI checks are claimed; native checks remain assigned to M7.
- **Remaining M4-02 tasks:** Voice late-result-after-disposal (Task 3) and Languages search/filter/lifecycle (Task 4). M4 must remain Partial until these approved CI-testable gaps are addressed or explicitly dispositioned.
- **Next:** Task 3 — Voice late-result-after-disposal coverage; requires maintainer authorization.


## 2026-11-18 — M4-02 Task 3: Voice late-result-after-disposal coverage

- **Status:** Task 3 Completed within its approved scope; global M4 remains **Partial**.
- **Coverage:** headless regression tests cover both a TTS catalog callback delivered after Voice page disposal and the complementary live-page update path. The disposed callback must return `GLib.SOURCE_REMOVE`, avoid replacing the combo model or changing selection, and clear the loading state.
- **Production changes:** none. The existing `_disposed` guard is sufficient; only `tests/test_preferences_page_resilience.py` changed. No dependencies or workflows were added.
- **Test-development qualification:** the initial RED runs exposed fixture/mock-base problems, not a production defect. No mutation run removing the guard was performed; therefore no observed RED from guard removal is claimed.
- **Exact implementation head:** `8a70fa257375f5da060b30568a6eeacd50b2f820`.
- **Evidence:** [CI #44199827587](https://github.com/D3M-Sudo/Anura/actions/runs/44199827587) passed: Python Quality **692 passed, 6 skipped, 290 deselected**; GTK Integration; Changelog Integrity; AppImage/Flatpak builds for x86_64/aarch64; AppImage release-set and multi-architecture artifact validation. [CodeQL #44199827449](https://github.com/D3M-Sudo/Anura/actions/runs/44199827449) passed; publish-release skipped as expected for a PR.
- **Limitations:** no local tests, native visual inspection, physical keyboard traversal or real Orca/AT-SPI checks are claimed; native checks remain M7 work.
- **CHANGELOG:** no change warranted because this task adds tests only.
- **Remaining M4-02 work:** Task 4 — Languages search/filter/install/remove/progress/cancellation/disposal coverage. M4 remains Partial.
- **Next:** Task 4; not started and requires explicit maintainer authorization.


## 2026-11-18 — M4-02 Task 4: Languages search/filter and list lifecycle

- **Status:** Task 4 completed within its bounded scope; global M4 remains **Partial** pending Task 5 disposition and native M7 validation.
- **Headless coverage:** ten tests in `tests/test_preferences_languages_lifecycle.py` passed, covering configured tessdata-host reachability; cancellation and late-callback suppression after page disposal; LanguageRow idle-source cleanup; accessible list naming; case-insensitive title search; downloaded-only default filtering; empty/non-empty stack state; stop-search reset; idempotent add events; and filter refresh after removal.
- **GTK integration:** `tests/test_preferences_languages_integration.py::test_languages_page_search_empty_reset_and_model_lifecycle` passed against the real Languages Preferences page, controlled GObject manager signals, real LanguageItem objects, GResource and isolated Gio memory GSettings. It verified filtering, search (including a non-downloaded language), empty state, reset, idempotent addition and removal refresh.
- **Production changes:** none for Task 4; no dependencies or permanent workflows added. No CHANGELOG update warranted. No production RED/GREEN correction or mutation-test result is claimed.
- **Exact implementation head:** `8e2a2f5d7ca3b8ec3b6f8ae478ecc0c94bc7c3bd`.
- **Exact-head CI:** [CI #44205336611](https://github.com/D3M-Sudo/Anura/actions/runs/44205336611) success. Python Quality **698 passed, 6 skipped, 291 deselected**; GTK Integration **461 passed, 6 skipped, 704 deselected**, including the new Languages integration test; Changelog Integrity; AppImage x86_64/aarch64; Flatpak x86_64/aarch64; AppImage release-set and multi-architecture artifact validation all passed. [CodeQL #44205336610](https://github.com/D3M-Sudo/Anura/actions/runs/44205336610) passed. The initial GTK cancellation was resolved by rerunning the job on the same SHA; the final run is green.
- **Review qualification:** in-session inspection of the test diff completed; independent code-review subagent unavailable, so no independent review is claimed.
- **Limitations:** this Task 4 GTK test covers search/filter/empty/reset and add/remove signals, not a complete real download-progress UI transition. Task 5 must explicitly map/disposition any remaining CI-testable progress criteria. Physical keyboard traversal and real Orca/AT-SPI remain M7 native checks; no local test execution or native accessibility verification is claimed.
- **Governance:** PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned` at the exact SHA above.
- **Next:** M4-02 Task 5 — full verification/acceptance-criteria disposition and closure review; requires separate maintainer authorization.


## 2026-11-18 — M4-02 Task 5: acceptance-criteria disposition

M4-02's CI-testable acceptance criteria are covered or explicitly dispositioned. This closes the bounded M4-02 test-coverage workstream only; global M4 remains **Partial** and native checks remain M7 work.

| Design acceptance area | Evidence / disposition |
|---|---|
| General color-scheme mapping, persistence, extra-language selection and removal/reset | `tests/test_preferences_page_resilience.py`; exact-head Python Quality passed. |
| Editor wrap-mode mapping and persistence | Headless resilience tests plus real GSettings integration in `tests/test_preferences_editor_integration.py`; exact-head Python Quality and GTK Integration passed. |
| Voice late result after disposal; preserve live success, catalog failure and volume behavior | Late/disposed and live callback tests in `tests/test_preferences_page_resilience.py`; existing failure/loading and volume tests plus `tests/test_preferences_voice_integration.py` remain in the suite. |
| Languages search/filter/empty/reset/add/remove | Headless lifecycle tests plus `test_languages_page_search_empty_reset_and_model_lifecycle` in GTK Integration. |
| Preserve model-quality cache invalidation | Existing `tests/test_preferences_language_quality.py::test_quality_change_invalidates_cache_before_reload`; included in Python Quality. |
| Download-progress UI transition | Explicitly not an M4-02 design acceptance criterion. Not tested or claimed; any further coverage needs separate scope approval. |
| Physical keyboard traversal, real Orca/AT-SPI, native visual verification | Deferred to M7; GTK CI cannot establish these properties. |

**Exact-head evidence:** `8e2a2f5d7ca3b8ec3b6f8ae478ecc0c94bc7c3bd`; CI [#44205336611](https://github.com/D3M-Sudo/Anura/actions/runs/44205336611) and CodeQL [#44205336610](https://github.com/D3M-Sudo/Anura/actions/runs/44205336610) passed. Python Quality **698 passed, 6 skipped, 291 deselected**; GTK Integration **461 passed, 6 skipped, 704 deselected**, including the Languages integration test; Changelog Integrity, AppImage/Flatpak x86_64/aarch64 and artifact validation passed. The GTK job's initial cancellation was resolved by rerunning it on the same SHA.

No production correction was made in Task 4; no dependency, permanent workflow or CHANGELOG change was added. The independent code-review subagent was unavailable; in-session diff inspection only. PR #648 remains Open/Draft/unmerged with base `feature` and head `fix/ui-modernization-aligned`. Global M4 remains **Partial** pending its remaining programme/native validation.
