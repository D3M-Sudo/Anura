# Handover: UI modernization alignment

## Purpose

This document transfers the context required to continue the UI modernization work originally proposed in [PR #448](https://github.com/D3M-Sudo/Anura/pull/448), adapting it to the current `feature` branch rather than applying the old branch wholesale.

This handover records the adapted implementation and its remaining validation. The modernization work is now present on `fix/ui-modernization-aligned`; it was adapted against `feature` rather than copied wholesale from PR #448.

## Current Git state

- Repository: `D3M-Sudo/Anura`
- Working branch: `fix/ui-modernization-aligned`
- Target branch: `feature`
- Branch creation base: `894ca811a58302c8a6322a8207c04f77af00e5e9`
- The branch was initially created from the then-current `feature` baseline; the PR targets `feature` and carries the adapted modernization plus subsequent remediation commits.
- `feature` must remain untouched by this work until an explicit authorization changes that constraint.
- No merge is authorized.
- Original PR #448 must remain open and unchanged until its implementation has been recovered/adapted, reviewed, and its replacement contents are demonstrably present in the new PR.

## Original PR #448: source record

- Title: **UI/UX modernization: Extracted/Welcome/Preferences/History restyling**
- URL: https://github.com/D3M-Sudo/Anura/pull/448
- State at handover: open, not merged, not draft
- Original head: `feat/ui-modernization`
- Original head commit: `f5f07d9c1c8f1fff0bda350844d91ed8ef320a34`
- Original base: `testing`
- Original base commit: `28a705a6e93fbfc95b808defbaedd2526afe4868`
- Recorded diff: 16 files changed; the PR description records the following work.

### Original proposed changes

1. Set a fixed teal brand accent globally through `@accent_color`, intentionally overriding the system accent; fix the downloaded-language badge's hard-coded blue.
2. Fix GTK CSS keyframes using the combined `0%, 100%` selector in `style.css`.
3. Restyle Extracted: simplify the header actions and add a bottom action bar for Undo, Redo, Search, Listen, and Share.
4. Restyle Welcome: make Screenshot the primary action and group Open, Paste, and Drop as secondary actions; strengthen the hero.
5. Split Preferences into General, Editor, Voice, and Languages, including new Python page classes `PreferencesEditorPage` and `PreferencesVoicePage`.
6. Apply a visual-only restyle to History; the original PR explicitly says it does not change History row expansion logic.
7. Apply boxed-list/card styling to the Keyboard Shortcuts list.
8. Rewrite `test_preferences_page_resilience.py` to reflect the Preferences page split and isolate TTS setup failure.

The original PR reported no new external dependencies. It also reported that a complete Flatpak build and a real GNOME desktop visual verification had not been performed. It called out a Welcome-page overflow below 360px as unresolved.

### Exact original changed-file inventory

- `anura/widgets/preferences_dialog.py`
- `anura/widgets/preferences_editor_page.py`
- `anura/widgets/preferences_general_page.py`
- `anura/widgets/preferences_voice_page.py`
- `data/io.github.d3msudo.anura.gresource.xml`
- `data/meson.build`
- `data/style.css`
- `data/ui/extracted_page.blp`
- `data/ui/history_page.blp`
- `data/ui/preferences_dialog.blp`
- `data/ui/preferences_editor.blp`
- `data/ui/preferences_general.blp`
- `data/ui/preferences_voice.blp`
- `data/ui/shortcuts_overlay.blp`
- `data/ui/welcome_page.blp`
- `tests/test_preferences_page_resilience.py`

The authoritative source for the full historical patch is the original PR diff: https://github.com/D3M-Sudo/Anura/pull/448

## Decisions and constraints confirmed for the aligned remediation

- Work from the current `feature` baseline on `fix/ui-modernization-aligned`; do not blindly cherry-pick the old PR.
- Preserve `feature`; do not commit to or otherwise modify it.
- Open a new PR targeting `feature` in **Draft** state.
- Keep PR #448 open and unchanged until the replacement implementation and its validation evidence have been reviewed; closure is a separate decision requiring explicit authorization.
- Evaluate fixed teal against the GNOME/system accent before deciding; do not assume either choice.
- Produce updated screenshots and visual documentation for all relevant windows and major states.
- Remediate all findings from the prior audit, including architecture, accessibility, responsiveness, interactions, and maintainability.
- Functional changes are allowed when justified and verified; document invasive behavior changes and regression coverage.
- Plan comprehensive validation: pytest, Blueprint compiler, GTK/Gtk.Builder/Gtk.Template and resource integration, accessibility, interactions, lifecycle/cleanup, translations, Flatpak build and runtime, and visual checks.
- Update all affected documentation, including README, CHANGELOG, guides, technical documentation, cross-links, screenshots, and translation catalogs.
- User is the sole maintainer; do not impose an external second-maintainer approval requirement.
- No merge without explicit authorization.

## Integration risks already identified

The old PR predates important changes now present on `feature`. Its implementation must be reviewed against the current code rather than copied over.

- **History:** current `feature` includes History V2 work (PR #434) and subsequent behavior/lifecycle changes. Preserve current History V2 behavior; evaluate the old PR's visual changes independently.
- **History retention:** current branch includes the runtime limit work associated with #510 and Clear History integrity work associated with #540.
- **TTS catalog:** current branch includes asynchronous TTS catalog loading associated with #532. The old `PreferencesVoicePage` synchronously calls `get_tts_service().get_supported_languages()`; this must not regress or block UI initialization.
- **Preferences lifecycle:** current branch includes idle callback cleanup associated with #539 (`_pending_idle_sources`, `_disposed`, scheduling/cancellation lifecycle). Preserve and test these protections.
- **Welcome accessibility:** current branch includes accessibility work associated with #544. Preserve it and test keyboard/focus/drop behavior and narrow-window layout.
- **Resources/build:** verify Blueprint sources, GResource manifests, Meson registration, Python imports, and template/resource loading as one coherent change.
- **Translations:** verify that newly introduced Python and Blueprint strings are included in the translation extraction/catalog workflow. Inspect `po/POTFILES` and generated catalogs rather than assuming the original PR's files are covered.
- **Accent policy:** check interaction with GNOME/system accent preferences and document the decision.

These are integration constraints, not a claim that the current branch has already passed a fresh verification run.

## Required continuation plan

1. Re-read current implementations on `feature` for every affected file and inspect the original PR patch side by side.
2. Build a per-file migration matrix: adopt, adapt, redesign, or reject each old change, with rationale.
3. Implement the accepted changes only on `fix/ui-modernization-aligned`.
4. Add/update regression tests, including the current async TTS, History V2, Preferences lifecycle, Welcome accessibility, and resource/translation paths.
5. Complete the visual review and capture the agreed screenshots; cover empty, populated, loading, error, confirmation, and disabled states where applicable.
6. Update documentation and CHANGELOG, then validate internal links and cross-references.
7. Run the complete available test/build/runtime matrix and record exact commands, results, and environment limitations.
8. Update the Draft PR with the implementation, migration rationale, screenshots, and evidence.
9. Only after confirming that the replacement PR contains the required implementation and supporting context should PR #448 be considered for closure. Closing it requires an explicit, evidence-based replacement rationale; do not close it merely because this handover exists.

## Validation status at handover

- Branch creation and initial equality with `feature`: verified at branch creation; current comparison is recorded in PR #648.
- PR #448 metadata and full diff: retrieved; its changed-file inventory contains 16 paths.
- The maintainer supplied a local validation report for head `90391da9ee5ac198869753744d3cfb1552868627`: all 14 Blueprint files compiled; GResource and GSettings schema validation passed; Ruff check/format and changelog integrity passed; headless pytest reported 595 passed, 5 skipped and 238 deselected; GTK tests under Weston reported 382 passed, 5 skipped and 600 deselected when `ANURA_CI_TEST_MODE` was unset.
- The same report exposed the PyGObject 3.48.2 incompatibility with `Gio.Settings.bind_with_mapping`. The implementation now uses explicit `get_double`/`set_double` synchronization, with reverse updates for external GSettings changes.
- Regression tests now exercise normalized volume persistence and external setting changes. A new GTK integration test instantiates the real PreferencesDialog using a memory-backed Gio.Settings backend; neither the updated tests nor this integration test has yet been run in the current session.
- The original teal's reported contrast failures were addressed by separating the darker suggested-action background from theme-aware text accents. Contrast calculations support the selected values, but a real light/dark desktop visual check remains outstanding.
- Current-head CI, real GNOME desktop accessibility/keyboard checks, Flatpak/AppImage builds and aarch64 validation remain outstanding and must be checked before the PR leaves Draft.
- No merge has been performed.
## Closure rationale for the original PR

**Do not close PR #448 at this stage.** The aligned PR now contains the adapted modernization implementation, but current-head CI, real desktop interaction/accessibility validation, packaging checks and final diff review remain outstanding. Reassess closure only after those gates pass and the replacement is demonstrably complete; closing #448 still requires explicit authorization.
