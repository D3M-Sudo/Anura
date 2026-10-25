# Anura — Milestone 2: Flathub Readiness (planning)

**Status:** Approved 2026-10-22, scheduled after Milestone 1
(`docs/planning/runtime-fixes-m1.md`).
**Scope:** 31 open issues about the Flatpak manifests, CI, release tooling and
Flathub submission prerequisites.
**Constraint:** `flatpak-builder`, `meson` and the GNOME 51 SDK are not available in
the planning sandbox. Every phase is therefore validated by pushing the branch and
watching the `flatpak-builder` and `python-quality` jobs; a PR is only mergeable once
the corresponding run is green.

## Why after Milestone 1

Every manifest edit flows into `release.sh` → `flatpak/io.github.d3msudo.anura.json`.
Landing packaging changes while runtime code is still moving would force repeated
manifest regeneration and mix two different verification models (headless pytest vs.
Flatpak builds). Milestone 1 also produces the dependency changes that Milestone 2
must mirror.

## Phase 2.0 — Build correctness

| # | Sev | Fix | Depends on |
| --- | --- | --- | --- |
| 479 | P1 | GNOME Platform/SDK 50 → 51 in the local manifest and all modules | — |
| 542 | P1 | Replace imlib2 configure flags the pinned release does not accept | 479 |
| 543 | P1 | Remove/replace `--disable-training` for Tesseract 5.3.4 | 479 |
| 546 | P2 | Exclude imlib2 headers, `.a/.la`, pkg-config files, helper binaries and demo data | 542 |
| 480 | P2 | Remove hardcoded `/app/lib/x86_64-linux-gnu` from `GI_TYPELIB_PATH`/`LD_LIBRARY_PATH` | 479 |
| 482 | P2 | Remove build-only Python tooling (scikit-build-core, pybind11, nanobind) from the runtime | — |
| 477 | P2 | Fail-closed license collection instead of `find ... || true` | — |
| 493 | P2 | Automated license inventory check of the final bundle | 477 |

Rationale: 479 is the highest-risk change (forces a full rebuild and can expose
further flag breakage), so it goes first; 542/543 are the flag fixes it may reveal;
546/482 trim the installed tree; 477/493 make licensing auditable.

## Phase 2.1 — CI and release integrity

| # | Sev | Fix |
| --- | --- | --- |
| 491 | P2 | Run the existing manifest-drift checker in CI on every manifest change |
| 484 | P2 | Validate the **generated** release manifest, not only the local one |
| 483 | P2 | Make desktop-file and AppStream validation mandatory |
| 541 | P3 | Fix the Codecov upload (token) or remove the failing step |
| 535 | P3 | Emit real newlines in the dependency-update issue body |
| 486 | P2 | Run the non-GTK tests that the current job skips |
| 488 | P2 | `uv sync --locked` and pin the uv version |
| 487 | P2 | `release.sh` preflight: clean worktree, tag existence, version coherence |
| 489 | P2 | Populate GitHub release notes from `CHANGELOG.md` |
| 485 | P3 | Never generate placeholder release notes |
| 481 | P3 | Replace the 0.2.1 placeholder notes in the metainfo |
| 494 | P2 | Verify and publish artifacts for every supported architecture |

Ordering: guardrails (491/484/483/486/488) before automation (487/489/485/481);
494 after 480.

## Phase 2.2 — Submission readiness

| # | Sev | Fix |
| --- | --- | --- |
| 504 | P1 | Document the Python dependency manifest and prove a clean offline build |
| 503 | P2 | Create the dedicated Flathub submission repository (manifest at root) |
| 501 | P2 | Pin the Anura source to an immutable, verifiable commit |
| 499 | P3 | Stable screenshot URLs (not a mutable branch) |
| 498 | P1 | Justify every `finish-arg`; test Wayland/X11 including the scrot fallback |
| 490 | P2 | Re-evaluate read-only XDG filesystem permissions |
| 497 | P2 | English/gettext completeness and final compiled metainfo |
| 495 | P1 | Disclose that TTS sends text to Google (metainfo + docs) |
| 496 | P2 | AI provenance statement for code, docs and packaging |
| 500 | P2 | Functional Flatpak tests (OCR/TTS/model download/screenshot + integrity negatives) |

Rationale: documentation and permissions must describe the final artifact, so they
come last. #495 pairs with the runtime fix for #505 and must use the same wording.

## Milestone 3 — History V2 features (not scheduled)

#454 (open in external editor), #455 (replay through TTS), #456 (re-OCR) require an
updated `docs/planning/history-v2-interactive-rows.md` design before any code.

## Verification per phase

1. `uv run python build-aux/check_manifest_consistency.py`
2. `uv run python build-aux/check_runtime_dependency_coverage.py --manifest local`
3. Push the branch and watch `flatpak-builder` plus `python-quality` on GitHub Actions.
4. At release time only: `release.sh` regeneration and
   `check_tessdata_consistency.py`.
