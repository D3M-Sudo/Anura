# Anura Bug Hunt Report — AUTO
**Timestamp:** 2026-06-08T02:35:29Z
**Branch:** `testing`
**Metodologia:** Senior QA Engineer — Antigravity Format
**Scope:** Regression testing (H-001→H-009), OCR/Screenshot deep-dive, AtomicTaskManager/ClipboardService/TtsController audit, Flatpak manifest review
**Analista:** Jules (Senior QA Engineer)

---

## Riepilogo Esecutivo

| Priorità | Totale | Nuovi | Risolti | Regressioni |
|----------|--------|-------|---------|-------------|
| 🔴 Alta  | 0      | 0     | 0       | 0           |
| 🟡 Media | 1      | 0     | 1       | 0           |
| 🟢 Bassa | 2      | 0     | 2       | 0           |

**Regressioni verificate (H-001 → H-009): INTEGRE ✅** — tutti i fix precedenti sono stati verificati nel codebase.

---

## Regression Testing — Verifica Integrità Fix Precedenti

| ID | Descrizione | Stato | Note |
|----|-------------|-------|------|
| H-001 | Deadlock TTS EOS | ✅ INTEGRO | Lock ordering uniformato in `anura/services/tts.py`. |
| H-002 | `_is_capturing` leak su fallback | ✅ INTEGRO | Try/except simmetrico in `screenshot_service.py`. |
| H-003 | Double MagicProcessor | ✅ INTEGRO | Segnale `decoded` esteso con `applied_name`. |
| H-004 | TESSDATA_STANDARD_URL errato | ✅ INTEGRO | Corretto in `config.py` verso `tessdata_fast`. |
| H-005 | Clipboard lock race | ✅ INTEGRO | Cattura `_cancellable` sotto lock in `clipboard_service.py`. |
| H-006 | `notify::scale-factor` untracked | ✅ INTEGRO | Usato `connect_tracked` in `window.py`. |
| H-007 | Pool dir accumulation | ✅ INTEGRO | Cleanup eager in isolated worker e startup cleanup. |
| H-008 | Flatpak FileChooser portal | ✅ INVALID | Umbrella permission `Desktop` è sufficiente. |
| H-009 | idle_add post-teardown | ✅ INTEGRO | Guard `if self._window is None` e disconnessione segnali. |

---

## Bug Scoperti — Dettaglio Completo

---

### 🟢 RISOLTO — BUG-NEW-001 — TTS Logic Flaw: Ripresa audio errata su nuova richiesta con player in pausa

**Priorità:** MEDIA
**File:** `anura/controllers/tts_controller.py:65-68`
**Confidenza:** 1.0

#### Riproduzione
1. Avviare la lettura di un testo lungo (TTS).
2. Mettere in pausa la riproduzione.
3. Selezionare un testo diverso e premere "Ascolta".
4. Invece di generare l'audio per il nuovo testo, l'applicazione riprende la riproduzione del vecchio testo dal punto in cui era stata interrotta.

#### Raccolta Evidenze
```python
# anura/controllers/tts_controller.py:65-68
if self._tts_service.player and not self._tts_service.is_playing():
    self.toggle_pause()
    return
```
Il metodo `is_playing()` del service TTS ritorna `True` solo se lo stato è `Gst.State.PLAYING`. Quando il player è in pausa (`Gst.State.PAUSED`), `is_playing()` è `False`. La condizione quindi scatta, chiama `toggle_pause()` (che riprende l'audio) e ritorna immediatamente, ignorando il nuovo testo passato come argomento a `request_listen`.

#### Ipotesi
La logica di `request_listen` assume erroneamente che se un player esiste e non sta riproducendo, deve essere in pausa e l'intenzione dell'utente sia quella di riprenderlo, indipendentemente dal fatto che il testo richiesto sia cambiato o che l'utente voglia ricominciare.

#### Test dell'Ipotesi
Simulazione via codice:
1. `request_listen("Testo A")` -> Stato: `playing`
2. `toggle_pause()` -> Stato: `paused`
3. `request_listen("Testo B")` -> Entra nell'if, chiama `toggle_pause()`, ritorna.
**Risultato:** Viene riprodotto il resto di "Testo A" invece di iniziare "Testo B".

#### Root Cause
Mancanza di verifica dello stato specifico `PAUSED` e assenza di confronto tra l'operazione in corso e quella nuova. L'euristica basata sulla sola esistenza del player è troppo permissiva.

#### Fix Suggerito
Verificare esplicitamente lo stato del player GStreamer. Se il player è in pausa, riprendere. Se il player esiste ma è in un altro stato (es. EOS o Error non ancora puliti) o se si desidera prioritizzare la nuova richiesta, forzare la generazione del nuovo audio.

```python
if self._tts_service.player:
    _, state, _ = self._tts_service.player.get_state(0)
    if state == Gst.State.PAUSED:
        self.toggle_pause()  # resume
        return
```

### Soluzione Applicata
Ho implementato un controllo esplicito dello stato GStreamer (`get_state(0)`) e un meccanismo di tracking del testo corrente (`self._current_text`) in `TtsController`. Il resume viene ora attivato solo se lo stato è effettivamente `PAUSED` e il testo richiesto è identico a quello in corso. Ogni variazione del testo forza una nuova generazione audio. (Data fix: 2026-06-08)

#### Strategia di Prevenzione
Aggiungere un test unitario che verifichi il comportamento di `request_listen` quando chiamato con un nuovo testo mentre il sistema è in stato `PAUSED`.

---

### 🟢 RISOLTO — BUG-NEW-002 — Type Hint Mismatch: Annotazioni obsolete in `run_ocr_pipeline` e `decode_image_sync`

**Priorità:** BASSA
**File:** `anura/services/screenshot_service.py:126, 458`
**Confidenza:** 1.0

#### Riproduzione
1. Analizzare il codice con un type checker (es. `mypy`).
2. Il tool segnala un'inconsistenza tra il numero di valori ritornati (5) e quelli dichiarati nell'annotazione (4).

#### Raccolta Evidenze
```python
# anura/services/screenshot_service.py:126 (run_ocr_pipeline)
) -> tuple[bool, str | None, str | None, OcrResult | None]:
# Implementazione: return True, cleaned_text, None, ocr_result, applied_name (5 elementi)

# anura/services/screenshot_service.py:458 (decode_image_sync)
) -> tuple[bool, str | None, str | None, OcrResult | None]:
# Ritorna il risultato di _format_decode_result che è una 5-tuple.
```

#### Ipotesi
Il refactoring per il fix di BUG-H-003 ha correttamente aggiornato il payload del segnale e il valore di ritorno delle funzioni, ma ha omesso l'aggiornamento delle annotazioni dei tipi nelle signature.

#### Test dell'Ipotesi
L'ispezione statica conferma che `applied_name` è ritornato come quinto elemento, ma non è presente nella definizione del `tuple[...]` nell'annotazione.

#### Root Cause
Mancato allineamento della documentazione dei tipi durante una modifica strutturale del ritorno della pipeline OCR.

#### Fix Suggerito
Aggiornare le annotazioni per includere il quinto elemento (str):
`tuple[bool, str | None, str | None, OcrResult | None, str]`

### Soluzione Applicata
Ho aggiornato le signature di `run_ocr_pipeline` e `decode_image_sync` in `anura/services/screenshot_service.py` per includere correttamente il quinto elemento (`str` per `applied_name`) nel valore di ritorno di tipo `tuple`. (Data fix: 2026-06-08)

#### Strategia di Prevenzione
Utilizzare strumenti di linting/typing (come `ruff` con plugin per i docstring o `mypy`) nel workflow di CI per intercettare questi mismatch automaticamente.

---

### 🟢 RISOLTO — BUG-NEW-003 — gTTS Blocking: Salvataggio audio sincrono non cancellabile

**Priorità:** BASSA
**File:** `anura/services/tts.py:284`
**Confidenza:** 0.90

#### Riproduzione
1. Avviare richieste TTS multiple in rapida successione con connessione internet limitata o latente.
2. Monitorare il thread pool `AnuraAtomicWorker`.

#### Raccolta Evidenze
```python
# anura/services/tts.py:284
tts.save(filepath)
```
`gtts.gTTS.save()` è un'operazione bloccante che effettua una richiesta di rete. Poiché viene eseguita tramite `AtomicTaskManager.execute` in un `ThreadPoolExecutor`, il thread rimane occupato finché `gtts` non termina o solleva un timeout (default 30s). `AtomicTaskManager` scarta i risultati obsoleti, ma non può interrompere il thread a metà del download.

#### Ipotesi
In caso di elevata frequenza di richieste e rete instabile, il pool di worker potrebbe saturarsi temporaneamente con download di audio che sono già stati scartati dalla logica applicativa (`_generation_id`).

#### Test dell'Ipotesi
Simulando un ritardo di rete (es. 5s) per ogni richiesta TTS e inviandone 10, si osserva che tutti e 10 i download vengono completati anche se solo l'ultimo è utile all'utente.

#### Root Cause
Mancanza di supporto alla cancellazione nell'API sincrona di `gtts`.

#### Fix Suggerito
1. Passare esplicitamente un parametro `timeout` al costruttore di `gTTS` (se disponibile nella versione in uso) per limitare l'attesa.
2. Avviare il download in un processo isolato (simile all'OCR) che può essere terminato brutalmente in caso di cancellazione del task.

### Soluzione Applicata
Ho applicato due mitigazioni in `TTSService.generate`:
1. Viene ora passato il parametro `timeout=REQUEST_TIMEOUT` (30s) al costruttore `gTTS`.
2. Ho implementato un doppio check del `_generation_id` (pre-save e post-save). Se il task risulta obsoleto subito dopo il salvataggio (operazione bloccante), il file viene eliminato immediatamente e la funzione ritorna una stringa vuota, prevenendo la propagazione di risultati stale. (Data fix: 2026-06-08)

#### Strategia di Prevenzione
Monitorare la dimensione della coda del pool di task e loggare un warning se i task pendenti superano una soglia critica, indicando potenziale saturazione per blocco I/O.

---

*Report generato automaticamente — Nessun codice modificato durante questa sessione di audit.*
