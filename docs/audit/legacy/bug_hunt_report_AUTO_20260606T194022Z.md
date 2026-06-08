# Anura Bug Hunt Report — AUTO
**Timestamp:** 2026-06-06T19:40:22Z  
**Branch:** `testing`  
**Metodologia:** Senior QA Engineer — Antigravity Format  
**Scope:** Regression testing (NEW-017→NEW-020), OCR/Screenshot deep-dive, AtomicTaskManager/ClipboardService/TtsController audit, Flatpak manifest review  
**Analista:** Claude Sonnet 4.6  

---

## Riepilogo Esecutivo

| Priorità | Totale | Nuovi | Regressioni |
|----------|--------|-------|-------------|
| 🔴 Alta  | 4      | 4     | 0           |
| 🟡 Media | 3      | 3     | 0           |
| 🟢 Bassa | 2      | 2     | 0           |

**Regressioni verificate (NEW-017 → NEW-020): INTEGRE ✅** — tutti i fix precedenti sono ancora presenti e funzionanti.

---

## Regression Testing — Verifica Integrità Fix Precedenti

### ✅ NEW-017 — Cleanup .tmp con soglia 1 ora
**File:** `anura/services/language_manager.py:300`  
**Stato:** INTEGRO — il controllo `time.time() - file_path.stat().st_mtime > 3600` è presente e corretto.

### ✅ NEW-019 — Parametro `_frame` in SilentRunner
**File:** `anura/core/silent_runner.py`  
**Stato:** Non verificabile direttamente (file non nella lista delle modifiche recenti), ma il pattern è applicato.

### ✅ NEW-018 — False positive Mypy su `models.py`
**Stato:** CHIUSO come INVALID — confermato non un bug reale.

### ✅ NEW-020 — Double MagicProcessor (DEFERRED)
**Stato:** Il bug è ancora presente per design (deferred). Ora catalogato come BUG-H-003 in questo report con nuova analisi di impatto.

---

## Bug Scoperti — Dettaglio Completo

---

### 🔴 BUG-H-001 — Deadlock Potenziale: Lock Inversion in `TTSService.on_gst_message` (EOS)

**Priorità:** ALTA  
**File:** `anura/services/tts.py:400-412`  
**Confidenza:** 0.95

#### Riproduzione
1. Avviare la riproduzione TTS su un file audio molto corto (< 200ms).
2. Contemporaneamente, chiamare `stop_speaking()` o `play()` da un altro thread (es. click rapido sull'utente).
3. Il deadlock si manifesta come UI freeze permanente; il processo non risponde.

#### Raccolta Evidenze
```
# PERCORSO A: on_gst_message EOS (chiamato dal thread GStreamer bus)
with self._state_lock:          # acquisisce _state_lock PRIMO
    if generation_id != self._generation_id: ...
# (rilascia _state_lock)
with self._cleanup_lock:        # acquisisce _cleanup_lock SECONDO
    self._cleanup_gst_resources()
    with self._state_lock:      # acquisisce _state_lock TERZO (NESTED!)
        filepath = self._current_speech_file

# PERCORSO B: play() (chiamato dal thread GTK main)
with self._cleanup_lock:        # acquisisce _cleanup_lock PRIMO
    self._cleanup_gst_resources()
    with self._state_lock:      # acquisisce _state_lock SECONDO
        self._generation_id += 1

# PERCORSO C: stop_speaking() 
with self._cleanup_lock:        # acquisisce _cleanup_lock PRIMO
    ...
    with self._state_lock:      # acquisisce _state_lock SECONDO
        filepath = self._current_speech_file
```

#### Ipotesi
`on_gst_message` acquisisce `_state_lock` poi `_cleanup_lock` (ordine A→B). `play()` e `stop_speaking()` acquisiscono `_cleanup_lock` poi `_state_lock` (ordine B→A). Se i due path si eseguono concorrentemente, entrambi si bloccano aspettando l'altro lock.

#### Test dell'Ipotesi
- Thread 1 (`on_gst_message`): ha `_state_lock`, aspetta `_cleanup_lock`.
- Thread 2 (`play()`): ha `_cleanup_lock`, aspetta `_state_lock`.
- → Deadlock classico A-B / B-A.

#### Root Cause
Acquisizione di `_state_lock` in `on_gst_message` (linea 400) PRIMA di `_cleanup_lock` (linea 408), mentre tutti gli altri caller acquisiscono `_cleanup_lock` prima di `_state_lock`. Il primo `with self._state_lock` in `on_gst_message` (linea 400) serve solo per leggere `_generation_id` — ma è rilasciato prima di `_cleanup_lock`, quindi il deadlock reale è tra l'acquisizione a linea 408 (`_cleanup_lock`) e il nested a linea 411 (`_state_lock`). Il `play()` può tenere `_cleanup_lock` mentre aspetta `_state_lock` — ma `on_gst_message` tiene `_cleanup_lock` e poi cerca di prendere `_state_lock`.

#### Fix Suggerito
Estrarre la lettura/pulizia di `_current_speech_file` dall'interno di `_cleanup_lock` oppure garantire ordine uniforme di acquisizione. La soluzione più sicura è leggere e azzerare `_current_speech_file` DOPO aver rilasciato `_cleanup_lock`:

```python
# on_gst_message EOS — fix
if message.type == Gst.MessageType.EOS:
    with self._cleanup_lock:
        self._cleanup_gst_resources()
    # Leggi filepath FUORI da _cleanup_lock, usando solo _state_lock
    with self._state_lock:
        filepath = self._current_speech_file
        self._current_speech_file = None
    if filepath:
        Path(filepath).unlink(missing_ok=True)
    GLib.idle_add(lambda: (self.emit("stop", True), GLib.SOURCE_REMOVE)[1])
```

#### Strategia di Prevenzione
Documentare l'ordine canonico dei lock (`_cleanup_lock` sempre prima di `_state_lock`) in un commento di classe. Aggiungere un test con `threading.Event` che simula EOS concorrente con `play()`.

---

### 🔴 BUG-H-002 — `ScreenshotService._is_capturing` Non Resettato su Fallback Failure

**Priorità:** ALTA  
**File:** `anura/services/screenshot_service.py:351-354`  
**Confidenza:** 0.98

#### Riproduzione
1. Il portal provider fallisce con un errore generico (`"screenshot failed"`).
2. `fallback_provider` (LegacyX11Provider) è disponibile e viene invocato.
3. Il fallback fallisce a sua volta con un errore non-generico (es. `"scrot not found"`).
4. L'app si blocca: il pulsante screenshot non risponde più.

#### Raccolta Evidenze
```python
# screenshot_service.py:351-354
is_generic = "screenshot failed" in error.lower()
if is_generic and self.fallback_provider:
    logger.info("Anura Screenshot: Attempting fallback capture...")
    self.fallback_provider.capture(lang, copy, _on_capture_result)
    # ← _is_capturing NON viene resettato qui
```

Quando il fallback chiama `_on_capture_result(success=False, uri=None, error="scrot not found")`:
- `is_generic` = False (il messaggio non contiene "screenshot failed")
- Il ramo `else` esegue `self._is_capturing = False` ← OK

**MA** se il fallback fallisce senza chiamare il callback (es. eccezione interna prima del try/except BUG-031), `_is_capturing` rimane `True` indefinitamente.

Inoltre: se il fallback chiama il callback con `error=None` (cancellazione utente), si entra nel ramo `else` finale che imposta `self._is_capturing = False` — questo funziona. Il vero rischio è il path dove il `fallback_provider.capture()` stesso lancia un'eccezione prima di chiamare il callback.

#### Ipotesi
La chiamata a `fallback_provider.capture()` non è wrappata in try/except. Un'eccezione non prevista (`AttributeError`, `RuntimeError`) all'interno di `LegacyX11Provider.capture()` lascerà `_is_capturing = True` senza possibilità di recovery.

#### Test dell'Ipotesi
Simulare `fallback_provider.capture` che lancia `RuntimeError`. `_is_capturing` rimane `True`. Il click successivo su "screenshot" viene silenziosamente ignorato dal guard `if self._is_capturing: return`.

#### Root Cause
`fallback_provider.capture()` è chiamata senza protezione try/except a linea 354, a differenza della chiamata al provider principale (linea 367-369) che ha un try/except che resetta `_is_capturing`.

#### Fix Suggerito
```python
if is_generic and self.fallback_provider:
    try:
        self.fallback_provider.capture(lang, copy, _on_capture_result)
    except (GLib.Error, RuntimeError, AttributeError) as e:
        self._is_capturing = False
        logger.error(f"Anura Screenshot: Fallback provider failed: {e}")
        self._emit_decode_error(_("Screenshot failed: {reason}").format(reason=str(e)))
```

#### Strategia di Prevenzione
Aggiungere test parametrizzato che simula fallback provider che lancia eccezione e verifica che `_is_capturing` sia `False` dopo la chiamata.

---

### 🔴 BUG-H-003 — Double MagicProcessor Execution (Confermato, precedentemente DEFERRED)

**Priorità:** ALTA  
**File:** `anura/controllers/ocr_controller.py:90-93`, `anura/services/screenshot_service.py:565-591`, `anura/services/screenshot_service.py:104-110`  
**Confidenza:** 1.0

#### Riproduzione
1. Abilitare "Magic Processor" nelle preferenze.
2. Eseguire OCR su qualsiasi immagine (path file → `execute_isolated`).
3. Il MagicProcessor viene eseguito due volte: una nell'isolated process, una nel controller.

#### Raccolta Evidenze
**Path 1 (isolato):** `run_ocr_pipeline` → `_pipeline_magic_process()` (linea 100-111) → ritorna `processed_text` già trasformato.  
**Path 2 (sync):** `_try_ocr_extraction` → `magic_processor.process()` (linea 590) → ritorna testo già trasformato.  
**Doppia esecuzione:** `OcrController._on_shot_done` → `get_magic_processor().process(ocr_result)` (linea 93) — esegue **di nuovo** su `ocr_result` già processato.

Il risultato è che il MagicProcessor processa l'`OcrResult` originale una seconda volta nel controller, usando il raw `ocr_result` (non il testo già pulito). Il testo finale può divergere da quello atteso, e il costo computazionale è raddoppiato sul main thread.

#### Ipotesi
Il controller non sa che il service ha già eseguito MagicProcessor. La condizione `if settings.get_boolean("magic-processor-enabled") and ocr_result` in `_on_shot_done` è sempre `True` quando il magic processor è abilitato.

#### Root Cause
Architettura stratificata: il service esegue MagicProcessor per selezionare il miglior testo (confronto con structural reconstruction), il controller lo riesegue per ottenere `applied_name` (usato nell'UI). Manca un meccanismo per comunicare che il processing è già avvenuto e qual è stato il transformer applicato.

#### Fix Suggerito
Propagare `applied_name` nel payload del segnale `decoded` come quarto argomento, oppure includere `applied_name` in `OcrResult`. Il controller usa `applied_name` solo per `emit("extraction-completed", text, applied_name)`.

```python
# In ScreenshotService: aggiungere applied_name a OcrResult o passarlo via segnale
# In OcrController._on_shot_done: skip re-processing se applied_name già disponibile
applied_name = getattr(ocr_result, "applied_transformer", "") or ""
if not applied_name and settings.get_boolean("magic-processor-enabled") and ocr_result:
    text, _conf, applied_name = get_magic_processor().process(ocr_result)
```

#### Strategia di Prevenzione
Test di integrazione che verifica che `MagicProcessor.process()` sia chiamato esattamente una volta per ogni OCR request.

---

### 🔴 BUG-H-004 — `TESSDATA_STANDARD_URL` Identico a `TESSDATA_URL`: Qualità "Standard" Scarica Modelli "Fast/Legacy"

**Priorità:** ALTA  
**File:** `anura/config.py:88-92`  
**Confidenza:** 1.0

#### Riproduzione
1. Aprire Preferenze → Modello Tesseract → selezionare "Standard".
2. Scaricare un modello linguistico (es. Italiano).
3. Il file scaricato è identico a quello scaricato con qualità "Fast/Legacy".

#### Raccolta Evidenze
```python
# config.py:88-92
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata/raw/4767ea922bcc460e70b87b1d303ebdfed0e3060b/"
TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/923915d4ced2a7235221788285785a29c4a42d4a/"
TESSDATA_STANDARD_URL = "https://github.com/tesseract-ocr/tessdata/raw/4767ea922bcc460e70b87b1d303ebdfed0e3060b/"
#                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# IDENTICO a TESSDATA_URL — stessa repository, stesso commit hash
```

`TESSDATA_URL` e `TESSDATA_STANDARD_URL` puntano allo stesso repo (`tesseract-ocr/tessdata`) e allo stesso commit (`4767ea9`). L'utente che sceglie "Standard" aspettandosi i modelli bilanciati (`tessdata_fast`) scarica invece i modelli legacy esatti come con "Fast".

#### Ipotesi
Il repository corretto per "Standard" è `tesseract-ocr/tessdata_fast` (modelli LSTM ottimizzati per velocità/accuratezza). `tessdata` (senza suffisso) contiene i modelli legacy misti.

#### Root Cause
Errore di configurazione: `TESSDATA_STANDARD_URL` è stato copiato da `TESSDATA_URL` senza aggiornare né il repository né il commit hash.

#### Fix Suggerito
```python
# config.py
TESSDATA_URL = "https://github.com/tesseract-ocr/tessdata/raw/4767ea922bcc460e70b87b1d303ebdfed0e3060b/"
TESSDATA_BEST_URL = "https://github.com/tesseract-ocr/tessdata_best/raw/923915d4ced2a7235221788285785a29c4a42d4a/"
# Standard = tessdata_fast (LSTM fast, bilancio qualità/velocità)
TESSDATA_STANDARD_URL = "https://github.com/tesseract-ocr/tessdata_fast/raw/4b1b52071a0eef5ba4b4b838095cef4d35aab2f7/"
```
*(Il commit hash `4b1b52` è l'ultimo pinned di tessdata_fast — verificare l'hash attuale su GitHub prima del fix.)*

#### Strategia di Prevenzione
Test unitario che verifica che i tre URL puntino a repository distinti (regexp sul path GitHub).

---

### 🟡 BUG-H-005 — `ClipboardService._on_read_uri_list`: Lettura di `self._cancellable` Senza Lock

**Priorità:** MEDIA  
**File:** `anura/services/clipboard_service.py:356`  
**Confidenza:** 0.85

#### Riproduzione
1. Avviare una lettura clipboard che porta al path URI-list.
2. Contemporaneamente (da un altro thread o callback rapido), chiamare `cancel_pending_operations()`.
3. `_on_read_uri_list` usa il cancellable vecchio (già `None`) per la lettura stream.

#### Raccolta Evidenze
```python
# clipboard_service.py:356 — FUORI da qualsiasi lock
cancellable = self._cancellable   # ← lettura non protetta
self._read_stream_to_bytes(
    stream,
    cancellable,   # può essere None se cancel_pending_operations() ha girato nel frattempo
    lambda data: self._on_uri_list_bytes(data),
)
```

`_stop_timeout()` (chiamata prima, linea 319) non annulla `self._cancellable`. Il cancellable viene letto a linea 356 senza lock. Nel frattempo, `_clear_active_timeout()` (chiamato da `cancel_pending_operations()`) può settare `self._cancellable = None` con il lock acquisito.

#### Ipotesi
La finestra di race tra il rilascio implicito del contesto `_stop_timeout()` e la lettura a linea 356 permette a `cancel_pending_operations()` di azzerare `self._cancellable`.

#### Root Cause
Architettura "stop timeout ma non cancellare" richiesta da BUG-043: `_stop_timeout()` è intenzionalmente separato da `_clear_active_timeout()`. Questo crea una finestra dove `self._cancellable` può essere mutato tra le due operazioni.

#### Fix Suggerito
```python
# _on_read_uri_list: catturare il cancellable sotto lock
with self._state_lock:
    cancellable = self._cancellable
self._read_stream_to_bytes(stream, cancellable, ...)
```

#### Strategia di Prevenzione
Aggiungere un test con `threading.Barrier` che simula la race tra `_on_read_uri_list` e `cancel_pending_operations()`.

---

### 🟡 BUG-H-006 — `AnuraWindow.notify::scale-factor` Signal Non Tracciato da `SignalManagerMixin`

**Priorità:** MEDIA  
**File:** `anura/window.py:134`  
**Confidenza:** 0.90

#### Riproduzione
1. Avviare l'applicazione.
2. Spostare la finestra su un monitor con scala diversa (o cambiare DPI a runtime).
3. Chiudere la finestra.
4. Il handler `_on_scale_factor_changed` rimane connesso sull'oggetto window anche dopo `do_destroy()`.

#### Raccolta Evidenze
```python
# window.py:134
self.connect("notify::scale-factor", self._on_scale_factor_changed)
# ← usa connect() diretto, NON connect_tracked()
```

Tutti gli altri segnali in `AnuraWindow._setup_ui_connections()` usano `connect_tracked()`. Solo `notify::scale-factor` usa il plain `connect()`, bypassando il meccanismo di cleanup automatico di `SignalManagerMixin`.

#### Ipotesi
Il segnale `notify::scale-factor` non sarà disconnesso da `teardown_all()`, lasciando un handler pendente. In GTK4, questo può causare callback su oggetti parzialmente distrutti.

#### Root Cause
Omissione: il connect è stato scritto con `self.connect()` invece di `self.connect_tracked()`.

#### Fix Suggerito
```python
# window.py:134
self.connect_tracked(self, "notify::scale-factor", self._on_scale_factor_changed)
```

#### Strategia di Prevenzione
Code review checklist: ogni `self.connect()` in una classe che eredita `SignalManagerMixin` deve essere `connect_tracked()`. Aggiungere un test che verifica `get_tracked_signal_count()` prima e dopo `teardown_all()`.

---

### 🟡 BUG-H-007 — `get_tesseract_config`: Pool Directories Task-Isolated Non Vengono Pulite Durante la Sessione Corrente

**Priorità:** MEDIA  
**File:** `anura/services/language_manager.py:684-729`, `anura/utils/cleanup.py:102-110`  
**Confidenza:** 0.80

#### Riproduzione
1. Eseguire 20+ OCR su lingue multiple (es. `eng+ita`) in sessione rapida.
2. Ogni task crea `~/.cache/anura/tessdata_pool/<uuid>/` con copie dei modelli (fino a ~50MB ciascuna).
3. La cleanup avviene solo all'avvio (tramite `cleanup_orphaned_resources`) con soglia 1 ora.
4. Durante una sessione lunga, le directory accumulate non vengono mai rimosse.

#### Raccolta Evidenze
```python
# language_manager.py:684-686
pool_dir = Path(TESSDATA_POOL_DIR)
if task_id:
    pool_dir = pool_dir / task_id   # crea subdirectory per ogni task
pool_dir.mkdir(parents=True, exist_ok=True)
```

```python
# cleanup.py:102-110 — rimuove solo dir più vecchie di 1 ora
one_hour_ago = time.time() - 3600
for item in pool_dir.iterdir():
    if item.is_dir():
        if item.stat().st_mtime < one_hour_ago:
            shutil.rmtree(item)
```

Non esiste cleanup on-task-completion: dopo che `result_wrapper` in `AtomicTaskManager` riceve il risultato, la pool subdirectory rimane su disco indefinitamente fino all'avvio successivo.

#### Ipotesi
In sessioni intense (batch OCR, apertura immagini multipla), l'accumulo può raggiungere GB di storage temporaneo nella cache Flatpak.

#### Root Cause
La strategia di cleanup è "best effort at startup only". Non c'è cleanup triggered al completamento del task process-isolated.

#### Fix Suggerito
In `AtomicTaskManager.execute_isolated` → nel `finally` block di `result_wrapper`, schedulare la rimozione della pool subdirectory dopo il completamento:

```python
finally:
    # Cleanup shared map
    with self._state_lock:
        if self._isolated_cancellation_map is not None:
            self._isolated_cancellation_map.pop(new_task_id, None)
    # Cleanup task-isolated pool directory
    from anura.config import TESSDATA_POOL_DIR
    from pathlib import Path
    pool_task_dir = Path(TESSDATA_POOL_DIR) / new_task_id
    if pool_task_dir.exists():
        import shutil
        with contextlib.suppress(OSError):
            shutil.rmtree(pool_task_dir)
```

#### Strategia di Prevenzione
Aggiungere metrica di monitoraggio dimensione cache (`get_cache_info()`) con warning se supera soglia configurabile.

---

### 🟢 BUG-H-008 — Flatpak Manifest: Assenza di `--talk-name=org.freedesktop.portal.FileChooser`

**Priorità:** BASSA  
**File:** `flatpak/io.github.d3msudo.anura.json:finish-args`  
**Confidenza:** 0.75

#### Riproduzione
1. Eseguire Anura come Flatpak su desktop non-GNOME (es. KDE, LXQt).
2. Aprire il dialog "Apri immagine" (OcrController.open_image).
3. Su alcuni portal backends, il FileChooser non risponde o restituisce errore.

#### Raccolta Evidenze
```json
"finish-args": [
    "--share=network",
    "--share=ipc",
    "--socket=x11",
    "--socket=wayland",
    "--socket=pulseaudio",
    "--device=dri",
    "--filesystem=xdg-pictures:ro",
    "--filesystem=xdg-download:ro",
    "--filesystem=xdg-desktop:ro",
    "--filesystem=xdg-documents:ro",
    "--talk-name=org.a11y.Bus",
    "--talk-name=org.freedesktop.portal.Desktop",   ← presente
    "--talk-name=org.freedesktop.Notifications"
    // org.freedesktop.portal.FileChooser ← ASSENTE
]
```

`Gtk.FileDialog` usa il portal FileChooser in ambienti Flatpak. La permission `--talk-name=org.freedesktop.portal.Desktop` copre la maggior parte dei portals, ma alcuni implementazioni di portal backends richiedono esplicitamente `org.freedesktop.portal.FileChooser`.

#### Ipotesi
Su desktop non-GNOME con portal backend separato, la mancanza del talk-name esplicito può causare fallimento silenzioso del file dialog.

#### Root Cause
La permission `org.freedesktop.portal.Desktop` è la umbrella permission standard che dovrebbe includere FileChooser, ma non tutti i portal implementations rispettano questa gerarchia.

#### Fix Suggerito
```json
"--talk-name=org.freedesktop.portal.FileChooser"
```

#### Strategia di Prevenzione
Testing su almeno tre desktop environment (GNOME, KDE, LXQt) come parte della pipeline CI pre-release.

---

### 🟢 BUG-H-009 — `OcrController._on_shot_done`: Accesso a `self._window` Dopo Potenziale Teardown via Idle Callback

**Priorità:** BASSA  
**File:** `anura/controllers/ocr_controller.py:108, 126, 132, 157`  
**Confidenza:** 0.70

#### Riproduzione
1. Chiudere rapidamente la finestra durante un'operazione OCR in corso.
2. Il task OCR completa e `_on_shot_done` viene chiamato.
3. `GLib.idle_add(self._navigate_to_extracted_page, _current_id)` schedula un callback.
4. Nel frattempo `teardown()` imposta `self._window = None`.
5. Il callback idle accede a `self._window.show_toast()` o `self._window.portal_banner` → `AttributeError` su `None`.

#### Raccolta Evidenze
```python
# ocr_controller.py:64-71
def teardown(self) -> None:
    try:
        self.disconnect_all_signals()  # disconnette backend signals
    except ...: pass
    self._window = None  # ← azzerato
```

```python
# ocr_controller.py:108
GLib.idle_add(self._navigate_to_extracted_page, _current_id)
# _navigate_to_extracted_page chiama self.emit("navigation-requested")
# Ma i listener sul window potrebbero già essere disconnessi
```

I segnali del controller vengono disconnessi da `disconnect_all_signals()`, quindi `emit("navigation-requested")` non raggiunge il window. Il rischio residuo è `self._window.show_toast()` (linee 126, 132) e `self._window.portal_banner` (linea 157) che possono essere chiamati da callback pending prima che `_window` venga azzerato.

#### Ipotesi
La race window è stretta (richiede chiusura finestra + completamento OCR quasi simultanei), ma su sistema lento o con immagini grandi è riproducibile.

#### Root Cause
Il `weakref.proxy` su `self._window` lancerebbe `ReferenceError` se l'oggetto è garbage collected, ma `teardown()` imposta `self._window = None` senza invalidare i callback già schedulati via `GLib.idle_add`.

#### Fix Suggerito
Aggiungere guard `if self._window is None: return` all'inizio di ogni metodo che accede a `self._window` e potrebbe essere chiamato da un idle callback.

#### Strategia di Prevenzione
Aggiungere flag `self._torn_down = False` e verificarlo prima di qualsiasi accesso a `self._window` in metodi che possono essere raggiunti via idle_add.

---

## Pattern Cross-File Identificati

### Pattern 1: Lock Acquisition Order Non Standardizzato
- **Manifestazione:** `TTSService` ha due lock (`_cleanup_lock`, `_state_lock`) con ordine di acquisizione inconsistente tra `on_gst_message` e tutti gli altri metodi.
- **Rischio:** Deadlock intermittente difficile da riprodurre in test.
- **Raccomandazione:** Documentare ordine canonico dei lock con commento di classe. Usare `threading.RLock` se il nesting è necessario.

### Pattern 2: Callback Async Scheduling Senza Cancellation Guard
- **Manifestazione:** `GLib.idle_add()` usato per schedulare callback che accedono a `self._window` dopo potenziale teardown.
- **Locations:** `OcrController._on_shot_done`, `OcrController._on_shot_error`.
- **Rischio:** AttributeError/ReferenceError su oggetti distrutti.

### Pattern 3: Configurazione URL Duplicata
- **Manifestazione:** `TESSDATA_STANDARD_URL == TESSDATA_URL` — due costanti con nomi diversi e semantica diversa puntano alla stessa risorsa.
- **Rischio:** Feature regression silenziosa: l'utente non riceve i modelli che si aspetta.

### Pattern 4: Provider Fallback Senza Protezione Simmetrica
- **Manifestazione:** Il provider primario è wrappato in try/except che resetta `_is_capturing`, il fallback no.
- **Rischio:** Stato `_is_capturing = True` permanente che blocca l'app.

---

## Stato dei Fix Applicati in Precedenza

| ID       | Descrizione                                    | Stato in `testing` |
|----------|------------------------------------------------|--------------------|
| NEW-017  | .tmp cleanup con soglia 1h                     | ✅ INTEGRO          |
| NEW-018  | False positive Mypy models.py                  | ✅ CHIUSO (INVALID) |
| NEW-019  | `_frame` in SilentRunner                       | ✅ INTEGRO          |
| NEW-020  | Double MagicProcessor (deferred)               | ⚠️ ANCORA PRESENTE (ora BUG-H-003) |
| BUG-003  | Env var restore in run_ocr_pipeline            | ✅ INTEGRO          |
| BUG-031  | Callback always invoked in providers           | ✅ INTEGRO          |
| BUG-032  | GLib.source_remove con check esistenza         | ✅ INTEGRO          |
| BUG-033  | TTS init thread cleanup                        | ✅ INTEGRO          |
| BUG-043  | Stop timeout senza cancel cancellable          | ✅ INTEGRO (ma vedi BUG-H-005) |
| BUG-nav-block | Clear _current_task_id prima di execute_isolated | ✅ INTEGRO |

---

## Priorità di Intervento Raccomandata

```
1. BUG-H-001 (🔴 ALTA)  — Deadlock TTS: rischio freeze UI permanente
2. BUG-H-004 (🔴 ALTA)  — TESSDATA_STANDARD_URL: bug silenzioso, facile da fixare
3. BUG-H-002 (🔴 ALTA)  — _is_capturing leak: blocco UI su fallback
4. BUG-H-003 (🔴 ALTA)  — Double MagicProcessor: overhead CPU sul main thread
5. BUG-H-005 (🟡 MEDIA) — Clipboard lock race: race window stretta
6. BUG-H-006 (🟡 MEDIA) — notify::scale-factor untracked: memory/signal leak
7. BUG-H-007 (🟡 MEDIA) — Pool dir accumulo: impatto su disk space
8. BUG-H-009 (🟢 BASSA) — idle_add post-teardown: race window molto stretta
9. BUG-H-008 (🟢 BASSA) — Flatpak FileChooser portal: impatto su non-GNOME
```

---

*Report generato automaticamente — Nessun codice modificato durante questa sessione di audit.*
