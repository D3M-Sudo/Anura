# M5-01 — Other windows and shared UI components audit

**Date:** 2026-11-17  
**Repository:** `D3M-Sudo/Anura`  
**Audited branch:** `fix/ui-modernization-aligned`  
**Audited source snapshot:** `0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a`  
**Mode:** read-only source, Blueprint and test-definition inspection  
**Outcome:** audit completed; no confirmed product defect; focused P2 test gaps proposed; no implementation authorized by this record.

## 1. Scope

The audit covers the remaining M5 surfaces and their important states:

- Keyboard Shortcuts overlay/window.
- About and fatal-error/application-information dialogs.
- Clear-history confirmation dialog.
- Language and share popovers.
- Welcome and Extracted page menus.
- Main-window banner and toast overlay.
- Desktop notifications, including XDG Portal and libnotify paths.

The audit distinguishes existing implementation, test evidence and behaviors that require runtime/manual verification. It does not claim a complete visual or accessibility validation.

## 2. Surface inventory and disposition

| Surface | Implementation evidence | Existing automated evidence inspected | Disposition |
|---|---|---|---|
| Keyboard Shortcuts | `anura/widgets/shortcuts_overlay.py`, `data/ui/shortcuts_overlay.blp`; resizable overlay, search entry, scrollable list, empty state, Escape handling and reduced-motion integration. | `tests/test_keyboard_shortcuts.py` checks setup/action registration and UI presence; `tests/test_shortcuts_consistency.py` checks accelerator parsing, uniqueness and registry/overlay consistency. | **Keep existing design.** Focused search/empty-state and close/focus behavior are candidates for P2 tests. |
| About | `DialogManager.show_about()` creates `Adw.AboutDialog`, with application identity, version, copyright, license, acknowledgements and project links. | No dedicated dialog-configuration assertion was identified in the focused test files reviewed. | **Keep native dialog.** No redesign or functional defect demonstrated; direct configuration test is P3. |
| Fatal error | `DialogManager.show_fatal_error()` uses `Adw.MessageDialog`, an explicit OK response and default response. | No direct `DialogManager` test was identified in the focused test files reviewed. | **Keep native dialog.** Add a narrow configuration/presentation test if test seams permit (P3). |
| Clear History | History uses `Adw.AlertDialog` with explicit Clear/Cancel responses, Cancel as default/close response and response wiring. | `tests/test_history_ui.py` verifies dialog construction, parent presentation, default/cancel behavior and that only Clear removes entries. | **Keep.** Existing coverage is appropriate for the reviewed contract. |
| Language popover | `anura/widgets/language_popover.py` handles filtering, Down-arrow navigation, selection and accessible list naming; the list label changes with search and resets on close. | `tests/test_widgets.py` covers Down-arrow navigation and accessible label updates across matching, empty and reset queries; related row tests cover selected state. | **Keep.** Existing tests already cover key semantics; add open/close focus tests only if runtime inspection identifies a gap. |
| Share popover/rows | Extracted Blueprint declares the share trigger and provider popover; `ShareRow` supplies tooltip and accessible label and activates the provider action. | `tests/test_widgets.py` checks row tooltip/accessibility setup and that all active provider icons resolve from resources. | **Keep.** Consider a focused activation/dismissal test only if the interaction contract is not covered elsewhere. |
| Welcome menu | `data/ui/welcome_page.blp` declares History, Preferences, Keyboard Shortcuts, About, Report an Issue and GitHub actions. | Shortcuts consistency tests cover accelerator/action registry alignment, but do not establish full menu-model action integrity. | **Keep menu hierarchy.** Add a P2 static/runtime action-resolution check. |
| Extracted menu | `data/ui/extracted_page.blp` declares Open in External Editor, Preferences, Keyboard Shortcuts, About and Report an Issue; screenshot has its own menu model. | No complete menu-model/action-resolution assertion was identified in the focused tests reviewed. | **Keep context-specific differences.** Add a P2 action-resolution check; do not force identical menus where page context differs. |
| Banner | `data/ui/window.blp` declares an `Adw.Banner` with a Dismiss action. | No focused banner dismissal/lifecycle assertion was identified in the inspected tests. | **Keep.** P2 test for dismissal and visibility/state transition. |
| Toasts | Main window uses `Adw.ToastOverlay`; controller outcomes route through window toasts in several flows. | `tests/test_history_ui.py` includes toast-routing regression coverage for controller outcomes. | **Keep.** Add only missing repeated-show/dismissal assertions if a stable test seam exists. |
| Desktop notifications | `NotificationService` prefers XDG Portal and falls back to libnotify; escapes markup, maps priorities, tracks Portal IDs, schedules dismissal and cleans active notifications. | `tests/test_notification_service.py` covers Portal success, libnotify fallback, invalid priority, action notifications and markup escaping. `tests/test_notification_privacy.py` protects OCR-text privacy and shared service use. | **Keep.** P3 candidates: Portal removal/cleanup and backend failure edge cases; no need to rewrite service. |

### Principal source and test references

- [Shortcuts overlay](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/anura/widgets/shortcuts_overlay.py)
- [Dialog manager](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/anura/core/dialogs.py)
- [Language popover](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/anura/widgets/language_popover.py)
- [Share row](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/anura/widgets/share_row.py)
- [Notification service](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/anura/services/notification_service.py)
- [Shortcuts consistency tests](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/tests/test_shortcuts_consistency.py)
- [Shortcuts tests](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/tests/test_keyboard_shortcuts.py)
- [Widget tests](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/tests/test_widgets.py)
- [History UI tests](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/tests/test_history_ui.py)
- [Notification service tests](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/tests/test_notification_service.py)
- [Notification privacy tests](https://github.com/D3M-Sudo/Anura/blob/0e07bdcf916a6a3eec3b61d9acafbfbbb8de989a/tests/test_notification_privacy.py)

## 3. Proposed P2 automated-test plan (not implementation authorization)

The goal is to close high-value verification gaps without redesigning already coherent components or duplicating existing tests.

| ID | Target | Proposed assertions | Likely test location | Acceptance criteria |
|---|---|---|---|---|
| M5-P2-01 | Shortcuts search and empty state | A known query filters to expected entries; an unmatched query exposes the empty state; clearing the query restores entries; Escape closes the overlay. | `tests/test_keyboard_shortcuts.py` or a focused Shortcuts UI test module. | Deterministic GTK test covers match, no-match, reset and close; no timing-dependent sleeps. |
| M5-P2-02 | Welcome/Extracted menu action integrity | Every declared menu action resolves to the intended application/window action scope; context-specific menu differences are explicit and tested. | New focused menu-model test or extension of existing action-registry tests. | Both menu models and the screenshot menu are checked; test fails for missing or mis-scoped actions without requiring desktop rendering. |
| M5-P2-03 | Banner and toast lifecycle | Dismiss hides the banner; repeated state changes do not leave stale visibility; toast routing remains tied to the active window and dismissal behavior is deterministic. | Focused window/widget integration tests. | Test uses controlled GTK/GLib main-context progression or injected seams, not arbitrary sleeps; existing History toast coverage is reused rather than duplicated. |

**P2 implementation boundary:** no production behavior change is currently proposed. If tests reveal a real defect, stop and present the defect, affected behavior and minimal remediation separately before changing application code.

## 4. P3 candidates (defer unless justified)

- Direct construction/presentation assertions for About and fatal-error dialogs.
- Portal notification removal on timeout and shutdown, including backend failure paths.
- Additional share/language popover focus restoration or dismissal tests, but only after checking that existing widget tests do not already provide equivalent coverage.
- Any pixel-level visual, live theme, Orca/AT-SPI or physical keyboard verification remains outside this audit and must not be represented as passed.

## 5. Evidence limits

- This was a static inspection of source, Blueprint definitions and test definitions at the exact audited source snapshot above.
- No test command, build, CI workflow or desktop session was run as part of this audit.
- No live GTK rendering, GNOME interaction, Orca/AT-SPI, screen-reader, keyboard traversal, notification-daemon or multi-monitor behavior is claimed as verified.
- A focused test search is evidence of the tests inspected, not proof that no equivalent assertion exists anywhere else in the repository.
- CI/CodeQL were checked separately on the same PR snapshot: CodeQL run [#44128147802](https://github.com/D3M-Sudo/Anura/actions/runs/44128147802) succeeded; CI run [#44128148026](https://github.com/D3M-Sudo/Anura/actions/runs/44128148026) was still in progress at the time of inspection. Neither result validates the M5 runtime behaviors listed above.

## 6. Disposition

- M5-01 read-only audit: **Completed**.
- M5 phase: **Partial**; the audit does not complete the phase.
- Existing coherent UI: **retain**, no gratuitous redesign.
- P2 plan: **proposed and documented**, implementation requires a separate bounded approval.
- P3 items: **deferred**.
- PR #648: remains Open/Draft/unmerged; base `feature`; no protected branch modified.
- CHANGELOG: unchanged because no product behavior changed.
