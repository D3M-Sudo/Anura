#!/bin/bash
#
# update_potfile.sh
# 
# Technical script for Anura OCR to extract translatable strings.

set -euo pipefail

DOMAIN_EXTENSION="io.github"
AUTHOR="d3msudo"
APPNAME="anura"
APPID="${DOMAIN_EXTENSION}.${AUTHOR}.${APPNAME}"

if [ "$1" == "-h" ]; then
    echo "Usage: $0 [lang]"
    exit 0
fi

lang="${1:-}"

tmpdir=$(mktemp -d "${TMPDIR:-.}/.anura-pot-update.XXXXXX")
trap 'rm -rf -- "$tmpdir"' EXIT

# 2. Extract version from root meson.build
# Using a more robust grep pattern to avoid 'meson' string interference
version=$(grep -Po "version:\s*'\K[^']+" ../meson.build | head -n 1)

echo "Anura: Starting string extraction for version $version..."

# 3. Extraction Phase
# Python Source Files
find ../$APPNAME -iname "*.py" | xargs xgettext --package-name=$APPNAME --package-version=$version --from-code=UTF-8 --output="$tmpdir/$APPNAME-python.pot" --keyword=_ --keyword=C_:1c,2 --keyword=pgettext:1c,2 --keyword=ngettext:1,2

# Blueprint UI Files (Treated as Python for string extraction compatibility)
find ../data/ui -iname "*.blp" | xargs xgettext --package-name=$APPNAME --package-version=$version --from-code=UTF-8 --output="$tmpdir/$APPNAME-blueprint.pot" -L Python --keyword=_ --keyword=C_:1c,2 --keyword=pgettext:1c,2 --keyword=ngettext:1,2

# Desktop Entry Files
find ../data/ -iname "*.desktop.in" | xargs xgettext --package-name=$APPNAME --package-version=$version --from-code=UTF-8 --output="$tmpdir/$APPNAME-desktop.pot" -L Desktop

# AppStream metainfo (replaces deprecated .appdata.xml.in naming)
find ../data/ -iname "*.metainfo.xml.in" | xargs xgettext --no-wrap --package-name=$APPNAME --package-version=$version --from-code=UTF-8 --output="$tmpdir/$APPNAME-metainfo.pot"

# 4. Concatenation Phase
# Combine all results into the official project template (APPID.pot)
msgcat --use-first "$tmpdir/$APPNAME-python.pot" "$tmpdir/$APPNAME-blueprint.pot" "$tmpdir/$APPNAME-desktop.pot" "$tmpdir/$APPNAME-metainfo.pot" > "$tmpdir/$APPID.pot"
msgfmt --check-format --check-header -o /dev/null "$tmpdir/$APPID.pot"

# 5. POTFILES Generation
# Update POTFILES for Meson/Intltool build compliance
grep -F "#: " "$tmpdir/$APPID.pot" > "$tmpdir/references.txt" || true
sed 's/#: //g;s/:[0-9]*//g;s/\.\.\///g' "$tmpdir/references.txt" | tr ' ' '\n' | sort -u > "$tmpdir/POTFILES"

# Replace tracked outputs only after extraction and validation succeed.
mv -- "$tmpdir/$APPID.pot" "$APPID.pot"
mv -- "$tmpdir/POTFILES" POTFILES
rm -f POTFILES.in

# 6. Language Update Phase (Optional argument)
if [ ! -z "${lang}" ]; then
    echo "Anura: Updating translation file for language: ${lang}..."
    if [ -f "${lang}.po" ]; then
        # Merges new strings with existing translations
        msgmerge --update --no-fuzzy-matching "${lang}.po" "${APPID}.pot"
    else
        # Initializes a new translation file if it doesn't exist
        msginit --locale="$lang" --input="$APPID.pot" --no-translator --output-file="$lang.po"
    fi
    # Ensure UTF-8 encoding
    sed -i 's/ASCII/UTF-8/' "${lang}.po"
fi

# 7. Finalization
# Keep the POT file named after the APPID for Meson i18n compatibility
# No renaming needed
rm -f $APPNAME.pot $APPNAME-python.pot $APPNAME-blueprint.pot $APPNAME-desktop.pot $APPNAME-metainfo.pot *.ui

echo "Anura: Extraction complete. Template saved as $APPID.pot"