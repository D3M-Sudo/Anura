# REPORT TECNICO DI AUDIT E BUG HUNTING - 2026-06-10

### **1. [Architettura di Build] -> Percorsi Hardcoded nel Manifest Flatpak**
- **Analisi**: Durante la validazione dei file `flatpak/io.github.d3msudo.anura.json` e `.local.json`, è stata rilevata la variabile `pybind11_DIR` impostata su `/app/lib/python3.13/...`. Questo rappresenta un punto di fragilità critico: se il runtime GNOME SDK aggiorna la versione di Python (es. a 3.14), la build fallirà poiché il percorso non sarà più valido.
- **Proposta di Fix**: Utilizzare un approccio dinamico nel manifest per localizzare la directory di `pybind11` o utilizzare pattern di globbing se supportati dal builder, oppure automatizzare l'iniezione della versione corretta tramite script di pre-build.
- **Comando di Validazione**: `grep -r "python3.13" flatpak/`

### **2. [OCR Core] -> Sovrascrittura della Variabile di Loop/Context (PLW2901)**
- **Analisi**: In `anura/services/screenshot_service.py` (riga 574), la variabile `img` definita dal context manager `with Image.open(file) as img:` viene sovrascritta dall'istruzione `img = img.convert("L")`. Sebbene Python gestisca il garbage collection, sovrascrivere il riferimento originale all'interno del suo stesso blocco `with` è considerato un anti-pattern che può causare comportamenti inattesi nella chiusura delle risorse di Pillow.
- **Proposta di Fix**: Rinominare la variabile di destinazione della conversione, ad esempio: `grayscale_img = img.convert("L")`.
- **Comando di Validazione**: `uv run ruff check anura/services/screenshot_service.py --select PLW2901`

### **3. [Language Manager] -> Race Condition nella Pulizia Startup (NEW-017)**
- **Analisi**: La funzione `init_tessdata` in `anura/services/language_manager.py` esegue una cancellazione incondizionata di tutti i file `.tmp` nella directory `tessdata`. In scenari multi-istanza (es. utente che apre l'app mentre un'altra istanza sta scaricando un modello), l'istanza appena avviata corromperà il download dell'altra.
- **Proposta di Fix**: Implementare una pulizia basata sull'età del file (age-based cleanup). Eliminare solo i file `.tmp` più vecchi di 1 ora, utilizzando `file_path.stat().st_mtime`.
- **Comando di Validazione**: `uv run pytest tests/test_language_manager.py -v -k test_init_tessdata_cleanup`

### **4. [TTS Controller] -> Logica di Ripresa Audio Errata**
- **Analisi**: In `anura/controllers/tts_controller.py`, la funzione `request_listen(text)` riprende incondizionatamente l'audio precedente tramite `toggle_pause()` se il player esiste ed è in pausa. Se l'utente estrae un nuovo testo differente mentre il precedente è in pausa e clicca "Ascolta", l'app riprenderà il vecchio audio invece di generare quello nuovo.
- **Proposta di Fix**: Aggiungere un controllo per verificare se il testo richiesto è identico a quello attualmente caricato nel player. Se il testo è diverso, distruggere il player esistente e procedere con una nuova generazione.
- **Comando di Validazione**: Test manuale: 1. OCR Testo A -> Play -> Pausa. 2. OCR Testo B -> Clicca "Listen". Risultato atteso: generazione audio per Testo B.

### **5. [System/Quality] -> Permessi File e Complessità Ciclo-automatica**
- **Analisi**: L'analisi statica ha rilevato diversi file Python con il bit di esecuzione attivo (`chmod +x`) ma privi di shebang line (violazione `EXE002`). Inoltre, funzioni core come `apply` in `image_filters.py` e `reconstruct` in `structural_reconstructor.py` hanno una complessità ciclotomatica > 10, rendendo la manutenzione e il testing dei path critici difficoltosi.
- **Proposta di Fix**: Eseguire `chmod -x` sui moduli che non sono entry-point e refactorizzare le funzioni complesse estraendo la logica di analisi spaziale in metodi privati più piccoli.
- **Comando di Validazione**: `uv run ruff check anura/ --select C901,EXE002`

---

### **RIEPILOGO STATO STABILITÀ**

- **Analisi Statica**: Il codice segue standard moderni ma presenta "noise" dovuto a import non al top-level (necessari in GTK per evitare circularity) che dovrebbero essere documentati come eccezioni intenzionali.
- **Test Suite**: Headless tests stabili (153 passed). La copertura sui widget GObject è limitata in ambiente headless e richiede il workflow `gtk-tests` con Weston per una validazione reale.
- **Memory Leak**: I test di stress sulla creazione di oggetti `OcrResult` non mostrano leak significativi (Delta RSS < 0.3MB su 1000 iterazioni), confermando l'efficacia dell'uso di `slots` e classi immutabili.
- **Integrità Log**: Il sistema di logging rotativo è configurato correttamente, ma la directory `~/.local/state/anura/logs` deve essere monitorata per assicurarsi che i permessi `0700` siano applicati consistentemente su diverse distribuzioni.
