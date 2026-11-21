# Anura M2-B Task 2 — Palette Design

## Intent
Consolidate the approved green palette in the existing GTK stylesheet so the UI modernization uses a consistent accent hierarchy in light and dark color schemes without redesigning screens.

## Approved color roles
- `#16A36A`: primary brand accent for non-text accents, icons, borders and feedback.
- `#0F7650`: dark accent for text on light surfaces and suggested-action backgrounds paired with white foreground text.
- `#21B77A`: text accent on dark surfaces.

## Goals
- Keep the existing global Adwaita accent-token integration.
- Preserve Screenshot as the Welcome page's primary suggested action.
- Keep hover, active, focus and disabled button states perceptible.
- Validate the text and graphical contrast roles against light and dark Adwaita surfaces.
- Add automated regression coverage without introducing dependencies.

## Non-goals
- No screen redesign or layout changes.
- No changes to OCR, navigation, application behavior or user preferences.
- No new runtime or development dependencies.
- No real-desktop, keyboard or Orca/AT-SPI validation in this task; those checks are explicitly skipped.

## Constraints
- Work only on `fix/ui-modernization-aligned`; do not write to `feature`.
- Keep PR #648 open and Draft. Do not merge.
- Preserve existing GTK/Adwaita defaults except for the approved accent roles and the narrowly scoped button state rules.
