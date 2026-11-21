# Localization catalogue integrity

Anura uses GNU gettext. English is the source language; the project maintainer directly maintains the English source strings and the Italian catalogue. The other 24 catalogues are community-maintained through Hosted Weblate and are not a project-maintained translation backlog.

## Source and catalogue inventory

- `po/LINGUAS` is the authoritative list of locale codes.
- The set of `po/*.po` files must match `po/LINGUAS` exactly. English is the source language and is intentionally absent.
- `po/io.github.d3m_sudo.anura.pot` is the gettext template.
- `po/POTFILES` must contain each source path referenced by the template exactly once, and every listed path must exist in the repository.
- Regenerate the template and source inventory from the repository root with `cd po && ./update_potfiles.sh`. Review both generated files before proposing them; do not edit translation catalogues as part of this workflow.

## CI validation

The `python-quality` job installs GNU gettext so the gettext-dependent template tests cannot silently skip. CI then:

1. Validates the maintainer-owned Italian catalogue with `msgfmt --check --check-format --check-header`.
2. Parses the POT template with gettext checks and tests for duplicate message identifiers.
3. Verifies that `LINGUAS` and the `.po` file inventory agree.
4. Verifies that `POTFILES` matches the template's source references and that every path exists.

The CI gate does not require all community translations to be complete, does not infer human review from populated `msgstr` fields, and does not block on community linguistic review. Community catalogues continue through Hosted Weblate and the established `testing` integration path.
