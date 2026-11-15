# Anura M2-B Task 4 Accessibility Remediation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Implement the approved A1–A5 accessibility remediations on the existing Anura UI modernization branch.

**Architecture:** Keep GTK's native accessible roles and value reporting. Centralize screen-reader announcements in a small utility, with callers responsible for announcing semantic transitions rather than high-frequency progress. Bind reduced-motion CSS to read-only GTK settings and keep theme-managed text colors intact.

**Tech Stack:** Python 3.12+, PyGObject, GTK 4, Libadwaita, Blueprint, pytest, existing GitHub Actions CI.

**Spec:** docs/superpowers/specs/2026-11-15-anura-m2b-accessibility-design.md

## Global Constraints

- Work only on fix/ui-modernization-aligned; PR #648 targets feature and remains Draft.
- Do not modify feature, development, testing or main.
- Do not merge, publish a release or add dependencies.
- Preserve existing accessibility labels, focus handling, OCR/TTS lifecycle and History V2 behavior.
- Manual GNOME/GTK visual, Orca/AT-SPI and manual keyboard checks remain excluded.
- Update CHANGELOG.md and HANDOVER.md; record automated and manual-validation limitations accurately.

## Review Focus

- GTK 4.14 CI versus GTK 4.22+ reduced-motion property availability — test fallback and preferred property paths.
- High-frequency OCR/search/download updates — assert announcements are deduplicated or debounced.
- Responsive Welcome action reparenting — assert focus remains on a visible, meaningful control.
- Disabled and secondary text — ensure app CSS does not override Adwaita theme semantics.
- Progress-bar value semantics — assert the language label does not replace native progress value reporting.

---

### Task 1: Language download progress accessibility (A1)

**Files:**
- Modify: anura/widgets/language_row.py
- Modify: data/ui/language_row.blp only if a static accessibility declaration is needed
- Create: tests/test_language_row_accessibility.py

**Interfaces:**
- Consumes: LanguageRow.item, LanguageRow.late_update(), LanguageManager downloading, downloaded, and download-failed signals.
- Produces: a progress bar named with translated language context; native fraction remains the progress value.

- [ ] Write tests test_progress_bar_accessible_name_includes_language, test_download_announcements_skip_percentage_updates, and test_download_completion_and_failure_are_announced.
- [ ] Run uv run pytest tests/test_language_row_accessibility.py -q; expected RED on missing accessible naming/announcement behavior.
- [ ] Set Gtk.AccessibleProperty.LABEL to a translated Download {language} label when the row item is assigned.
- [ ] Announce download start once, and completion/failure once; never announce each percentage.
- [ ] Re-run the focused test file; expected GREEN.

### Task 2: OCR, TTS and search status announcements (A2)

**Files:**
- Create: anura/utils/accessibility.py
- Modify: anura/widgets/welcome_page.py
- Modify: anura/widgets/extracted_page.py
- Create: tests/test_accessible_status_announcements.py
- Modify: po/POTFILES only if a new translatable Python module contains gettext strings.

**Interfaces:**
- Produces: announce_accessible(widget, message, priority); no-op for empty/unrooted targets.
- OCR announces only changed status text; TTS announces generating/playing/paused/stopped transitions; search announces settled result counts after a debounce.

- [ ] Write tests test_ocr_status_announces_only_changed_messages, test_tts_announces_state_transitions_without_idle_noise, and test_search_result_announcement_is_debounced.
- [ ] Run uv run pytest tests/test_accessible_status_announcements.py -q; expected RED.
- [ ] Implement the GTK announcement helper and semantic state transitions.
- [ ] Cancel pending search announcement sources on query clear and widget destruction.
- [ ] Re-run the focused test file; expected GREEN.

### Task 3: Focus traversal and responsive restoration tests (A3)

**Files:**
- Modify: tests/test_audit_ui_widgets.py
- Modify: tests/test_welcome_page_accessibility.py only if a focused unit regression is useful.
- Modify: anura/widgets/welcome_page.py only if an automated regression demonstrates a real focus defect.

**Interfaces:**
- Consumes: WelcomePage._set_action_layout(), _focus_more_options_idle(), _focus_widget_idle(), and the actual GTK widget tree.
- Produces: display-backed regression coverage for initial tab traversal, wide/compact focus order and focus restoration after reparenting.

- [ ] Write GTK tests test_welcome_initial_tab_focus_is_language_selector, test_welcome_wide_action_focus_order, test_welcome_compact_action_focus_order, and test_welcome_focus_restores_after_responsive_reparenting.
- [ ] Run the focused tests in the existing Weston-backed GTK CI tier; expected RED for any uncovered behavior.
- [ ] Make only the smallest behavior correction required by a reproduced failure.
- [ ] Re-run the focused GTK tests; expected GREEN.

### Task 4: Reduced-motion preference support (A4)

**Files:**
- Modify: anura/window.py
- Modify: data/style.css
- Create: tests/test_reduced_motion.py

**Interfaces:**
- Produces: a reduced-motion CSS class on the application window, synchronized with GTK settings.
- Prefer gtk-interface-reduced-motion when the property exists; otherwise respect gtk-enable-animations. Never write to either global setting.

- [ ] Write tests test_reduced_motion_uses_interface_preference_when_available, test_reduced_motion_falls_back_to_enable_animations, test_reduced_motion_class_tracks_setting_changes, and test_reduced_motion_css_disables_custom_motion.
- [ ] Run uv run pytest tests/test_reduced_motion.py -q; expected RED.
- [ ] Implement the setting adapter, signal lifecycle and CSS overrides for Anura-authored transitions/keyframes.
- [ ] Re-run the focused tests; expected GREEN.

### Task 5: Expanded contrast and theme-role coverage (A5)

**Files:**
- Modify: tests/test_ui_palette.py
- Modify: data/style.css only if an explicit application-controlled color fails the approved contrast thresholds.

**Interfaces:**
- Consumes: existing palette helpers and CSS selectors for downloaded, focus, disabled, processing and custom UI states.
- Produces: a contrast matrix for application-controlled foreground/background pairs, plus assertions that secondary and disabled text remain theme-managed.

- [ ] Add tests for focus-indicator contrast on light/dark surfaces, downloaded text, suggested-action text, processing-state semantics, secondary text and disabled controls.
- [ ] Run uv run pytest tests/test_ui_palette.py -q; expected RED for missing coverage or an actual contrast defect.
- [ ] Correct only application-controlled colors that fail the relevant 3:1 graphical or 4.5:1 normal-text threshold.
- [ ] Re-run the focused test file; expected GREEN.

### Task 6: Documentation and final verification

**Files:**
- Modify: CHANGELOG.md
- Modify: HANDOVER.md
- Update: this plan with completion/evidence notes.

- [ ] Record A1–A5 implementation, exact commits and CI run URLs/results.
- [ ] Run the full existing PR CI matrix on the final branch head; read each job conclusion.
- [ ] Re-check PR #648 state/head/base and compare feature with fix/ui-modernization-aligned.
- [ ] Confirm protected branch SHAs are unchanged and PR remains open/Draft/unmerged.
- [ ] Run a final whole-branch self-review; no subagent reviewer is available in this environment.

## Verification Commands

- Headless tier: uv run pytest tests/ -m "not gtk" --cov=anura --cov-report=term-missing (the workflow applies its documented ignore list).
- GTK tier: uv run pytest tests/ -m gtk -v --timeout=30 --override-ini "addopts=-v --tb=short" under the existing Weston CI setup.
- Static checks: existing Ruff, formatter, mypy, Bandit, changelog-integrity and CodeQL jobs.

## Execution Notes

- The local container cannot resolve GitHub; the linked GitHub repository connector is the available repository interface. Use the existing PR's GitHub Actions runs as the test execution environment; do not claim local tests were run.
- The working branch is the isolated feature branch. Use expected-head checks when advancing its ref.
- If a workflow does not trigger on a branch update, do not invent a workflow or bypass the CI gate; inspect the existing PR checks and use the established repository process.
