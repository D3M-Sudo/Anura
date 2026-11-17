# M4-01 — Preferences and language selector audit

**Date:** 2026-11-17  
**Audit type:** read-only source, template, settings-schema and test-coverage review  
**Inspected branch/head at audit start:** `fix/ui-modernization-aligned` / `84ff4d50a3291b4328d28e657b251144d979e9c6`  
**Scope:** Preferences General, Editor, Voice and Languages; installed/downloadable language rows; main language-selection popover; language manager signal contract; GSettings schema; related automated tests.

## Executive result

The four Preferences pages are separated coherently and their principal settings mappings are consistent with the GSettings schema. Voice volume is normalized between the 0–100 UI and the 0.0–1.0 stored value. TTS language options are populated from cache first and refreshed asynchronously. Language installation/removal state, progress, completion/failure announcements, filtering and selected-language metadata have existing implementation and partial automated coverage.

The audit found three lifecycle/behavior issues and one accessibility/coverage gap. These are static findings; no runtime reproduction is claimed and no application code was changed.

## Page and state matrix

| Surface | Controls and states inspected | Existing evidence | Audit result |
|---|---|---|---|
| Preferences / General | Color scheme (System/Light/Dark); secondary OCR language; smart text parsing; autocopy; QR link handling; History enablement and size | GSettings bindings for boolean switches; explicit mappings for color scheme; language-manager downloaded/removed refresh; tests cover initialization and History limit persistence | Core mappings are coherent. Missing targeted tests for color-scheme mapping and secondary-language selection/refresh/removal. |
| Preferences / Editor | Line numbers; current-line highlight; wrap mode (word/char/none) | Boolean Gio.Settings bindings; explicit enum mapping for wrap mode | Implementation is straightforward; no focused tests found for wrap-mode mapping or persistence/binding behavior. |
| Preferences / Voice | Volume; TTS language (Auto or supported language); cold/warm catalog states; worker failure; disposal | Bidirectional volume synchronization; cache-first catalog; worker-thread refresh; `_disposed` guard before applying result; resilience and integration tests | Existing asynchronous design is bounded and does not block page construction. Missing explicit test for page disposal before the worker result is dispatched. |
| Preferences / Languages | Fast/Standard/Best model quality; installed-language list; search; empty state; add/install/remove; progress; download success/failure; network/metered banner | Cache invalidation before reload is tested; LanguageRow labels/announcements/state styling have tests; LanguageManager download/cache behavior is tested | Main flows exist. Network probe and idle-source lifecycle findings below; coverage does not exercise the complete page lifecycle or all state transitions. |
| Main language selector | Search, empty results, selection, active marker, accessible list label, Down-arrow navigation, Manage Languages action | Search/filter and selection tests; row accessible label/SELECTED state test; direct handler test for Down-arrow; list accessible label updated in source | Good baseline semantics. Existing keyboard test invokes the handler directly and is not a real input traversal test. |
| Language row | Install/remove controls; downloaded style; progress; accessible names; announcements; idle callbacks | Tests cover labels, progress announcement de-duplication, completion/failure announcement and installed-state styling | Lifecycle bookkeeping issue F03 below; no regression test currently covers completed idle-source cleanup. |

## Findings

### M4-F01 — Network banner probes a different host from the model download source

**Priority:** P2  
**Evidence:** `PreferencesLanguagesPage.check_connection()` calls `Gio.NetworkAddress.new("google.com", 443)` and reports that OCR models are unreachable when that probe fails. The configured model download bases in `anura/config.py` are GitHub repositories (`github.com/tesseract-ocr/tessdata*`), and `DownloadManager` downloads from those configured URLs.

**Impact:** Google reachability is not a reliable proxy for GitHub model-source reachability. Networks that block Google but allow GitHub can show a false warning; the inverse can also occur.

**Recommendation:** Probe the actual configured model source (or describe the banner as generic connectivity rather than model-source reachability). Keep metered-network messaging separate from source reachability.

**Evidence boundary:** Static source comparison only; no network behavior was exercised.

### M4-F02 — OCR model reachability callback has no page-disposal guard or cancellation

**Priority:** P2  
**Evidence:** `PreferencesLanguagesPage.check_connection()` calls `can_reach_async()` without a `Gio.Cancellable`. `_on_connection_checked()` updates `self.banner` after the asynchronous completion. The page's `do_destroy()` only tears down tracked signal handlers; it does not cancel the reachability operation or mark the page disposed.

**Impact:** A result can arrive after the Preferences page has been closed/unparented and still mutate its banner. This is an asynchronous lifecycle gap; the audit did not reproduce a crash.

**Recommendation:** Add an owned cancellable/disposed state, cancel on disposal, and guard the callback before touching widgets. Add a deterministic test for completion after disposal.

### M4-F03 — LanguageRow retains IDs for idle callbacks that have already completed

**Priority:** P3  
**Evidence:** `LanguageRow._idle_update_ui()` returns `GLib.SOURCE_REMOVE`, but does not discard its own source ID from `self._idle_ids`. The same set receives IDs from the initial idle and later download-completion/failure refreshes. `do_destroy()` subsequently calls `GLib.source_remove()` for every retained ID.

**Impact:** The set accumulates stale IDs and disposal can attempt to remove sources that have already auto-removed. This can generate GLib critical diagnostics and makes the lifecycle bookkeeping inaccurate.

**Recommendation:** Prune each source ID when its callback runs, using the same tracked-source pattern already used by `PreferencesDialog._schedule_idle()`. Add a regression test that lets callbacks finish before disposal.

### M4-F04 — Preferences installed-language list has no explicit accessible name

**Priority:** P2 (accessibility/coverage)  
**Evidence:** `data/ui/preferences_languages.blp` declares the installed-language `Gtk.ListView` without an explicit accessible label. By contrast, `data/ui/language_popover.blp` labels the language list and `LanguagePopover._on_search_changed()` updates that label with result counts and the no-results state.

**Impact:** The Preferences list has named child controls, but the list container itself lacks the explicit contextual name present in the main selector. The audit cannot establish how every AT-SPI client exposes the unnamed container.

**Recommendation:** Give the installed/downloadable language list a localized accessible name that identifies its purpose and, if useful, its filtered/installed state. Add a direct accessible-property assertion. Validate with real Orca/AT-SPI only in the already deferred M7 manual-verification stage.

## Test coverage gaps

- General: no focused tests found for color-scheme index/value mapping or extra-language selection, download refresh and removal reset.
- Editor: no focused tests found for `word` / `char` / `none` mapping or persistence.
- Voice: existing tests cover volume conversion, external setting synchronization and worker failure; no explicit late-result-after-disposal test was found.
- Languages: tests cover model-quality mapping/cache invalidation and selected LanguageRow accessibility states; no complete PreferencesLanguagesPage lifecycle test covers reachability callback cancellation, empty/search transitions, install/remove/progress and disposal together.
- Main selector: existing tests cover search, selection, row state and the Down-arrow handler, but the keyboard test calls the handler directly. It does not prove physical/virtual keyboard traversal.
- LanguageRow: no test found that proves completed idle IDs are pruned before `do_destroy()`.

## Existing strengths / preserved semantics

- GSettings schema choices match the color-scheme, tessdata-quality and editor-wrap-mode mappings in the page code.
- History limit UI bounds (1–500) match the schema range.
- TTS volume UI range (0–100) maps to the schema's normalized 0.0–1.0 range.
- Voice catalog initialization uses cached data first and does not synchronously block the Preferences constructor on a cold catalog.
- The model-quality change invalidates the language cache before reloading the list.
- Language rows use language-specific accessible names for install/remove/progress controls and announce download start/completion/failure.
- Main language selector rows update their accessible label and SELECTED state when the active language changes.

## Verification limits and exclusions

- This was a read-only inspection of source, Blueprint templates, GSettings schema and test definitions. No tests were executed for this audit.
- No runtime visual rendering, real Orca/AT-SPI session or manual keyboard test was performed.
- F-303-02 remains suspended because the current GitHub Actions XTest → Weston → Wayland → GTK input path does not reliably deliver injected keys to GTK. That limitation is recorded separately; it is not evidence of an Anura production defect.
- No OCR engine, OCR pipeline, dependency, setting semantics, application source, workflow, CHANGELOG, protected branch or PR metadata was changed.

## Approved remediation — M4-F01 through M4-F04 (2026-11-17)

The maintainer approved remediation of all four findings with targeted regression tests. The changes below resolve the audited findings without changing OCR engine selection, download semantics, metered-network messaging, model quality settings or language-manager behavior.

| Finding | Resolution |
|---|---|
| M4-F01 | The reachability probe now derives its host from `TESSDATA_URL` and checks HTTPS port 443, rather than probing `google.com`. |
| M4-F02 | The page owns a `Gio.Cancellable`, cancels any previous probe before starting a replacement, cancels on destruction, and ignores callbacks after disposal or from superseded requests. |
| M4-F03 | `LanguageRow._schedule_idle_update()` tracks each one-shot source and removes its ID as soon as the callback begins, before the source returns `GLib.SOURCE_REMOVE`. |
| M4-F04 | The Preferences model ListView receives the localized accessible label “Available OCR models”; the message was added to the gettext POT template. |

### Regression coverage

Added `tests/test_preferences_languages_lifecycle.py` with four focused tests:

- `test_network_probe_targets_the_configured_ocr_model_host`
- `test_disposing_languages_page_cancels_probe_and_ignores_late_result`
- `test_language_row_prunes_idle_id_when_refresh_callback_finishes`
- `test_preferences_language_list_has_an_explicit_accessible_name`

The tests use deterministic GI test doubles and run in the existing Python quality job. On documentation-inclusive head `c0eaa426e2fa2c37eeb43c7e04200fe67848bb37`, CI [#44109820125](https://github.com/D3M-Sudo/Anura/actions/runs/44109820125) reported Python quality success (661 passed, 6 skipped, 283 deselected) and Changelog integrity success. CodeQL [#44109819932](https://github.com/D3M-Sudo/Anura/actions/runs/44109819932) passed on the same head. GTK Integration failed only in the four previously suspended F-303-02 virtual keyboard tests (449 passed, 4 failed, 5 skipped, 667 deselected); those failures are the known XTest/Weston-to-GTK input-delivery/focus limitation and do not involve the M4 test file. AppImage x86_64/aarch64 jobs were still running at the last check; Flatpak and downstream artifact-validation jobs were skipped because GTK Integration failed.

### Scope and limits

- Changed application files: `anura/widgets/preferences_languages_page.py`, `anura/widgets/language_row.py`.
- Changed verification/i18n files: `tests/test_preferences_languages_lifecycle.py`, `po/io.github.d3m_sudo.anura.pot`, `CHANGELOG.md`.
- No workflow, dependency, OCR engine, OCR pipeline, model source path, protected branch or PR state was changed.
- Real Orca/AT-SPI and manual visual/keyboard verification were not performed; these remain excluded/deferred under the global roadmap. The automated test asserts the GTK accessible label property, not the behavior of a real screen reader.

## Recommended disposition

M4-01 audit and the approved M4-F01–F04 remediation are complete within their bounded scope. Global M4 remains **Partial** because the broader Preferences mapping, secondary-language refresh/removal, Voice late-result lifecycle and cross-surface keyboard/accessibility coverage gaps remain outside this remediation.
