# Priorità operative — audit Flathub Anura

**Baseline:** `testing@ceeb66c9b0c4b5b81357e7924de7601584a5883e`  
**Branch documentale:** `docs/flathub-audit-2026-10`  
**Data:** 2026-10-17  
**Stato:** piano, nessun gate tecnico eseguito.

## Decisione sintetica

Anura **non va ancora considerata pronta per la submission**. L'audit ha individuato almeno una contraddizione nella dichiarazione privacy, un controllo licenze incompleto e diversi gate tecnici non eseguiti. Non è stato dimostrato che il pacchetto fallisca; allo stesso modo, non esiste ancora evidenza sufficiente per dichiararlo conforme.

## P0 — prima di qualunque candidate per submission

| Ordine | Azione | Rilievi | Criterio di completamento |
|---|---|---|---|
| 1 | Correggere la trasparenza sulla TTS remota | FH-01 | Metainfo e documentazione spiegano chiaramente che il testo viene inviato al servizio remoto quando TTS è usata |
| 2 | Completare inventario licenze e file installati | FH-11, FH-16 | Ogni modulo/asset ha licenza e copyright verificati nel pacchetto; tessdata incluso correttamente |
| 3 | Valutazione umana della provenienza IA | FH-05, FH-20 | Maintainer documenta cosa è stato generato/assistito e applica la policy attuale; nessun contenuto IA nel manifesto di submission |
| 4 | Verificare il runtime Flathub effettivamente più recente | FH-02, FH-23 | Ramo runtime ospitato e latest confermato il giorno della preparazione; scelta registrata |
| 5 | Confermare la strategia di dependency manifest e build offline | FH-21, FH-12 | Tutte le dipendenze sono dichiarate e la build offline pulita riesce |

**Perché questo ordine:** trasparenza e licenze sono questioni sostanziali prima di distribuire; la policy IA e la scelta runtime influenzano il packaging; il modello di dipendenze deve essere chiarito prima di investire nella submission.

## P1 — prima di chiamare il pacchetto release candidate

| Azione | Rilievi | Criterio di completamento |
|---|---|---|
| Buildare su x86_64 e aarch64 e investigare percorsi x86_64 hardcoded | FH-04 | Entrambe le architetture buildano e i flussi principali sono testati |
| Rendere obbligatori i validator AppStream e desktop file | FH-06, FH-14, FH-18, FH-22 | CI fallisce in caso di validator assente o errore; metainfo finale valido e inglese completo |
| Testare il manifesto generato per la release | FH-03, FH-18 | Generazione controllata, lint del manifesto generato e build riuscita; nessuna modifica manuale al file generato |
| Verificare permessi statici e uso dei portal | FH-07, FH-17 | Ogni permesso è motivato; portal usati quando richiesti e adeguati; X11/Wayland provati |
| Ampliare test funzionali e regressione | FH-09, FH-12, FH-15 | Test OCR, screenshot, download/checksum, TTS, installazione e avvio documentati |
| Stabilizzare sorgente e screenshot di release | FH-08, FH-10 | Sorgente identificata in modo riproducibile; screenshot verificati contro la release |
| Preparare separatamente il repository di submission | FH-13, FH-19 | Manifesto alla root, metainfo integrato upstream, solo file richiesti e policy IA rispettata |

## P2 — hardening e manutenzione

- Documentare e ripetere i test di integrità dei modelli con casi negativi: checksum errato, file troncato, timeout e interruzione.
- Riesaminare i comandi di copia licenze che terminano con `|| true`; evitare che una licenza necessaria mancante venga mascherata.
- Stabilire un controllo per gli screenshot in ogni release, dato che gli URL attuali puntano a `main`.
- Mantenere aggiornato questo registro dopo ogni modifica a manifesti, dipendenze, runtime, permessi o flusso release.

## Sequenza pratica proposta

1. **Review documentale** dei rilievi e delle fonti ufficiali.
2. **Intervento privacy e licenze**, su branch correttivo separato quando autorizzato.
3. **Audit dependency manifest/offline build** e inventario completo dei moduli.
4. **Decisione runtime**, poi build GNOME target e test x86_64/aarch64.
5. **Gate CI e metadati**, inclusi manifest release generato e linter.
6. **Test funzionali e permessi** su host Flatpak.
7. **Preparazione manuale della submission** da parte del maintainer secondo la policy IA corrente.

Questo ordine è una proposta tecnica: non autorizza da solo modifiche al codice, installazioni, release o invio a Flathub.

## Regole operative permanenti

- Non creare mai una Pull Request senza richiesta esplicita dell'utente.
- Non modificare direttamente `testing`; creare un branch dedicato dalla baseline verificata.
- Non modificare manualmente `flatpak/io.github.d3msudo.anura.json`, che è generato dallo script release.
- Non creare o automatizzare la PR di submission Flathub né generare per essa messaggi di commit, descrizioni o commenti.
- Nessuna build/installazione o altra modifica del repository va considerata completata finché non è stata realmente eseguita e verificata.

## Fonti normative

- [Flathub requirements](https://docs.flathub.org/docs/for-app-authors/requirements) — policy IA, licenze, permessi, build senza rete, manifest e dependency manifest.
- [Flathub runtimes](https://docs.flathub.org/docs/for-app-authors/runtimes) — ciclo di supporto e runtime ospitati.
- [Flathub submission](https://docs.flathub.org/docs/for-app-authors/submission) — procedura di submission.
- [Flathub linter](https://docs.flathub.org/docs/for-app-authors/linter) — lint e criteri.
