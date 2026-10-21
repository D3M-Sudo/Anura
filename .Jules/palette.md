## 2026-09-21 - Synchronize SearchEntry Accessible Label with Match Occurrences Count
**Learning:** Screen readers cannot always detect changes in external search result count labels automatically without focus shifts or live regions. Dynamically updating the `Gtk.AccessibleProperty.LABEL` on the focused `Gtk.SearchEntry` widget itself whenever search occurrences change ensures screen readers announce search progress and match counts immediately as the user types or navigates matches.
**Action:** Always synchronize `Gtk.AccessibleProperty.LABEL` directly on search entries when search match counts update, and reset it to the default entry label when text is cleared.

## 2026-10-18 - Header Bar Destructive Action Button Sensitivity
**Learning:** Header bar action buttons for bulk/destructive operations (e.g. 'Clear all history') should dynamically update their sensitivity state (`set_sensitive(bool(items))`) based on whether the view contains actionable items. Disabling the button when empty prevents accidental or confusing trigger clicks that open empty confirmation dialogs.
**Action:** Always bind or update action button sensitivity (`set_sensitive`) during view refresh methods whenever underlying item collections can be empty.

## 2026-10-19 - Dynamic Accessible Label for Header Bar Language Selector Buttons
**Learning:** In GTK4 header bar menu buttons that act as state selectors (e.g. OCR language selector), setting a visible button text label alone is insufficient for screen readers and tooltips. Dynamically setting both `set_tooltip_text` and `Gtk.AccessibleProperty.LABEL` to include both the current active state and the click action prompt (e.g. 'OCR language: English (click to change)') ensures screen readers announce the complete state and interaction hint when focused.
**Action:** Always update both tooltip and `Gtk.AccessibleProperty.LABEL` with active item context and interaction guidance on header bar state selector buttons whenever the active selection changes.
