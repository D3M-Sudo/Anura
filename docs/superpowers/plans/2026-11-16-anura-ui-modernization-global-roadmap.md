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
| M0 | Full application audit | Complete inventory of windows/components/states/functions; current behavior, visual/functional/accessibility/architecture/performance/Linux-compatibility findings; prioritized requirements and traceability baseline | **Completed — M0-A inventory, M0-B traceability/evidence reconciliation and M0-C prioritized backlog/document reconciliation are complete. The programme proceeds to M1-05; this does not imply that all M0 findings are implemented.** |
| M1 | Design System and themes | Approved shared palette/tokens and reusable patterns; typography/spacing/component rules; automatic/light/dark and force-light/force-dark behavior verified | **Partial — M1-02 conventions, M1-03 audit, M1-04 implementation, M1-05 audit and M1-06 bounded implementation/regression coverage are complete within their scopes. M1-06 closes the two Medium findings; final AppImage aarch64 distribution CI is still running. Low-priority CSS/typography cleanup remains deferred.** |
| M2 | Welcome and main navigation | Welcome and main-shell/navigation experience meet responsive, visual, interaction and focus criteria | **Partial — M2-A through M2-E audits and M2-D/M2-F targeted lifecycle fixes completed; M2-F exact-head CI and CodeQL passed. The phase remains partial pending broader Welcome/main-shell criteria and global M2 exit conditions** |
| M3 | Extracted and History | Extracted/OCR and History surfaces consistently modernized without functional regressions | **Partial — Extracted header/action area and scroll protections exist; History modernization is not established as complete** |
| M4 | Preferences and languages | General, Languages, Editor, Voice and language selector meet shared visual, responsive, lifecycle and accessibility criteria | **Partial — Preferences split and selected lifecycle work exist; full page and language-selector audit remains** |
| M5 | Other windows and components | Shortcuts, About, dialogs, popovers, menus, notifications, banners and toasts audited and addressed where justified | **Not started as a complete phase — Shortcuts received limited resizing work; app-wide coverage is unverified** |
| M6 | Responsive behavior and accessibility | Cross-window responsive, focus, contrast, accessible naming/announcements and reduced-motion requirements tested consistently | **Partial — selected automated accessibility and responsive work exists in PR #648; cross-window coverage remains** |
| M7 | Integration and consolidation | Integrated regression suite, documentation/CHANGELOG, translations review, screenshots at agreed timing, and distribution/build validation complete | **Partial — PR #648 has strong branch-level CI evidence; full app-wide phase exit criteria remain** |

## 4.1 Current prioritized backlog (M0-C, 2026-11-16)

M0-C consolidated the operational backlog. The task list is a planning baseline, not blanket implementation authorization. Every implementation requires a separate bounded proposal and explicit approval.

| ID | Priority | Task / boundary | Dependencies | Exit criteria |
|---|---|---|---|---|
| M1-05 | P1 | **Completed** — read-only cross-surface audit; report: [M1-05 audit](../../audit/ui-design-system-m1-05-2026-11-16.md). | M1-04 | 14 Blueprint templates, 15 Python UI modules and related styles/docs/tests inventoried; findings F1–F4 recorded with priorities and evidence limits. |
| M1-06 | P1 | **Implementation and regression tests complete; final AppImage aarch64 CI pending.** F1 reduced-motion handling in Shortcuts; F2 production-tree color-scanner enforcement in pytest. | M1-05; explicit approval received | Initial/live motion preferences, older-GTK fallback, close/dispose cleanup, root motion suppression, production-tree scanner and path/value rationale allowlist covered by tests. Final AppImage aarch64 job must pass before closure; F3/F4 remain deferred. |
| M2-01 | P1 | Complete the residual Welcome/main-shell audit, including navigation, states and focus affordances. | M2-E, M2-F | Requirement-to-surface matrix, findings and test gaps; separate automated evidence from excluded manual checks. |
| M3-01 | P1 | Full Extracted and History audit: states, actions, scrolling, list/row/empty/confirmation behavior. | M1-05 | Surface/state inventory, behavior-preservation map, findings and test gaps; no OCR internals or mockup-only features. |
| M4-01 | P1 | Full Preferences and language-selector audit across General, Editor, Voice, Languages and asynchronous states. | M1-05 | Page/state matrix, lifecycle/accessibility findings and test gaps; preserve settings semantics. |
| M5-01 | P2 | Audit Shortcuts, About, dialogs, popovers, menus, banners, toasts and notifications. | M1-05 | Component/state inventory and evidence-backed disposition; coherent surfaces may remain unchanged. |
| M6-01 | P2 | Cross-window responsive/accessibility coverage matrix and approved automated-test gap closure. | M2-01, M3-01, M4-01, M5-01 | Reference viewport matrix plus focus, naming, announcements, contrast and reduced-motion evidence; exclusions explicit. |
| M7-01 | P2 | Define the global integration and final validation plan. | M1-05 through M6-01; M1-06 disposition | Traceability/validation plan, exact evidence requirements, translation review and deferred screenshot timing. |
| M7-02 | P3 | Execute approved global integration, documentation and distribution validation. | M7-01 and explicit approval | Regression/packaging evidence, relevant docs/CHANGELOG, translation review and final requirement dispositions. |

P1 establishes foundational audits and justified gap closure; P2 completes cross-surface validation and integration planning; P3 executes final integration. M1-06 implementation and regression coverage are complete within scope, with final AppImage aarch64 validation pending. No task authorizes implementation merely by appearing in this table.

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

**M1-02 completed:** the GTK4/Libadwaita-first typography, spacing and custom-radius conventions are documented in `docs/ui-design-system.md`; Blueprint/GTK CSS spacing is normalized and statically guarded. The shared numeric spacing scale is documented rather than expressed as CSS custom properties because GTK CSS does not support arbitrary numeric custom properties. One 6 px Welcome compact-action spacing exception is retained to preserve responsive geometry and is explicitly guarded by a regression test. M1 as a whole remains Partial.

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
| Green palette and runtime stylesheet | Green semantic palette, GResource CSS provider registration, palette/contrast tests; M1-05 cross-surface audit recorded targeted gaps | M1-06 implementation/test coverage closes reduced-motion handling in Shortcuts and production-tree color-scanner enforcement; AppImage aarch64 CI remains pending; manual/pixel validation remains excluded |
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
4. **M0-C — Prioritize the phase backlog.** The bounded, dependency-ordered M1–M7 audit/implementation backlog was synthesized and reviewed in chat on 2026-11-16. Its roadmap record remains separate from this M1 audit update; no implementation was authorized by backlog review.
5. **M1-A/M1-B — Design-system and theme audit.** **Completed 2026-11-16** in read-only mode; findings and evidence limits are recorded below. M1 remains Partial because design-system consolidation and app-wide runtime theme coverage are not complete.
6. **M2-A — Welcome and main-navigation read-only audit. Completed 2026-11-16**; findings and evidence limits are recorded below. No code changes were made.
7. **M2-B — focused read-only verification of complete NavigationView transition paths and state restoration. Completed 2026-11-16**; findings and evidence limits are recorded below. No code changes were made.
8. **M2-C — bounded automated integration-test proposal. Completed 2026-11-16 (planning only).** The two navigation paths, focus/side-effect assertions and maintainer-approved state-retention policies are specified in the task record below. No implementation was authorized.
9. **M2-D — implement the approved Extracted and History navigation-state policies, add automated regression tests, update CHANGELOG and record exact CI evidence. Completed 2026-11-16 on `bb316f94d37629cc7566b24330a87b6e86029db3`; M2 remains Partial at global scope.**

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
- **Historical note:** at the time of the M1-05 audit, M1-06 was the next conditional candidate. The later approved F1/F2 implementation and test evidence are recorded in the M1-06 section below. F3/F4 remain deferred.
- No tests or workflows were run for M1-05; this is static source/test-definition inspection only. No runtime rendering, manual GNOME/GTK visual, Orca/AT-SPI or manual keyboard checks are claimed. Live multi-monitor checks remain excluded; screenshots remain deferred.
- No application source, tests, workflows, CHANGELOG, dependencies, OCR behavior, architecture, protected branches or PR metadata were modified. PR #648 remains Open/Draft/unmerged, base `feature`, head branch `fix/ui-modernization-aligned`.


## M1-06 — Reduced-motion and production UI color scanner (2026-11-16)

- **Status: implementation and regression coverage complete; final AppImage aarch64 CI pending.** Work is isolated to `fix/ui-modernization-aligned`; no protected branch or PR metadata was changed.
- **F1:** `ShortcutsOverlay` reuses `sync_reduced_motion_class()`, observes only GTK settings properties exposed by the current runtime, updates on live preference changes, and disconnects handlers on close-request and destruction. While reduced motion is active it removes the root `anura-fade-in` and `anura-card` classes because the shared `.reduced-motion *` selector does not match the root widget itself; those classes are restored in normal-motion mode. No CSS palette or desktop-wide settings were changed.
- **F2:** `tests/test_ui_color_scanner.py` now scans the actual repository root and approves only exact `(relative_path, normalized_value)` pairs with non-empty semantic rationales. The test reports path, line, literal and syntax for any unclassified finding. Existing fixture tests and the scanner implementation remain unchanged.
- **TDD evidence:** test-only GTK run #43973177077 on `2a937aca9e196973dfa6646c986fe84909fb8dad` produced four expected failures before F1 implementation; test-only run #43973548114 on `f7f03be1f5eddecf9257d6cc75e52cb0c0ddee4f` remained red before implementation; run #43974133349 on `08870472896167b7321e9aa71b557ebdd8f93b3b` reproduced missing close-path cleanup. Final implementation/test SHA: `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`.
- **Green evidence on SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`:** Python quality `644 passed, 6 skipped, 277 deselected`; GTK Integration `447 passed, 5 skipped, 650 deselected, 2 warnings`; Ruff lint/format, mypy, Bandit, Changelog integrity, AppImage x86_64, Flatpak x86_64/aarch64 and multi-architecture release artifact validation passed. CodeQL #43974750821 passed. CI #43974750869 still has AppImage aarch64 in progress.
- **Exclusions:** no manual visual, Orca/AT-SPI, manual keyboard or live multi-monitor validation is claimed. Screenshots remain deferred. M1-05 findings F3 and F4 remain deferred.
