---
trigger: on_bug
---

# Anura OCR Debugging

Hypothesis-driven debugging for GTK4/Python desktop applications. Terse, technical, no filler.

## Triggers

- GTK/GLib warnings/errors
- Tesseract OCR failures
- Flatpak sandbox issues  
- Thread safety violations
- GSettings problems
- "Debug this" / "Why is this broken"
- Failing pytest tests

## Pipeline

### 1. Repro
Establish deterministic failing command. No repro → no hypotheses. Hard rule.
```bash
# Common repro patterns
GSETTINGS_SCHEMA_DIR=builddir/data python3 -m anura.main
uv run pytest tests/ -m "not gtk" -v
uv run env PYTHONPATH="/usr/lib/python3/dist-packages:$PYTHONPATH" GI_TYPELIB_PATH="/usr/lib/x86_64-linux-gnu/girepository-1.0:/usr/lib/girepository-1.0" pytest tests/ -v
flatpak-builder --run builddir flatpak/com.github.d3msudo.anura.json anura
```

### 2. Localize + Debug
- Grep symbols from bug: GObject signals, Tesseract lang codes, GLib threads
- Check recent files: services/, widgets/, utils/
- Generate **5–8 primary hypotheses** across ≥4 of 7 axes:
  - **Data**: Image format, tessdata corruption, clipboard content
  - **Control-flow**: Signal emission order, async callback chains
  - **Concurrency**: GLib.idle_add() misuse, thread violations
  - **Config**: GSettings schema, language validation patterns
  - **Deps**: Flatpak modules, Python packages, system libs
  - **Env**: XDG portals, display server, locale
  - **Contract**: URI validation, lang_code patterns, API contracts

- Add 2–3 adversarial hypotheses from missed categories
- Each hypothesis gets ONE typed experiment: `probe` | `assertion` | `test`

### 3. Gate 1 — hypothesis review
Print markdown table:
```
| ID | Origin | Axis | Claim (≤80 chars) | Exp | Cost |
```
Ask user: `[Enter] run all · [e] edit · [s] skip`.

### 4. Run
Execute experiments sequentially. Record verdict: `killed | survived | inconclusive`.

### 5. Gate 2 — survival review
Print survival table. Order: killed, survived, inconclusive.
`S = count(survived) + count(inconclusive)`.

### 6. Fix + promote
**Only if `S == 1`.** Minimal fix. Reference hypothesis id.
Promote surviving experiment to `tests/` as regression test.

## Ship-the-fix guard (non-negotiable)

- `S != 1` → **refuse to write fix code**. Print: `"<S> hypotheses still alive. Shipping fix now = guessing which one. Run another round of falsification, or explicitly accept you're guessing?"`
- `--yolo` skips gates, NOT fix-refusal.
- Repro flips mid-run → halt, harden repro first.

## Anura-specific debugging patterns

### Thread safety violations
```python
# WRONG - signal from secondary thread
self.emit("decoded", text, copy)

# CORRECT - use GLib.idle_add()
GLib.idle_add(self.emit, "decoded", text, copy)
```

### Language validation failures
```python
from anura.config import LANG_CODE_PATTERN
if not re.match(LANG_CODE_PATTERN, lang_code):
    raise ValueError(f"Invalid language code: {lang_code}")
```

### URI security issues
```python
from anura.utils.validators import uri_validator
if not uri_validator(url):
    return False  # Block malicious URIs
```

### Flatpak sandbox issues
- Check `flatpak-builder --run` for XDG portal access
- Verify file permissions in `xdg-download`
- Test with `GSK_RENDERER=cairo` for non-GNOME desktops

## Tone

No pleasantries. No "I'll now…". Just do. Fragments OK. Exact technical terms.

---
Generated for Anura OCR — GTK4/Libadwaita + Python + Meson + Flatpak
