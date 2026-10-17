# Registro dei rilievi Flathub — Anura

**Baseline:** `testing@ceeb66c9b0c4b5b81357e7924de7601584a5883e`  
**Versione:** `0.2.0`  
**Stato:** audit statico; build pratica e validazioni finali non eseguite.

Le priorità sono valutazioni operative dell'audit, non severità ufficiali assegnate da Flathub.

## Sintesi

| ID | Priorità | Rilievo | Stato |
|---|---|---|---|
| FH-01 | Bloccante per trasparenza | Dichiarazione privacy in conflitto con TTS remoto | Confermato |
| FH-02 | Alta | Runtime GNOME 50 da confrontare con il runtime più recente ospitato da Flathub | Aggiornamento/test da fare |
| FH-03 | Alta | CI non garantisce la build e il lint del manifesto di release generato | Confermato come lacuna di pipeline |
| FH-04 | Alta | Supporto reale aarch64 non provato; presenti percorsi espliciti x86_64 | Rischio da verificare |
| FH-05 | Alta | Provenienza del materiale assistito da IA da ricostruire | Non verificato |
| FH-06 | Media-alta | Validatori AppStream e desktop file opzionali nel build Meson | Confermato |
| FH-07 | Media-alta | Permessi statici sandbox da giustificare e minimizzare | Revisione necessaria |
| FH-08 | Media | Screenshot referenziati tramite `main` mutabile | Rischio manutentivo; contenuti attuali coerenti |
| FH-09 | Media | Smoke test non coprono end-to-end i flussi OCR/TTS/download/screenshot | Confermato come lacuna di test |
| FH-10 | Media | Manifesto usa tag applicativo senza commit pin esplicito; tag v0.2.0 non firmato | Confermato |
| FH-11 | Media | Copertura e installazione delle licenze dei moduli non dimostrate completamente | Da verificare |
| FH-12 | Media | Test pratici di download modelli, build offline e flussi di rete assenti | Non eseguiti |
| FH-13 | Alta | Repository dedicato di submission non ancora preparato/verificato | Aperto |
| FH-14 | Media | Completezza inglese e metainfo finale da validare | Non verificato |
| FH-15 | Alta | Build e test su host reali non eseguiti durante l'audit | Aperto |
| FH-16 | Media-alta | Licenza Apache-2.0 dei modelli tessdata non installata esplicitamente dal modulo | Confermato dal manifesto ispezionato |
| FH-17 | Media-alta | Uso di filesystem statico e fallback screenshot da rivalutare con i portal | Revisione necessaria |
| FH-18 | Media-alta | Validazione metadati non è un gate esplicito obbligatorio di release | Confermato come lacuna di pipeline |
| FH-19 | Alta | Struttura del repository di submission separata non predisposta | Aperto |
| FH-20 | Alta | Provenienza IA e dichiarazione richiesta non ancora accertate dal maintainer | Aperto |
| FH-21 | Alta | Adeguatezza del dependency manifest per submission da chiarire | Aperto |
| FH-22 | Media | Localizzazione inglese non verificata con compilazione e controlli | Aperto |
| FH-23 | Alta | Compatibilità completa con GNOME 51 non testata | Aperto |

## Dettaglio dei rilievi

### FH-01 — Privacy e Google TTS

**Evidenza:** `data/io.github.d3msudo.anura.metainfo.xml.in` dichiara che nessun dato utente o testo estratto viene mai trasmesso esternamente, ma menziona la funzione TTS basata su Google TTS. `anura/services/tts/speech_generator.py` passa il testo a `gtts.gTTS(text, ...)` e salva l'audio generato. gTTS utilizza il servizio web Google Translate TTS.

**Valutazione:** la dichiarazione assoluta è incompatibile con il comportamento della funzione TTS quando attivata. Non è prova di comportamento malevolo; è una questione di trasparenza e consenso informato.

**Azione:** descrivere chiaramente che l'OCR avviene localmente, mentre il testo scelto per la sintesi vocale viene inviato al servizio remoto quando l'utente usa TTS. Verificare anche README, dialogo About, informativa e documentazione.

### FH-02 / FH-23 — Runtime

**Evidenza:** manifesto release e manifesto locale usano `org.gnome.Platform` / `org.gnome.Sdk` versione `50`; CI usa container `gnome-50`. GNOME 51 è stato annunciato e il relativo SDK Flatpak è stato dichiarato disponibile.

**Azione:** ricontrollare il runtime effettivamente più recente ospitato da Flathub al momento dell'invio. Se GNOME 51 è ancora il target richiesto, aggiornare in un branch dedicato tutti i riferimenti coerenti e testare build, avvio e funzionalità. L'annuncio di disponibilità non prova la compatibilità dell'app.

### FH-03 / FH-18 — Manifesto e gate di release

**Evidenza:** `flatpak/README.md` specifica che `io.github.d3msudo.anura.local.json` è il manifesto mantenuto a mano e che `io.github.d3msudo.anura.json` è generato da `build-aux/release.sh`. La CI descritta nel workflow builda il manifesto locale; i validatori AppStream e desktop sono dichiarati in Meson con `required: false`.

**Azione:** introdurre gate espliciti per la validazione del metainfo e del desktop file e per il lint/build del manifesto generato, senza modificare manualmente il manifesto generato. Eseguire i controlli prima della creazione della release.

### FH-04 — aarch64 e percorsi dipendenti dall'architettura

**Evidenza:** il manifesto non restringe esplicitamente le architetture; nel build environment compaiono percorsi `x86_64-linux-gnu` in `GI_TYPELIB_PATH` e `LD_LIBRARY_PATH`.

**Valutazione:** questi percorsi sono un rischio da provare, non una dimostrazione di fallimento aarch64. Flathub usa normalmente `x86_64` e `aarch64`.

**Azione:** eseguire build e test su entrambe le architetture; usare percorsi multiarch corretti o configurazione non hardcoded se i test dimostrano che serve.

### FH-05 / FH-20 — Policy IA

**Evidenza:** repository con `AGENTS.md` e regole per assistenti IA; la loro presenza non determina la provenienza effettiva dei contenuti.

**Azione:** il maintainer deve ricostruire quali contributi inclusi nel prodotto, nella documentazione e nel packaging siano stati generati o assistiti dall'IA, poi applicare la policy Flathub corrente. Il manifesto di submission non deve includere contenuto IA; un agente IA non deve aprire o automatizzare la PR di submission né redigerne messaggi o commenti.

### FH-06 / FH-14 / FH-22 — Metainfo, desktop e inglese

**Evidenza:** esistono `data/io.github.d3msudo.anura.metainfo.xml.in`, `data/io.github.d3msudo.anura.desktop.in` e cataloghi gettext sotto `po/`. `po/LINGUAS` non elenca `en`, il che da solo non indica un errore perché l'inglese può essere la lingua sorgente.

**Azione:** rendere obbligatoria la validazione con strumenti AppStream e desktop-file; validare il metainfo finale compilato, controllare campi, screenshot, release, traduzioni e testi UI in inglese.

### FH-07 / FH-17 — Permessi sandbox

**Evidenza:** il manifesto concede rete, IPC, X11, Wayland, audio, DRI e accesso read-only a Pictures, Downloads, Desktop e Documents; dichiara accesso ai bus portal, notifiche e accessibility. È presente un fallback screenshot X11 con `scrot`.

**Azione:** giustificare ogni permesso in relazione a una funzione utente. Valutare se i portal possono sostituire permessi filesystem statici o fallback più ampi. Non rimuovere permessi indiscriminatamente: provare i flussi GNOME, Wayland e X11 e documentare i limiti.

### FH-08 — Screenshot AppStream

**Evidenza:** le immagini puntate da URL `raw.githubusercontent.com/.../main/data/screenshots/` sono presenti; il controllo GitHub API precedente ha riscontrato gli stessi hash Git su `main` e tag `v0.2.0` per tutti e quattro gli screenshot.

**Valutazione:** nessuna discrepanza attuale rilevata. Il ramo `main` è mutabile, quindi una futura modifica potrebbe cambiare le immagini pubblicate senza aggiornare la release.

**Azione:** mantenere gli screenshot coerenti con la versione distribuita e verificare gli URL in ogni release.

### FH-09 / FH-12 / FH-15 — Test mancanti

**Evidenza:** i controlli statici e gli smoke test esistenti non dimostrano tutti i flussi reali; durante questo audit non sono state eseguite build Flatpak o prove su host.

**Azione:** coprire OCR su immagini reali, download dei modelli, checksum e installazione atomica, modalità offline, TTS con trasmissione remota esplicitata, screenshot portal su Wayland, fallback su X11, installazione/avvio e architetture supportate.

### FH-10 — Pinning e provenienza sorgente

**Evidenza:** il manifesto release usa il tag `v0.2.0` senza campo commit esplicito. I metadati GitHub ispezionati indicano che il tag `v0.2.0` non era firmato e non era immutabile.

**Valutazione:** non è automaticamente una violazione Flathub; riduce la garanzia di riproducibilità se il tag viene spostato.

**Azione:** valutare il pinning a un commit verificato nel manifesto di submission, mantenendo allineata la procedura release. Non assumere che la firma del tag sia requisito Flathub senza verifica della policy attuale.

### FH-11 / FH-16 — Licenze

**Evidenza:** il modulo `tessdata` include modelli `eng.traineddata` e `ita.traineddata` da `tessdata_fast` tag `4.1.0` con SHA-256; il manifesto ispezionato non installa esplicitamente la licenza del modulo tessdata. Il progetto Tesseract indica Apache-2.0 per i dati.

**Ulteriore rischio:** alcune istruzioni di copia licenze dei moduli Python terminano con `|| true`; quindi l'assenza di una licenza non fa fallire la build.

**Azione:** verificare licenza e copyright per ogni modulo e asset distribuito, includere le licenze richieste sotto `$FLATPAK_DEST/share/licenses/$FLATPAK_ID`, e controllare il contenuto del pacchetto finale. Evitare di rendere silenziosamente opzionale una licenza obbligatoria.

### FH-13 / FH-19 — Repository di submission

**Evidenza:** i manifesti upstream sono sotto `flatpak/`; non è stato preparato o verificato un repository Flathub separato.

**Valutazione:** la posizione dei manifesti nel repository upstream non è di per sé una violazione. Il requisito della struttura a root riguarda il repository di submission.

**Azione:** predisporre la submission soltanto dopo aver chiarito runtime, dependency manifest, licenze e policy IA. Non creare PR automaticamente.

### FH-21 — Dependency manifest

**Evidenza:** presenti `pyproject.toml`, `uv.lock` e moduli Python dichiarati nel manifesto Flatpak. Non è stato provato se la struttura attuale soddisfi tutti i requisiti di submission per il manifest delle dipendenze Python.

**Azione:** consultare la guida Flathub corrente per il metodo di build effettivo; garantire che tutte le dipendenze siano dichiarate, scaricate come sorgenti con checksum e disponibili offline durante la fase di build.

## Integrità download dei modelli — esito positivo statico

Il codice in `anura/services/language/download_manager.py` include controlli fail-closed: checksum richiesto, limiti di dimensione annunciata e trasferita, verifica di hash Git blob prima dell'installazione, sostituzione atomica con `os.replace()` e pulizia dei temporanei. `build-aux/check_tessdata_consistency.py` controlla coerenza fra configurazione e manifesti.

La progettazione statica appare difensiva. Non è però stata verificata con download reali o test runtime in questa fase. L'uso di SHA-1 come Git blob ID non va classificato da solo come blocco senza evidenze aggiuntive; i modelli inclusi nel pacchetto hanno anche SHA-256 nei manifesti.

## Fonti normative e tecniche

- [Flathub requirements](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub linter](https://docs.flathub.org/docs/for-app-authors/linter)
- [flatpak-builder-lint](https://github.com/flathub-infra/flatpak-builder-lint)
- [GNOME 51 release announcement](https://discourse.gnome.org/t/gnome-51-released/38820)
- [Tesseract tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast)
- [Tesseract tessdata README](https://github.com/tesseract-ocr/tessdata)
- [gTTS documentation](https://gtts.readthedocs.io/en/stable/module.html)
