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
cp "$SOURCE_ROOT/build-aux/appimage/licenses/type2-runtime-LICENSE" \
  "$APPDIR/usr/share/licenses/io.github.d3m_sudo.anura/AppImage-type2-runtime-LICENSE"

cd "$SOURCE_ROOT"
uv export --locked --no-dev --no-emit-project --format requirements-txt \
  --output-file "$APPDIR/.requirements.txt"
uv pip install --python "$(command -v python3)" --target "$PYTHON_SITE" \
  --requirement "$APPDIR/.requirements.txt"
cp -a "$SOURCE_ROOT/anura" "$PYTHON_SITE/"
python3 "$SOURCE_ROOT/build-aux/generate_release_notes.py" \
  "$SOURCE_ROOT/CHANGELOG.md" "$PYTHON_SITE/anura/_release_notes.py" "$APP_VERSION"

cat > "$APPDIR/usr/lib/anura/appimage_entrypoint.py" <<'PY'
from __future__ import annotations

import os
from pathlib import Path
import sys

appdir = Path(os.environ["APPDIR"])
python_paths = (
    appdir / "usr/lib/python3.12/site-packages",
    appdir / "usr/lib/python3/dist-packages",
)
os.environ["PYTHONPATH"] = os.pathsep.join(map(str, python_paths))
os.environ["GSETTINGS_SCHEMA_DIR"] = str(appdir / "usr/share/glib-2.0/schemas")
os.environ["ANURA_LOCALE_DIR"] = str(appdir / "usr/share/locale")
os.environ["TESSDATA_PREFIX"] = str(appdir / "usr/share/tesseract-ocr/5/tessdata")
os.environ["TESSDATA_PREFIX_SYSTEM"] = os.environ["TESSDATA_PREFIX"]

lib_dirs = [path for path in (appdir / "usr/lib").glob("*-linux-gnu") if path.is_dir()]
lib_dirs.append(appdir / "usr/lib")
typelib_dirs = [str(path) for path in appdir.glob("usr/lib/**/girepository-1.0") if path.is_dir()]
if typelib_dirs:
    os.environ["GI_TYPELIB_PATH"] = os.pathsep.join(typelib_dirs)
gst_dirs = [path for path in lib_dirs if (path / "gstreamer-1.0").is_dir()]
os.environ["GST_PLUGIN_PATH"] = os.pathsep.join(str(path / "gstreamer-1.0") for path in gst_dirs)

sys.path[:0] = [str(path) for path in python_paths]
from gi.repository import Gio  # noqa: E402

resource_path = appdir / "usr/share/anura/io.github.d3m_sudo.anura.gresource"
Gio.resources_register(Gio.Resource.load(str(resource_path)))

from anura import main  # noqa: E402

raise SystemExit(main.main(os.environ["ANURA_VERSION"]))
PY

# Keep the conventional command available for shells and desktop integrations
# that invoke "anura" directly; AppRun itself uses the ELF Python interpreter.
cat > "$APPDIR/usr/bin/anura" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
: "${APPDIR:?AppImage runtime did not set APPDIR}"
exec "$APPDIR/usr/bin/python3" "$APPDIR/usr/lib/anura/appimage_entrypoint.py" "$@"
SH
chmod 0755 "$APPDIR/usr/bin/anura"

desktop-file-validate "$APPDIR/usr/share/applications/io.github.d3m_sudo.anura.desktop"
desktop-file-validate "$APPDIR/io.github.d3m_sudo.anura.desktop"
test -s "$APPDIR/usr/share/anura/io.github.d3m_sudo.anura.gresource"
test -s "$APPDIR/usr/share/glib-2.0/schemas/gschemas.compiled"
test -d "$PYTHON_SITE/anura"
rm -rf "$APPDIR/.blueprint-ui" "$APPDIR/.requirements.txt"
echo "Prepared relocatable AppDir for $APPIMAGE_ARCH ($APP_VERSION)"
