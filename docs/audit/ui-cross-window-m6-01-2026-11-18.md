# M6-01 — Cross-window responsive and accessibility audit

**Date:** 2026-11-18  
**Repository:** `D3M-Sudo/Anura`  
**Audited branch:** `fix/ui-modernization-aligned`  
**Audited source HEAD:** `62b28215ccea8b90ea3c494206f26e2171a729a5`  
**Audit type:** read-only source, template, existing-test and roadmap review  
**Disposition:** M6-01 audit/matrix completed within the documentation-only scope approved by the maintainer. No code, tests, dependencies, workflows or runtime behavior were changed.

**Status:** Completed — bounded cross-window audit and evidence matrix.
**Programme boundary:** Global M6 remains **Partial**. M7/P9 native-host validation obligations remain open and are not represented as passed.

## 1. Purpose and scope

M6-01 reconciles responsive and accessibility evidence across the complete application UI scope, not only the windows previously modified in M1–M5. The review covers the main shell and all identified windows/pages, dialogs, popovers, menus, reusable rows, notifications and transient states.

The audit reviewed the current branch's repository instructions, the global and PR workstream roadmaps, the M1/M4/M5 audit records, 14 Blueprint UI templates, the principal Python UI modules, shared styling and the existing responsive/accessibility test suites.

This is an evidence inventory, not a claim that every surface has been manually rendered or fully accessibility-tested. Existing automated assertions are distinguished from native GTK behavior that CI cannot establish.

## 2. Coverage model

The review uses the global reference viewport set:

- **360×600** — narrow/compact viewport.
- **640×480** — constrained intermediate viewport.
- **900×600** — initial-window target.
- **1280×800** — wide viewport.

The 900×600 value is the global initial-window target; it is not, by itself, proof that every window has a test at that size.

Each surface is assessed against:

1. Responsive geometry, reflow, scrolling, overflow and essential-control reachability.
2. Keyboard focus order, focus restoration, keyboard-operable actions and navigation between windows/pages.
3. Accessible names, roles, states and status/progress announcements.
4. Contrast, semantic color use and light/dark theme behavior.
5. Reduced-motion behavior and lifecycle of transient UI.
6. Cross-window consistency of shared interaction patterns.

Status definitions:

- **Solida:** meaningful automated evidence exists for the reviewed contract; this is not equivalent to complete native accessibility validation.
- **Parziale:** evidence exists, but important dimensions or interactions remain uncovered.
- **Gap:** no sufficiently specific evidence was identified in the reviewed sources.

## 3. Cross-window matrix

| Surface | Responsive / geometry evidence | Focus / interaction evidence | Accessible semantics / announcements | Assessment |
|---|---|---|---|---|
| Main window and navigation shell | Window geometry has dedicated automated coverage; no complete all-window viewport matrix was identified. | Navigation-state and focus restoration have partial coverage. | OCR/TTS and status-announcement mechanisms exist; complete shell-wide semantic audit is not established. | **Partial** |
| Welcome | Responsive compact/wide layouts, constrained-height scrolling and viewport-allocation tests exist. | Initial focus, action order, compact/wide transitions and focus restoration after reparenting are covered by automated tests. | Drop-area and language-selector labels/states have targeted assertions. | **Solid for the reviewed automated contracts** |
| Extracted / OCR | Text presentation and scrolling behavior have component-level coverage; no full viewport matrix across all extracted states was identified. | Navigation focus and selection/action state have partial automated coverage. | Result/status announcements and action labels have targeted coverage, but the complete interaction is not proven natively. | **Partial** |
| History | Expanded text areas are bounded and scrollable; long-text behavior and state restoration are tested. | History-to-Welcome focus restoration has a dedicated integration test; physical traversal across row actions is not proven. | Copy, Editor and TTS action labels have targeted tests; full AT-SPI exposure remains unverified. | **Partial** |
| Preferences — General, Languages, Editor, Voice | Four pages and the 640×480 initial content geometry are source/template evidence; a cross-page viewport matrix is absent. | Settings persistence, Languages search/filter and lifecycle are covered; full focus traversal between pages is not established. | Languages list naming and relevant progress/status behavior have targeted tests; all controls are not independently audited. | **Partial** |
| Language selector and popover | Search/list behavior exists; no complete geometry matrix at reference viewports was identified. | Selected state and Down-arrow handler are tested; handler-level coverage is not physical keyboard traversal. | Search label and selected state have targeted assertions. | **Partial** |
| LanguageRow and ShareRow | Reusable component behavior is covered; narrow-width geometry and truncation are not comprehensively tested. | Component actions and state transitions have targeted tests. | Language context, progress-bar name and download announcements; ShareRow accessibility assertions exist. | **Partial** |
| Keyboard Shortcuts | Resizing/scrolling behavior is represented in the UI; complete compact viewport diagnostics are not established. | Search, Escape and shortcut registry consistency are tested; complete physical focus traversal remains open. | Shortcut descriptions and entries are checked for consistency; native screen-reader output is not verified. | **Partial** |
| About and dialogs | Native Libadwaita components are used; a complete responsive geometry suite was not identified. | Clear History confirmation/response behavior has tests; About and fatal-dialog interaction coverage is limited. | No complete dialog-by-dialog accessible-name/role audit was established. | **Partial** |
| Menus, popovers, banners, toasts and notifications | Native component geometry is relied upon; cross-surface viewport evidence is incomplete. | Menu action resolution and banner dismissal have automated contracts; transient lifecycle and all signal paths are not uniformly verified. | Notification privacy and selected component labels are covered; announcement/dismissal semantics need reconciliation. | **Partial** |

## 4. Existing automated evidence

The following files were identified as relevant evidence on the audited branch. Their presence does not imply that every test in each file was rerun during this documentation task.

| Evidence area | Existing test sources | What the reviewed tests support |
|---|---|---|
| Welcome responsive/focus | `tests/test_audit_ui_widgets.py`, `tests/test_widgets.py` | Viewport-based layout, compact/wide focus order, reparenting and constrained-height behavior. |
| Window geometry | `tests/test_window_geometry.py` | Window geometry and resize-related contracts. |
| Extracted/navigation | `tests/test_widgets.py` | Extracted state, navigation focus and interaction lifecycle contracts. |
| History | `tests/test_history_ui.py`, `tests/test_history_navigation_focus.py` | Long text, bounded expanded area, scroll restoration, action labels and a real GTK focus-restoration integration path. |
| Preferences/Languages | `tests/test_preferences_languages_lifecycle.py`, `tests/test_preferences_languages_integration.py`, `tests/test_preferences_editor_integration.py`, `tests/test_preferences_voice_integration.py` | Search/filter/empty/reset/list lifecycle, accessible list name and selected settings persistence/integration. |
| Language and share components | `tests/test_language_row_accessibility.py`, `tests/test_widgets.py` | Progress name/fraction/reveal behavior, download announcements, language selector state and ShareRow labels. |
| Keyboard Shortcuts | `tests/test_keyboard_shortcuts.py`, `tests/test_shortcuts_consistency.py`, `tests/test_m5_02_ui_contracts.py` | Registry/overlay consistency, search/empty/reset and selected UI contracts. |
| Contrast and theme | `tests/test_ui_palette.py`, `tests/test_widgets.py` | Approved palette contrast, focus-indicator contrast and selected theme-transition behavior. |
| Reduced motion | `tests/test_reduced_motion.py`, `tests/test_widgets.py` | Reduced-motion preference handling, live transitions and older-GTK fallback contracts. |
| Status announcements | `tests/test_accessible_status_announcements.py`, `tests/test_language_row_accessibility.py` | Selected OCR/TTS/search and language-download announcements. |
| Menus, dialogs and transient UI | `tests/test_m5_02_menu_actions.py`, `tests/test_m5_02_ui_contracts.py`, `tests/test_history_ui.py`, `tests/test_notification_privacy.py` | Static action resolution, selected banner/toast contracts, clear-history dialog response and notification privacy. |

## 5. Prioritized residual gap register

| Priority | Surface / concern | Gap | Recommended next disposition |
|---|---|---|---|
| P1 | Extracted and History | No single viewport/overflow matrix proves all essential controls remain reachable through representative states and text lengths. | Define bounded automated geometry/scroll/focus cases before proposing code changes. |
| P1 | Preferences | Four pages lack a unified responsive, focus and accessible-control matrix. | Inventory page-level controls and identify the smallest meaningful GTK integration contracts. |
| P1 | Shortcuts and popovers | Compact geometry and complete keyboard focus traversal remain incompletely evidenced. | Add test proposals for compact viewport, search results, empty state and focus entry/exit. |
| P1 | Cross-window focus | Current tests cover selected transitions, not a complete navigation graph or every interactive surface. | Build a route-to-focus expectation table; avoid assuming handler tests prove physical traversal. |
| P2 | Accessible semantics | Names, roles, states and announcements are covered selectively rather than for every interactive control and transient state. | Build a control/state inventory and prioritize user-visible actions and asynchronous status. |
| P2 | Contrast and themes | Palette and selected states are tested, but not every semantic role/state on every surface. | Map shared tokens to surfaces and states; add tests only for uncovered application-controlled colors. |
| P2 | Reduced motion | Shared reduced-motion behavior exists, but per-surface animation consumers are not comprehensively traced here. | Trace animation consumers and verify only those with application-controlled motion. |
| P3 | Dialogs and transient lifecycle | About/fatal dialog, toast lifecycle, and some popover/banner signal interactions have deferred or limited coverage. | Preserve existing M5 exclusions; propose separate bounded scope only where evidence justifies it. |

## 6. Explicit validation limits

The following are **not** established by this audit or by the existing CI evidence:

- Rendered GTK/Libadwaita visual correctness, density, clipping and reflow on a native desktop.
- Physical Tab/Shift+Tab traversal or real keyboard interaction.
- Orca output, AT-SPI exposure or operation with an enabled accessibility bridge.
- Live window-manager, monitor, work-area and multi-monitor geometry behavior.
- Actual pointer activation and Gtk.Template signal wiring where tests call controller/handler methods directly.
- Installed-package host smoke testing.

The current GTK CI configuration uses `NO_AT_BRIDGE=1` and `GTK_A11Y=none`; it cannot be cited as Orca/AT-SPI evidence. In particular, the M4 network retry regression test calls `check_connection()` directly and does not prove the banner button's physical click/signal wiring. Physical History keyboard traversal remains separately tracked under issue #655.

These checks remain assigned to M7 native-host validation and are not counted as passed.

## 7. M6-01 disposition and next steps

- **M6-01 audit/matrix:** completed within the approved documentation-only scope.
- **Code/tests/workflows/dependencies:** unchanged by this task.
- **M6 global phase:** remains **Partial**.
- **M6-02 proposed next task:** convert the P1/P2 gaps above into a bounded automated-test plan, map each proposed test to an exact surface and acceptance criterion, and obtain explicit approval before implementing tests or production changes.
- **M7:** retain native visual, physical keyboard, Orca/AT-SPI, live desktop geometry and installed-package checks as deferred obligations.

This document records audit findings and recommendations only. It does not authorize test implementation, production changes, CI workflow changes, dependency additions, branch changes, PR state transitions or merge.
