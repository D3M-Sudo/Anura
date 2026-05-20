# REPORT INVESTIGATIVO TECNICO — ANURA OCR (Branch: flathub-testing)

## 1. RISULTATI DELL'INVESTIGAZIONE TECNICA

### 1.1 Limitazione Single-Path Tesseract
*   **File:** `anura/config.py` (Righe 92-132)
*   **Codice Critico:**
    ```python
    primary_code = lang_code.split("+")[0]
    user_model = os.path.join(TESSDATA_DIR, f"{primary_code}.traineddata")
    if os.path.exists(user_model):
        return f'--tessdata-dir "{TESSDATA_DIR}" --psm 3 --oem 1'
    ```
*   **Analisi Impatto:** Tesseract non accetta percorsi multipli. Attualmente, Anura controlla solo il primo componente (es. "eng" in "eng+ita") e imposta il `--tessdata-dir` su quella directory. Se `ita.traineddata` si trova nell'altro percorso (es. uno in `/app` e uno in `~/.local`), Tesseract fallirà silenziosamente o produrrà output errati per la seconda lingua.

### 1.2 Aggressività del TextPreprocessor
*   **File:** `anura/utils/text_preprocessor.py` (Righe 182-195, 260-272, 104-111)
*   **Codice Critico:**
    ```python
    def _normalize_whitespace(self, text: str) -> str:
        return " ".join(text.split()) # Distrugge i line break (\n)

    def _remove_artifacts(self, text: str) -> str:
        cleaned = self._bullets_re.sub("", text, count=0) # Rimuove bullet point utili
    ```
*   **Analisi Impatto:** L'uso di `" ".join(text.split())` converte tutto il testo in una singola riga, rendendo impossibile l'OCR di tabelle, ricevute o codice sorgente. Il rescaling sistematico (LANCZOS) su immagini già nitide ma piccole introduce overhead computazionale senza benefici reali di precisione.

### 1.3 Mancanza di USER_AGENT
*   **File:** `anura/language_manager.py` (Riga 396) e `anura/config.py` (Riga 80)
*   **Codice Critico:**
    ```python
    response = requests.get(url, timeout=REQUEST_TIMEOUT, stream=True)
    ```
*   **Analisi Impatto:** Sebbene `USER_AGENT` sia definito in `config.py`, non viene mai iniettato nelle chiamate `requests.get()`. Questo espone l'app a blocchi da parte dei server GitHub (403 Forbidden) o rate limiting aggressivo per mancanza di identificazione del client.

### 1.4 Ridondanza e Gestione Thread
*   **File:** `anura/widgets/language_popover.py` (Righe 123-145) e `anura/gobject_worker.py` (Righe 22-95)
*   **Analisi Impatto:** `populate_model()` chiama `get_downloaded_codes(force=True)` ad ogni apertura del popover e ad ogni segnale di download, causando I/O sincrono non necessario. `GObjectWorker` non gestisce la cancellazione: se un utente avvia un download e chiude l'app o cambia lingua, il thread continua a girare fino al timeout, sprecando banda e risorse.

### 1.5 Mappatura TTS (Gap Analysis)
*   **File:** `anura/services/tts.py` (Righe 46-125)
*   **Gap Analysis:** Su 121 lingue supportate da Tesseract nel `LanguageManager`, solo 76 sono mappate in `TTSService`.
*   **Mappature mancanti rilevate (Esempi):**
    - `afr` (Afrikaans) -> `af`
    - `amh` (Amharic) -> `am`
    - `aze_cyrl` -> `az`
    - `fil` (Filipino) -> `tl`
    - `isl` (Icelandic) -> `is`

---

## 2. PROPOSTA DEL PIANO DI AZIONE (Dettaglio dei Fix)

### 2.1 Soluzione "Dynamic Pooling" (Multi-language)
*   **Architettura:** Creazione di una directory `~/.cache/anura/tessdata_pool/`.
*   **Logica:** In `get_tesseract_config()`, se `lang_code` contiene `+`:
    1. Identifica tutti i file `.traineddata` necessari.
    2. Per ogni file, crea un hard link (o copia `shutil.copy2` come fallback) dai percorsi sorgente (`/app/...` o `~/.local/...`) verso la cartella di pool.
    3. Ritorna `--tessdata-dir` puntando alla cache pool.
*   **Vantaggio:** Garantisce a Tesseract un'unica directory coerente senza restrizioni UI.

### 2.2 Hardening Preprocessor & GSchema
*   **GSchema:** Aggiunta di `<key name="ocr-preprocessing" enum="...">` con valori `['off', 'image-only', 'full']`. Default: `image-only`.
*   **Integrazione:**
    - `image-only`: Esegue solo `enhance_image()` (Pillow). Salta `clean_extracted_text()`.
    - `full`: Comportamento attuale (distruttivo).
    - `off`: Passa l'immagine raw a Tesseract.
*   **Fix Whitespace:** Sostituire `" ".join(text.split())` con una logica basata su `re.sub(r'[ \t]+', ' ', text)` per preservare i caratteri `\n`.

### 2.3 Refactoring requests.Session
*   **Implementazione:** Inizializzare `self.session = requests.Session()` in `LanguageManager.__init__`.
*   **Configurazione:** Iniezione centralizzata di `USER_AGENT` e criteri di timeout/retry.
*   **Vantaggio:** Migliore gestione delle connessioni e conformità agli header richiesti dai server.

### 2.4 Hardening GObjectWorker & Popover
*   **Cancellazione:** Aggiunta parametro opzionale `cancellable: Gio.Cancellable = None` a `GObjectWorker.call`.
*   **Controllo:** Monitoraggio `cancellable.is_cancelled()` nei loop di download.
*   **Popover:** Utilizzare cache locale per `downloaded_codes`, eliminando `force=True` ridondanti.

### 2.5 TTS Enhancement & Feedback
*   **Gap Fix:** Estensione di `LANG_MAP` con le mappature identificate.
*   **Visual Feedback:** Implementazione di `Adw.Toast` in `ExtractedPage._on_tts_error` per segnalare la mancanza di supporto TTS per specifiche lingue.

---

## 3. STRATEGIA DI TESTING

### 3.1 Unit Testing (pytest)
*   **Test Preprocessor:** Validazione della preservazione della formattazione (`\n`) in modalità `image-only`.
*   **Test Pooling:** Mocking del filesystem per verificare la creazione atomica del pool di modelli.
*   **Test Validator:** Verifica sicurezza contro path traversal in `LanguageManager`.

### 3.2 Esecuzione Headless
I test verranno eseguiti in ambiente sandbox isolato:
```bash
uv run xvfb-run -a pytest tests/ -m "not gtk"
```

---
*Documento generato dall'Agente AI Senior (Jules) — Investigazione Tecnica completata.*
