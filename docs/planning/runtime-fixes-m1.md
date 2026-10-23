# Anura — Milestone 1: Runtime Fixes (planning)

**Status:** Active — approved 2026-10-22 (option A: Milestone 1 now, Milestone 2 later).
**Baseline:** `feature @ bc165c3`.
**Scope:** 36 open issues affecting application code (bugs, security, privacy,
reliability, performance, hygiene). Packaging/Flathub work is tracked separately in
`docs/planning/flathub-readiness-m2.md`.
**Owning documents:** this file, `docs/README.md`.

## Progress

| Batch | State | Landed |
| --- | --- | --- |
| 0 — Quality gates | Done (workflow diff pending maintainer) | #518, #517, #514, #515, #516 |
| 1 — Security & privacy | Done | #527, #524, #522, #509, #505, #529 |
| 2 — Reliability & lifecycle | Partial — 6 of 11 | #547, #528, #530, #533, #523, #520 |
| 3 — State, UI & privacy UX | Partial — 2 of 11 | #534, #537 |
| 4 — Hygiene | Not started | — |

Baseline at Batch 0: 323 headless tests passing; after the current work: 406 passing
(+83 regression tests). Gates at every commit: `ruff check`, `ruff format --check`,
`bandit -c pyproject.toml -r .`, non-strict `mypy`, `pytest -m "not gtk"`.

### Resume notes

Remaining Batch 2 work, in dependency order:

1. **#531** — manager-owned shutdown cancellable + close of the active response.
   #520 (response ownership) has landed, so this is the only prerequisite left.
2. **#507** — replace the single task slot with per-kind lanes in
   `AtomicTaskManager`; always deliver callback *or* errorback. Largest change of
   the milestone and the prerequisite for the three below.
3. **#508** — proportional TTS watchdog (needs the lane generation ids from #507).
4. **#506** — bounded shutdown wait (same file as #507).
5. **#526** — executor identity guard on `BrokenProcessPool` (same file as #507).

Remaining Batch 3 work: #540 → #510 → #511 (history sequence),
then #536 (non-initializing TTS lookup), #532 (cached gTTS catalog),
#539 (idle source ids), #538 (DnD cancellable identity), #525 (clipboard
fallback identity), #521 (tessdata lease).

Batch 4: #512, #513 (AGENTS.md alignment), #544.

### Deviations from the original plan

- #514, #515 and #516 moved from Batch 4 to Batch 0 (they were the only mypy
  errors left once `--ignore-missing-imports` was enabled).
- #509 only needed `anura/window.py`: the CLI path already validates the path
  through `validate_image_resource()` before decoding.
- #534 and #537 landed in Batch 2/3 order inverted relative to the plan (both are
  notification fixes and share no files with the earlier reliability work).
- The CI workflow edit in #517 cannot be pushed by this identity; the diff is
  posted on the issue.

## Motivation

The repository has 70 open issues but no severity labels, so triage is implicit and
regressions compete with cosmetic hygiene. This plan assigns every runtime issue a
severity (P0–P3), a batch, an execution order, the files it touches, and the
regression test that proves the fix. Batches are ordered so that shared files are
modified once and so that later refactors do not invalidate earlier tests.

## Baseline measured on `feature @ bc165c3`

| Check | Result |
| --- | --- |
| `pytest tests/ -m "not gtk"` | 323 passed, 28 skipped, 2 collection errors (`gi` not installed in the audit sandbox) |
| `ruff check` | 0 findings |
| `ruff format --check` | 34 files would be reformatted |
| `mypy --strict anura/` | 329 errors in 49 files |
| `bandit -r anura/` | 0 issues |
| `vulture anura/` | ~20 findings at 60% confidence |

Consequence: `ruff format --check` and `mypy --strict` cannot be enabled as blocking
gates today; see D4.

## Severity rubric

| Level | Definition | Release policy |
| --- | --- | --- |
| **P0** | Security/privacy exploitable, data integrity, denial of service | Blocks release |
| **P1** | Crash, hang, functional loss, conditional privacy leak | Fix in this milestone |
| **P2** | Degradation, rare race, resource leak, performance | Fix after all P1 |
| **P3** | Hygiene, type safety, tests, CI | Dedicated batch |
| `*` | Requires a product/architecture decision before code | Decision gate |

## Execution model

- **Triage first.** Most issues cite `testing @ 9e9e2247`; the work branch is
  `feature @ bc165c3`. Before writing code, reproduce or re-verify each finding on
  the current tree. If already fixed, close the issue with evidence and no code.
- **One commit per issue** (`fix(scope): summary` + `Refs #NNN`), **one PR per
  batch**. Issues are closed only after the batch gate is green.
- **Gate per batch:** `ruff check`, `bandit -r anura/`, `mypy` (non-strict),
  `pytest -m "not gtk"`, plus the regression tests listed below.
- **No new runtime dependencies.** No direct edits to protected files
  (`po/*.po`, `anura/_release_notes.py`, `data/ui/*.ui`, release manifest).
  `CHANGELOG.md` receives `[Unreleased]` entries only.
- GTK-marked tests cannot run in the audit sandbox (no `gi`, no display); such
  fixes ship with headless tests plus a manual/CI check noted in the PR.

## Decisions

| ID | Question | Resolution |
| --- | --- | --- |
| **D1** | #505 — gTTS 2.5.4 hardcodes `verify=False` with no public switch | Subclass `gTTS` inside `SpeechGenerator` overriding `stream()` with `verify=True`, pinned to the audited upstream behaviour; test asserts `verify=True` |
| **D2** | #529 — QR autolinks default `true` | Default `false`; existing users keep their stored value; loopback/private destinations always require confirmation |
| **D3** | #513 — code (5 files, gzip) vs `AGENTS.md` (3 files, plain) | **Documentation is stale**: commit `26f08f5` (2026-05-26) intentionally introduced 5 rotations + gzip ("Hardened logging with 5-file retention and gzip compression"), one day after the `AGENTS.md` wording landed in `a2b0a74` (2026-05-25). Action: update `AGENTS.md`, do **not** change `logger.py` |
| **D4** | #517 — `mypy --strict` reports 329 errors | Enable non-strict `mypy` as a CI gate now; per-module strictness tracked separately. `ruff format --check` only after the format-only commit |
| **D5** | #521 — tessdata liveness | Stop deleting top-level models belonging to other languages; pool subdirectories get an owner PID + heartbeat lease before deletion |

## Batches

### Batch 0 — Quality gates (P3, prerequisite)

| # | Sev | Fix | Files |
| --- | --- | --- | --- |
| 518 | P3 | `[tool.bandit]` with `targets = ["anura"]`, `exclude_dirs = ["tests", ...]` | `pyproject.toml` |
| 517 | P3 | CI: `ruff format --check`, `bandit`, non-blocking `vulture`, non-strict `mypy`; formatting baseline as a separate commit | `.github/workflows/main.yml`, `pyproject.toml` |
| 514 | P3 | `None` guard in `_on_clear_response` | `anura/widgets/history_page.py` |
| 515 | P3 | `TypedDict` entries for the shortcuts data model | `anura/widgets/shortcuts_overlay.py` |
| 516 | P3 | `type: ignore[no-redef]` on the headless `GObject` stub | `anura/utils/signal_manager.py` |

**Reordering note:** #514, #515 and #516 moved from Batch 4 into Batch 0. After
`--ignore-missing-imports`, non-strict `mypy` reports exactly four errors, all from
those three issues; fixing them is what makes the mypy gate blocking instead of
advisory. Batch 0 is therefore a hard prerequisite for every later batch.

Batch 0 lands first so that every later batch is checked by the same gates and so
that the 29-file formatting diff does not collide with functional changes.

### Batch 1 — Security and privacy (P0/P1)

| # | Sev | Fix | Files | Regression test |
| --- | --- | --- | --- | --- |
| 527 | **P0** | History dir `0700`, temp file `0600` via `os.open(..., O_CREAT \| O_EXCL)`, correct under umask 022 | `anura/services/history_service.py` | `tests/test_history_permissions.py` |
| 524 | **P0** | Hard cap (~1 MiB) on `text/uri-list` streams; stop reading, cancel/close, no retained chunks | `anura/services/clipboard_service.py` | `tests/test_clipboard_stream_limits.py` |
| 522 | **P0** | Explicit pixel/dimension budget (~40 MP) and `DecompressionBombWarning` promoted to error in both sync and isolated paths | `anura/utils/validators.py`, `anura/config.py`, `anura/services/screenshot_service.py` | `tests/test_image_pixel_limits.py` |
| 509 | P1 | `stat()` before `load_contents_async` (file dialog and `--file`) | `anura/window.py`, `anura/main.py`, `anura/utils/validators.py` | `tests/test_image_size_precheck.py` |
| 505 | **P0\*** | TLS verification restored for gTTS traffic (D1) | `anura/services/tts/speech_generator.py` | `tests/test_tts_tls_verify.py` |
| 529 | P1\* | `autolinks` default `false`; explicit confirmation for QR-derived URLs (D2) | `data/io.github.d3msudo.anura.gschema.xml`, `anura/main.py` | `tests/test_qr_autolinks_policy.py` |

### Batch 2 — Reliability and lifecycle (P1/P2)

| # | Sev | Fix | Files |
| --- | --- | --- | --- |
| 547 | P1 | Move `gtts.gTTS(...)` inside the guarded block; clean partial output; re-raise `SystemExit`/`KeyboardInterrupt` | `anura/services/tts/speech_generator.py` |
| 528 | P1 | `Gst.filename_to_uri()` instead of `f"file://{path}"` | `anura/services/tts/audio_player.py` |
| 530 | P1 | `urlsplit()`-based hostname/TLD validation independent of port/query/fragment | `anura/transformers/url_transformer.py` |
| 533 | P1 | `timeout=` on `image_to_data`, kill the Tesseract child on cancel, recover the single-worker pool | `anura/services/screenshot_service.py`, `anura/config.py` |
| 523 | P1 | Non-blocking file-ready wait (`Gio.timeout_add` or worker thread + idle) | `anura/services/screenshot/legacy_provider.py`, `anura/utils/file_ready_retry.py` |
| 520 | P2 | `with session.get(..., stream=True)` / `finally: response.close()` on every early return | `anura/services/language/download_manager.py` |
| 531 | P1 | Manager-owned shutdown cancellable + close of the active response | `anura/services/language/download_manager.py`, `anura/main.py` |
| 507 | P1 | Per-kind lanes (ocr/tts/capture) instead of a single slot; always deliver callback **or** errorback; no orphan MP3 | `anura/core/atomic_task_manager.py`, callers |
| 508 | P2 | Timeout proportional to text length instead of fixed 35 s | `anura/controllers/tts_controller.py`, `anura/config.py` |
| 506 | P1 | Shutdown with deadline, no unbounded join on TTS work | `anura/core/atomic_task_manager.py`, `anura/main.py` |
| 526 | P2 | Tear down only when `self._process_executor is failed_executor` | `anura/core/atomic_task_manager.py` |

Ordering constraints: `520 → 531`; `507 → 508 → 506 → 526`; `547` and `528` are
independent and land first.

### Batch 3 — State, UI and privacy UX (P1/P2)

| # | Sev | Fix | Files |
| --- | --- | --- | --- |
| 540 | P1 | Restore the in-memory cache when `_persist()` fails; UI distinguishes failure from success | `anura/services/history_service.py`, `anura/widgets/history_page.py` |
| 510 | P1 | Live `history-limit` via setter + `changed::history-limit` | `anura/window.py`, `anura/widgets/preferences_general_page.py`, `anura/services/history_service.py` |
| 511 | P2 | Persist off the main thread with coalesced writes and a per-entry size cap | `anura/services/history_service.py`, `anura/controllers/ocr_controller.py` |
| 534 | P1 | Generic notification body; no OCR text by default | `anura/controllers/ocr_controller.py` |
| 537 | P2 | Single `NotificationService` instance via `get_notification_service()` | `anura/main.py`, `anura/controllers/ocr_controller.py` |
| 536 | P1 | Clean up TTS only if already instantiated (non-initializing lookup) | `anura/main.py`, `anura/utils/singleton.py` |
| 532 | P2 | Use the cached gTTS catalog on the UI thread; refresh asynchronously under a lock | `anura/widgets/preferences_general_page.py`, `anura/services/tts/language_mapper.py` |
| 539 | P2 | Track and remove `GLib.idle_add` source IDs on destroy | `anura/widgets/preferences_dialog.py` |
| 538 | P2 | Per-operation cancellable; clear only on identity match | `anura/widgets/welcome_page.py` |
| 525 | P2 | Same identity rule for the URI-list fallback | `anura/services/clipboard_service.py` |
| 521 | P2 | Never delete other-language models; PID + heartbeat lease for pool directories (D5) | `anura/utils/cleanup.py` |

Ordering constraints: `540 → 510 → 511`.

### Batch 4 — Hygiene (P3)

`#512` (loguru in history service), `#513` (`AGENTS.md` alignment, per D3),
`#544` (test that actually exercises constructor initialisation).

`#514`, `#515` and `#516` were moved into Batch 0 (see the reordering note there).

## Verification

```bash
uv run ruff check .
uv run ruff format --check .
uv run bandit -r anura/
uv run mypy anura/
uv run pytest tests/ -v -m "not gtk"
```

GTK/toolkit paths (`#523`, `#532`, `#538`, `#539`, `#521`, `#529`) additionally
need a smoke test on a real desktop session; the PR states which paths were
verified manually.

## Open blockers

- **#517 — workflow wiring:** the CI automation identity (`cline-cloud[bot]`) is a
  GitHub App without the `workflows` permission, so it cannot push changes to
  `.github/workflows/*.yml`. The configuration and the local commands are in place
  (`[tool.mypy]`, `[tool.bandit]`, format baseline, clean mypy); the workflow diff is
  posted on the issue for a maintainer to apply.

## Out of scope

- Milestone 2 (packaging/Flathub, 31 issues): `docs/planning/flathub-readiness-m2.md`.
- Milestone 3 (History V2 features #454–#456): requires an updated design document
  in `docs/planning/history-v2-interactive-rows.md` before implementation.


