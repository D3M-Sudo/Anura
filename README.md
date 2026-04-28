# Anura

 Intuitive text extraction tool (OCR) optimized for Linux desktop environments.

---

<div align="center">
<figure>
<img src="data/screenshots/anura-window-dark.png" alt="Anura window dark">
</figure>

[![Latest Release](https://img.shields.io/github/v/release/D3M-Sudo/Anura?color=blue&logo=github)](https://github.com/D3M-Sudo/Anura/releases/latest)
</div>

Quickly extract text from almost any source: videos, screencasts, PDFs, webpages, or photos.  
Capture a screen area and get the text instantly copied to your clipboard.

**Anura** also features built-in support for decoding QR codes in just a few clicks!

## Key Features

- **Instant OCR**: Select a portion of the screen and copy the text.
- **QR Code Support**: Automatic recognition of links and data from QR codes.
- **System Integration**: Designed to integrate seamlessly with Linux Mint and GTK-based desktops.
- **Privacy-focused**: Local text processing without sending data to external servers.

## Installation

### Flatpak (Stable Release)

La prima versione stabile è ora disponibile. Puoi scaricare il bundle `.flatpak` direttamente dalla pagina delle [Releases](https://github.com/D3M-Sudo/Anura/releases/latest).

Per installarlo sul tuo sistema Linux Mint:

```zsh
flatpak install --user ~/Downloads/com.github.d3msudo.anura.flatpak
```

## Development and Build

[GNOME Builder](https://wiki.gnome.org/Apps/Builder) is recommended for development.  

To compile Anura:

1. Open the project folder in Builder.

2. Press **"Run" (F5)**. Builder will automatically download the required runtimes and compile the application.

## Localization

Anura is translated using Weblate. If you want to help translate the app into your language, please visit our project page:

[![Translation status](https://hosted.weblate.org/widgets/anura/-/horizontal-auto.svg)](https://hosted.weblate.org/engage/anura/)

## Contributing

Any help is appreciated! Anura follows the GNOME project [Code of Conduct](https://gitlab.gnome.org/World/amberol/-/blob/main/code-of-conduct.md).

## License

Anura is released under the **MIT** license. See the `LICENSE` file for more details.

---

*Fork based on Frog by Andrey Maksimov, adapted and maintained for the Anura ecosystem.*
