#!/usr/bin/env bash
# Restore runtime soname files that appimage-builder 1.1.0 may omit while
# staging APT package symlinks. Sources are installed on the native runner,
# whose architecture was checked before the AppImage build.
set -euo pipefail

APPDIR="${1:?usage: stage_runtime_libraries.sh APPDIR APP_LIBDIR}"
APP_LIBDIR="${2:?usage: stage_runtime_libraries.sh APPDIR APP_LIBDIR}"
SOURCE_LIBDIR="/usr/lib/$APP_LIBDIR"
DEST_LIBDIR="$APPDIR/usr/lib/$APP_LIBDIR"

case "$APP_LIBDIR" in
  x86_64-linux-gnu|aarch64-linux-gnu) ;;
  *) echo "::error::Unsupported AppImage library directory: $APP_LIBDIR"; exit 2 ;;
esac
[[ -d "$APPDIR/usr" ]] || { echo "::error::AppDir is missing usr/: $APPDIR"; exit 1; }
[[ -d "$SOURCE_LIBDIR" ]] || { echo "::error::Native runner library directory is missing: $SOURCE_LIBDIR"; exit 1; }
mkdir -p "$DEST_LIBDIR"

for soname in liblzo2.so.2 libEGL.so.1; do
  source="$SOURCE_LIBDIR/$soname"
  if [[ ! -e "$source" ]]; then
    echo "::error::Required native runtime library is unavailable: $source"
    exit 1
  fi
  resolved="$(readlink -f "$source")"
  if [[ ! -f "$resolved" ]]; then
    echo "::error::Runtime library target is not a regular file: $resolved"
    exit 1
  fi
  # Dereference the package symlink and store the ABI soname as a regular
  # file, avoiding dangling or absolute symlinks in the relocatable AppDir.
  install -m 0644 "$resolved" "$DEST_LIBDIR/$soname"
  if ! file -b "$DEST_LIBDIR/$soname" | grep -q '^ELF '; then
    echo "::error::Staged runtime library is not an ELF object: $soname"
    exit 1
  fi
  echo "Staged $soname from $resolved"
done
