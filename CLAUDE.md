# CLAUDE.md — Anura OCR Project Guide

> Regole per l'agente AI Cline. Letto automaticamente all'inizio di ogni sessione.

## Tech Stack

- **Linguaggio**: Python 3.12+
- **Build**: Meson ≥ 1.5.0
- **Distribuzione**: Flatpak (`com.github.d3msudo.anura`)
- **UI**: GTK4 + Libadwaita + Blueprint Compiler 0.16.0
- **OCR**: pytesseract + Tesseract 5.5.0
- **QR**: pyzbar + zbar
- **TTS**: gTTS + GStreamer playbin3
- **Screenshots**: Xdp.Portal (libportal)
- **Settings**: GSettings singleton → `anura/services/settings.py`
- **Linter**: **ruff** solo — mai flake8, pylint o black

## Architettura

### Filosofia
- SOLID, KISS, DRY
- Funzionale/declarativo su OOP/imperativo
- Type hints su tutte le funzioni pubbliche
- Dataclass per strutture dati, Enum per stati, Union/Literal per tipi complessi
- Regex `LANG_CODE_PATTERN` da `anura/config.py` per validazione lingue
- `uri_validator()` da `anura/utils/validators.py` per URI

### Struttura progetto
```
anura/
├── main.py           ← AnuraApplication (Adw.Application)
├── window.py         ← AnuraWindow (DnD, FileDialog, paste)
├── config.py         ← Costanti, APP_ID, lang_code validation
├── language_manager.py  ← Download/gestione modelli tessdata
├── services/         ← clipboard, screenshot, notification, tts, share, settings
├── types/            ← Dataclass/enum: download_state, language_item
├── utils/            ← validators, cleanup, signal_manager
└── widgets/          ← extracted_page, welcome_page, preferences, ...
```

### Naming conventions
- `PascalCase`: classi, GTK4 widgets
- `snake_case`: directory, file, variabili, funzioni, metodi
- `on_` prefisso per event handlers: `on_extract_clicked`
- verbi booleani: `is_loading`, `has_error`
- `_` prefisso per metodi privati

## Regole di Codice — ASSOLUTE

### Thread Safety — VIOLAZIONE = CRASH
- **MAI** emettere GObject signal da thread secondari
- **SEMPRE** `GLib.idle_add(self.emit, "signal-name", data)`
- Pattern cancellazione atomica: `__slots__` + `Gio.Cancellable`
- `GLib.timeout_add` → ritorna `GLib.SOURCE_REMOVE` quando finito

### File protetti — MAI MODIFICARE
- `po/*.po`
- `anura/_release_notes.py`
- `data/ui/*.ui`
- `CHANGELOG.md`

### Scrittura file
- Pattern atomico: `tempfile.NamedTemporaryFile` + `shutil.move`
- **No subprocess** — usa GLib/GIO invece

### Internazionalizzazione (i18n)
- `_("text {var}").format(var=value)` — MAI `_(f"...")`
- `ngettext()` per plurali
- Dopo nuove UI string → ricordare di eseguire `./generate_pot.sh`
- Logger, eccezioni, GSettings keys NON devono essere tradotti

### Gestione errori — Early Return Pattern
- Guardie e validazioni all'inizio delle funzioni
- Happy path alla fine
- `is None` non `== None`
- Nessun `except Exception` che silenzia bug reali
- `try/except` specifici, non generici

### Dipendenze
- **`uv` esclusivo**: `uv add`, `uv remove`, `uv sync`
- Mai `pip install`, `pip freeze`, `poetry`, `pip-tools`
- `uv run` per script e comandi

## Comandi di Sviluppo

### Setup ambiente
```bash
# System dependencies (Ubuntu/Debian)
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1 \
    blueprint-compiler libportal-gtk4-dev \
    tesseract-ocr python3-pil python3-pip \
    gstreamer1.0-plugins-good gstreamer1.0-pulseaudio

# Python dependencies
uv sync --dev
```

### Build (Meson)
```bash
.venv/bin/meson setup builddir
.venv/bin/meson compile -C builddir
```

### Run da source
```bash
GSETTINGS_SCHEMA_DIR=builddir/data python3 -m anura.main
```

### Flatpak
```bash
flatpak-builder --force-clean builddir flatpak/com.github.d3msudo.anura.json
flatpak-builder --run builddir flatpak/com.github.d3msudo.anura.json anura
```

## Testing

### Setup GSchema
```bash
mkdir -p builddir
cp data/com.github.d3msudo.anura.gschema.xml builddir/
glib-compile-schemas builddir/
export GSETTINGS_SCHEMA_DIR="builddir"
```

### Comandi test
```bash
# Pure Python tests (no GTK)
uv run pytest tests/ -v -m "not gtk"

# GTK tests (con system gi)
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" \
  GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" \
  GSETTINGS_SCHEMA_DIR="builddir" \
  pytest tests/ -v

# File specifici
uv run pytest tests/test_config.py -v
uv run pytest tests/test_uri_validator.py -v
```

### Markers
- `@pytest.mark.gtk` — test che richiedono GTK/GLib
- `@pytest.mark.network` — test che richiedono rete

### Troubleshooting test
- `ValueError: Namespace Xdp not available` → `sudo apt install gir1.2-xdpgtk4-1.0`
- `ModuleNotFoundError: No module named 'gi'` → usa PYTHONPATH sopra
- `RuntimeError: GSettings schema not found` → compila schema in builddir
- `TesseractError missing argument` → `pytesseract.TesseractError("msg", "msg")`

## Conventional Commits

Formato messaggi di commit:
```
<type>(<scope>): <titolo conciso>

- Modifica 1: descrizione breve
- Modifica 2: descrizione breve

Files changed:
- path/to/file: descrizione
```

Tipi: `feat:`, `fix:`, `refactor:`, `docs:`, `style:`, `test:`, `chore:`

## Pattern di Sicurezza

- Input validation su TUTTO: `LANG_CODE_PATTERN` per Tesseract, `uri_validator()` per URI
- File download atomici: tempfile + shutil.move
- Operazioni in sandbox Flatpak: XDG Portal, no filesystem fuori da `xdg-download`
- Nessuna telemetria — Anura è privacy-first
- Cache linguaggi con `functools.lru_cache`
- Lazy loading per risorse pesanti

## Workflow per Richieste Specifiche

Chiedimi direttamente questi comandi:

| Comando | Azione |
|---------|--------|
| `commit` | Analisi git status/diff → Conventional Commit |
| `bug analysis` | Analisi statica bug file-per-file |
| `code quality` | Audit qualità + refactoring sistematico |
| `fix check` | Verifica post-fix (5 passi) |
| `review` | Code review completo (10 audit) |
| `dead code` | Trova codice morto (import, funzioni, classi) |
| `debug <problema>` | Debug ipotesi-driven con falsificazione |
| `vibe clean` / `tidy up` | Pulizia codice seguendo pattern progetto |
| `dead-code` | Analisi codice morto: import inutilizzati, funzioni, classi |
| `vibe check` | Report pulizia senza modifiche |