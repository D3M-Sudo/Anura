#!/usr/bin/env bash
# Audit ELF dependencies for Anura's AppImage runtime, excluding only known
# APT-closure payloads that are not part of Anura's runtime contract.
set -euo pipefail

is_non_runtime_elf() {
  local path="$1" root="$2" libdir="$3"
  case "$path" in
    "$root/usr/bin/systemd-"*|"$root/usr/bin/journalctl"|"$root/usr/bin/busctl"|"$root/usr/bin/networkctl"|"$root/usr/bin/localectl"|"$root/usr/bin/timedatectl"|"$root/usr/bin/hostnamectl"|"$root/usr/bin/loginctl"|"$root/usr/bin/kernel-install"|"$root/usr/bin/varlinkctl") return 0 ;;
    "$root/usr/lib/systemd/"*|"$root/usr/lib/$libdir/systemd/"*|"$root/usr/lib/$libdir/cryptsetup/"*) return 0 ;;
    # These are optional visualisation/GL plugins pulled in by APT, not used
    # by Anura's GTK UI or audio/TTS path. Other GStreamer plugins remain audited.
    "$root/usr/lib/$libdir/caca/libgl_plugin.so"*) return 0 ;;
    "$root/usr/lib/$libdir/gstreamer-1.0/libgstgl-"*) return 0 ;;
    *) return 1 ;;
  esac
}

if [[ "${1:-}" == "--self-test" ]]; then
  root=/app
  libdir=x86_64-linux-gnu
  is_non_runtime_elf "$root/usr/bin/systemd-inhibit" "$root" "$libdir"
  is_non_runtime_elf "$root/usr/lib/$libdir/systemd/libsystemd-core-255.so" "$root" "$libdir"
  is_non_runtime_elf "$root/usr/lib/$libdir/cryptsetup/libcryptsetup-token-systemd-tpm2.so" "$root" "$libdir"
  is_non_runtime_elf "$root/usr/lib/$libdir/caca/libgl_plugin.so.0.0.0" "$root" "$libdir"
  is_non_runtime_elf "$root/usr/lib/$libdir/gstreamer-1.0/libgstgl-1.0.so.0" "$root" "$libdir"
  ! is_non_runtime_elf "$root/usr/lib/python3.12/site-packages/gi/_gi.cpython-312-x86_64-linux-gnu.so" "$root" "$libdir"
  ! is_non_runtime_elf "$root/usr/lib/$libdir/libgtk-4.so.1" "$root" "$libdir"
  ! is_non_runtime_elf "$root/usr/lib/$libdir/gio/modules/libgiolibproxy.so" "$root" "$libdir"
  echo "PASS: AppImage ELF audit scope self-test"
  exit 0
fi

APP_ROOT="${1:?usage: audit_elf_dependencies.sh APP_ROOT APP_LIBDIR}"
APP_LIBDIR="${2:?usage: audit_elf_dependencies.sh APP_ROOT APP_LIBDIR}"
[[ -d "$APP_ROOT/usr" ]] || { echo "::error::AppDir has no usr directory: $APP_ROOT"; exit 1; }
# libproxy's backend and PulseAudio's private helper live in subdirectories;
# add those exact runtime directories rather than suppressing their failures.
export LD_LIBRARY_PATH="$APP_ROOT/usr/lib/$APP_LIBDIR:$APP_ROOT/usr/lib/$APP_LIBDIR/libproxy:$APP_ROOT/usr/lib/$APP_LIBDIR/pulseaudio:$APP_ROOT/usr/lib"

missing=0
audited=0
skipped=0
while IFS= read -r -d '' elf; do
  if ! file -b "$elf" | grep -q "^ELF "; then
    continue
  fi
  if is_non_runtime_elf "$elf" "$APP_ROOT" "$APP_LIBDIR"; then
    skipped=$((skipped + 1))
    continue
  fi
  audited=$((audited + 1))
  deps="$(ldd "$elf" 2>&1 || true)"
  unresolved="$(printf '%s\n' "$deps" | grep 'not found' || true)"
  if [[ -n "$unresolved" ]]; then
    echo "::error file=$elf::Unresolved bundled ELF dependencies:"
    printf '%s\n' "$unresolved"
    missing=1
  fi
done < <(find "$APP_ROOT/usr" -type f -print0)

echo "Audited $audited runtime ELF objects; excluded $skipped explicitly classified non-runtime APT payloads."
if [[ "$missing" -ne 0 ]]; then
  echo "::error::AppDir contains unresolved shared-library dependencies in the audited runtime scope"
  exit 1
fi
echo "All audited AppImage runtime ELF dependencies resolve in the clean-host baseline."
