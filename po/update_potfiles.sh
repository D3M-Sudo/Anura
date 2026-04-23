#!/bin/bash
#
# update_potfile.sh
# 
# Technical script for Anura OCR to extract translatable strings.

DOMAIN_EXTENSION="com.github"
AUTHOR="d3msudo"
APPNAME="anura"
APPID="${DOMAIN_EXTENSION}.${AUTHOR}.${APPNAME}"

if [ "$1" == "-h" ]; then
    echo "Usage: $0 [lang]"
    exit 0
fi

lang="$1"

# 1. Clean environment
# Remove any old temporary .pot files safely
rm -f *.pot

# 2. Extract version from root meson.build
# Using a more robust grep pattern to avoid 'meson' string interference
version=$(grep -Po "version:\s*'\K[^']+" ../meson.build | head -n 1)

echo "Anura: Starting string extraction for version $version..."

# 3. Extraction Phase
# Python Source Files
find ../$APPNAME -iname "*.py" | xargs xgettext --package-name=$APPNAME --package-version=$version --from-code=UTF-8 --output=$APPNAME-python.pot

# Blueprint UI Files (Treated as Python for string extraction compatibility)
find ../data/ui -iname "*.blp" | xargs xgettext --package-name=$APPNAME --package-version=$version --from-code=UTF-8 --output=$APPNAME-blueprint.pot -L Python

# Desktop Entry Files
find ../data/ -iname "*.desktop.in" | xargs xgettext --package-name=$APPNAME --package-version=$version --from-code=UTF-8 --output=$APPNAME-desktop.pot -L Desktop

# AppData/AppStream metadata
find ../data/ -iname "*.appdata.xml.in" | xargs xgettext --no-wrap --package-name=$APPNAME --package-version=$version --from-code=UTF-8 --output=$APPNAME-appdata.pot

# 4. Concatenation Phase
# Combine all results into the official project template (APPID.pot)
msgcat --use-first $APPNAME-python.pot $APPNAME-blueprint.pot $APPNAME-desktop.pot $APPNAME-appdata.pot > $APPID.pot

# 5. POTFILES Generation
# Update POTFILES for Meson/Intltool build compliance
sed 's/#: //g;s/:[0-9]*//g;s/\.\.\///g' <(grep -F "#: " $APPID.pot) | sort | uniq | sed 's/ /\n/g' | uniq > POTFILES.in
cat POTFILES.in | sort | uniq > POTFILES
rm -f POTFILES.in

# 6. Language Update Phase (Optional argument)
if [ ! -z "${lang}" ]; then
    echo "Anura: Updating translation file for language: ${lang}..."
    if [ -f "${lang}.po" ]; then
        # Merges new strings with existing translations
        msgmerge --update --no-fuzzy-matching "${lang}.po" "${APPID}.pot"
    else
        # Initializes a new translation file if it doesn't exist
        msginit --locale=$lang --input $APPID.pot --no-translator
    fi
    # Ensure UTF-8 encoding
    sed -i 's/ASCII/UTF-8/' "${lang}.po"
fi

# 7. Finalization
# Rename the APPID.pot to the standard project name for the build system
mv $APPID.pot $APPNAME.pot.bak
rm -f *.pot
mv $APPNAME.pot.bak $APPNAME.pot

echo "Anura: Extraction complete. Template saved as $APPNAME.pot"