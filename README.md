<h1 align="center">Anura</h1>

<p align="center">
  Jumping from pixels to text in a single leap
</p>

<p align="center">
  <strong>Intuitive text extraction for the Linux desktop.</strong><br>
  OCR · QR Decoding · Privacy-first · Native GTK4
</p>

<p align="center">
  <img src="data/screenshots/anura-window-dark.png" alt="Anura Screenshot" width="800" />
</p>

<p align="center">
  <a href="https://github.com/D3M-Sudo/Anura/releases/latest">
    <img src="https://img.shields.io/github/v/release/D3M-Sudo/Anura?color=4A90D9&logo=github&label=release&style=flat-square" alt="Latest Release" />
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-22c55e?style=flat-square" alt="License: MIT" />
  </a>
  <a href="https://hosted.weblate.org/engage/anura/">
    <img src="https://img.shields.io/badge/translations-Weblate-orange?style=flat-square" alt="Translation status" />
  </a>
  <a href="https://github.com/D3M-Sudo/Anura/releases/latest">
    <img src="https://img.shields.io/badge/distribution-Flatpak-4A90D9?style=flat-square&logo=flatpak" alt="Flatpak" />
  </a>
</p>

---

Anura lets you capture any region of your screen and instantly extract the text inside — from videos, screencasts, PDFs, webpages, or photos. The result lands straight in your clipboard, ready to paste.

It also decodes **QR codes** in a single click, with full system integration on modern GTK-based Linux desktops.

---

## Features

| | |
| --- | --- |
| 📷 **Instant OCR** | Select a screen region — text is copied automatically |
| 🔲 **QR Code Decoding** | Recognizes links and data from QR codes |
| 🌍 **Multi-language** | Supports 100+ Tesseract language models |
| 🔊 **Text-to-Speech** | Read extracted text aloud via gTTS |
| 🔒 **Privacy-first** | All processing happens locally — no data leaves your machine |
| 🎨 **Native GTK4** | Designed for GNOME, built with Libadwaita |
| 🚀 **Async D&D** | Smooth, non-blocking drag-and-drop experience |

---

## Installation

### Flatpak — Stable Release

Download the `.flatpak` bundle from the [Releases](https://github.com/D3M-Sudo/Anura/releases/latest) page, then install:

```bash
flatpak install --user ~/Downloads/io.github.d3msudo.anura.flatpak
```

### Runtime requirements

Anura captures screenshots through the **XDG Desktop Portal**. The portal frontend is shipped with `xdg-desktop-portal` (typically already installed), but it needs a *backend* matching your desktop session. **GNOME and KDE ship one by default**, but other desktops (notably **LXQt**) do not — Anura cannot bundle a portal backend inside the Flatpak because it must run on the host with access to the compositor.

| Desktop session | Install command (Ubuntu 24.04+) | Notes |
| --- | --- | --- |
| GNOME / Ubuntu Desktop | already installed | Uses `xdg-desktop-portal-gnome` or `-gtk` |
| KDE Plasma / Kubuntu | already installed | Uses `xdg-desktop-portal-kde` |
| **LXQt / Lubuntu** | `sudo apt install xdg-desktop-portal-kde` | Also create `~/.config/xdg-desktop-portal/lxqt-portals.conf` |
| Xfce | `sudo apt install xdg-desktop-portal-gnome` | Or `-kde`; `-gtk` no longer provides Screenshot |
| MATE | `sudo apt install xdg-desktop-portal-gnome` | Or `-kde` |
| Cinnamon | `sudo apt install xdg-desktop-portal-gnome` | Or `-kde` |
| Budgie | `sudo apt install xdg-desktop-portal-gnome` | Or `-kde` |
| wlroots (Sway, Hyprland, river, Niri) | `sudo apt install xdg-desktop-portal-wlr` | May need `xdg-desktop-portal` ≥ 1.15 |

After installing, **log out and back in** so the portal D-Bus service reloads. If the screenshot still fails, capture an `anura_debug.log` and the `domain=…, code=…` line will narrow down the cause.

#### Host screenshot fallback (Flatpak only)

Some desktop sessions ship a portal frontend but no backend that exposes the
`Screenshot` interface for the active session — most notably **LXQt / Xfce /
Openbox on Ubuntu 24.04+**, where `xdg-desktop-portal-gtk` 1.15.x removed
Screenshot upstream and `xdg-desktop-portal-kde` 5.27.x only registers it
when KWin is the window manager.

When the portal returns the libportal generic `Screenshot failed` error,
Anura's Flatpak transparently falls back to a host-side screenshot CLI via
`flatpak-spawn --host`. To enable that path, install **at least one** of
the following tools on the host:

```bash
# Recommended — GTK-based UI, works on every X11 desktop:
sudo apt install gnome-screenshot

# Optional fallback — tiny, CLI-driven (~200 KB):
sudo apt install scrot
```

Anura tries them in this order: `gnome-screenshot` →
`xfce4-screenshooter` → `spectacle` → `scrot` → `maim` → ImageMagick
`import`. The first installed tool runs its native region-selection UI,
writes a PNG into `~/Downloads/.anura-shot-<uuid>.png`, and Anura OCRs the
result and deletes the temp file. If no tool is installed, Anura surfaces
the original portal-failure banner so you know what to install.

Outside the Flatpak (e.g. when running from source), the host fallback is
not used; the portal is the only path.

---

## Troubleshooting

### Debug Logging

Anura supports configurable logging levels via the `ANURA_LOG_LEVEL` environment variable:

```bash
# Default level (INFO)
ANURA_LOG_LEVEL=INFO flatpak run io.github.d3msudo.anura

# Verbose debugging
ANURA_LOG_LEVEL=DEBUG flatpak run io.github.d3msudo.anura

# Trace level (most detailed)
ANURA_LOG_LEVEL=TRACE flatpak run io.github.d3msudo.anura
```

Valid levels: `TRACE`, `DEBUG`, `INFO` (default), `WARNING`, `ERROR`, `CRITICAL`

### Common Issues

**Screenshot fails with "No portal backend found"**
- Install the appropriate portal backend for your desktop (see table above)
- Log out and back in to reload portal services
- If still failing, install host screenshot tools (gnome-screenshot or scrot)

**Language models not downloading**
- Check network connection
- Verify `~/.var/app/io.github.d3msudo.anura/data/anura/tessdata/` exists
- Set `ANURA_LOG_LEVEL=DEBUG` for detailed download logs

**Text extraction shows no results**
- Ensure the image contains readable text
- Try different language settings
- Check if the image resolution is too low

---

## Building from Source

### Prerequisites

| Tool | Version |
| ---- | ------- |
| Meson | ≥ 1.5.0 |
| Python | ≥ 3.12 |
| GTK4 + Libadwaita | latest |
| Tesseract OCR | ≥ 5.0 |
| ZBar | any |
| Blueprint Compiler | ≥ 0.16.0 |

**Fedora:**

```bash
sudo dnf install meson python3-gobject gtk4-devel libadwaita-devel \
    tesseract zbar-devel blueprint-compiler
```

**Ubuntu / Linux Mint / Debian:**

```bash
sudo apt install meson python3-gi python3-gi-cairo gir1.2-gtk-4.0 \
    gir1.2-adw-1 tesseract-ocr libzbar0 blueprint-compiler
```

---

### GNOME Builder *(recommended)*

1. Install [GNOME Builder](https://wiki.gnome.org/Apps/Builder) from Flathub
2. Open the project folder in Builder
3. Press **Run (F5)** — Builder handles runtimes and compilation automatically

---

### Meson *(manual)*

```bash
git clone https://github.com/D3M-Sudo/Anura.git
cd Anura

meson setup builddir --prefix=/usr/local
ninja -C builddir

# Run without installing
./builddir/bin/anura

# Or install system-wide
sudo ninja -C builddir install
```

---

### Flatpak *(distributable bundle)*

```bash
flatpak-builder --force-clean build-flatpak \
    flatpak/io.github.d3msudo.anura.json
```

---

## Code Quality

Anura uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [pytest](https://pytest.org) for testing.

```bash
# Activate the virtual environment first
source .venv/bin/activate

# Lint
ruff check anura/ build-aux/

# Format
ruff format anura/

# Auto-fix
ruff check --fix anura/

# Run tests (no GTK required)
pytest tests/ -m "not gtk" -v

# Run GTK-dependent tests (requires setup)
mkdir -p builddir
cp data/io.github.d3msudo.anura.gschema.xml builddir/
glib-compile-schemas builddir/
export GSETTINGS_SCHEMA_DIR="builddir"
pytest tests/test_screenshot_service.py tests/test_clipboard_service.py tests/test_tts_service.py -v
```

> **Note:** Tests marked `@pytest.mark.gtk` require system GTK libraries and GSettings schema.  
> See `.windsurf/rules/testing.md` for complete setup instructions.

---

## Localization

Anura is translated via [Weblate](https://hosted.weblate.org/engage/anura/). Contributions in any language are welcome.

<p align="center">
  <a href="https://hosted.weblate.org/engage/anura/">
    <img src="https://hosted.weblate.org/widgets/anura/-/horizontal-auto.svg" alt="Translation status" />
  </a>
</p>

**For maintainers** — after changing translatable strings, from the `po/` directory:

```bash
# Update the POT file and POTFILES
./update_potfiles.sh

# Sync all locale files before committing
for f in *.po; do msgmerge -U "$f" io.github.d3msudo.anura.pot --backup=none; done
```

Then push `io.github.d3msudo.anura.pot`, `POTFILES`, and the updated `.po` files to keep Weblate in sync.

---

## Contributing

Any help is appreciated — bug reports, translations, code, or design feedback.

Anura follows the GNOME project [Code of Conduct](https://gitlab.gnome.org/World/amberol/-/blob/main/code-of-conduct.md).  
See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines and workflow details.

---

## License

Released under the **MIT** license. See [`LICENSE`](LICENSE) for details.

---
