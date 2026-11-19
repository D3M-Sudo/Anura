# Anura M6-02 — Cross-window automated test coverage plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use the approved execution method selected by the maintainer after reviewing this plan. If subagent execution is selected, use `superpowers:subagent-driven-development`; otherwise use the explicitly approved native workflow. Steps use checkbox syntax for tracking.

**Goal:** Define a bounded, evidence-driven automated-test programme for the P1/P2 responsive and accessibility gaps identified by M6-01, without implementing tests or changing product code in this task.

**Architecture:** Reuse the existing pytest, GTK Integration and Python Quality jobs. Use headless tests only for deterministic model/controller contracts; use real GTK widgets and the existing virtual-Wayland integration job for allocation, scrolling, focus state and widget semantics that require a GTK display. Keep physical keyboard, Orca/AT-SPI and native desktop checks outside the automated acceptance claim.

**Tech Stack:** Python, pytest, PyGObject, GTK 4, Libadwaita, Gio/GSettings, Blueprint resources, existing GitHub Actions workflows.

**Source audit:** `docs/audit/ui-cross-window-m6-01-2026-11-18.md`

## Global Constraints

- Work only on `fix/ui-modernization-aligned`; PR #648 remains Open, Draft, unmerged, base `feature`.
- This document is a test plan only. It authorizes no test implementation, production fix, workflow change, dependency, CHANGELOG change, PR transition or merge.
- Do not modify `feature`, `development`, `testing` or `main`.
- Reuse current test infrastructure; do not add dependencies or permanent/temporary workflows.
- Do not duplicate existing assertions. Extend an existing test module only when the new cases remain cohesive; otherwise use the exact new test paths listed below.
- A missing test is not evidence of a product defect. No production change is in scope. Any future production fix requires a separately approved scope and a demonstrated failing regression.
- Reference viewports are 360×600, 640×480, 900×600 and 1280×800. They are test inputs, not a claim that every existing window already passes at each size.
- Do not treat GTK CI virtual input as physical keyboard validation. The CI environment disables the accessibility bridge with `NO_AT_BRIDGE=1` and `GTK_A11Y=none`.
- Do not claim native visual rendering, Orca/AT-SPI, physical Tab/Shift+Tab, live window-manager/monitor behavior, installed-package host smoke or real desktop pointer interaction.
- Do not update global phase status until the approved implementation tasks and exact-head CI evidence justify it.

## Review Focus

1. **Small viewport and constrained height:** content may remain allocated while essential actions are clipped or inaccessible; tests must assert bounds, scrollability and action reachability, not only widget construction.
2. **Long or expanded content:** long OCR/history text and expanded rows may displace actions; tests must prove the intended scroller owns overflow and action controls remain reachable.
3. **Page changes and focus:** switching Preferences pages or navigating between Welcome, Extracted and History may leave focus on hidden/unmapped controls; tests must assert visible, mapped focus targets after supported programmatic routes.
4. **Search and empty states:** filtering can hide all rows or groups while leaving stale focus or inaccessible recovery actions; tests must cover both results and no-results states.
5. **Asynchronous/transient state:** progress, status announcements, banner visibility and disposal can change accessible state; tests must assert meaningful transitions without percentage-level announcement noise or stale callbacks.

---

## 1. Current evidence and coverage disposition

This plan is based on the M6-01 read-only source/template/test audit and the existing test files listed below. The test names proposed later in this document are candidates, not existing tests and not claims of current coverage.

| Surface / requirement | Existing evidence to retain | Remaining CI-testable gap |
|---|---|---|
| Welcome | `tests/test_audit_ui_widgets.py`, `tests/test_widgets.py`, `tests/test_welcome_page_accessibility.py` | No new M6-02 work proposed unless a concrete regression appears while building route tests; reviewed Welcome contracts are already comparatively solid. |
| Extracted / OCR | `tests/test_widgets.py`; `tests/test_audit_ui_widgets.py` | A viewport matrix that proves long-result scrolling and reachability of copy/share/TTS/navigation actions is not established. |
| History | `tests/test_history_ui.py`, `tests/test_history_navigation_focus.py` | No complete responsive matrix for expanded rows/long text/action reachability. Physical row-action traversal remains issue #655 / M7. |
| Main window geometry | `tests/test_window_geometry.py` | Pure geometry and reference viewport sizing exist; these tests do not prove every child surface reflows or that all live monitor/window-manager constraints work. |
| Preferences | `tests/test_preferences_page_resilience.py`, `tests/test_preferences_languages_lifecycle.py`, `tests/test_preferences_languages_integration.py`, `tests/test_preferences_editor_integration.py`, `tests/test_preferences_voice_integration.py` | No unified four-page responsive geometry and focus-entry/exit matrix. Existing GSettings/lifecycle tests must remain intact. |
| Language selector / popover / rows | `tests/test_widgets.py`, `tests/test_language_row_accessibility.py`, `tests/test_preferences_languages_integration.py` | Compact geometry and programmatic focus entry/exit are not comprehensively covered. Direct Down-arrow handler tests are not physical keyboard traversal. |
| Keyboard Shortcuts | `tests/test_keyboard_shortcuts.py`, `tests/test_m5_02_ui_contracts.py`, `tests/test_shortcuts_consistency.py` | Search and Escape contracts exist; compact layout, search-result focus and focus return to the invoking control need bounded GTK assertions. |
| Accessible names / status | `tests/test_accessible_status_announcements.py`, `tests/test_language_row_accessibility.py`, `tests/test_history_ui.py`, `tests/test_welcome_page_accessibility.py` | Evidence is selective; no inventory demonstrates that every high-value interactive control and dynamic state has an application-authored name/label. |
| Contrast / theme | `tests/test_ui_palette.py`, `tests/test_widgets.py`, `tests/ui_color_scanner.py`, `tests/test_ui_color_scanner.py` | Token and selected-state coverage exists; semantic roles/states across the complete surface inventory are not yet reconciled. |
| Reduced motion | `tests/test_reduced_motion.py`, `tests/test_widgets.py` | Shared preference/fallback behavior exists; remaining application-controlled animation consumers need a source inventory before adding tests. |
| Menus / dialogs / banners / toast / notifications | `tests/test_m5_02_menu_actions.py`, `tests/test_m5_02_ui_contracts.py`, `tests/test_notification_privacy.py` | P3 dialog construction, transient lifecycle and some actual template-signal paths remain deferred; they are not pulled into this M6-02 P1/P2 plan. |

## 2. Requirement-to-test traceability matrix

| ID / priority | Requirement and surface | Proposed test target | Layer | Acceptance criterion |
|---|---|---|---|---|
| M6-R01 / P1 | Extracted: responsive geometry and essential actions | New `tests/test_m6_02_extracted_history_responsive.py`; `anura/widgets/extracted_page.py`; `data/ui/extracted_page.blp` | GTK integration | At each selected reference viewport, a long OCR result remains inside its intended scroll region; copy/share/TTS and navigation controls remain mapped, sensitive when appropriate, and within the owning page/window bounds. No child may be silently clipped outside both viewport and scrollable region. |
| M6-R02 / P1 | History: expanded row and long-text overflow | Same new module; `anura/widgets/history_page.py`; `data/ui/history_page.blp` | GTK integration | Long text is scrollable within the designated region; expanding a row does not make its Copy/Editor/TTS actions unreachable; the page/window does not grow beyond the test viewport. Preserve existing refresh/scroll restoration tests. |
| M6-R03 / P1 | Preferences: General, Languages, Editor, Voice geometry | New `tests/test_m6_02_preferences_responsive.py`; `anura/widgets/preferences_dialog.py`, `preferences_general_page.py`, `preferences_languages_page.py`, `preferences_editor_page.py`, `preferences_voice_page.py`; corresponding `data/ui/preferences_*.blp` | GTK integration | Each of the four pages can be instantiated and switched to at the reference viewports. The page content remains reachable through its intended scrolling/container behavior; page-specific primary controls are mapped and within the dialog bounds. |
| M6-R04 / P1 | Preferences: focus entry/exit on page switch | Same Preferences test module | GTK integration | After opening Preferences and switching among General/Languages/Editor/Voice using the supported programmatic page-selection seam, focus is either retained on a visible control or moved to a documented visible fallback; it is never left on an unmapped/hidden control. Do not simulate physical Tab traversal. |
| M6-R05 / P1 | Shortcuts: compact geometry, search results and focus return | New `tests/test_m6_02_shortcuts_popover_focus.py`; `anura/widgets/shortcuts_overlay.py`; `data/ui/shortcuts_overlay.blp` | GTK integration for deterministic geometry/filtering; native validation in M7/P9 for focus grants | At 360×600 and 640×480, the search field and result/empty-state content remain visible and scrollable; debounced filtering produces the expected result/empty state. CI does not assert parent/overlay activation, initial search focus or focus retention after filtering. Native M7/P9 validation must check initial focus, focus after filtering and focus return on close where the public API supports it. Existing search/Escape behavior remains unchanged. |
| M6-R06 / P1 | Language selector/popover compact geometry, filtering and state | Same Shortcuts/popover module; `anura/widgets/language_popover.py`, `language_popover_row.py`; `data/ui/language_popover.blp`, `language_popover_row.blp` | GTK integration for deterministic geometry/state; native validation in M7/P9 for focus grants | Search/list content remains scrollable at compact viewports; filtering, empty state, selected state, tooltip/accessibility metadata and deterministic close-state cleanup remain consistent. CI does not assert initial search focus or focus after popover close. Native M7/P9 validation must check real activation, initial search focus and focus behavior after close. |
| M6-R07 / P1 | Cross-window focus routes | New `tests/test_m6_02_navigation_focus_routes.py`; `anura/window.py`; `data/ui/window.blp`, `welcome_page.blp`, `extracted_page.blp`, `history_page.blp` | GTK integration | For supported programmatic routes Welcome→Extracted, Extracted→Welcome, Welcome→History and History→Welcome, the destination page is visible/mapped and focus resolves to its documented primary action or a documented fallback. Preserve the existing History→Welcome regression rather than duplicating it. |
| M6-R08 / P2 | High-value controls have explicit accessible names and roles | New `tests/test_m6_02_accessible_control_contracts.py`; relevant widget modules/templates listed in the audit report | Headless + GTK integration | A finite inventory of user-critical controls (OCR actions, History row actions, language search/install/remove/progress, Preferences page controls, Shortcuts search/close, primary Welcome actions) has explicit, meaningful labels/names and expected widget roles where the GTK API exposes them. Dynamic labels track the action/state. Do not infer Orca output from GTK property assertions. |
| M6-R09 / P2 | Status announcements cover meaningful state transitions | Extend `tests/test_accessible_status_announcements.py` and `tests/test_language_row_accessibility.py` only for uncovered transitions | Headless | Start/completion/failure and OCR/TTS/search state changes produce one concise announcement per meaningful transition; intermediate percentage updates do not spam announcements. Existing LanguageRow and status tests are reused, not copied. |
| M6-R10 / P2 | Theme/contrast semantic roles across surfaces | Extend `tests/test_ui_palette.py` and `tests/test_ui_color_scanner.py`; inspect shared CSS and all 14 audited Blueprint templates | Headless/static | Every application-authored semantic color use in the audited surface inventory resolves to an approved token or has an explicit documented exception. Add contrast assertions only for uncovered token/state combinations; do not duplicate current palette threshold tests. |
| M6-R11 / P2 | Reduced-motion coverage for remaining application-controlled consumers | Extend `tests/test_reduced_motion.py` only after tracing CSS/Python animation consumers | Headless + GTK integration where state requires a widget | Every remaining application-controlled animation consumer has a deterministic reduced-motion assertion or a documented reason it does not animate. Do not test toolkit-owned Libadwaita transitions as application behavior. |
| M6-R12 / P3 deferred | About/fatal dialogs, Portal timeout/shutdown, toast dismissal/lifecycle, unverified banner/template signal paths | Existing M5 audit and tests; no new M6-02 test file | Deferred / separate approval | No M6-02 acceptance claim. Keep P3 scope deferred; any later test proposal requires a separate task and explicit maintainer approval. |

## 3. Viewport and geometry test protocol

| Viewport | Intended stress | Required surfaces |
|---|---|---|
| 360×600 | Narrow width; compact actions; long labels | Extracted, History, all Preferences pages, Shortcuts, language popover |
| 640×480 | Constrained width and height; vertical overflow | Extracted, History, all Preferences pages, Shortcuts, language popover |
| 900×600 | Initial-window reference geometry | P1 surfaces above; baseline comparison |
| 1280×800 | Wide layout and excess-space behavior | P1 surfaces above; ensure no accidental fixed-size clipping or stretched controls |

Test harness requirements:
- Use the existing GTK integration setup and real GTK/Libadwaita widgets/templates; do not create a second compositor or new CI workflow.
- Create a test window, set its default size to the target viewport, present it, and drain the GLib main context until allocation/mapping stabilizes using the established bounded-wait pattern already used by `tests/test_history_navigation_focus.py`.
- Assert actual widget allocations against the viewport and relevant ancestor bounds. For content intended to overflow, assert that the correct scrolled window owns the overflow and that the vertical/horizontal adjustments have a meaningful upper/page-size relationship.
- Assert deterministic reachability using public widget state (`get_mapped`, `get_visible`, `get_sensitive`, allocation bounds and scroll adjustments); do not treat a non-null widget or a handler invocation as proof of visible/reachable interaction. Do not assert window activation or focus grants in the virtual-Wayland CI lane.
- Parameterize only where the same invariant applies. Do not force every page into every viewport if a particular dialog/popover has a distinct sizing contract; document the narrower case and why.
- Avoid pixel snapshots, color sampling and screenshot-diff thresholds in this phase; native rendering remains M7.

## 4. Test layering and execution order

1. **Headless contracts:** deterministic mapping, label/state transitions, announcement deduplication and source/token inventory. Run in the existing Python Quality job.
2. **GTK integration contracts:** actual widget construction, allocation, scrolling, filtering/state transitions and GTK-exposed accessible properties. Run in the existing GTK Integration job on virtual Wayland. Focus-grant-dependent window/popover assertions are excluded from this lane and retained for native M7/P9.
3. **Static/source contracts:** use only for stable declarations that cannot be observed through a public runtime seam; do not substitute source-string checks for behavior when a GTK test can prove it.
4. **Native/manual checks:** excluded from M6-02 automated acceptance and retained for M7; no simulation result may be described as native evidence.

Recommended order:
- First P1 responsive geometry: M6-R01 through M6-R03.
- P1 programmatic page-switch/navigation focus contracts: M6-R04 and M6-R07 remain separate deterministic tasks; Shortcuts/Language Selector focus grants in M6-R05/R06 are deferred to M7/P9.
- Then P2 semantics/announcements: M6-R08 and M6-R09.
- Then P2 theme/reduced motion: M6-R10 and M6-R11.
- Keep M6-R12 deferred.

Each implementation task must be independently reviewable and must complete its focused test cycle plus full exact-head CI before the next task begins. If one task exposes a product defect, stop at the failing test and request a separate production-fix authorization; do not silently expand a test-only task.

## 5. Proposed file map for a future approved implementation

**New test modules (not created by M6-02):**
- `tests/test_m6_02_extracted_history_responsive.py` — Extracted and History viewport/overflow invariants.
- `tests/test_m6_02_preferences_responsive.py` — four Preferences pages, compact geometry and focus on page switching.
- `tests/test_m6_02_shortcuts_popover_focus.py` — Shortcuts overlay and language popover compact geometry/focus lifecycle.
- `tests/test_m6_02_navigation_focus_routes.py` — supported main-window navigation routes and destination focus.
- `tests/test_m6_02_accessible_control_contracts.py` — finite high-value control-name/role/state inventory.

**Existing test modules to extend only when necessary:**
- `tests/test_accessible_status_announcements.py`
- `tests/test_language_row_accessibility.py`
- `tests/test_ui_palette.py`
- `tests/test_ui_color_scanner.py`
- `tests/test_reduced_motion.py`

**Production sources/templates to inspect during implementation, not modify by default:**
- `anura/window.py`
- `anura/widgets/extracted_page.py`, `history_page.py`, `preferences_dialog.py`
- `anura/widgets/preferences_general_page.py`, `preferences_languages_page.py`, `preferences_editor_page.py`, `preferences_voice_page.py`
- `anura/widgets/shortcuts_overlay.py`, `language_popover.py`, `language_popover_row.py`
- `data/ui/window.blp`, `extracted_page.blp`, `history_page.blp`, `preferences_dialog.blp`, `preferences_general.blp`, `preferences_languages.blp`, `preferences_editor.blp`, `preferences_voice.blp`, `shortcuts_overlay.blp`, `language_popover.blp`, `language_popover_row.blp`

## 6. Acceptance gates for M6-02 planning

M6-02 planning is complete when:
- Every P1/P2 gap in the M6-01 report is either mapped to a proposed test with an acceptance criterion or explicitly dispositioned as already covered/deferred.
- Every proposed test maps to an exact surface, existing/new test module, test layer and source/template target.
- The four reference viewport cases and the conditions for using them are explicit.
- Existing tests are identified for reuse; duplicate assertions are avoided.
- P3 deferrals and all M7 native checks are explicit.
- The plan makes no claim that proposed tests exist or have passed.
- Only documentation files are changed in the planning task.

## 7. Exclusions and governance

The following remain outside M6-02 and cannot be marked passed by its CI:
- rendered visual inspection on the maintainer's GNOME/GTK desktop;
- physical Tab/Shift+Tab traversal, including History row suffix actions tracked by issue #655;
- native window activation and focus grants for Shortcuts/Language Selector (initial search focus, focus after filtering, and focus after popover close);
- Orca/AT-SPI and any screen-reader output with an enabled bridge;
- live multi-monitor/window-manager/work-area geometry;
- actual pointer activation or template signal wiring not invoked through an established GTK integration seam;
- installed AppImage/Flatpak package smoke tests on the maintainer's host;
- About/fatal-dialog completeness, Portal timeout/shutdown cleanup, toast dismissal/lifecycle and other P3 transient behavior.

**Authorization boundary:** approval of this plan will authorize only the specific test-only tasks the maintainer selects. It will not authorize production fixes, dependency changes, workflow changes, CHANGELOG edits, PR state/base changes or merge. Production changes require a separate explicit approval and RED→GREEN evidence.

## 8. Planning disposition

- **M6-02:** P1/P2 completed within approved CI-testable scopes; P3 selective deterministic geometry/filter/state coverage implemented on `758c8e568dea6d9a964fc9a3513800953410eb2a`, with exact-head CI/CodeQL pending. P3 activation/focus-grant assertions are deferred to M7/P9.
- **M6 global phase:** remains **Partial**.
- **M7:** native visual, physical keyboard, Orca/AT-SPI, live desktop geometry, installed-package checks and P3 Shortcuts/Language Selector activation/focus-grant validation remain deferred.
- **Branch/PR:** `fix/ui-modernization-aligned`; PR #648 must remain Open/Draft/unmerged, base `feature`.
