# Handover: UI modernization alignment

## Purpose

This document transfers the context required to continue the UI modernization work originally proposed in [PR #448](https://github.com/D3M-Sudo/Anura/pull/448), adapting it to the current `feature` branch rather than applying the old branch wholesale.

This handover records the adapted implementation and its remaining validation. The modernization work is now present on `fix/ui-modernization-aligned`; it was adapted against `feature` rather than copied wholesale from PR #448.

## Current operational snapshot — M3-01 audit and F-301/F-302 remediation (2026-11-17)

- **Authoritative global status:** M0 Completed; M1 Completed (operationally); **M2 Completed (operationally)**; **M3 Partial**; M4 Partial; M5 Not started as a complete phase; M6 Partial; M7 Partial.
- **M3-01 audit:** Extracted and History baseline audit completed read-only. No production defect was established. F-301 was a contradictory test expectation against the chosen A1 refresh-preservation contract; F-302 was a limited search-announcement edge-case coverage gap (an existing debounced plural-result test was already present).
- **F-301:** updated `tests/test_history_expansion_real.py` to verify refresh restores the same still-existing expanded entry and maintains single-row expansion. Commits: `e7ee3032bc375ea953c18a809b2ccd42a9397aad`, formatting-only `0988708e88a162417a9622500c813ae3c1a98dac`.
- **F-302:** expanded `tests/test_accessible_status_announcements.py` for Searching state, singular announcement after 400 ms at LOW priority, zero results and clearing/cancelling pending announcement. Stable LOW-priority sentinel fix is in `56d794502d84c0dfc392230867b4c90b6d08ee91`.
- **Exact-head validation:** CI [#2497](https://github.com/D3M-Sudo/Anura/actions/runs/44006990401) and CodeQL [#699](https://github.com/D3M-Sudo/Anura/actions/runs/44006990338) both succeeded on `56d794502d84c0dfc392230867b4c90b6d08ee91`. Python quality, Changelog integrity, GTK Integration, AppImage/Flatpak x86_64+aarch64 builds and release artifact validators passed; `publish-release` was skipped as expected for a PR.
- **Evidence limitations:** no local test execution or TDD red→green demonstration is claimed. CI does not establish real Orca/AT-SPI or manual keyboard behavior; those checks remain excluded/deferred. F-303 (History action labels and keyboard traversal) remains unaudited.
- **M2-G01 completed:** History → Welcome focus behavior passed exact-head CI on `7d34cf8f92435c85d9ba3537ead42c7bb98519a4`.
- **M2-G02 completed:** asynchronous Welcome drag-and-drop and eight regression tests passed on exact head `f52e437d9bdfdf6200d26449152e3ffeeacc14be`. CI [#43995410588](https://github.com/D3M-Sudo/Anura/actions/runs/43995410588) and CodeQL [#43995410567](https://github.com/D3M-Sudo/Anura/actions/runs/43995410567) both succeeded on that exact head. Python quality: 652 passed, 6 skipped, 279 deselected; GTK Integration, Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and release artifact validation passed. `publish-release` was skipped as expected for a PR.
- **Operational closure decision:** the maintainer selected option A. All M2 requirements selected for automated verification are complete. Manual GNOME/GTK visual, keyboard and real Orca/AT-SPI checks are deferred to M7 and are not claimed as passed. Live multi-monitor verification remains excluded. App-wide menu consistency and intentional menu differences are deferred to M5.
- The [global roadmap](docs/superpowers/plans/2026-11-16-anura-ui-modernization-global-roadmap.md) owns current phase status, priorities, dependencies and global traceability. The [PR #648 roadmap](docs/superpowers/plans/2026-11-16-anura-ui-modernization-roadmap.md) owns detailed PR workstream history and exact-SHA evidence.
- PR #648 was rechecked: Open, Draft, unmerged, base `feature`, head branch `fix/ui-modernization-aligned`. No PR metadata/state change or merge was made.
- No protected branch was modified. M3-01 audit and F-301/F-302 bounded test remediation are recorded; M3 remains Partial. F-303 is the next read-only audit, and no F-303 implementation is authorized.


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


## M2-D — Extracted and History navigation-state completion (2026-11-16)

- Extracted OCR text survives navigation away and back; the next completed extraction replaces it.
- History preserves expanded-entry identity and vertical scroll through refresh/navigation during the current application session only; no restart persistence was added.
- Automated tests cover Extracted retention/replacement and round-trip navigation, focus acquisition on Extracted navigation, TTS stop on return to Welcome, and History state restoration/stale callbacks/removed entries.
- Exact implementation head: `bb316f94d37629cc7566b24330a87b6e86029db3`.
- CI Quality Check & Release [#43885843452](https://github.com/D3M-Sudo/Anura/actions/runs/43885843452): success; Python Quality 630 passed/6 skipped/277 deselected; GTK Integration 436 passed/5 skipped/636 deselected/2 warnings; Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, AppImage release-set and multi-architecture release-artifact validation all succeeded. `publish-release` was skipped as expected for a PR.
- CodeQL [#43885843419](https://github.com/D3M-Sudo/Anura/actions/runs/43885843419): success on the same SHA.
- Manual GNOME/GTK visual, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed.
- PR #648 remains Open/Draft/unmerged, base `feature`; no protected branch or release was changed.


## M2-E — Welcome and main-shell residual-gap audit (2026-11-16)

Read-only audit completed on `fix/ui-modernization-aligned` at pre-recording head `97a42a0c17252cc2a36be563e87255cb2d306e63`.

- **Welcome:** existing implementation and automated coverage substantially address the responsive action hierarchy, four reference viewports (360×600, 640×480, 900×600, 1280×800), constrained-height scrolling, responsive focus preservation, drag/drop and language-selector accessibility. No broad rewrite is justified.
- **High-priority finding:** History can start TTS via its row controls, but the normal `Adw.NavigationView` back path to Welcome does not necessarily invoke `AnuraWindow.show_welcome_page()`, where `tts_controller.stop()` currently runs. Playback may continue after returning from History.
- **Coverage gaps:** no end-to-end test was found for the real `AnuraWindow` History-open/back route or focus restoration across that route.
- **Geometry:** helper/policy tests cover sizing and monitor selection. The maintainer explicitly declined live multi-monitor geometry verification; do not add it.
- **Verification:** source/test inspection only; no tests or CI run for M2-E. No source, test, workflow or CHANGELOG changes were made. Manual GNOME/GTK visual, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed or blockers.
- Context7 Libadwaita navigation documentation was consulted. AI Delivery Evidence Checker was used to structure criteria, but its combined verdict endpoint returned `out_of_scope`; no combined verdict is claimed.
- PR #648 remains Open/Draft/unmerged, base `feature`. No protected branch or PR metadata was modified.

**Next:** prepare the M2-F plan only; implementation requires separate explicit approval. Live multi-monitor verification remains out of scope.

## M2-F — History TTS navigation lifecycle (2026-11-16)

### Implementation

- Centralized the History TTS lifecycle in `AnuraWindow` by tracking `Adw.NavigationView:visible-page` with `connect_tracked`.
- Whenever the previous visible page is History and the new page differs, TTS is stopped irrespective of destination (native back/gesture, Welcome, Extracted or another page).
- The explicit `show_welcome_page()` path continues to stop TTS and the lifecycle handler avoids issuing a duplicate stop for that transition.
- Five GTK integration tests use the real `AnuraWindow` and `Adw.NavigationView`: native History → Welcome, explicit History → Welcome, History → Extracted, entering/remaining in History, and History exit while TTS is idle. All passed.
- Changed files: `anura/window.py`, `tests/test_widgets.py`, `CHANGELOG.md`. No dependency, OCR, Welcome redesign, manifest, workflow or live multi-monitor changes.

### Validation evidence

- Exact code/CHANGELOG head: `acd1f03e3dee92173af98b4afe7f712806747afe`.
- CI Quality Check & Release [#43897822566](https://github.com/D3M-Sudo/Anura/actions/runs/43897822566) completed **success** on that SHA:
  - Python Quality: **630 passed, 6 skipped, 277 deselected**.
  - GTK Integration: **441 passed, 5 skipped, 636 deselected, 2 warnings**; all five M2-F regressions passed.
  - Changelog integrity passed.
  - AppImage x86_64/aarch64 and Flatpak x86_64/aarch64 builds passed.
  - Complete AppImage release-set and multi-architecture release-artifact validation passed.
  - `publish-release` skipped as expected for a PR; no release was published.
- CodeQL [#43897822286](https://github.com/D3M-Sudo/Anura/actions/runs/43897822286) passed on the same code head.
- The CI evidence is attributed to the code/CHANGELOG SHA above; subsequent roadmap and handover updates are documentation-only commits and were not part of that CI run.
- Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed. Live multi-monitor verification remains explicitly out of scope.

### Current state

- PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`.
- No protected branch or PR metadata was modified; no merge or release was performed.
- The next task requires a bounded plan and separate explicit approval.


## M1-02 — GTK4/Libadwaita design conventions (2026-11-16)

- **Outcome:** M1-02 completed; global M1 remains Partial.
- Added `docs/ui-design-system.md` documenting semantic typography roles, spacing scale (4/8/12/16/24 px), custom corner-radius roles, native control hierarchy, theme compatibility and GTK CSS limitations.
- Normalized Blueprint and GTK CSS spacing and added four static regression tests in `tests/test_ui_palette.py`. Updated `CHANGELOG.md`.
- Preserved one documented 6 px gap in the Welcome compact screenshot action. Changing it to 8 px caused three narrow-viewport GTK integration regressions; the 6 px exception is guarded by the new regression test.
- No OCR engines/pipelines/models, architecture, dependencies, portal or OS integration were changed. No manual visual, Orca/AT-SPI or manual keyboard verification is claimed.
- Implementation range: `b4f8c0798933fb410dd4bf24cb808e183aba932a` → `6dece44cd3deb57fc43cb276db4a291a771e9584`.
- GitHub Actions [#43907544843](https://github.com/D3M-Sudo/Anura/actions/runs/43907544843) succeeded on the exact head: Python **634 passed, 6 skipped, 277 deselected**; GTK **441 passed, 5 skipped, 640 deselected, 2 warnings**; Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and release artifact validations passed. `publish-release` skipped as expected.
- CodeQL [#43907544861](https://github.com/D3M-Sudo/Anura/actions/runs/43907544861) succeeded on the same SHA.
- AI Delivery Evidence Checker: delivery criteria supported; test-evidence assessment partial and combined verdict `needs_more_evidence` due to its inability to inspect code/run CI and a mismatch treating documentation criterion C7 as a runtime-test criterion. CI logs and source/diff were independently inspected; checker output is not treated as a code audit.
- PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`. No merge or release occurred.

**Next:** prepare a bounded M1-03 semantic-color role audit plan; no implementation until separately approved.

## M1-03 — Semantic color-role audit (2026-11-16)

- Read-only audit completed on `fix/ui-modernization-aligned` at pre-documentation head `f5225e2e82973db63822ca8b3b26cf13619b907a`.
- Inspected `data/style.css`, all 14 Blueprint UI files, relevant Python widget/application modules, `anura/main.py`, `docs/ui-design-system.md` and `tests/test_ui_palette.py`. No source, test, CHANGELOG or workflow files were changed.
- Color roles: `#16A36A` brand/graphical accent; `#0F7650` + white suggested-action pair and light standalone green; `#21B77A` dark standalone green; `@warning_color` semantic warning; GTK/Libadwaita theme colors for surfaces, text and borders; translucent black shadows decorative.
- Representative calculated contrast ratios: white on `#0F7650` 5.63:1; `#0F7650` on `#F6F5F4` 5.17:1; `#21B77A` on `#242424` 6.00:1 and `#353535` 4.74:1. `#16A36A` is 3.24:1 on white and is not a general normal-text color. Ratios are sample calculations, not runtime theme measurements.
- Findings: no Critical/High issue demonstrated. Medium: downloaded-language success state uses explicit light/dark green values rather than a semantic Libadwaita success class. Low: repeated green literals and no exhaustive repository-wide hardcoded-color scanner. Informational: no explicit error color role in audited CSS; no missing user-facing error state inferred.
- Theme mode mapping for `default`, `force-light`, `force-dark` is present through `Adw.StyleManager`. Custom green states have dark overrides; surfaces and warning remain theme-managed.
- Coverage gaps: no runtime cross-surface theme-switching test across all three modes; no repository-wide color-literal guard; no explicit semantic success/error class test. Existing contrast tests use representative fixed surfaces.
- Context7 confirmed Libadwaita semantic classes `.accent`, `.success`, `.warning`, `.error` and theme-aware color guidance.
- AI Delivery Evidence Checker: 10 criteria extracted; delivery partially supported (5 supported, 5 partial), test evidence partially supported, verdict `needs_more_evidence` (level 3). No tests were run during this audit. Historical CI #43907544843 is on SHA `6dece44cd3deb57fc43cb276db4a291a771e9584`, not the audit head.
- Manual GNOME/GTK visual, Orca/AT-SPI and manual keyboard checks remain excluded, not passed.
- PR #648 remains Open/Draft/unmerged, base `feature`, head `fix/ui-modernization-aligned`. No protected branch or PR metadata changed.

**M1-04 design proposal (2026-11-16):** approach B selected. Design document: [`docs/superpowers/specs/2026-11-16-m1-04-semantic-colors-design.md`](docs/superpowers/specs/2026-11-16-m1-04-semantic-colors-design.md), commit `b724f2688475bfd94e03c6e085863bfbc066c80c`. It specifies conditional `.success` adoption, role-safe color consolidation, a classified production-UI color scanner and automated tests for all three theme modes. This is design-only; implementation and tests remain unauthorized pending approval and a separate implementation plan.

**M1-04 implementation update (2026-11-16):** the approved implementation plan has been started. The deterministic production UI color scanner and its eight unit tests are present. Exact-SHA CI [#43928078842](https://github.com/D3M-Sudo/Anura/actions/runs/43928078842) and CodeQL [#43928078536](https://github.com/D3M-Sudo/Anura/actions/runs/43928078536) passed on `f300740f2691c0a122ea4b067b607a41cef51273`. Python: **642 passed, 6 skipped, 277 deselected**; GTK: **441 passed, 5 skipped, 648 deselected, 2 warnings**; Ruff formatting: **232 files already formatted**. Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64, multi-architecture artifact validation and complete AppImage release-set validation passed. `publish-release` was skipped as expected.

**Status: M1-04 Partial, not complete.** The successful CI confirms the scanner and existing test/build suites, but not the remaining semantic success-style consolidation or new GTK runtime theme-transition coverage. The current `.downloaded label` CSS fallback remains; the inspected `LanguageRow.update_ui()` does not apply a corresponding `downloaded` style class. No runtime contrast result is claimed. No CHANGELOG entry was added because this delivered scanner work does not change user-visible behavior or establish a release-relevant maintenance change.

- Manual GNOME/GTK visual checks, real Orca/AT-SPI and manual keyboard checks remain excluded, not passed.
- No OCR, dependency, architecture, portal or OS integration changes were made.
- PR #648 remains Open/Draft/unmerged, base `feature`; no protected branch or PR metadata was changed.

**Historical next-step note — superseded by M0-C (2026-11-16):** prepare the remaining M1-04 semantic-style and GTK theme-transition work. M1-04 was subsequently completed within its approved scope; see the completion record and current operational snapshot above.


## M1-04 — semantic color consolidation (2026-11-16)

M1-04 implementation completed on `fix/ui-modernization-aligned` at `7f6a7045feefb019c869cc74aecc31a5e991a74d`. The scanner, downloaded-language class linkage and GTK theme-transition tests are implemented. CI #43951965392 and CodeQL #43951968944 both passed on the exact SHA. Python: 643 passed, 6 skipped, 277 deselected; GTK Integration, Changelog integrity, AppImage x86_64/aarch64, Flatpak x86_64/aarch64 and release artifact validation passed. `publish-release` was skipped for PR validation.

The application-owned light/dark green fallback is retained; Libadwaita `.success` was not adopted because it cannot guarantee contrast on the resolved application surfaces. Automated theme tests validate transitions and CSS-class state, not pixel-level contrast across all desktop themes. Manual visual, Orca/AT-SPI and keyboard checks remain excluded. M1 and the global M0–M7 programme remain Partial. PR #648 remains Open/Draft/unmerged, targeting `feature`; no protected branch was changed.


## M1-06 — implementation handover (2026-11-16)

- **Implementation/test SHA:** `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`.
- **F1:** `ShortcutsOverlay` uses the existing reduced-motion helper, observes supported GTK setting notifications, suppresses root animation/transition classes in reduced mode, restores them in normal mode, and disconnects settings callbacks on close-request and destruction.
- **F2:** the existing UI color scanner now runs against the actual repository tree in pytest with exact path/value approvals and semantic rationales. No scanner implementation or CI workflow change was required.
- **TDD:** expected red GTK runs confirmed the missing reduced-motion propagation and missing close-path cleanup before the corresponding fixes. Final GTK suite passes.
- **Final CI evidence:** CI #43974750869 completed with conclusion `success` on the exact source/test SHA `35fa684e72fd4e83eae4d58d4b7e731a00d2486b`. All 9 executable jobs passed: Python quality (644 passed, 6 skipped, 277 deselected); GTK Integration (447 passed, 5 skipped, 650 deselected, 2 warnings); Changelog integrity; AppImage x86_64 and aarch64 builds, architecture/update-metadata verification, clean-host smoke tests and artifact uploads; Flatpak x86_64 and aarch64 builds/runtime checks; multi-architecture Flatpak artifact validation; and complete AppImage release-set validation. The `publish-release` job was skipped as expected for a pull request. CodeQL #43974750821 also passed on the same source/test SHA.
- **Ruling — root motion classes:** the shared `.reduced-motion *` selector excludes the root widget. The implementation therefore removes `anura-fade-in` and `anura-card` from the Shortcuts root while reduced motion is enabled, restoring them otherwise; this avoids a CSS-wide selector change and preserves normal behavior. Cost if wrong: root-level motion could remain visible despite reduced-motion preference.
- **Ruling — close lifecycle:** GTK integration showed that calling `Gtk.Window.destroy()` in the test did not exercise the existing `do_destroy()` cleanup path. Settings handlers are therefore also disconnected in `close-request`, with `do_destroy()` retained as an idempotent fallback. Cost if wrong: a close path that bypasses both hooks could retain a settings callback.
- F3/F4 follow-up is recorded below: F3 cleanup and F4 documentation are complete within the approved scope. Manual visual, Orca/AT-SPI, keyboard and live multi-monitor tests remain excluded and are not claimed.


## M1-07 — CSS selector and typography follow-up (2026-11-17)

- **Outcome:** F3 cleanup and F4 documentation completed on `fix/ui-modernization-aligned`; M1 remains globally Partial.
- **F3 evidence:** temporary workflow [#43981815120](https://github.com/D3M-Sudo/Anura/actions/runs/43981815120) completed successfully on audit commit `498f8de52cff7c4ea9d12f0ea9a9b19e913d81ce`. Its `git grep` covered all tracked files outside `data/style.css`. No candidate class references were found in Python or Blueprint application sources. Remaining text matches were documentation, the workflow itself, changelog wording, and Welcome screenshot/asset names; these are not class consumers. The job log is the primary evidence; artifact [m1-f3-selector-audit](https://github.com/D3M-Sudo/Anura/actions/runs/43981815120/artifacts/14283985075) was uploaded.
- **F3 change:** removed the unused `.anura-pulse`, `.anura-spinner`, `.anura-toast`, `.share-row`, `.welcome-page`, `.welcome-card`, `.language-popover`, `.language-row` and `.screenshot-btn.ready` rules, their dedicated keyframes, and stale reduced-motion references to `.share-row`/`.welcome-card`. No candidate selector was retained as a speculative future reservation because no tracked consumer or approved near-term use was identified. Active `.anura-button`, `.anura-card`, `.anura-fade-in` and `.anura-slide-up` rules remain.
- **Audit boundary:** literal tracked-file search cannot prove absence of a class name synthesized at runtime from fragments or supplied by an external integration. It does establish no direct textual consumer in the tracked application sources/resources inspected at the audited SHA.
- **F4 outcome:** `.heading` is the documented Libadwaita standard heading style. The `.title` and `.h4` labels used in `data/ui/language_row.blp` and `data/ui/preferences_languages.blp` are not part of the documented Adwaita typography utility set (`.title-1`–`.title-4`, `.heading`, `.body`, `.caption`, etc.). GTK accepts arbitrary CSS class names; those names alone do not establish a supported typographic role. The guide now records their current intent and limitations. No Blueprint/code class was changed.
- **Temporary workflow:** removed after collecting the successful run and artifact. No permanent workflow was added.
- **Files updated:** `data/style.css`, `docs/ui-design-system.md`, this M1-05 audit report, global and PR #648 roadmaps, `CHANGELOG.md`, and this handover/ledger.
- **Validation:** the full PR CI and CodeQL are to be checked against the resulting source/documentation head before this task is declared fully verified. No local tests or manual visual/assistive-technology checks are claimed.
- **Governance:** PR #648 remains Open, Draft, unmerged, base `feature`; protected branches and PR metadata were not changed.
