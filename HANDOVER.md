# Handover: UI modernization alignment

## Purpose

This document transfers the context required to continue the UI modernization work originally proposed in [PR #448](https://github.com/D3M-Sudo/Anura/pull/448), adapting it to the current `feature` branch rather than applying the old branch wholesale.

This handover records the adapted implementation and its remaining validation. The modernization work is now present on `fix/ui-modernization-aligned`; it was adapted against `feature` rather than copied wholesale from PR #448.

> **Roadmap hierarchy:** the [Global Anura UI/UX Modernization Roadmap](docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md) is the primary plan for the complete application-wide M0–M7 modernization, all windows/components and global requirement traceability. The [PR #648 workstream roadmap](docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md) is subordinate and preserves detailed implementation/task/CI evidence for that PR only. This handover remains the technical/history record. After every completed task, update the global roadmap—and the PR #648 workstream roadmap when relevant—before starting another task.

## Current Git state

- **Global modernization plan:** [M0–M7 Global Roadmap](docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md).
- **PR #648 detailed workstream:** [PR #648 Roadmap](docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md). Its completion records only the contribution made by this PR and is not evidence that all application windows have been modernized.

- Repository: `D3M-Sudo/Anura`
- Working branch: `fix/ui-modernization-aligned`
- Target branch: `feature`
- Branch creation base: `894ca811a58302c8a6322a8207c04f77af00e5e9`
- The branch was initially created from the then-current `feature` baseline; the PR targets `feature` and carries the adapted modernization plus subsequent remediation commits.
- `feature` must remain untouched by this work until an explicit authorization changes that constraint.
- No merge is authorized.
- Original PR #448 has been closed as superseded by PR #648 after confirming that its relevant implementation was adapted and transferred. Keep the original diff as historical reference; do not reopen it without explicit authorization.

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
- PR #448 is closed as superseded by PR #648; its original diff remains the historical source record.
- Retain the fixed green brand palette while separating the darker suggested-action background color from text accents; use theme-aware text colors for light and dark surfaces.
- Complete the visual review across relevant windows and major states. Updated screenshots and visual documentation are deferred to the next release cycle as agreed.
- Remediate all findings from the prior audit, including architecture, accessibility, responsiveness, interactions, and maintainability.
- Functional changes are allowed when justified and verified; document invasive behavior changes and regression coverage.
- Plan comprehensive validation: pytest, Blueprint compiler, GTK/Gtk.Builder/Gtk.Template and resource integration, accessibility, interactions, lifecycle/cleanup, translations, Flatpak build and runtime, and visual checks.
- Update all affected documentation, including README, CHANGELOG, guides, technical documentation, cross-links and translation catalogs. Screenshot assets remain deferred to the next release cycle.
- User is the sole maintainer; do not impose an external second-maintainer approval requirement.
- No merge without explicit authorization.


## OCR request ownership and spinner lifecycle

The agreed concurrency policy is **latest operation started wins**. Starting a new file, clipboard, screenshot or drag-and-drop request immediately invalidates the previous request, including work still loading input or waiting for screenshot capture. The window assigns a monotonically increasing operation ID and publishes it to the screenshot backend before cancelling prior work, so even synchronous cancellation callbacks from the previous provider are already stale.

- File loading and clipboard OCR propagate the operation ID through `AtomicTaskManager`; in-memory decoding publishes GObject signals only from a lane-validated callback.
- Screenshot capture callbacks, portal URI resolution, isolated OCR results, status/errors and queued navigation all check the active operation ID. URI parsing runs outside `OCR_LANE`; isolated OCR starts on the GTK thread only after the parser-lane callback is validated, avoiding nested tasks superseding one another in the same lane.
- Drag-and-drop claims ownership at the initial drop event, carries the ID through both asynchronous stream callbacks, and ignores stale read failures/results. Starting any other OCR request cancels a pending DnD stream read.
- Spinner visibility is released only by the active operation. DnD visual reset is separate from spinner ownership; clipboard and invalid-drop errors cannot hide another request's spinner.
- Regression coverage includes stale capture callbacks, queued signal delivery, superseded spinner cleanup, generation publication before cancellation, DnD token propagation and screenshot service cancellation/fallback behavior.
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
5. Complete the visual review; cover empty, populated, loading, error, confirmation, and disabled states where applicable. Screenshot capture remains deferred to the next release cycle as agreed.
6. Update documentation and CHANGELOG, then validate internal links and cross-references.
7. Run the complete available test/build/runtime matrix and record exact commands, results, and environment limitations.
8. Update the Draft PR with the implementation, migration rationale and validation evidence; screenshot assets remain deferred as agreed.
9. Keep PR #648 as the active continuation. PR #448 has already been closed with the explicit replacement rationale recorded in PR #648; do not reopen or merge either PR without authorization.

## Validation status

- PR #648 remains open and Draft, targeting `feature`; working branch `fix/ui-modernization-aligned`.
- Current comparison at validated head `045bb368c4f7c566cac8c52eb715becfd360d845` against `feature` commit `4a967caf3dc5392308dbb99e3d2f419947abe2bd`: 192 commits ahead, 0 behind.
- Temporary M2-B Welcome validation run #43721302302 passed: Blueprint/GResource/GSettings compilation and Weston headless startup; 25 GTK tests passed (2 warnings); 4 Welcome accessibility tests passed.
- Main CI run #43721302304 passed: Changelog integrity, Python quality, GTK Integration (391 passed, 5 skipped, 613 deselected, 1 warning), AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and release-artifact validation. `publish-release` was skipped.
- CodeQL run #43721302253 passed.
- The temporary workflow `.github/workflows/m2b-welcome-validation.yml` was used to obtain focused evidence, and its results/logs were reviewed and recorded in PR #648 and this handover before the workflow was removed. GitHub Actions retains the run history.
- The main GTK workflow's Weston surface was increased to 1920×1080 to represent the 1280×800 test viewport; this permanent CI adjustment remains.
- The CHANGELOG already describes the final Welcome responsive behavior accurately; the changelog-integrity job passed, so no duplicate entry was added.
- The four viewport cases (360×600, 640×480, 900×600, 1280×800), measured breakpoint, Screenshot primary-action invariant and focus fallback tests passed.
- Automated accessibility tests are not real assistive-technology verification: the temporary workflow set `NO_AT_BRIDGE=1` and `GTK_A11Y=none`.
- Real GNOME/GTK visual review, Orca/AT-SPI, keyboard navigation/focus order and desktop light/dark checks were not performed: the user explicitly chose to skip manual verification. They are not represented as passed or used as a blocker for continuing the automated M2-B work.
- No merge has been performed or authorized.

## Closure rationale for the original PR

**PR #448 is closed as superseded by PR #648.** The relevant modernization work was adapted to the current `feature` baseline and transferred to `fix/ui-modernization-aligned`, preserving later functionality and lifecycle protections. PR #648 remains the active Draft continuation; its remaining CI, packaging, baseline synchronization and real-desktop validation gates are independent of the closure of #448.


## M2-B Task 1 — Welcome Page responsive implementation update (2026-11-15)

### Implementation and automated validation

- Screenshot remains the primary action.
- Open Image, Paste Image and Drop Image are the same three controls in both layouts: a homogeneous horizontal row when their measured preferred widths, spacing and margins fit; otherwise they are presented in the More options popover.
- The action controls are reparented, not duplicated. The full-page `DropTargetAsync` remains attached to the Welcome page.
- The action area uses an `Adw.Clamp` and vertical `Gtk.ScrolledWindow`; the measured width is monitored through a GTK frame-clock callback. Focus is restored after reparenting with idle callbacks.
- The main GTK workflow's Weston headless surface is 1920×1080 so the 1280×800 M1 viewport test has a sufficiently large virtual output.
- Temporary focused validation [run #43721302302](https://github.com/D3M-Sudo/Anura/actions/runs/43721302302) passed: 25 GTK tests (2 warnings), 4 Welcome accessibility tests, Blueprint compilation, GResource/GSettings compilation and Weston startup.
- Main CI [run #43721302304](https://github.com/D3M-Sudo/Anura/actions/runs/43721302304) passed: 391 GTK integration tests, Python quality, changelog integrity, AppImage x86_64/aarch64 and Flatpak x86_64/aarch64 validation. Release publication was skipped.
- CodeQL [run #43721302253](https://github.com/D3M-Sudo/Anura/actions/runs/43721302253) passed.
- The temporary focused workflow was removed after recording its evidence in PR #648 and this handover. Its historical GitHub Actions run remains accessible.
- The CHANGELOG already contains the accurate Welcome responsive entry; no duplicate was added.

### Remaining gates

- Perform real GNOME/GTK visual and interaction checks, including Orca/AT-SPI, keyboard navigation and focus order.
- Confirm the green appearance in light and dark themes on a real desktop session.
- The temporary workflow disables AT-SPI via `NO_AT_BRIDGE=1` and `GTK_A11Y=none`; its passing tests are not a substitute for screen-reader verification.
- Keep PR #648 Draft. This Task 1 validation did not authorize a merge or Task 2; Task 2 was subsequently authorized and is recorded below.


## M2-B Task 2 — Design System palette and runtime stylesheet (2026-11-15)

### Approved palette and implementation

- Applied the approved green tokens in `data/style.css`: `accent_color #16A36A`, `accent_bg_color #0F7650`, and `accent_fg_color #FFFFFF`.
- Downloaded-language text uses `#0F7650` on light surfaces and `#21B77A` on dark surfaces. The suggested-action foreground remains white on the darker green background.
- Added explicit focus and disabled rules for `.anura-button`; Screenshot remains the Welcome page's suggested-action primary control.
- Root cause of the inert stylesheet: `style.css` was packaged in the GResource but no application startup path created and registered a `Gtk.CssProvider`.
- Added `load_css_provider()` in `anura/core/resources.py`: it loads `/io/github/d3msudo/anura/style.css` from GResource and registers the provider on the default GDK display at `Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION`.
- `AnuraApplication.do_startup()` invokes the loader and retains the provider in `self._css_provider` for the application lifetime. A missing display is handled as a display-less CLI invocation and does not abort startup.
- Added GTK regression coverage in `tests/test_audit_ui_widgets.py`: one test loads the real GResource stylesheet and registers its provider on the active display; a second test verifies that a missing display returns `None` without raising. `tests/test_app_lifecycle.py` also verifies that `AnuraApplication` retains the provider returned by the loader.
- Added a CHANGELOG entry and corrected the current palette description from teal to green.

### Test-first and CI evidence

- The new GTK regression test was first run without the implementation and failed as expected with `ImportError: cannot import name 'load_css_provider'`.
- After implementation, the same test passed.
- Python quality job on implementation head `01a97fed9bf92a51741013799199006b64e4e009`: 611 passed, 6 skipped, 241 deselected; Ruff, formatting, mypy, Bandit and Flatpak dependency coverage passed.
- GTK Integration Tests on the same head: 394 passed, 5 skipped, 617 deselected; both stylesheet-provider and no-display tests passed. One pre-existing warning was reported from Blueprint compiler (`invalid escape sequence '\\
- Changelog integrity passed on the implementation head; CodeQL run #43744308755 passed on that head.
- AppImage x86_64/aarch64 jobs were still running on implementation head `01a97fed9bf92a51741013799199006b64e4e009` when this handover update was prepared. An earlier code-equivalent run built both AppImage architectures and validated the complete AppImage release set successfully. Flatpak x86_64/aarch64 jobs were still running; consult the current CI run for their final results before making a release-readiness claim.
- No local desktop visual review, Orca/AT-SPI or manual keyboard checks were performed; this follows the user's explicit decision to skip manual verification and is not claimed as automated coverage.

### Current repository state

- PR #648 remains open and Draft, targeting `feature`; no merge was performed.
- The PR branch was rebased onto the current `feature` baseline without changing `feature`; compare the current PR head with `feature` for the latest ahead/behind count.
- The temporary authorized-rebase workflow was removed after use. No temporary validation workflow was added for this task.
`).
- Changelog integrity and CodeQL passed on the documented head.
- AppImage x86_64/aarch64 and Flatpak x86_64/aarch64 build jobs were still running when this handover update was prepared; consult the linked CI run for their final results before making a release-readiness claim.
- No local desktop visual review, Orca/AT-SPI or manual keyboard checks were performed; this follows the user's explicit decision to skip manual verification and is not claimed as automated coverage.

### Current repository state

- PR #648 remains open and Draft, targeting `feature`; no merge was performed.
- The PR branch was rebased onto the current `feature` baseline without changing `feature`; at the time of this record it was 214 commits ahead and 0 behind.
- The temporary authorized-rebase workflow was removed after use. No temporary validation workflow was added for this task.

## M2-B Task 3 — Shell geometry implementation update (2026-11-15)

### Implemented

- Main Window: the initial-size helper now clamps to 90% of the selected monitor geometry while adapting its minimum dimensions down to the available bounds. Removed the fixed 360×360 Blueprint size requests that could override the clamp.
- Monitor selection: before the native surface exists, choose the connected monitor with the largest geometry instead of assuming monitor index 0. After realization, use Gdk.Display.get_monitor_at_surface() to identify the monitor actually containing the window.
- Monitor changes: track Gdk.Surface::enter-monitor and re-clamp the current dimensions when the window enters another monitor.
- Window state: persist width and height only when the window closes in its normal state; maximized and fullscreen dimensions are not stored.
- Extracted: the existing HeaderBar was already compact (two start-side actions and one end-side menu action); a regression test records that structure. Existing scroll/reflow behavior is preserved.
- Preferences: removed fixed width/height requests so the dialog can adapt to narrower viewports while retaining its preferred content size.
- Shortcuts: made the overlay resizable. Its existing Gtk.ScrolledWindow and automatic vertical scrollbar remain in place.

### Platform constraint

GTK 4's Gdk.Monitor exposes monitor geometry but does not provide a separate work-area API for excluding panels and docks. The implementation therefore clamps against monitor geometry and does not claim a universal panel/dock-aware work-area calculation. The actual surface monitor is resolved after realization; the largest-monitor fallback is used only before that point.

### Test-first and CI evidence

- G1 RED: the initial small-monitor and Blueprint-minimum tests failed as expected (320×240 returned for a 300×250 monitor; fixed 360px requests remained in the Blueprint).
- G1 GREEN: after the clamp and Blueprint changes, the GTK job passed both regressions and the four viewport cases.
- G2/G4/G6 RED: the monitor-selection, monitor-size, normal-state persistence, resizable Shortcuts and Preferences minimum-size tests failed before their implementation; the compact Extracted HeaderBar contract passed.
- G2/G4/G6 GREEN: CI run [#43748956043](https://github.com/D3M-Sudo/Anura/actions/runs/43748956043) passed Python quality, Changelog integrity and GTK Integration Tests. GTK result: **410 passed, 5 skipped, 617 deselected**, 2 warnings. The final two tests guard the existing Extracted text scroller and History entry-list scroller.
- Python quality on that run passed Ruff, formatting, type checking, Bandit and the Python test suite. CodeQL run [#43748956079](https://github.com/D3M-Sudo/Anura/actions/runs/43748956079) passed.
- AppImage x86_64/aarch64 and Flatpak x86_64/aarch64 jobs were still running when this entry was written; consult the latest PR CI run before claiming full packaging validation.

### Remaining validation and repository state

- Manual GNOME/GTK visual review, Orca/AT-SPI and keyboard checks were explicitly skipped at the user's request and are not claimed as completed.
- PR #648 remains open and Draft, targeting feature. No merge was performed.
- The implementation is confined to fix/ui-modernization-aligned; feature, development, testing and main were not modified.


## M2-B Task 4 — Accessibility remediation implementation (2026-11-15)

### Implemented A1–A5

- **A1 — Language downloads:** each Gtk.ProgressBar receives a translated accessible label containing the language name. Native progress reporting remains intact through set_fraction(). Download start is announced once, completion/failure once; percentage updates are not announced.
- **A2 — Status announcements:** added anura.utils.accessibility.announce_accessible() with a mapped-widget guard and announcement priority. Welcome OCR status announces distinct phases only; TTS announces generating/playing/paused transitions on the visible navigation page; search-result counts are announced at low priority after a 400 ms debounce. Pending search announcements are cancelled on query changes/clear and widget destruction.
- **A3 — Focus traversal:** added Weston-backed GTK tests for initial tab focus, wide/compact action traversal, responsive focus restoration, and focus transfer from More options to Screenshot. No production focus correction was needed. An initial compact-layout test used child_focus() on the local Gtk.Box, which did not model the actual window-level tab traversal; the regression test now exercises Gtk.Window.child_focus() and passes.
- **A4 — Reduced motion:** the application reads gtk-interface-reduced-motion when present and falls back to gtk-enable-animations; it updates an application CSS class on GTK setting notifications and does not write desktop-wide settings. GTK's GtkReducedMotion and GtkSettings:gtk-interface-reduced-motion are available since GTK 4.22; older supported GTK builds use the fallback.
- **A5 — Contrast/theme roles:** focus indicators and History empty-state icons now use scheme-aware green shades. Tests cover 3:1 graphical contrast, downloaded text, suggested-action text, processing-state semantics, and preservation of theme-managed secondary/disabled text.

### Test-first and CI evidence

- The accessibility regression tests were introduced before the implementation. Python-quality run #43758437418 on test-first commit d3ce6efca882b0f801f7e00c8426b266e071a1fd failed on the expected missing A1/A2/A4/A5 behavior (download label/announcements, status announcements, reduced-motion support and contrast rules).
- Implementation commit: 21dbb3c69527558b0f5047a45cd3f690b773f54a.
- Final code/test head at the time of this record: 38ecb348c741b87b4e5c886f8770b84a40bbac99.
- Python quality on run #43760732944: 626 passed, 6 skipped, 262 deselected; Ruff, formatting, mypy, Bandit and Flatpak runtime dependency coverage passed.
- Weston-backed GTK Integration Tests on the same run: 416 passed, 5 skipped, 632 deselected, 2 warnings.
- Changelog integrity passed. CodeQL run #43760732956 passed.
- AppImage x86_64 and aarch64 builds, architecture/update-metadata checks and clean-host smoke tests passed; complete multi-architecture AppImage release-set validation passed.
- Flatpak aarch64: all 22 steps passed in job #132955104373 of run #43760732944, including no-source-download build, Blueprint/resource checks, headless runtime, GI typelibs, positive and negative sandbox OCR tests, desktop/AppStream validation and licence inventory. Flatpak x86_64: failed before the application build in original job #132955104383 and failed again in rerun #132959138004 and final documentation-head job #132959229160. The logs consistently report OSTree Invalid cross-device link while updating org.gnome.Sdk, followed by xvfb-run exit 139. These failures occur before Anura's application build and are treated as a runner/runtime-update issue; no project workaround was introduced.

### Validation boundaries and repository state

- Manual GNOME/GTK visual review, Orca/AT-SPI and manual keyboard checks remain explicitly excluded; no claim of screen-reader runtime conformance is made. The focus checks above are automated Weston-backed tests.
- PR #648 remains open and Draft, targeting feature; no merge was performed.
- The implementation and test changes are confined to fix/ui-modernization-aligned. feature remains at cb079b0b55e252a7ac054fe1b6f57030ddc7b1f9; compare reported 264 commits ahead and 0 behind. No protected branch was modified.


### Flatpak retry outcome

- The x86_64 Flatpak retry reproduced the original failure: the GNOME SDK/runtime update hit OSTree Invalid cross-device link and xvfb-run exited 139 before Anura was built.
- The independent final documentation-head x86_64 job reproduced the same pre-build failure. This is consistent across the original run, retry and final-head run; no source-code or manifest change is justified by this evidence.
- The aarch64 Flatpak job completed all 22 validation steps successfully on the code-equivalent implementation head, including offline rebuild, sandbox smoke tests, both OCR functional cases and licence inventory.

## M2-B Task 4 — Final CI completion (2026-11-15)

- Final PR workflow [#43762681835](https://github.com/D3M-Sudo/Anura/actions/runs/43762681835) completed with overall conclusion **success** on branch `fix/ui-modernization-aligned`, head `f4979df9bc82dc60e23c82d77d674d9a0862ad95`, targeting `feature` at `cb079b0b55e252a7ac054fe1b6f57030ddc7b1f9`.
- All 9 executable jobs in the CI Quality Check & Release run passed: Changelog integrity; Python quality; GTK Integration Tests; AppImage x86_64; AppImage aarch64; Flatpak x86_64; Flatpak aarch64; complete AppImage release-set validation; and multi-architecture Flatpak release-artifact validation. The separate CodeQL workflow also completed successfully.
- Python quality: **626 passed, 6 skipped**. GTK Integration: **416 passed, 5 skipped, 632 deselected, 2 warnings**.
- Both Flatpak architectures completed build, offline-build verification, Blueprint/resource checks, headless runtime, GI typelib checks, positive and negative sandbox OCR tests, desktop/AppStream validation and licence inventory. The multi-architecture Flatpak artifact validator also passed.
- Both AppImage architectures passed build, architecture/update-metadata checks and clean-host smoke tests. The complete AppImage release-set validator passed.
- The earlier x86_64 Flatpak OSTree `Invalid cross-device link` runner failure did not recur in this final run. No source or manifest workaround was needed.
- The workflow's `publish-release` job was skipped, as expected for a pull-request validation run; no release was published.
- The full Task 4 CI matrix is now complete. The implementation/test/documentation validation gate is green.
- Manual GNOME/GTK visual review, Orca/AT-SPI and manual keyboard checks remain excluded by user decision; this CI result does not claim real desktop or screen-reader conformance.
- PR #648 remains open and Draft, targeting `feature`. No merge or protected-branch modification was performed.
