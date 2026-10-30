# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Changed
- Flatpak: every `finish-arg` is now mapped to the feature that needs it in `flatpak/README.md`, and `tests/test_flatpak_manifest_hygiene.py` fails when the manifest, the documentation or the source pinning drift apart (an unpinned `file`/`archive`/`git` source or an undocumented permission) (#498, #504)
- Release: `generate_release_notes.py --markdown` produces the GitHub release body from the `CHANGELOG.md` section for the tag, so a release can no longer be published with an empty body (#489)
- Docs: `docs/reference/dependencies.md` explains how the manifest satisfies the Flathub dependency-manifest requirement and how to prove an offline build (#504)
- Packaging: the licence inventory checker no longer requires the licences of build-only modules (`scikit-build-core`, `pybind11`, `nanobind`), which are removed from the runtime together with their licence copies; they are reported as `SKIP` and listed under `excluded_build_only` in the JSON evidence (#493)
- Release: `build-aux/release.sh` now refuses to run on a dirty tree, on an existing tag or outside the release branch (`RELEASE_BRANCH` overrides it), and it builds the AppStream entry from the `CHANGELOG.md` section instead of writing a `TODO` placeholder (#487, #485)
- Release: `build-aux/pin_source_commit.py` writes the tag's commit into the submission manifest, so a moved tag cannot change the sources; `--check` verifies it (#501)
- Docs: the privacy statements now separate local OCR from the optional text-to-speech feature, which uploads the selected text to Google; `SECURITY.md` gains a data-flow table (#495)
- AppStream: the screenshot URLs are pinned to the `v0.2.1` tag instead of the mutable `main` branch, and the 0.2.1 release notes replace the placeholder with the actual changes (#499, #481)
- Tests: `tests/test_appstream_metadata.py` validates the metainfo (id, licenses, developer, launchable, screenshots pinned to the version, releases without placeholders), the desktop entry and the gettext catalogue set (#497)
- Flatpak: the application's own MIT license is now installed by Meson (`install_data`), so it reaches `share/licenses/io.github.d3msudo.anura/LICENSE` regardless of flatpak-builder's automatic recording; the build-only modules' auto-recorded license directories are removed together with the modules (#478, #482)
- Packaging: license checks no longer print `FATAL: …` inside the build commands — flatpak-builder echoes each command, and that text looked like a missing-license error for a license that was actually present (#477); the inventory checker now also requires the application license and the native modules' licenses and records the full listing as JSON evidence (#493)
- Flatpak: license collection is now fail-closed. Every module installs a deterministic license file (source `LICENSE` for sdists, the dist-info license for wheels) and the build fails when it is missing; the `loguru` wheel ships no license file, so its LICENSE comes from the hash-pinned sdist (#477)
- Packaging: `build-aux/check_license_inventory.py` derives the expected `share/licenses` inventory from the manifest and verifies a built prefix, failing on missing or empty files; it can also emit the inventory as a CI artefact (#493)
- Flatpak: imlib2 1.12.6 no longer receives configure options it does not recognize (`--without-bmp`, `--without-xbm`, `--without-xpm`, `--with-loader-dir`), and its helper programs and demo data are removed from the runtime (#542, #546)
- Flatpak: Tesseract's ignored `--disable-training` option is gone; the training tools the build installs are removed from the final prefix instead (#543)
- Flatpak: the build environment no longer hardcodes `/app/lib/x86_64-linux-gnu`, so the manifest is architecture-neutral (#480)
- Flatpak: the build-only Python tooling (`scikit-build-core`, `pybind11`, `nanobind`) and its license files are removed from the runtime (#482)
- Performance/History: `record()` no longer serialises, `fsync`s and replaces the whole `history.json` on the GTK main thread. Entries are appended in memory and written by a coalesced background writer; each entry is capped at 100,000 characters, and `do_destroy()` flushes pending writes through `close()` so nothing is lost at exit. `clear()` and `set_limit()` stay synchronous because they must be able to report a failure and roll back (#511)
- History: the service now logs through the project's `loguru` logger instead of the standard library, so the configured format, rotation and retention apply to it like everywhere else (#512)
- Docs: `AGENTS.md` now describes the logging policy that is actually implemented (5-file retention, gzip compression) instead of the pre-`26f08f5` wording; the code was intentional and is unchanged (#513)
- CI: the `python-quality` job now enforces `ruff format --check`, `bandit -c pyproject.toml -r .`, non-strict `mypy` and a non-blocking `vulture` report, on top of `ruff check` and pytest, with a single shared `uv sync --dev` step. `[tool.bandit]` excludes `tests/` (pytest's asserts, `try/except/pass` and subprocess mocks produced ~1,100 non-actionable findings), and Markdown is excluded from `ruff format` because ruff ≥ 0.15 also reformats fenced code blocks inside documentation (#517, #518)
- Formatting: applied the `ruff format` baseline to 29 Python files (mechanical, behaviour-neutral) so the format check can be a blocking gate (#517)
- Flatpak: updated the Python modules requested by FEDC in #427 — zxing-cpp 3.0.0 → 3.1.1, Pillow 12.3.0 → 13.0.0 (security release), charset-normalizer 3.4.7 → 3.5.2, libportal 0.9.1 → 0.11.0 and scikit-build-core 1.0.1 → 1.1.1. `pyproject.toml` now requires `pillow>=13.0.0` and `zxing-cpp>=3.1.1`, with `uv.lock` regenerated so `sync_dependencies.py --check` stays green
- Flatpak: zxing-cpp 3.1 builds its Python wheel with nanobind instead of pybind11, so `python3-nanobind` 2.11.0 was added and the zxing build no longer sets `pybind11_DIR`. `pybind11` stays (updated to 3.1.0) because Pillow 13 now imports `pybind11.setup_helpers` at build time
- Flatpak: scikit-build-core is installed from its `1.1.1` wheel; FEDC's proposed sdist could not be installed by the module's `--no-build-isolation` build command, which referenced the old wheel by filename. The `x-checker-data` now pins `packagetype: bdist_wheel`, and `tests/test_flatpak_manifest_build_commands.py` guards wheel modules against the same mismatch

### Removed
- Development tooling: dropped the `safety` dev dependency (and its entry in the Dependabot `dev-deps` group). It was added by the one-off June 2026 audit (`ead78f1`) to produce `docs/audit/safety_scan.json`, which is no longer tracked; no workflow, test or build script invokes it, and dependency scanning is covered by Dependabot and CodeQL. The development graph drops from 72 to 39 packages (also losing `cryptography`, `httpx`, `h11`, `pydantic` and `nltk`, which came in through it); runtime dependencies and the Flatpak manifests are untouched. `bandit` is kept

### Fixed
- OCR/tessdata: startup cleanup no longer deletes shared top-level models or directories owned by a live process. Task pool directories carry an `owner.pid` lease written when the pool is created, and cleanup removes a directory only when its owner is dead or, for legacy directories without a lease, when it is older than a day. The previous rules removed every model that did not match the active language and every directory older than an hour, which could pull the models out from under a concurrent OCR task or a second instance (#521)
- OCR: a stale `BrokenProcessPool` callback can no longer tear down a healthy replacement pool. The teardown now runs only when the executor that failed is still the current one, instead of resetting whichever pool happens to be installed (#526)
- TTS/shutdown: a generation blocked in gTTS no longer delays application exit. TTS now runs on a dedicated daemon thread (`execute_daemon`, same lane and versioning semantics) instead of the shared `ThreadPoolExecutor`, whose workers CPython joins at interpreter exit; `shutdown()` also cancels every lane and no longer waits for the running task (#506)
- TTS: the generation watchdog is now proportional to the text (30 s base + 1.5 s per 100-character gTTS fragment, capped at 5 min) instead of a fixed 35 s, and on expiry the TTS lane is cancelled so a late result is discarded instead of arriving after the UI already gave up (#508)
- Tasks: `AtomicTaskManager` now keeps one slot per task kind (`ocr`, `tts`, `cleanup`) instead of a single global one. A screenshot, an OCR run or the post-OCR file cleanup no longer cancels an in-flight TTS generation (and vice versa); only a newer task in the same lane supersedes the previous one, and a superseded task reports through the new `on_superseded` hook — used by the TTS controller to drop its pending state — instead of having its result discarded silently (#507)
- TTS: opening Preferences no longer freezes the window while the gTTS language catalog is fetched. On a cold cache the combo is filled from the cached catalog only and the catalog is refreshed on a worker thread, applied via `GLib.idle_add`; programmatic repopulation does not write the setting back, and a failed fetch is no longer cached permanently so a later retry can succeed (#532)
- Downloads: `shutdown()` now sets a manager-owned signal and closes the active HTTP response, so an in-flight model download stops instead of streaming until the request and retry timeouts expire. New download requests are refused once shutdown has begun, so the process can exit while the window is closing (#531)
- Preferences: language-download signals now schedule their refresh through a tracked idle source. The source id is remembered and removed in `do_destroy()`, and the wrapper re-checks a disposed flag, so a download that finishes while the dialog is closing can no longer refresh destroyed child pages (#539)
- Drag and drop: the cancellable is now carried through the async chain and cleared only by the callback that owns it. A delayed callback from a cancelled drop could clear the newest drop's cancellable, leaving the active read uncancellable by the next drop or by `do_destroy()` (#538)
- Clipboard: the texture read clears its cancellable only when it still owns it. When texture decoding failed and the URI-list fallback started, the outer `finally` erased the *fallback's* cancellable, so the 10-second watchdog treated its timeout as stale and `cancel_pending_operations()` could no longer cancel the pending read (#525)
- History: a failed clear no longer empties the view. The in-memory cache is replaced only after the empty state is persisted and is restored when the write fails, and the failure is reported with a toast. Previously the list looked cleared while `history.json` still held every entry, which then "came back" after a restart (#540)
- History: changing `history-limit` in Preferences now applies immediately. The window reacts to `changed::history-limit` and updates the live service, which trims and persists when the limit shrinks; previously the value was read only at startup (#510)
- Screenshot (X11/scrot fallback): the file-ready wait no longer runs inside the async process callback. The old `wait_for_file()` loop slept on the GTK main thread for up to ~5 s after every capture; it is now a `GLib.timeout_add` poll with the same retry policy, and the unused blocking method was removed (#523)
- OCR: `pytesseract.image_to_data()` now runs with a 120 s budget (`OCR_TIMEOUT_SECONDS`) in both the isolated worker and the synchronous path. pytesseract kills the Tesseract child when the budget expires, so a pathological image can no longer keep the single OCR worker busy indefinitely (and cancellation, which is only checked before/after the call, cannot be held hostage). A timeout is reported as an OCR error instead of a silent empty result (#533)
- Downloads: the streamed HTTP response is now closed on every exit path of a model download (oversized `Content-Length`, size mismatch with the pinned model, cancellation, oversized stream, I/O error and success). An unread stream kept its connection and socket alive, and repeated failures could starve the session pool (#520)
- URL transformer: TLD detection now parses the candidate instead of requiring `/` right after the TLD, so URLs followed by a query string, a fragment or an explicit port (`https://example.com?next=/x`, `…#section`, `…:8443/path`) are no longer discarded; one-character, numeric and non-ASCII TLDs, host-less URLs and malformed ports are still rejected (#530)
- TTS: playback builds a real `file://` URI instead of concatenating the prefix with the path, so a cache directory containing spaces, `#`, `?`, `%` or non-ASCII characters no longer makes a successful generation fail to play (#528)
- TTS: a stale or unsupported speech language no longer breaks the failure path. The gTTS constructor runs inside the guard, so its `ValueError` (and `gTTSError` from the API) map to the normal empty-path result the pipeline already handles, and any partial MP3 is removed (#547)
- History: the clear-confirmation callback now re-checks the history service before using it, so a window teardown between opening the dialog and the user response can no longer raise `AttributeError` (#514)
- UI: `ShortcutsOverlay.shortcuts_data` is typed with `TypedDict` entries, so category and shortcut lookups are checked instead of being inferred as `Collection[str]` (#515)
- Types: the headless `GObject` fallback used when PyGObject is unavailable is now marked as an intentional redefinition, keeping `mypy` clean in CI (#516)
- Flatpak: automated certifi updates no longer break the build — the FEDC update now rewrites the certifi filename referenced by the module's `build-commands` (the 2026.10.18 bump made `pip3 install` look for the previous 2026.7.22 tarball). Covered by `tests/test_fedc_certifi.py`
- Clipboard: `hand_off_to_manager()` and `wait_until_replaced()` now refuse to iterate the default GLib main context when it is already running (an active GTK loop, or another thread owns it), logging a warning and returning `False` instead of re-entering the loop (AUDIT-001, #469)

### Security
- Privacy: shutting down a silent CLI run no longer constructs the TTS service. `_cleanup_services()` used the lazy `get_tts_service()` getter, which built `TTSService` — starting a Google language-catalog fetch — purely to call `cleanup()`; it now uses a non-initializing singleton lookup and only cleans up a service that was actually used (#536)
- Notifications: the successful-extraction notification no longer includes the first 80 characters of the recognised text. Banners and notification history can be visible on the lock screen, and the text may be a private message or a credential; the body is now generic (#534)
- Notifications: the application now uses the same `NotificationService` singleton as the controllers, so shutdown withdraws the portal notification IDs that OCR actually created instead of cleaning up an unrelated instance (#537)
- QR codes: `autolinks` now defaults to off, and loopback/private-network destinations (`localhost`, loopback, RFC 1918, link-local, `.local`, unspecified) always require an explicit confirmation even when it is enabled. A crafted QR code can no longer navigate the browser into a local admin UI or an intranet service without user action (#529)
- TTS: speech generation now verifies the server certificate. gTTS 2.5.4 hardcodes `verify=False` in its request loop and exposes no switch, so extracted text was sent to Google and the returned audio received over a channel whose peer was never authenticated (a MITM could read the text or replace the MP3). A minimal subclass reproduces the pinned upstream request loop with `verify=True` (#505)
- Images: a decoded-pixel budget (`MAX_IMAGE_PIXELS`, 40 MP) is now enforced from the image header before any `convert()`, barcode or OCR work, in the isolated worker, the synchronous OCR path and the clipboard file decode. The 50 MiB byte limit alone could not catch a decompression bomb: a small file can expand to an arbitrarily large bitmap (#522)
- Files: opening an image from the file dialog now validates the file from its metadata (`is_file`, `stat`, read access) before `load_contents_async()`, so a multi-gigabyte file chosen through the "All files" filter is rejected without being read into memory. The post-load byte check stays as defence in depth (#509)
- Clipboard: a `text/uri-list` payload is now capped at 1 MiB while streaming. Past the cap the read is cancelled, the stream closed and the buffered chunks dropped before any join/decode/split, so a clipboard source that advertises an enormous stream can no longer exhaust memory during a paste (the 10 s watchdog bounds elapsed time, not bytes) (#524)
- History: the JSON store is now created with `0700` on the directory and `0600` on the file (temporary file created with `os.open(..., O_CREAT | O_EXCL)`), and a pre-existing permissive directory is tightened. With a default umask of `022` the directory was `0755` and the file `0644`, so other local accounts could read the extracted text (#527)
- Dependabot #49, #50, #51: `urllib3` 2.7.0 → 2.8.0, fixing the unbounded chunk-size line buffered by `HTTPResponse.stream()`/`read_chunked()`, the HTTPS proxy TLS configuration that could be ignored or overridden, and the infinite loop on chunked deflate streaming. The Flatpak `python3-urllib3` module was resynced by `build-aux/sync_dependencies.py` (wheel 2.8.0 + sha256)
- Dependabot #47, #48 (`anyio`): no longer in the dependency graph. `anyio` was only reachable through `httpx`, which was required exclusively by the `safety` dev tool removed above; `uv.lock` now has no `anyio` entry, so the IDNA 2003 host-name encoding in `TLSStream` (TLS certificate spoofing) and the process-pool workers blocked on undrained stderr no longer apply
- Dependabot #32 (`nltk`): no longer in the dependency graph. The direct dev dependency was unused (never imported by the application, the tests or the build scripts), and dropping `safety` removes the only transitive path (`safety 3.8.1` requires `nltk>=3.9`), so NLTK's unfixed model-artifact path traversal cannot be reached from this project at all. NLTK was never shipped in the Flatpak

## [0.2.1] - 2026-10-20

### Added
- History: rows now expand (Enter, Space or click on the row) to show the full extracted text in a scrollable area of limited height; one row is open at a time and all rows start collapsed every time the page is opened. The copy button stays in the row header. The text area is created on the first expansion, so a long history with large entries opens as fast as before (History V2, minimal cut). Tests: `tests/test_history_expansion_real.py` runs the real page and real widgets
- History: each row of the History page now has a copy button that copies the stored text to the clipboard, with icon and toast feedback (History V2, minimal cut). Row activation is intentionally not bound to any action yet. The action logic lives in the new `HistoryController`, which reports outcomes through signals, so `HistoryPage` stays a UI shell
- Tests: `tests/test_pot_template.py` validates the gettext template with the checks that apply to a template (it parses, no duplicate msgids, the History strings are extracted). `msgfmt -c` is not one of them: it rejects the placeholder header xgettext writes, and is meant for the translated `.po` files

### Changed
- History: the Clear button is insensitive while there are no entries, so it can no longer open an empty confirmation dialog

### Fixed
- History: row titles and subtitles were parsed as Pango markup, so extracted text containing `&` or `<` (for example "R&D" or code such as `if (a<b)`) produced an empty row title and `<b>`-style text lost its tags
- Clipboard: copying text (extracted text, QR URL, History rows) did not reach other applications, so it could not be pasted anywhere. `ClipboardService.set()` wrapped the text in a `GLib.Variant`, which GTK publishes only as the unreadable `GVariant` format; it now publishes a plain string (`text/plain`). Present since the change that replaced `Gdk.Clipboard.set_text()` (v0.1.5, v0.2.0)
- Silent CLI mode (`--silent`) never ran the OCR and then hung: the runner called `GLib.MainContext.push()`/`pop()`, which do not exist in PyGObject (`push_thread_default()`/`pop_thread_default()` do; `AttributeError`), and its main-loop callbacks took no arguments while PyGObject passes the source `user_data`, so every callback raised `TypeError` and not even the 60 s timeout could end the loop. Found on PyGObject 3.48.2; the only test mocked the whole runner
- Silent CLI mode (`--silent`): the copied text could not be pasted once the process exited, because the clipboard belongs to the process that set it. The text is now handed to the desktop clipboard manager when there is one; otherwise the process keeps serving the clipboard for up to 30 seconds, or until another application copies something, and then exits. Checked on X11 with and without a clipboard manager; on Wayland the backend cannot hand content to a manager, so only the wait applies
- CLI: `anura --file <image>` (with or without `--silent`) crashed with a `TypeError` before processing anything. The file name comes from GLib as a bytestring, `unpack()` turns it into a list of integers and `Path()` rejects that; it is now decoded to a string, non-ASCII names included. The test that covered this fed a plain string, which GLib never delivers. Found on PyGObject 3.48.2 / GLib 2.80

## [0.2.0] - 2026-09-21

### Added
- Added undo/redo buttons to the OCR result editor, synced with the shortcuts overlay
- Tessdata model integrity verification (defensive audit F1): build-time manifest `anura/data/tessdata_checksums.json` with pinned git-blob SHA-1 hashes (generated by `build-aux/generate_tessdata_checksums.py`), verified by `anura/utils/tessdata_integrity.py` before a downloaded model is installed; anti-drift check extended in `build-aux/check_tessdata_consistency.py`
- Eliminated manual dual-maintenance of the Flatpak manifests: the release manifest is now generated by `build-aux/release.sh` from the local manifest (never hand-edited) with release-time self-checks
- Synchronized the keyboard shortcuts overlay with the actions actually registered in the app: new Editor category (select all, copy, undo, redo, search, external editor), Text-to-Speech category with pause/resume (`<Primary><Alt>L`), and previously undocumented accelerators (`<Primary>comma` documented, duplicate aliases deduplicated)
- Added `tests/test_shortcuts_consistency.py`: bidirectional anti-drift test (headless-safe, per `docs/reference/dependencies.md`) ensuring the shortcuts overlay and `ActionRegistry` accelerators stay in sync, with a documented whitelist for native widget bindings (select-all, undo, redo, Escape)
- Migrated the OCR result text editor to **GtkSourceView 5** (`GtkSource.View`/`GtkSource.Buffer`) with native search bar (`<Primary>f`), editor preferences (line numbers, current line highlight, wrapping), and an "Open in External Editor" action (`<Primary><Shift>E`) with safe `Gtk.FileLauncher` handoff

### Fixed
- Fixed conftest.py: pytest collection/setup errors (reported under the 'error' key in terminalreporter.stats) are now printed alongside test failures ('failed' key) before os._exit() in pytest_sessionfinish, instead of being silently invisible in CI output
- Fixed screenshot fallback (BUG-004): trigger the bundled scrot fallback on any non-None portal error on X11 sessions
- Made tessdata downloads fully atomic (defensive audit F2): models are downloaded to `*.tmp` files and installed via `os.replace()`, so a crash mid-install can never leave a truncated `*.traineddata` in place
- Hardened OCR external-editor export files (defensive audit F3): exports now go to `$XDG_RUNTIME_DIR/anura/exports` (per-user, per-session) instead of the shared `/tmp/anura_exports`, created via `tempfile.mkstemp()` with mode `0600` and random names; stale export files are cleaned on boot
- Fixed leaked temporary screenshot file when the scrot spawn fails in the legacy X11 provider (defensive audit F4)
- Hardened the legacy scrot provider to reject group/world-writable binaries (defensive audit F5)
- Fixed dead next/prev search navigation in the OCR editor (defensive audit F6): PyGObject exposes `forward()`/`backward()` (the old `forward2`/`backward2` names do not exist on this binding), so the previous hasattr guards silently disabled navigation
- Enabled wrap-around in search (defensive audit F7): `GtkSource.SearchSettings` defaults to `wrap_around=FALSE`, so search stopped at the last/first match; wrap-around is now enabled at init
- Hardened preferences dialog init so TTS failures cannot break history binding
- Silenced isolated OCR worker terminal log flood
- Removed stale/incorrect shortcut entries from the shortcuts overlay (`<Primary>?`, `<Primary>/`, `<Primary><Shift>O`, `F1`, `F10`, `Tab`/`Shift+Tab`) and deduplicated accelerator aliases both in the overlay and `ActionRegistry` (`<Primary>F1`/`<Primary>K`/`<Primary>W`/`<Primary>Period` removed in favour of `<Primary>H`/`<Primary>Q`/`<Primary>Comma`)
- Repinned orphaned tessdata commit SHAs to release tag 4.1.0 in `anura/config.py` and both Flatpak manifests (Bug #6)
- Exposed cached language list and pause state on `TTSService` for correct TTS UI state synchronization

### Changed
- Regenerated and reorganized translation catalogs
- Documented the GTK/PyGObject headless testing approach (system `python3-gi` + venv site-packages via `PYTHONPATH`) in `docs/reference/dependencies.md`
- CI: added `gir1.2-gtksource-5` system dependency to the GTK integration test workflow
- Updated documentation screenshots (welcome, extracted, history, preferences) in `README.md` and the AppStream metainfo
- Reorganized the `docs/` tree: normative references moved to `docs/reference/`, the active plan kept in `docs/planning/`, and resolved audit reports archived under `docs/audit/legacy/reports/` with consistent kebab-case names; added `docs/audit/README.md` and updated all cross-references
- Removed the stale `docs/audit/legacy/raw/` tool outputs (clean/empty bandit+ruff runs, environmental mypy noise, outdated vulture listings)

## [0.1.5] - 2026-09-11

### Added
- Implemented Extraction History V1 (opt-in local history of recent OCR extractions, newest-first JSON persistence with atomic writes and corruption recovery, HistoryPage with clear action, `history-enabled`/`history-limit` GSettings keys, `win.show-history` navigation) — see `docs/history-v1.md`
- Added F-005 runtime dependency coverage check (`build-aux/check_runtime_dependency_coverage.py`) enforcing that every uv.lock runtime dependency is represented in both Flatpak manifests
- Implemented UI theme selector with System, Light, and Dark options using `Adw.StyleManager`
- Added `color-scheme` GSettings key for persistent theme preference storage
- Implemented selection-aware text statistics and actions on OCR results page (Palette)
- Added Undo/Redo functionality to ExtractedPage for improved text editing workflow
- Enhanced accessibility with keyboard navigation improvements and better drop button tooltips
- Implemented NormCap-inspired UX improvements for better user experience
- Added comprehensive accessibility enhancements to WelcomePage and LanguagePopover
- Implemented dynamic copy button tooltip and accessibility feedback in Palette
- Added manual workflow execution capability for dependency sync in CI/CD
- Configured Dependabot for automated dependency updates on testing branch
- Added comprehensive docstrings, type hints, and integration tests for ClipboardService fallback paths
- Implemented six-pillar CI hardening framework for improved test reliability
- Added enhanced diagnostic logging for host screenshot operations

### Fixed
- Resolved `AtomicTaskManager` deadlock and child process hang issues
- Fixed GTK integration test suite hanging with comprehensive multi-step fix (atexit, os._exit(), Weston cleanup, signal sourcing)
- Eliminated clipboard infinite fallback loop and stale source_remove warnings
- Fixed TTS play/pause/stop state desynchronization in extracted_page (5 bugs)
- Resolved X11 screenshot fallback issues in testing branch
- Added `BrokenProcessPool` recovery to `AtomicTaskManager` for enhanced error handling (CRIT-01)
- Fixed OcrController weak references against ReferenceError during window destruction
- Fixed static type-checking and path concatenation issues
- Fixed flatpak pybind11 cmake path resolution during zxing build
- Resolved clipboard spinner stuck and source_remove warnings (BUG-PASTE + BUG-032)
- Fixed path mocking in tests (Path.exists instead of os.path.exists)
- Caught PermissionError from Path.exists() for inaccessible parent directories
- Released _state_lock before ProcessPoolExecutor.shutdown() to prevent deadlock
- Fixed test assertion to use GTK4 set_content() instead of removed set_text()
- Resolved GObject metaclass conflicts and TESSDATA_DIR patching in tests
- Fixed ruff linting violations (F841 unused variable, I001 import sorting, B028, SIM910)
- Fixed CI workflow SHA resolution errors and image pull failures
- Fixed undefined HTML variable and unused import in CI workflow
- Hardened CI/CD workflows with immutable action pinning and credential protection
- Resolved 4 bugs from debug session 2026-05-25
- Fixed 7 bugs identified by automated Kimi analysis (2026-05-26)
- Reset fallback flag in clipboard service and enhanced portal error logging
- Remediated GTK integration test failures and GTK4 regressions
- Fixed Python-quality CI failures
- Removed complex async callback tests that fail in CI
- Fixed failing integration tests by simplifying test logic
- Terminated child processes to prevent GHA limbo hangs
- Resolved structural test mismatches and cleaned TTS debt
- Restored missing TTSService facade export
- Fixed DialogManager import in AnuraWindow
- Fixed ruff style checks and import ordering across services

### Changed
- Decomposed LanguageManager into specialized managers (DownloadManager, CacheManager, LanguageValidator) in anura/services/language/
- Optimized OCR layout parsing and structural reconstruction (Bolt optimization)
- Optimized image mean calculation in ContrastEnhancementFilter
- Restructured and modernized CI/CD pipeline with comprehensive GTK integration test fixes
- Performed systematic bug hunting and modernization sweep across the codebase
- Technical remediation for Flatpak, Pathlib, and Safety patterns
- Rewrote AI-generated comments for clarity and professionalism
- Translated project documentation from Italian to English
- Updated flatpak-dependencies.yml workflow
- Moved audit-related files (bugs-observed.json, bugs-summary.md) into dedicated docs/audit/ directory
- Exposed loading_languages and finalized test suite alignment
- Style fixes: import ordering and typing annotations across services
- Audit-driven stability hardening and build fixes
- Updated Flatpak dependencies: Leptonica 1.87.0, imlib2 1.12.6
- Updated dependency versions: ruff ≥0.15.21, meson ≥1.11.2, pytest ≥9.1.1, pillow ≥12.3.0
- Enhanced error handling and logging throughout the application
- Improved portal environment diagnostics and user guidance
- Unified GI mock injection to resolve metaclass conflict in non-CI mode
- Synced CI ignore lists and added ANURA_CI_TEST_MODE to python-quality job

### Security
- **HIGH**: Fixed Pango markup injection in notifications (hardened against markup attacks)
- **HIGH**: Fixed hierarchical ID collision and OCR pipeline instability
- **HIGH**: Fixed Config Layer Leakage and enhanced lifecycle safety
- Hardened local data storage permissions for sensitive data
- Hardened sanitize_text by stripping Private Use (Co) and Surrogate (Cs) Unicode categories
- Hardened is_safe_url_string to reject mixed-script homograph attacks
- Hardened image resource validation for DoS prevention (MAX_IMAGE_SIZE_BYTES enforcement)
- Remediated architectural resource leaks across core services (v2/v3)
- Completed Phase 2 forensics and remediated logic flaws across the codebase
- Installed Claude Bug Bounty toolkit and required security scanners for ongoing auditing
- Implemented dynamic URI scheme validation in ShareService (BUG-035 remediation)

### Removed
- Deleted CHANGELOG_REMEDIATION.md

## [0.1.4.3] - 2026-05-16 {version-0.1.4.3}

### Added

- Advanced TextPreprocessor utility with intelligent image enhancement and OCR text cleanup
- Smart text preprocessing including common OCR error correction, whitespace normalization, and punctuation fixing
- Structured data extraction from OCR text (emails, URLs, phone numbers, dates)
- Adaptive image enhancement based on brightness/contrast analysis for better OCR accuracy
- Modern ShortcutsOverlay widget with live search and categorized keyboard shortcuts
- Enhanced keyboard shortcuts overlay with search functionality and elegant Adw.Window-based interface
- Configurable logging level via `ANURA_LOG_LEVEL` environment variable for debugging
- Host screenshot fallback system using `flatpak-spawn --host` for missing portal backends
- Persistent install-hint banner when screenshot portal backend is missing
- Desktop-aware portal advice messages with environment-specific guidance
- Enhanced diagnostic logging for host screenshot operations
- Comprehensive drag-and-drop functionality with visual feedback and proper lifecycle management
- Complete drag-and-drop event handlers (enter, leave, motion, drop) with CSS styling for hover states
- Enhanced AboutDialog with complete legal information for Flathub compliance
- Full copyright and MIT license text for transparency
- Open source dependencies attribution in legal information
- Complete legal information ensuring Flathub compliance requirements
- Asynchronous Drag-and-Drop implementation to prevent UI freezes, especially in VM environments
- Fallback for URI list on clipboard texture read failure
- Optimized image thresholding using Look-Up Tables (LUT) for performance
- Enhanced accessibility and Micro-UX improvements for the OCR results page
- Persistent Drag-and-Drop controller for better stability
- Clickable QR URL notifications via XDG Desktop Portal (Flatpak-safe)
- Autocopy for QR-detected URLs with improved toast feedback
- Pattern-based file filters for image selection dialog
- Real-time word count status bar in OCR results page
- Standardized localization infrastructure and Application ID

### Fixed

- Fixed notification service cleanup by removing incorrect underscore reference
- Fixed URI validator function call in window.py for proper URL validation
- Fixed dialog response handling for browser launch failures with proper error management
- Fixed extra language combo signal connection to ensure it's always connected regardless of settings
- Fixed modal property removal from shortcuts window for better user experience
- Fixed keyboard shortcuts test to match correct method signature with _param parameter
- Fixed five UI/runtime bugs from Flatpak debug log
- Fixed three additional bugs (release notes parse, TTS AttributeError, screenshot diagnostic)
- Fixed Gio.Subprocess.wait() method usage instead of wait_sync()
- Fixed host screenshot file existence check with retry loop
- Fixed designer credit and share-row action prefix corrections
- Fixed incomplete URL substring sanitization (security fix)
- Resolved multiple critical runtime bugs, memory leaks, and signal leaks across core services
- Fixed X11 Drag-and-Drop deadlocks and portal file transfer freezes
- Corrected Text-to-Speech (TTS) state transitions, visual feedback, and "zombie audio" issues
- Fixed localization initialization and updated Italian translations
- Fixed broken status window in "Legal Information" page
- Resolved GTK navigation warnings and ruff linting violations (E501, W292)
- Fixed About dialog property names and legal information display
- Improved error handling for browser launch and file filters
- Fixed UI spinner animations and state management
- Fixed missing trailing newline in anura/window.py
- Fixed path traversal vulnerability in LanguageManager.remove_language (HIGH severity)
- Fixed URL userinfo spoofing in uri_validator (security fix)
- Fixed URL truncation during QR code extraction and hand-off
- Fixed clipboard infinite fallback loop on image read failures
- Fixed callback exception handling in clipboard service
- Fixed Gio.Notification API usage for XDG Portal compatibility
- Fixed i18n bindings in Flatpak and globalized autocopy behavior
- Fixed Flatpak hybrid UI regression (i18n)
- Fixed localization issues and cleaned up UI code
- Fixed broken state warning on Acknowledgements page
- Fixed navigation focus race condition
- Removed compiled gresource from git tracking and updated .gitignore
- Fixed line length violation in notification service tests

### Changed

- Enhanced screenshot service with host fallback capabilities
- Improved error handling and logging throughout the application
- Better portal environment diagnostics and user guidance
- Updated release notes generation logic with hybrid GitHub link display
- Lower threshold for GitHub link from 15 to 12 items for better UX
- Enhanced drag-and-drop drop target attachment to welcome page widget
- Improved release notes generation with tracking for truncated sections
- Refactored Drag-and-Drop system for improved reliability
- Optimized Flatpak build and updated dependencies (urllib3)
- Improved OCR pipeline and image processing performance
- Deep codebase audit and concurrency hardening across all services
- Pre-compiled regex patterns and optimized PIL thresholding for performance
- Optimized URI validation performance with compiled regex
- Optimized image enhancement pipeline
- Optimized QR code detection by restricting symbol scan
- i18n: full audit and fixed hardcoded UI strings across the application
- i18n: stabilized infrastructure and synchronized translations (Phase 1A)
- i18n: finalized Italian localization and fixed navigation focus (Phase 1B)
- Palette: UX and accessibility improvements across ExtractedPage
- Refactored language API, removed dead code, improved test coverage
- Standardized loading spinner size across the application
- Updated testing documentation

## [0.1.4.2] - 2026-05-05 {version-0.1.4.2}

### Fixed

- Fixed `__slots__` conflict in ClipboardService - missing `_cancellable` in declaration causing AttributeError
- Fixed ruff linting errors across codebase including import sorting and code style issues
- Fixed concurrency issues in TTS and clipboard services against race conditions
- Fixed memory leaks and added structural robustness throughout application
- Fixed API contract, thread safety, and race condition issues in core services
- Fixed Flatpak manifest warnings by removing `_comment` properties

### Changed

- Extracted URI validation to utils module and relaxed IP/localhost restrictions
- Improved code quality with comprehensive type hints and cleanup
- Implemented atomic cancellation for Clipboard and thread-safe signal emission for TTS GStreamer bus
- Enhanced thread safety patterns across all services
- Added comprehensive unit tests for core services
- Resolved all remaining linting errors and line length issues

## [0.1.4.1] - 2026-05-02 {version-0.1.4.1}

### Fixed

- Fixed missing `Adw.init()` call causing "greyed out UI" on some systems
- Fixed GResource bundle loading to properly exit on failure instead of continuing with broken UI
- Fixed notification portal API to use proper GLib.Variant format (a{sv}) for XDG Portal compatibility
- Fixed notification import consistency with absolute imports throughout main.py
- Fixed HTML escaping in release notes generation to prevent XSS vulnerabilities

### Changed

- Added CHANGELOG.md as source of truth for release notes
- Added translate URL to metainfo for Weblate integration

## [0.1.4] - 2026-05-01 {version-0.1.4}

### Fixed

- Fixed critical thread-safety issues and race conditions in language manager and screenshot service
- Fixed memory leaks in widget lifecycle management and GStreamer bus watch
- Fixed all Flatpak manifest dependencies (requests, urllib3, certifi, hatchling, pyzbar)
- Fixed blueprint compiler output directory for Flatpak builds
- Fixed gresource bundle loading with correct UI file paths
- Fixed filesystem permissions for Open Image and Drag & Drop in sandbox
- Fixed silent CLI mode to properly exit without opening UI window
- Fixed CLI exit code to return 0 on success instead of 1
- Fixed code quality issues: lint errors, import sorting, gettext shadowing
- Fixed Telegram share URL to send text as message instead of URL

### Changed

- Updated OARS content rating for Flathub compliance
- Improved CI/CD workflow with smoke tests and build verification
- Updated tessdata-fast to pinned commit SHA for reproducible builds

## [0.1.3] - 2026-04-25 {version-0.1.3}

### Fixed

- Fixed import error in screenshot service (tessdata_config casing)
- Fixed missing init_tessdata() method in LanguageManager
- Fixed settings module path mismatch (moved to anura/services/settings.py)
- Fixed blueprint-compiler GIRepository compatibility with GNOME Platform 49

### Changed

- Improved TTS cache file location (XDG_CACHE_HOME)

## [0.1.0] - 2026-04-23 {version-0.1.0}

### Added

- Initial release of Anura (fork of Frog)
- Complete rebranding to Anura
- Removed all telemetry and PostHog tracking for total privacy
- Optimized sharing service: added X (formerly Twitter) and Instagram
- Updated dependencies for modern Linux distributions
