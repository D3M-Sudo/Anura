# Anura Bug Hunt Report — AUTO
**Timestamp:** 2026-07-03T07:41:05Z
**Branch:** `main`
**Metodologia:** Senior QA Engineer — Antigravity Format (@bug-hunter)
**Scope:** Audit di stabilità e sicurezza, Regression Testing, Deep-dive OCR/Screenshot, Resource Audit.
**Analista:** Jules (Senior QA Engineer)

---

## Riepilogo Esecutivo

| Priorità | Totale Findings | Regressioni | Nuovi Bug Logici | Issue Qualità/Stabilità |
|----------|-----------------|-------------|------------------|-------------------------|
| 🔴 Alta  | 0               | 0           | 0                | 0                       |
| 🟡 Media | 2               | 0           | 0                | 2                       |
| 🟢 Bassa | 2               | 0           | 0                | 2                       |

L'audit conferma che il codebase di Anura OCR mantiene un elevato standard di stabilità. I fix per le regressioni critiche passate (deadlock TTS, leak `_is_capturing`, double-processing) sono integri e correttamente implementati. Non sono stati rilevati nuovi bug logici bloccanti o vulnerabilità di sicurezza immediate.

---

## Regression Testing — Verifica Integrità Fix Precedenti

| ID | Descrizione | Stato | Note |
|----|-------------|-------|------|
| BUG-H-001 | Deadlock TTS EOS (Lock Inversion) | ✅ INTEGRO | Ordine di acquisizione lock canonico rispettato in `tts.py`. |
| BUG-H-002 | `_is_capturing` leak su fallback | ✅ INTEGRO | Try/except simmetrico presente in `screenshot_service.py`. |
| BUG-H-003 | Double MagicProcessor Execution | ✅ INTEGRO | Segnale `decoded` esteso; MagicProcessor rimosso dal controller. |
| BUG-H-004 | TESSDATA_STANDARD_URL errato | ✅ INTEGRO | Punta correttamente al repository `tessdata_fast`. |
| BUG-H-005 | Clipboard lock race (`_cancellable`) | ✅ INTEGRO | Snapshot del cancellable eseguito sotto lock. |
| BUG-H-006 | `notify::scale-factor` untracked | ✅ INTEGRO | Utilizzato `connect_tracked` in `window.py`. |
| BUG-H-007 | Pool dir accumulation | ✅ INTEGRO | Cleanup eager nell'isolated worker implementato. |
| BUG-H-009 | idle_add post-teardown | ✅ INTEGRO | Disconnessione segnali e weakrefs gestiti via `SignalManagerMixin`. |
| BUG-NEW-001| TTS Resume logic flawed | ✅ INTEGRO | Controllo `Gst.State.PAUSED` e delta-text implementato. |

---

## Bug Scoperti — Dettaglio Completo

---

### 🟡 ISSUE-001 — Anti-pattern: Sovrascrittura Variabile Context Manager (PLW2901)

**Priorità:** MEDIA
**File:** `anura/services/screenshot_service.py:644`
**Confidenza:** 1.0

#### Riproduzione
1. Eseguire l'analisi statica con Ruff (`uv run ruff check anura/ --select PLW2901`).
2. Osservare l'errore segnalato nel metodo `_process_image_decode`.

#### Raccolta Evidenze
```python
# anura/services/screenshot_service.py:644
with Image.open(file) as img:
    # ...
    if img.mode != "L":
        img = img.convert("L")  # ← PLW2901
```

#### Ipotesi
L'assegnazione `img = img.convert("L")` sovrascrive il riferimento all'oggetto aperto dal context manager `with`. Sebbene in Python questo non causi un crash immediato, è un anti-pattern che può rendere ambigua la chiusura delle risorse di Pillow (che avviene all'uscita dal blocco `with` sul riferimento originale).

#### Test dell'Ipotesi
Eseguendo un test di stress con migliaia di immagini convertite, il garbage collector potrebbe non chiudere tempestivamente i file handle originali se il riferimento viene perso prematuramente.

#### Root Cause
Uso dello stesso nome variabile (`img`) per l'oggetto originale del context manager e per il risultato della trasformazione (una nuova istanza di `Image`).

#### Fix Suggerito
Utilizzare un nome differente per l'immagine processata:
```python
if img.mode != "L":
    grayscale_img = img.convert("L")
    extracted, ocr_result, applied_name = self._try_ocr_extraction(
        grayscale_img, lang, start_time, task_id=task_id
    )
```

#### Strategia di Prevenzione
Includere la regola `PLW` (Pillow/Pylint) nella configurazione Ruff del progetto per bloccare questi anti-pattern in fase di CI.

---

### 🟡 ISSUE-002 — Complessità Ciclotomatica Elevata in LanguageManager (C901)

**Priorità:** MEDIA
**File:** `anura/services/language_manager.py:462`
**Confidenza:** 0.90

#### Riproduzione
1. Eseguire `uv run ruff check anura/ --select C901`.
2. Osservare che `download_begin` ha un valore di complessità pari a 21.

#### Raccolta Evidenze
Il metodo `download_begin` gestisce:
- Validazione ISO 639-2.
- Verifica binario Tesseract.
- Mapping dei nomi file.
- Creazione directory e permessi 0700.
- Download via `requests` con stream.
- Security limit DoS (Content-Length e Cumulative bytes).
- Throttling dei segnali di progresso (100ms logic).
- Installazione atomica via `shutil.copy2`.
- Cleanup dei file temporanei.

#### Ipotesi
L'elevata complessità rende il metodo difficile da testare esaustivamente (richiederebbe decine di percorsi di test) e aumenta il rischio di bug latenti in caso di modifiche alla logica di sicurezza.

#### Test dell'Ipotesi
Tentando di aggiungere una nuova guardia di sicurezza, la probabilità di introdurre una regressione in un path di errore esistente è alta a causa del nesting profondo dei blocchi `try/finally/with`.

#### Root Cause
Violazione del Single Responsibility Principle: il metodo integra logica di networking, sicurezza di sistema e gestione UI (segnali).

#### Fix Suggerito
Refactoring mediante estrazione di metodi privati:
- `_validate_request(code)`
- `_stream_response_to_file(url, tmp_path, cancellable)`
- `_handle_progress_emit(downloaded, total_size, start_time)`

#### Strategia di Prevenzione
Impostare un limite rigoroso `max-complexity = 10` nel file `pyproject.toml` per forzare il refactoring delle funzioni che superano questa soglia.

---

### 🟢 ISSUE-003 — EXDEV Fallback Silence

**Priorità:** BASSA
**File:** `anura/services/language_manager.py:754`
**Confidenza:** 0.85

#### Riproduzione
1. Configurare un ambiente dove `$XDG_CACHE_HOME` è su un filesystem diverso da `/app`.
2. Avviare OCR multi-lingua.
3. Osservare che in caso di errore nella copia fallback, il log non fornisce dettagli sui path coinvolti.

#### Raccolta Evidenze
```python
# anura/services/language_manager.py:754
if e.errno == errno.EXDEV:
    try:
        shutil.copy2(source_path, dest_path)
    except OSError as copy_err:
        logger.error(f"Anura Pooling: Failed to copy {code}: {copy_err}")
```

#### Ipotesi
In ambienti Flatpak complessi, se `shutil.copy2` fallisce dopo un errore `EXDEV`, diagnosticare il motivo (permessi, spazio disco, path inesistenti) è difficile senza i percorsi completi.

#### Test dell'Ipotesi
Simulando un `OSError` (es. `ENOSPC`) durante il fallback, il log riporta solo l'errore generico senza indicare se è il sorgente (/app) o la destinazione (~/.cache) ad avere problemi.

#### Root Cause
Log di errore incompleto nel ramo di catch del fallback cross-filesystem.

#### Fix Suggerito
Arricchire il messaggio di log:
```python
logger.error(f"Anura Pooling: Failed to copy {code} from {source_path} to {dest_path}: {copy_err}")
```

#### Strategia di Prevenzione
Review dei blocchi `except OSError` per garantire che i path critici siano sempre inclusi nelle stringhe di log.

---

### 🟢 ISSUE-004 — Signal Disconnection Failure Guard

**Priorità:** BASSA
**File:** `anura/utils/signal_manager.py:155`
**Confidenza:** 0.95

#### Riproduzione
1. Disconnettere manualmente un handler GObject tracciato dal `SignalManagerMixin`.
2. Chiamare `teardown_all()`.
3. Osservare i warning nel log (già gestiti, ma indicativi di un tracking "lossy").

#### Raccolta Evidenze
```python
# anura/utils/signal_manager.py:155
try:
    if emitter:
        emitter.disconnect(handler_id)
        disconnected_count += 1
except (TypeError, RuntimeError, AttributeError) as e:
    logger.debug(f"SignalManagerMixin: Could not disconnect handler {handler_id}...")
```

#### Ipotesi
Sebbene il mixin sia robusto, non tiene traccia se un emitter è già stato distrutto nativamente, portando a tentativi di disconnessione su oggetti "dead".

#### Test dell'Ipotesi
Distruggendo un oggetto emitter prima di chiamare `teardown()` sul consumer, il mixin tenta comunque la disconnessione.

#### Root Cause
Assenza di un meccanismo di `weakref` sugli emitter all'interno della mappa `_signal_connections`.

#### Fix Suggerito
Utilizzare `weakref.WeakKeyDictionary` per `_signal_connections` per rimuovere automaticamente le voci relative a emitter distrutti.

#### Strategia di Prevenzione
Utilizzare questo pattern di tracking solo per segnali a lunga durata, preferendo `connect_object` (se disponibile) per segnali con lifecycle legato al widget.

---

## Ambiente e Sicurezza (Sandbox Audit)

- **Manifest Flatpak:** Le permessi `finish-args` sono limitati ai path `xdg-*` minimi necessari in modalità sola lettura (`:ro`). L'uso di `TESSDATA_PREFIX` è configurato correttamente per la gerarchia interna `/app`.
- **Log Masking:** È stata confermata la presenza di `mask_url` nelle chiamate critiche di `ScreenshotService`, prevenendo il leak di credenziali nei log rotativi.

---

## Conclusioni Finali
Il sistema si dimostra resiliente. L'architettura basata su `SignalManagerMixin` e `AtomicTaskManager` isola efficacemente i componenti, riducendo drasticamente il rischio di race condition globali. Si raccomanda di indirizzare le issue di complessità ciclotomatica e l'anti-pattern PLW2901 nel prossimo ciclo di refactoring per mantenere la manutenibilità a lungo termine.

**Esito Audit:** superato con raccomandazioni minori. ✅

---
*Report generato da Jules (Senior QA Engineer) — @bug-hunter methodology.*
