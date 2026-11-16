# Repository governance (single maintainer)

This repository is maintained by one person. The governance model must not require approval from a second maintainer, an external reviewer, or another person who cannot reliably be available.

## Promotion flow

Use this one-way promotion chain: `feature` → `testing` → `development` → `main`. Work on short-lived topic/fix branches; do not develop directly on protected branches. The source-branch sequence is a maintainer procedure: GitHub branch protection does not itself enforce that a PR comes from the immediately preceding branch.

- `feature`: integration branch; accept topic/fix branches and approved automation PRs.
- `testing`: promotion from `feature`.
- `development`: promotion from `testing`.
- `main`: release branch; promotion from `development`, with releases published only from reviewed version tags.

## Pull-request and CI requirements

Require a pull request for all four promotion branches. Set required approvals to **zero**; code-owner review and external reviewer requirements must remain disabled. Before merging, the maintainer inspects the diff, confirms the target branch and documentation/CHANGELOG updates, and verifies the required CI checks. A green CI run is necessary but does not authorize a merge. Auto-merge is not permitted.

## Recommended GitHub rules

Apply these settings to `feature`, `testing`, `development` and `main`:

- Require a pull request before merging.
- Require **0 approvals**; do not require code-owner review.
- Require the relevant status checks from the main CI workflow and CodeQL. Select exact check names from successful PR runs after confirming that each check is emitted for the target branch.
- Block force pushes and branch deletion.
- Do not enable auto-merge.
- Do not grant routine bypass to automation identities; keep workflow write permissions scoped to the jobs that need them.
- Where supported, enforce rules for administrators too, while retaining zero required approvals. Confirm a compliant PR remains mergeable before relying on the ruleset.

| Branch | Expected PR source | Branch-specific protection |
| --- | --- | --- |
| `feature` | Topic/fix branches; approved automation PRs | Require the full Python, GTK, Flatpak x86_64/aarch64, AppImage x86_64/aarch64, artifact-validation and CodeQL checks. This is the primary integration gate. |
| `testing` | `feature` | Require the same full CI and CodeQL checks, and require the PR branch to be up to date before merge. This is the first promotion gate. |
| `development` | `testing` | Require the same full CI and CodeQL checks and an up-to-date PR branch. Treat merges as stabilization candidates; do not bypass a failed architecture job. |
| `main` | `development` | Require the same full CI and CodeQL checks and an up-to-date PR branch. Keep tag-triggered release verification as a separate maintainer-controlled gate; a PR CI pass does not prove release publication. |

GitHub's ordinary branch rules can require checks and PRs, but cannot reliably
enforce the expected *source branch* shown above. Verify that source manually
during the single-maintainer review. The exact required-check names must be
selected from successful PR runs; do not guess check names or require a check
that is not emitted for that branch.

## Automation boundaries

- `dependency-sync.yml` updates only the Dependabot PR head. Manual dispatch must run from a non-protected working branch and must never push directly to a protected branch.
- `flatpak-dependencies.yml` may open its certifi update PR against `feature`; it remains subject to normal CI and manual review.
- Automation must not merge PRs, bypass required checks, or push commits directly to protected branches.
- Workflow permissions should be scoped to the job that needs them and limited to the minimum required capabilities.

## Configuration boundary

This document defines policy; it does not configure GitHub. Branch protection, rulesets, bypass actors, auto-merge settings and required status-check selections are GitHub-side settings and must be verified in repository administration after configuration.