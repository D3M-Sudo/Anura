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

- Branch creation and initial equality with `feature`: verified at branch creation.
- PR #448 metadata and full diff: retrieved.
- PR #448 changed-file inventory: retrieved (16 paths).
- PR #448 issue comments, review submissions, and inline review threads: none returned by the connector at handover.
- Local repository checkout and GTK/Blueprint/Flatpak runtime environment: unavailable in the session used to create this handover.
- The adapted implementation is present on this branch, including the Preferences page split, extracted/welcome layout changes, History and Shortcuts styling, resource registration, translation extraction entries and regression tests.
- No pytest, Blueprint, GTK, accessibility, translation, Flatpak, runtime, or screenshot validation is claimed as completed.
- No merge has been performed.

## Closure rationale for the original PR

**Do not close PR #448 at this stage.** The aligned PR now contains the adapted modernization implementation, but current-head CI, real desktop interaction/accessibility validation, packaging checks and final diff review remain outstanding. Reassess closure only after those gates pass and the replacement is demonstrably complete; closing #448 still requires explicit authorization.
