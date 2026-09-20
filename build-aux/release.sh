#!/bin/bash
#
# Release script for Anura
# Automatically pins tessdata ref (release tag recommended) and creates git tag
#
# Usage: ./build-aux/release.sh <version> [tessdata_ref]
# Example: ./build-aux/release.sh 0.1.4 4.1.0

set -e

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
DATE=$(date +%Y-%m-%d)

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

# Create new release entry
RELEASE_ENTRY="    <release version=\"$VERSION\" type=\"stable\" date=\"$DATE\">
      <description>
        <!-- TODO: Add release notes before publishing -->
        <p>Release $VERSION.</p>
      </description>
    </release>"

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
- Pin tessdata to ref $TESSDATA_REF in the local Flatpak manifest
- Regenerate the release Flatpak manifest from the local one
- Update metainfo for v$VERSION release"

echo "Creating tag v$VERSION..."
git tag -a "v$VERSION" -m "Anura v$VERSION

Release highlights:
- Tessdata models pinned to ref $TESSDATA_REF
- See CHANGELOG.md for full details"

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
