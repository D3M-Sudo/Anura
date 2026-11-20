# M1-05 — Cross-surface Design System adoption audit

**Date:** 2026-11-16  
**Repository:** `D3M-Sudo/Anura`  
**Branch:** `fix/ui-modernization-aligned`  
**Source snapshot reviewed:** `fb1bcbe89f0ce982fc4fadad60630a5a88496dd1`  
**Mode:** read-only source, template, documentation and test inspection.

**Status:** Completed — bounded M1-05 cross-surface adoption audit, including the documented F3/F4 follow-up.
**Programme boundary:** Global M1 remains **Partial**. The original F1/F2 findings and their subsequent M1-06 remediation are distinct from this audit closure; this status does not claim application-wide Design System completion or native visual/accessibility validation.

## 1. Scope and method

Reviewed the UI source and evidence on the source snapshot above:

- 14 Blueprint templates under `data/ui/`;
- 15 Python UI modules under `anura/widgets/`, plus `anura/window.py`, `anura/main.py` and the reduced-motion utility;
- `data/style.css` and `docs/ui-design-system.md`;
- `tests/test_ui_palette.py`, `tests/test_ui_color_scanner.py`, `tests/ui_color_scanner.py`, relevant GTK widget/lifecycle tests and the CI workflow test commands.

The audit traced documented typography, spacing, radii, palette/theme roles and custom CSS classes to their Blueprint/Python consumers and automated checks. It did not execute the application, tests or workflows. No local checkout or runtime rendering was available.

## 2. Surface adoption matrix

| Surface | Existing implementation / conventions | Audit disposition |
|---|---|---|
| Main window and navigation shell | `Adw.ApplicationWindow`, `Adw.ToastOverlay`, `Adw.NavigationView`; initial Blueprint size 900×600 | **Acceptable baseline.** Uses native Libadwaita shell components. No M1-specific geometry defect established. |
| Welcome | `Adw.StatusPage`, `Adw.Clamp`, native suggested-action/pill controls, `.welcome-hero`; responsive action reparenting and a documented 6 px exception | **Acceptable baseline.** Semantic hero title exception and spacing exception are documented and statically guarded. |
| Extracted | `Adw.ToolbarView`, native header/search/footer patterns, `GtkSource.View`, `.extracted-page`, `.anura-button` | **Mostly native.** Uses theme-managed editor surfaces and shared button treatment. No new concrete token defect established. |
| History | `Gtk.Stack`, `Gtk.ListBox`, `boxed-list`/ `card`, `.history-empty-state`, native `Adw.ExpanderRow` and flat row actions | **Consistent with conventions.** Custom empty-state color treatment has static light/dark contrast coverage. |
| Language popover and rows | Native popover/list/search; `.lang-selector`, `.search_box`, `.language_popover_row`; dynamic `.downloaded` state | **Mostly consistent.** Downloaded state is correctly linked to the existing CSS class. Two typography class names are not mapped in the design-system document; see F4. |
| Preferences dialog and pages | `Adw.PreferencesDialog`, `Adw.PreferencesPage`, `Adw.PreferencesGroup`, native `SwitchRow`, `ComboRow`, `SpinRow`; Languages uses Clamp, Banner, boxed-list and StatusPage | **Strong native adoption.** No reason for a broad restyle. Theme-specific runtime coverage is not exhaustive, but most controls remain Libadwaita-managed. |
| Keyboard Shortcuts | Separate `Adw.Window`, native toolbar/list, dynamically generated `Adw.PreferencesGroup` and `Adw.ActionRow`; root receives `.anura-fade-in` and `.anura-card` | **Gap:** separate top-level window does not receive the reduced-motion class applied by `AnuraWindow`; see F1. |
| Share rows and transient UI | Native `ListBoxRow`, `Adw.ToastOverlay`, `Adw.Banner`, popovers and dialogs | **Mostly native.** Several custom stylesheet selectors appear to have no current source/template consumer; see F3. |

## 3. Findings

### F1 — Medium: reduced-motion treatment misses the separate Shortcuts window

**Evidence**

- `anura/window.py:128-136` reads GTK motion settings and calls `_sync_reduced_motion_class()` on the main `AnuraWindow`.
- `anura/window.py:223-229` updates that class when GTK motion settings change.
- `data/style.css:304-312` applies the reduced-motion overrides under the `.reduced-motion` ancestor selector.
- `anura/widgets/shortcuts_overlay.py:42` defines `ShortcutsOverlay` as a separate `Adw.Window`; lines 66–67 add `.anura-fade-in` and `.anura-card` to that window itself.
- The inspected Shortcuts window path does not call `sync_reduced_motion_class` or add `.reduced-motion`.

**Impact**

The main-window reduced-motion class cannot cover a separate top-level Shortcuts window. Its root-level `.anura-fade-in` animation therefore has no corresponding reduced-motion suppression in the inspected path. This is a concrete consistency/accessibility gap, not a claim that every GTK animation is uncontrolled.

**Recommendation**

In a separately approved M1-06 implementation, apply the same GTK motion preference to the Shortcuts window (including changes while it is open), or remove the app-authored root animation if that is the simpler supported behavior. Add an automated regression for the separate window. Do not alter desktop-wide settings.

### F2 — Medium: color scanner is not enforced against the production tree

**Evidence**

- `tests/ui_color_scanner.py` implements repository discovery and `find_unclassified_ui_colors()`.
- `tests/test_ui_color_scanner.py` contains eight tests using temporary fixture directories. They validate scanner behavior, but do not invoke it against the actual repository tree.
- `tests/test_ui_palette.py` checks selected palette roles, contrast, spacing, radii and typography; it does not invoke the scanner.
- `.github/workflows/main.yml:84` and `:276` run the pytest suites. No production-tree scanner invocation or test gate was found in the inspected workflow/test path.
- A read-only scan of the 15 inspected production UI/template/CSS files found literal colors in `data/style.css` only: brand tokens `#16A36A`, `#0F7650`, `#FFFFFF`; semantic light/dark green states `#0F7650`, `#21B77A`; and three black-alpha shadow values. No hard-coded color strings were found in the inspected Python UI modules.

**Impact**

The scanner can detect unclassified literals when called, but its current fixture tests do not make it a repository-wide CI guard. A newly added production UI color can therefore evade the intended policy unless a caller explicitly runs the scanner with an approved path/value rationale map.

**Recommendation**

Add a production-tree test or explicit CI command that calls `scan_ui_color_literals()` and fails on findings not present in a reviewed path-specific rationale map. Keep the rationale map small and semantic; do not centralize values that intentionally represent distinct roles. This requires a separately approved M1-06 implementation.

### F3 — Low: apparently orphaned custom CSS selectors

The following custom selectors have no matching class declaration in the inspected Blueprint templates or Python UI modules:

- `.anura-pulse`, `.anura-spinner`, `.anura-toast` and `.anura-toast.hiding`;
- `.share-row`;
- `.welcome-page` and `.welcome-card`;
- `.language-popover` and `.language-row`;
- `.screenshot-btn.ready`.

The current source uses different names or native components in several corresponding areas (for example `.lang-selector`, `.language_popover_row`, `Adw.ToastOverlay`). This is a source-to-style traceability finding, not proof that every selector is harmful or that runtime code cannot add a class indirectly.

**Recommendation**

Treat these as cleanup candidates. Before removing any rule, confirm no generated resource or external integration applies the class. No cleanup is required for M1 completion if the selectors are intentionally reserved and documented.

### F4 — Low: two typography classes are not mapped in the design-system guide

- `data/ui/language_row.blp:23` applies the `title` style class.
- `data/ui/preferences_languages.blp:65` applies both `heading` and `h4`.
- `docs/ui-design-system.md:7-20` documents `title-1`, `title-2`/`title-3`, `heading`, `body`, `dim-label` and `caption`, but does not explain these two class usages.

These may be valid native GTK/Libadwaita style classes and are not classified as defects by this audit. Their intended semantic roles should be recorded or the classes should be normalized only after checking their toolkit meaning.

## 4. Areas that pass the static adoption review

- **Spacing:** all 14 Blueprint templates are included in the spacing-scale regression test. The stylesheet's numeric margin/padding declarations are also checked. The single 6 px Welcome exception is documented beside the declaration and guarded by the test.
- **Radii:** the custom stylesheet radii are within the documented scale (12 px and 9999 px); 6 px remains reserved.
- **Typography overrides:** the only application-authored `font-size` declaration is the documented 1.15em Welcome hero emphasis, retaining the `title-1` semantic class.
- **Palette:** the three application palette tokens remain `#16A36A`, `#0F7650`, `#FFFFFF`. The light/dark green pair remains limited to downloaded text, History empty-state icon and focus roles. Native theme colors such as `@theme_base_color`, `@theme_fg_color`, `@borders` and `@warning_color` are retained where appropriate.
- **Theme behavior:** `tests/test_app_lifecycle.py:131-149` verifies the `default`, `force-light` and `force-dark` mapping through the actual `Adw.StyleManager`. `tests/test_widgets.py:1001-1040` checks class continuity for downloaded language, History empty state and focus treatment through repeated theme transitions. This is targeted state coverage, not rendered-pixel validation across every surface or desktop theme.
- **Native control hierarchy:** Preferences and most list, dialog, search, popover and navigation structures use GTK4/Libadwaita components rather than recreating native controls.

## 5. Priority and M1-06 recommendation

| Priority | Finding | Disposition |
|---|---|---|
| P1 | F1 — reduced-motion omission on separate Shortcuts window | Recommend bounded M1-06 fix and regression test |
| P1 | F2 — no production-tree CI gate for the color scanner | Recommend bounded M1-06 test/CI integration and rationale map |
| P3 | F3 — apparently orphaned CSS selectors | Follow-up completed: tracked-file consumer audit found no production source consumers; unused rules/keyframes removed |
| P3 | F4 — undocumented `title`/`h4` typography roles | Follow-up completed: toolkit semantics and current use documented; no Blueprint change |

**M1-05 disposition: Completed.** The cross-surface inventory and evidence-backed findings are recorded. **M1 remains Partial** because F1 and F2 are demonstrated gaps and require a separately approved implementation. M1-06 remains conditional and is not authorized by this audit.

## 6. Evidence limits and exclusions

- This was a static source/template/documentation/test-definition audit at source SHA `fb1bcbe89f0ce982fc4adad60630a5a88496dd1`.
- No tests, local commands, GitHub Actions workflows or application runtime were executed as part of this audit.
- No GTK rendered-pixel contrast or theme snapshot comparison is claimed.
- Manual GNOME/GTK visual checks, real Orca/AT-SPI checks and manual keyboard-navigation checks remain excluded, not passed.
- Live multi-monitor geometry verification remains excluded.
- Screenshot capture remains deferred to the next release cycle.
- No application source, tests, workflows, CHANGELOG, dependencies, OCR behavior, architecture, protected branches or PR metadata were modified by M1-05.
- PR #648 was Open, Draft, unmerged, base `feature`, head branch `fix/ui-modernization-aligned` at the source snapshot checked for this audit.


## 7. M1 F3/F4 follow-up — 2026-11-17

This addendum resolves the two low-priority follow-ups without changing the scope or conclusions of the original M1-05 source snapshot.

### F3 — consumer audit and cleanup

- Temporary GitHub Actions run [#43981815120](https://github.com/D3M-Sudo/Anura/actions/runs/43981815120) completed successfully on branch `fix/ui-modernization-aligned`, commit `498f8de52cff7c4ea9d12f0ea9a9b19e913d81ce`. The job checked out that exact commit and ran `git grep` across all tracked files other than `data/style.css`.
- The search found no candidate class references in Python or Blueprint application sources. Matches were limited to the temporary workflow's own pattern, documentation/audit text, a historical CHANGELOG phrase, and Welcome screenshot/asset names. These substring matches are not runtime class consumers.
- The artifact [m1-f3-selector-audit](https://github.com/D3M-Sudo/Anura/actions/runs/43981815120/artifacts/14283985075) was uploaded successfully. A second earlier push-triggered audit run [#43981785415](https://github.com/D3M-Sudo/Anura/actions/runs/43981785415) also completed successfully on the preceding workflow commit.
- Removed from `data/style.css`: `.anura-pulse`, `.anura-spinner`, `.anura-toast`/`.hiding`, `.share-row`, `.welcome-page`, `.welcome-card`, `.language-popover`, `.language-row` and `.screenshot-btn.ready`; also removed their dedicated `pulse`, `spin`, `toastSlideIn`, `toastSlideOut` and `readyPulse` keyframes and obsolete reduced-motion references to `.share-row` and `.welcome-card`.
- No candidate was retained as a reserved future selector: the tracked repository and approved near-term plan supplied no justified consumer. Existing active application styles and animations were retained.
- **Limit:** a literal search of tracked files cannot exclude a class name assembled from fragments at runtime or supplied by an external integration. It does establish no direct textual consumer in the tracked application sources/resources at the audited commit.

### F4 — toolkit semantics and documentation

- The Libadwaita style-class reference documents `.title-1`–`.title-4` as the title hierarchy and `.heading` as the standard UI-heading style. It does not list `.title` or `.h4` as typography utility classes.
- GTK allows arbitrary CSS class names; the names `title` and `h4` do not, by themselves, guarantee a standard Libadwaita typographic role. The current `heading` class is supported; `title` on the LanguageRow label and `h4` on the Languages section label are documented as legacy/unverified styling hooks.
- `docs/ui-design-system.md` now records these roles and the relevant official GTK/Libadwaita references. No Blueprint code or class assignment was changed, consistent with the approved documentation-only F4 scope.

**Follow-up disposition:** F3 cleanup completed; F4 documentation completed. The original M1-05 audit remains historically valid for its stated snapshot. Neither follow-up closes global M1; cross-surface Design System adoption and verification remain broader work.
