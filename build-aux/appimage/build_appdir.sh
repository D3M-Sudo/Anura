#!/usr/bin/env bash
set -euo pipefail
: "${TARGET_APPDIR:?appimage-builder must set TARGET_APPDIR}"
: "${APP_VERSION:?APP_VERSION is required}"
: "${APPIMAGE_ARCH:?APPIMAGE_ARCH is required}"
SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APPDIR="$TARGET_APPDIR"
PYTHON_SITE="$APPDIR/usr/lib/python3.12/site-packages"

mkdir -p "$APPDIR/usr/share/anura" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/metainfo" "$APPDIR/usr/share/glib-2.0/schemas" "$APPDIR/usr/share/icons/hicolor/scalable/apps" "$APPDIR/usr/share/locale" "$APPDIR/usr/lib/anura" "$APPDIR/usr/bin" "$PYTHON_SITE" "$APPDIR/.blueprint-ui" "$APPDIR/usr/share/licenses/io.github.d3m_sudo.anura"

for source in "$SOURCE_ROOT"/data/ui/*.blp; do
  output="$APPDIR/.blueprint-ui/$(basename "${source%.blp}").ui"
  blueprint-compiler compile "$source" --output "$output"
done

glib-compile-resources "$SOURCE_ROOT/data/io.github.d3m_sudo.anura.gresource.xml" --sourcedir="$APPDIR/.blueprint-ui" --sourcedir="$SOURCE_ROOT/data" --target="$APPDIR/usr/share/anura/io.github.d3m_sudo.anura.gresource"
cp "$SOURCE_ROOT/data/io.github.d3m_sudo.anura.gschema.xml" "$APPDIR/usr/share/glib-2.0/schemas/"
glib-compile-schemas "$APPDIR/usr/share/glib-2.0/schemas"

for po_file in "$SOURCE_ROOT"/po/*.po; do
  language="$(basename "$po_file" .po)"
  destination="$APPDIR/usr/share/locale/$language/LC_MESSAGES"
  mkdir -p "$destination"
  msgfmt --check --output-file="$destination/io.github.d3m_sudo.anura.mo" "$po_file"
done

cp "$SOURCE_ROOT/data/io.github.d3m_sudo.anura.desktop.in" "$APPDIR/usr/share/applications/io.github.d3m_sudo.anura.desktop"
sed 's/^Exec=anura$/Exec=AppRun/' "$SOURCE_ROOT/data/io.github.d3m_sudo.anura.desktop.in" > "$APPDIR/io.github.d3m_sudo.anura.desktop"
cp "$SOURCE_ROOT/data/io.github.d3m_sudo.anura.metainfo.xml.in" "$APPDIR/usr/share/metainfo/io.github.d3m_sudo.anura.metainfo.xml"
cp "$SOURCE_ROOT/data/icons/io.github.d3m_sudo.anura.svg" "$APPDIR/usr/share/icons/hicolor/scalable/apps/"
cp "$SOURCE_ROOT/data/icons/io.github.d3m_sudo.anura.svg" "$APPDIR/io.github.d3m_sudo.anura.svg"
cp "$SOURCE_ROOT/LICENSE" "$APPDIR/usr/share/licenses/io.github.d3m_sudo.anura/LICENSE"

cd "$SOURCE_ROOT"
uv pip install --python "$(command -v python3)" --target "$PYTHON_SITE" .

cat > "$APPDIR/usr/lib/anura/appimage_entrypoint.py" <<'PY'
from __future__ import annotations
import os
from pathlib import Path
from gi.repository import Gio
appdir = Path(os.environ["APPDIR"])
resource_path = appdir / "usr/share/anura/io.github.d3m_sudo.anura.gresource"
Gio.resources_register(Gio.Resource.load(str(resource_path)))
from anura import main  # noqa: E402
raise SystemExit(main.main(os.environ["ANURA_VERSION"]))
PY

cat > "$APPDIR/usr/bin/anura" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
: "${APPDIR:?AppImage runtime did not set APPDIR}"
export PYTHONPATH="$APPDIR/usr/lib/python3.12/site-packages:$APPDIR/usr/lib/python3/dist-packages${PYTHONPATH:+:$PYTHONPATH}"
export GSETTINGS_SCHEMA_DIR="$APPDIR/usr/share/glib-2.0/schemas"
export ANURA_LOCALE_DIR="$APPDIR/usr/share/locale"
export TESSDATA_PREFIX="$APPDIR/usr/share/tesseract-ocr/5/tessdata"
export TESSDATA_PREFIX_SYSTEM="$TESSDATA_PREFIX"
export ANURA_VERSION="__APP_VERSION__"
export GST_PLUGIN_PATH="$APPDIR/usr/lib/gstreamer-1.0:$APPDIR/usr/lib/x86_64-linux-gnu/gstreamer-1.0:$APPDIR/usr/lib/aarch64-linux-gnu/gstreamer-1.0"
mapfile -t typelib_dirs < <(find "$APPDIR/usr/lib" -type d -name girepository-1.0 -print)
if ((${#typelib_dirs[@]})); then
  export GI_TYPELIB_PATH="$(IFS=:; echo "${typelib_dirs[*]}")"
fi
exec "$APPDIR/usr/bin/python3" "$APPDIR/usr/lib/anura/appimage_entrypoint.py" "$@"
SH
sed -i "s/__APP_VERSION__/$APP_VERSION/" "$APPDIR/usr/bin/anura"
chmod 0755 "$APPDIR/usr/bin/anura"

desktop-file-validate "$APPDIR/usr/share/applications/io.github.d3m_sudo.anura.desktop"
desktop-file-validate "$APPDIR/io.github.d3m_sudo.anura.desktop"
test -s "$APPDIR/usr/share/anura/io.github.d3m_sudo.anura.gresource"
test -s "$APPDIR/usr/share/glib-2.0/schemas/gschemas.compiled"
test -d "$PYTHON_SITE/anura"
rm -rf "$APPDIR/.blueprint-ui"
echo "Prepared relocatable AppDir for $APPIMAGE_ARCH ($APP_VERSION)"
