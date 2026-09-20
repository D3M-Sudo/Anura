# Anura — audit/legacy/reports (historical index)

Append-only archive of historical QA/security reports. **Do not treat findings
here as open issues** — every report below ends with applied fixes already
merged on `testing`. Archival rules live in `../README.md`.

| Report | Date | Type | Key content | Status |
| --- | --- | --- | --- | --- |
| [bug_hunt_report_AUTO_20260606T194022Z.md](bug_hunt_report_AUTO_20260606T194022Z.md) | 2026-06-06 | Automated bug hunt | TTS lock inversion on EOS, regression checks (NEW-017…NEW-020) | Resolved |
| [bug_hunt_report_AUTO_20260608T023529Z.md](bug_hunt_report_AUTO_20260608T023529Z.md) | 2026-06-08 | Automated bug hunt | TTS resume-on-new-request flaw, obsolete type hints in OCR pipeline | Resolved |
| [bug_hunt_report_20260610.md](bug_hunt_report_20260610.md) | 2026-06-10 | Technical audit | Hardcoded Flatpak manifest paths, loop-variable overwrite (PLW2901), language-manager startup race, TTS resume logic | Resolved |
| [bug_hunt_report_20260617.md](bug_hunt_report_20260617.md) | 2026-06-17 | Audit | File permissions (EXE002), Flatpak Python paths, headless GObject coverage, complexity/refactoring | Resolved |
| [bug_hunt_report_AUTO_20260714T064630Z.md](bug_hunt_report_AUTO_20260714T064630Z.md) | 2026-07-14 | Automated bug hunt | Lazy-init race, unchecked resource metadata, leaked timeout source, signal/deadlock analysis | Resolved |
| [bug_hunt_report_AUTO_20260801T114500Z.md](bug_hunt_report_AUTO_20260801T114500Z.md) | 2026-08-01 | Automated bug hunt | Hardcoded site-packages path, GStreamer bus teardown race, Pillow version drift, weakref lifetime | Resolved |
| [bug_hunt_report_AUTO_20260803T072523Z.md](bug_hunt_report_AUTO_20260803T072523Z.md) | 2026-08-03 | Automated bug hunt | Headless metaclass conflict, async GStreamer bus callbacks, EXDEV/hardlink handling | Resolved |
| [bug_hunt_report_QA.md](bug_hunt_report_QA.md) | 2026-08-16 | Pre-release QA | Quality, bug hunt and code review for v0.1.5 | Resolved |
| [bugs-summary.md](bugs-summary.md) | 2026-08-16 | QA summary | 8 bugs found / 8 fixed; tools: ruff, bandit, mypy, pytest, meson, flatpak-builder | Resolved |
| [bugs-observed.json](bugs-observed.json) | 2026-08-16 | QA data | Structured bug data (companion of `bugs-summary.md`) | Resolved |
| [history-v1-plan.md](history-v1-plan.md) | 2026-08 | Superseded plan | Pre-implementation History V1 plan (baseline `testing @ a52f4563`); normative reference is `docs/reference/history-v1.md` | Superseded |
| [diagnosis-vm-followup-2026-09-17.md](diagnosis-vm-followup-2026-09-17.md) | 2026-09-17 | Follow-up diagnosis | VM findings: model-quality cache invalidation, screenshot spinner, match-case icon, external-editor portal | Resolved |
| [diagnosis-full-test-tiers-2026-09-20.md](diagnosis-full-test-tiers-2026-09-20.md) | 2026-09-20 | Diagnostics / test audit | Full diagnostics and test-tier audit at `HEAD: aba2884` (5 skipped tests, dependency coverage) | Resolved |
