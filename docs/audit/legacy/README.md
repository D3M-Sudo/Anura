# Anura — audit/legacy (historical, append-only)

This directory preserves **historical** QA/security audit material for
traceability. Do **not** treat findings here as open issues — every report
below ends with applied fixes already merged on `testing`.

## Layout

- `reports/` — human-readable reports (bug hunts, QA summaries, VM/full
  diagnoses) plus the superseded pre-implementation plan
  `reports/history-v1-plan.md` and its companion `bugs-observed.json` /
  `bugs-summary.md`. See `reports/README.md` for the per-report index.

## Rules

- **Append-only**: add new dated reports, never rewrite or delete existing files.
  Exception (2026-09-21): the former `raw/` tool outputs were removed during the
  `docs/` consolidation — they held no actionable findings (clean bandit run,
  empty ruff output), or stale/environmental noise (mypy `gi` stubs, outdated
  vulture listings), and are reproducible locally via the dev tools. All report
  content is preserved in the dated reports under `reports/`.
- New pre-implementation plans belong here under `reports/` once superseded;
  active (not yet implemented) plans live in a top-level `docs/planning/`
  directory, recreated when needed.
