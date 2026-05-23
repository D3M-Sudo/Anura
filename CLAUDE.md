# CLAUDE.md — Anura OCR Project Guide

> Regole per l'agente AI. Letto automaticamente all'inizio di ogni sessione.

## Tech Stack

- **Linguaggio**: Python 3.12+
- **Build**: Meson ≥ 1.5.0
- **Distribuzione**: Flatpak (`io.github.d3msudo.anura`)
- **UI**: GTK4 + Libadwaita + Blueprint Compiler 0.16.0
- **OCR**: pytesseract + Tesseract 5.5.0
- **QR/Barcode**: zxing-cpp 2.3.0 (replaces pyzbar)
- **TTS**: gTTS + GStreamer playbin3
- **Screenshots**: Xdp.Portal (libportal) + fallback **scrot** (X11)
- **Settings**: GSettings singleton → `anura/services/settings.py`
- **Linter**: **ruff** solo — mai flake8, pylint o black

## Architettura

### Filosofia
- SOLID, KISS, DRY. Mixin per classi "God" (es. `AnuraWindow`).
- `AtomicTaskManager` per esecuzione asincrona a singolo slot con versioning UUID.
- Type hints obbligatori su funzioni pubbliche.
- `validators.sanitize_text` per pulizia output OCR (Unicode control chars).
- `uri_validator()` per validazione URI centralizzata.

### Struttura progetto
```
anura/
├── main.py              ← AnuraApplication (Adw.Application)
├── window.py            ← AnuraWindow (Mixin-based)
├── window_mixins/       ← ocr_mixin, tts_mixin, dnd_mixin
├── atomic_task_manager.py ← Task threading & versioning
├── services/            ← clipboard, screenshot, notification, tts, share, settings
├── utils/               ← barcode_detector, image_filters, structural_reconstructor, validators
└── widgets/             ← extracted_page, welcome_page, preferences, shortcuts_overlay
```

## Regole di Codice — ASSOLUTE

### Thread Safety & Atomic Execution
- **MAI** emettere GObject signal o modificare UI da thread secondari.
- **SEMPRE** usare `AtomicTaskManager.execute()`.
- Discard automatico dei risultati obsoleti tramite ID task.
- `SignalManagerMixin` + `connect_tracked()` per cleanup automatico segnali.

### File protetti — MAI MODIFICARE
- `po/*.po`
- `anura/_release_notes.py`
- `data/ui/*.ui`
- `CHANGELOG.md` (manutenzione via Keep a Changelog)

### Internazionalizzazione (i18n)
- `_("text {var}").format(var=value)` — MAI `_(f"...")`.
- `ngettext()` per plurali.
- Dopo nuove stringhe UI → `cd po && ./update_potfiles.sh`.

### Gestione errori — Early Return Pattern
- Guardie e validazioni all'inizio. Happy path alla fine.
- Nessun `except Exception` generico che silenzia bug.

### Dipendenze
- **`uv` esclusivo**: `uv add`, `uv sync`. Mai `pip` o `poetry`.

## Comandi di Sviluppo

### Setup & Build
```bash
uv sync --dev
uv run meson setup builddir
uv run meson compile -C builddir
GSETTINGS_SCHEMA_DIR=builddir/data python3 -m anura.main
```

### Testing
```bash
# Headless
uv run pytest tests/ -v -m "not gtk"
# Full (richiede display)
./setup-gschema.sh && ./tests/setup_resources.sh
export GSETTINGS_SCHEMA_DIR="builddir"
uv run pytest tests/ -v
```

## Sicurezza & Privacy
- **DoS**: Validazione `MAX_IMAGE_SIZE_BYTES` prima del caricamento.
- **Sanificazione**: Rimozione caratteri di controllo Unicode dall'OCR.
- **Validazione**: Controllo URI rigoroso prima di `UriLauncher`.
- **Zero Telemetria**: Nessun tracciamento o analytics.
