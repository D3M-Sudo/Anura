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
9. Manual GNOME/GTK visual checks, real Orca/AT-SPI checks and manual keyboard-navigation checks are currently excluded by the maintainer. Record them as **excluded**, never passed or pending blockers. Automated GTK focus/accessibility tests remain in scope and are permitted.
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
| M0 | Full application audit | Complete inventory of windows/components/states/functions; current behavior, visual/functional/accessibility/architecture/performance/Linux-compatibility findings; prioritized requirements and traceability baseline | **Partial — M0-A inventory and M0-B traceability/evidence reconciliation completed; M0-C prioritization and remaining audit synthesis are next** |
| M1 | Design System and themes | Approved shared palette/tokens and reusable patterns; typography/spacing/component rules; automatic/light/dark and force-light/force-dark behavior verified | **Partial — green palette/runtime CSS implemented in PR #648; app-wide system audit and theme coverage remain** |
| M2 | Welcome and main navigation | Welcome and main-shell/navigation experience meet responsive, visual, interaction and focus criteria | **Partial — Welcome and selected shell behavior implemented in PR #648; full navigation audit and acceptance remain** |
| M3 | Extracted and History | Extracted/OCR and History surfaces consistently modernized without functional regressions | **Partial — Extracted header/action area and scroll protections exist; History modernization is not established as complete** |
| M4 | Preferences and languages | General, Languages, Editor, Voice and language selector meet shared visual, responsive, lifecycle and accessibility criteria | **Partial — Preferences split and selected lifecycle work exist; full page and language-selector audit remains** |
| M5 | Other windows and components | Shortcuts, About, dialogs, popovers, menus, notifications, banners and toasts audited and addressed where justified | **Not started as a complete phase — Shortcuts received limited resizing work; app-wide coverage is unverified** |
| M6 | Responsive behavior and accessibility | Cross-window responsive, focus, contrast, accessible naming/announcements and reduced-motion requirements tested consistently | **Partial — selected automated accessibility and responsive work exists in PR #648; cross-window coverage remains** |
| M7 | Integration and consolidation | Integrated regression suite, documentation/CHANGELOG, translations review, screenshots at agreed timing, and distribution/build validation complete | **Partial — PR #648 has strong branch-level CI evidence; full app-wide phase exit criteria remain** |

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
| Green palette and runtime stylesheet | Green semantic palette, GResource CSS provider registration, palette/contrast tests | M1 must audit shared tokens, all surfaces and all theme modes |
| Welcome primary/secondary actions | Screenshot primary; Open/Paste/Drop responsive grouping | Complete remaining M2 audit of navigation and all states |
| Welcome responsiveness and scrolling | Adaptive actions, scroll container, focus restoration; constrained-viewport test passed in recorded CI | Extend M6 coverage only where M0 identifies gaps in other windows |
| Main window geometry | Monitor-aware clamp, monitor-change handling, normal-size persistence | M2/M6 audit other windows and geometry constraints; no universal dock-aware guarantee |
| Extracted | Compact header/action bar and existing scroller regression protection | M3 audit full Extracted/OCR states and action behavior |
| History | Selected theme/contrast and scroller protections are recorded | M3 full History visual/interaction audit remains; no claim of full restyle |
| Preferences | General/Editor/Voice/Languages split and selected async lifecycle protections | M4 audit each page, language selector and all states |
| Keyboard Shortcuts | Resizability and existing scroll behavior | M5 full visual, interaction and accessibility audit |
| About, dialogs, popovers, menus, banners, toasts, notifications | No complete app-wide implementation evidence established | M5 inventory and disposition required |
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
4. **M0-C — Prioritize the phase backlog.** Next: synthesize M0-A/M0-B findings into bounded, dependency-ordered tasks with acceptance criteria and test plans for maintainer approval.
5. Proceed through M1–M7 in dependency order. The maintainer must explicitly approve each implementation task before code changes.

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
