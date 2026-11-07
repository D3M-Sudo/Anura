# Changelog integrity

The CI guard compares the base and head revisions of `CHANGELOG.md` and blocks removal of bullets from `[Unreleased]`. Rewording is treated as removal of the old wording plus addition of the replacement.

Intentional removal requires an exact original bullet, a rationale of at least 20 characters, and a GitHub issue/PR reference in `.github/changelog-removals.json`. Duplicate identical bullets require one authorization per removed occurrence. Keep records as an audit trail; patterns and partial matches are not accepted.

Append entries to existing category headings. Duplicate category headings are not permitted within `[Unreleased]`.
