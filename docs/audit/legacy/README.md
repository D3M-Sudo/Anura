# Anura — audit/legacy (historical, append-only)

This directory preserves **historical** QA/security audit material for
traceability. Do **not** treat findings here as open issues — every report
below ends with applied fixes already merged on `testing`.

## Layout

- `reports/` — human-readable reports (bug hunts, QA summaries) plus the
  superseded pre-implementation plan `reports/history-v1-plan.md` and its
  companion `bugs-observed.json` / `bugs-summary.md`.
- `raw/` — unprocessed tool outputs (bandit, mypy, ruff, vulture `.txt`/`.json`).

## Rules

- **Append-only**: add new dated reports, never rewrite or delete existing files.
- New pre-implementation plans belong here under `reports/` once superseded;
  active (not yet implemented) plans live in a top-level `docs/planning/`
  directory, recreated when needed.
