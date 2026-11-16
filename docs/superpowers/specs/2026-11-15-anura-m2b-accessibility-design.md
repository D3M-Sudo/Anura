# Anura M2-B Task 4 — Accessibility Remediation Design

**Date:** 2026-11-15  
**Status:** Approved by the maintainer; implementation authorized.

## Intent

Close the source-level accessibility gaps found in the M2-B Task 4 audit while preserving the accessibility groundwork already present in Welcome, Extracted, Preferences and History. The goal is to provide meaningful names for language-download progress, concise announcements for asynchronous status changes, automated focus regression coverage, motion-preference handling for application-authored CSS, and broader contrast regression coverage.

## Goals

- Give every language download progress bar a translated, language-specific accessible name while retaining GTK's native progress value.
- Announce meaningful OCR, TTS, search and language-download state changes without announcing every progress tick or every keystroke.
- Protect focus order, initial keyboard traversal and focus restoration across Welcome's responsive action reparenting.
- Respect the GTK reduced-motion preference for application-authored CSS transitions and keyframe animations.
- Extend contrast tests to the custom palette, downloaded/processing states, focus indicators, secondary text and disabled controls in light and dark schemes.

## Non-goals

- No broad accessibility rewrite or new dependency.
- No claim of runtime screen-reader conformance based on source tests.
- No manual GNOME/GTK visual review, Orca/AT-SPI session or manual keyboard verification; these remain explicitly excluded.
- No changes to OCR/TTS business logic, model downloads or user preferences beyond accessible feedback and motion adaptation.
- No merge and no changes to protected branches.

## Approved approaches

1. **Accessible announcements:** use GTK's Gtk.Accessible.announce() API (available from GTK 4.14) rather than inventing a custom live-region mechanism. Announce semantic state transitions only; debounce search-result announcements and never announce each download percentage.
2. **Reduced motion:** GTK's native widget transitions respect toolkit animation settings, but Anura also defines its own CSS transitions and keyframe animations. Add an application-window CSS class driven by Gtk.Settings: prefer gtk-interface-reduced-motion when available (GTK 4.22+), and fall back to gtk-enable-animations on older GTK 4 versions. Do not modify the global setting.
3. **Focus and contrast:** preserve the existing widget hierarchy and theme-managed colors. Add automated GTK focus traversal/reparenting tests and a contrast matrix for explicit application colors; verify secondary/disabled theme roles are not overridden by application CSS.

## Constraints and implementation decisions

- Work only on fix/ui-modernization-aligned; PR #648 remains Draft and targets feature.
- Keep feature, development, testing and main unchanged.
- Use the existing GTK/PyGObject/Libadwaita stack; no dependencies.
- Use test-first changes. Run the headless Python test tier and Weston-backed GTK integration tier through the PR's existing GitHub Actions workflows.
- Add new user-visible strings to gettext extraction inputs where needed; update CHANGELOG.md and HANDOVER.md.
- Treat CI as automated evidence only. The excluded manual checks must not be reported as performed.

## Acceptance

A1–A5 are implemented with regression tests; relevant CI jobs pass on the final branch head; documentation records exact evidence and remaining limitations; PR #648 remains open, Draft and unmerged.
