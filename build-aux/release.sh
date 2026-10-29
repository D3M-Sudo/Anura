#!/bin/bash
#
# Release script for Anura
# Automatically pins tessdata ref (release tag recommended) and creates git tag
#
# Usage: ./build-aux/release.sh <version> [tessdata_ref]
# Example: ./build-aux/release.sh 0.1.4 4.1.0

set -e

# --- i18n policy (D5) ---
# Do NOT regenerate po/*.pot or run msgmerge here.
# Translations are managed externally via Weblate.
# Local xgettext runs introduce spurious '#:' line-reference diffs
# that conflict with the Weblate-managed .po files (see #447).
# Structural pot generation is delegated to dedicated PRs
# that run: cd po && ./update_potfiles.sh
# --- end i18n policy ---

VERSION="$1"
# Default: tessdata release tag (Bug #6, 2026-09). Do NOT re-pin to commit SHAs:
# upstream tesseract-ocr repos rewrite history, orphaning hardcoded SHAs (404).
TESSDATA_REF="${2:-4.1.0}"

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [tessdata_ref]"
    echo "Example: $0 0.1.4"
    echo "Example with custom tessdata ref: $0 0.1.4 4.0.0"
    exit 1
fi

# Validate version format
if ! echo "$VERSION" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(\.[0-9]+)?$'; then
    echo "Error: Version must be in format X.Y.Z or X.Y.Z.W (e.g., 0.1.4 or 0.1.4.3)"
    exit 1
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

MANIFEST_FILE="$PROJECT_ROOT/flatpak/io.github.d3msudo.anura.json"
MANIFEST_LOCAL="$PROJECT_ROOT/flatpak/io.github.d3msudo.anura.local.json"
METAINFO_FILE="$PROJECT_ROOT/data/io.github.d3msudo.anura.metainfo.xml.in"
MESON_BUILD_FILE="$PROJECT_ROOT/meson.build"
PYPROJECT_FILE="$PROJECT_ROOT/pyproject.toml"
UV_LOCK_FILE="$PROJECT_ROOT/uv.lock"
DATE=$(date +%Y-%m-%d)

# --- Preflight (#487) -------------------------------------------------------
# Nothing below this point is safe to run twice or on a dirty tree: the script
# stages files, commits and tags. Refuse early instead of leaving a partial
# release behind.
if [ -n "$(git -C "$PROJECT_ROOT" status --porcelain)" ]; then
    echo "✗ Working tree or index is not clean. Commit or stash your changes first:"
    git -C "$PROJECT_ROOT" status --short
    exit 1
fi

if git -C "$PROJECT_ROOT" rev-parse -q --verify "refs/tags/v$VERSION" >/dev/null; then
    echo "✗ Tag v$VERSION already exists."
    exit 1
fi

CURRENT_BRANCH="$(git -C "$PROJECT_ROOT" rev-parse --abbrev-ref HEAD)"
EXPECTED_BRANCH="${RELEASE_BRANCH:-main}"
if [ "$CURRENT_BRANCH" != "$EXPECTED_BRANCH" ]; then
    echo "✗ Releases are cut from '$EXPECTED_BRANCH' (current: '$CURRENT_BRANCH')."
    echo "  Switch branch, or set RELEASE_BRANCH=<branch> to override."
    exit 1
fi

# Release notes come from CHANGELOG.md, the single source of truth. The helper
# exits when the section is missing or still a placeholder, so a release can
# never publish "TODO" metadata (#485).
echo "Reading release notes for $VERSION from CHANGELOG.md..."
RELEASE_ENTRY="$(python3 "$SCRIPT_DIR/generate_release_notes.py" --metainfo "$PROJECT_ROOT/CHANGELOG.md" "$VERSION" "$DATE")"

echo "=== Anura Release $VERSION ==="
echo "Tessdata ref: $TESSDATA_REF"
echo "Release date: $DATE"
echo ""

# Update meson.build with new version
echo "Updating $MESON_BUILD_FILE with version $VERSION..."
if [ -f "$MESON_BUILD_FILE" ]; then
    # Update version in meson.build (format: version: 'X.Y.Z')
    sed -i "s/version: '[0-9]\+\.[0-9]\+\.[0-9]\+'/version: '$VERSION'/" "$MESON_BUILD_FILE"
    if grep -q "version: '$VERSION'" "$MESON_BUILD_FILE"; then
        echo "✓ $MESON_BUILD_FILE updated successfully"
        git add "$MESON_BUILD_FILE"
    else
        echo "✗ Failed to update $MESON_BUILD_FILE"
        exit 1
    fi
else
    echo "⚠ $MESON_BUILD_FILE not found, skipping"
fi

echo ""

# Keep every declared version in step: pyproject.toml is the source uv reads,
# and the lockfile repeats the same version for the virtual `anura` package.
# Both are rewritten with Python (no network, no re-lock) so a release can
# never leave the project version behind: `uv sync --frozen` compares them.
echo "Updating $PYPROJECT_FILE and $UV_LOCK_FILE with version $VERSION..."
python3 - "$PYPROJECT_FILE" "$UV_LOCK_FILE" "$VERSION" <<'PY'
import re
import sys

pyproject_path, lock_path, version = sys.argv[1:4]

with open(pyproject_path, encoding="utf-8") as handle:
    text = handle.read()
text, replaced = re.subn(
    r'^version = "[^"]*"$', f'version = "{version}"', text, count=1, flags=re.MULTILINE
)
if replaced != 1:
    sys.exit(f"pyproject.toml: expected exactly one version line, found {replaced}")
with open(pyproject_path, "w", encoding="utf-8") as handle:
    handle.write(text)

with open(lock_path, encoding="utf-8") as handle:
    text = handle.read()
text, replaced = re.subn(
    r'(name = "anura"\nversion = ")[^"]*(")',
    lambda match: f"{match.group(1)}{version}{match.group(2)}",
    text,
    count=1,
)
if replaced != 1:
    sys.exit(f"uv.lock: expected exactly one anura package entry, found {replaced}")
with open(lock_path, "w", encoding="utf-8") as handle:
    handle.write(text)

print(f"✓ pyproject.toml and uv.lock updated to {version}")
PY
git add "$PYPROJECT_FILE" "$UV_LOCK_FILE"

echo ""

# Update the local manifest with the pinned tessdata ref. The release
# manifest is generated from this one further below and must never be
# hand-pinned here directly, or the generation step would silently discard
# this update.
echo "Updating $MANIFEST_LOCAL with pinned tessdata ref..."
sed -i "s|tessdata_fast/raw/[^/]*/|tessdata_fast/raw/${TESSDATA_REF}/|g" "$MANIFEST_LOCAL"

# Verify the change was made
if grep -q "tessdata_fast/raw/${TESSDATA_REF}/" "$MANIFEST_LOCAL"; then
    echo "✓ Manifest updated successfully"
else
    echo "✗ Failed to update manifest"
    exit 1
fi

# Update metainfo.xml with new release
echo ""
echo "Updating $METAINFO_FILE with new release entry..."

# The release entry was generated from CHANGELOG.md during preflight (#485).

# Insert after the <releases> opening tag
if grep -q '<releases>' "$METAINFO_FILE"; then
    # sed's a\ (append) command does not reliably handle a multi-line
    # replacement passed via a shell variable under GNU sed: every embedded
    # newline after the first gets parsed as a new sed script line instead
    # of literal appended text, which fails outright as soon as one of those
    # lines starts with a character sed doesn't recognize as a command (e.g.
    # the "<" of "<description>"). Write the entry to a temp file and use
    # sed's r (read-file) command instead, which inserts the file's content
    # verbatim after the matched line and preserves $METAINFO_FILE's mode.
    RELEASE_ENTRY_FILE=$(mktemp)
    printf '%s\n' "$RELEASE_ENTRY" > "$RELEASE_ENTRY_FILE"
    sed -i "/<releases>/r $RELEASE_ENTRY_FILE" "$METAINFO_FILE"
    rm -f "$RELEASE_ENTRY_FILE"
    echo "✓ Metainfo updated successfully"
else
    echo "✗ Could not find <releases> tag in metainfo file"
    exit 1
fi

# Generate the release (Flathub) manifest from the local manifest.
# $MANIFEST_FILE is never hand-edited: every module is copied verbatim from
# $MANIFEST_LOCAL except the `anura` module's source (dir -> git+tag), and the
# local-only top-level `branch` / `separate-locales` keys are dropped.
echo ""
echo "Generating $MANIFEST_FILE from $MANIFEST_LOCAL..."
GENERATED_MANIFEST="${MANIFEST_FILE}.tmp"
jq --indent 4 --arg VERSION "$VERSION" \
  'del(.branch, ."separate-locales")
   | .modules |= map(
       if .name == "anura"
       then .sources = [{"type": "git", "url": "https://github.com/D3M-Sudo/Anura.git", "tag": ("v" + $VERSION)}]
       else . end)' \
  "$MANIFEST_LOCAL" > "$GENERATED_MANIFEST"

# Validate before replacing the real file.
if ! jq empty "$GENERATED_MANIFEST" >/dev/null 2>&1; then
    echo "✗ Generated manifest is not valid JSON"
    rm -f "$GENERATED_MANIFEST"
    exit 1
fi
if grep -q '"type": "dir"' "$GENERATED_MANIFEST"; then
    echo "✗ Generated manifest still contains a \"dir\" source (anura module was not rewritten)"
    rm -f "$GENERATED_MANIFEST"
    exit 1
fi

mv "$GENERATED_MANIFEST" "$MANIFEST_FILE"
echo "✓ $MANIFEST_FILE generated successfully"

# Self-check: the two manifests must now be consistent by construction, since
# the release manifest was just derived from the local one.
echo ""
echo "Running post-generation self-checks..."
python3 "$SCRIPT_DIR/check_manifest_consistency.py"
python3 "$SCRIPT_DIR/check_tessdata_consistency.py"
python3 "$SCRIPT_DIR/check_runtime_dependency_coverage.py" --manifest both
echo "✓ Self-checks passed"

# Show summary
echo ""
echo "=== Summary of changes ==="
echo "Files modified:"
echo "  - $MESON_BUILD_FILE (version bumped to $VERSION)"
echo "  - $PYPROJECT_FILE (version bumped to $VERSION)"
echo "  - $UV_LOCK_FILE (anura package version bumped to $VERSION)"
echo "  - $MANIFEST_LOCAL (tessdata pinned to ref $TESSDATA_REF)"
echo "  - $METAINFO_FILE (release $VERSION added)"
echo "  - $MANIFEST_FILE (regenerated from $MANIFEST_LOCAL)"
echo ""

# Git operations
echo "=== Git operations ==="
echo "Adding files to git..."
git add "$MANIFEST_FILE" "$MANIFEST_LOCAL" "$METAINFO_FILE"

echo "Creating commit..."
git commit -m "Release v$VERSION

- Bump version to $VERSION in meson.build
- Keep pyproject.toml and the uv.lock anura entry at the same version
- Pin tessdata to ref $TESSDATA_REF in the local Flatpak manifest
- Regenerate the release Flatpak manifest from the local one
- Update metainfo for v$VERSION release"

echo "Creating tag v$VERSION..."
git tag -a "v$VERSION" -m "Anura v$VERSION

Release highlights:
- Tessdata models pinned to ref $TESSDATA_REF
- See CHANGELOG.md for full details"

# The repository manifest pins the tag; the Flathub submission manifest should
# pin the commit it resolves to, so a moved tag cannot change the sources (#501).
RELEASE_COMMIT="$(git -C "$PROJECT_ROOT" rev-parse "v$VERSION^{commit}")"
echo "Source commit for v$VERSION: $RELEASE_COMMIT"
echo "For the submission manifest: build-aux/pin_source_commit.py --tag v$VERSION"

echo ""
echo "=== Release v$VERSION prepared successfully ==="
echo ""
echo "Next steps:"
echo "  1. Review the commit: git show HEAD"
echo "  2. Push to remote: git push origin main --tags"
echo "  3. The CI will build the Flatpak automatically"
echo "  4. MANDATORY: the CI creates the GitHub release with the Flatpak"
echo "     bundle but EMPTY notes — populate the body from CHANGELOG.md"
echo "     (see 'Release Process' in AGENTS.md)"
echo ""
echo "To push now, run:"
echo "  git push origin main --tags"
