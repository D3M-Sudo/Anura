# Piano di chiusura dell'audit Flathub

**Baseline:** `testing@ceeb66c9b0c4b5b81357e7924de7601584a5883e`  
**Scopo:** piano proposto; non indica attività già completate.

## Principi di esecuzione

- Non modificare direttamente `testing`.
- Ogni correzione applicativa va sviluppata su un branch dedicato creato da una baseline aggiornata e verificata.
- Non modificare manualmente `flatpak/io.github.d3msudo.anura.json`: il manifesto è generato da `build-aux/release.sh`.
- Non eseguire build o installazioni senza verificare prima che l'ambiente abbia gli strumenti necessari e che l'operazione sia autorizzata.
- Non aprire né automatizzare la PR di submission Flathub con un agente IA; non affidare a un agente IA testo di commit, descrizione PR o commenti della submission.
- Verificare nuovamente policy e runtime ufficiali subito prima dell'invio.

## Fase A — Trasparenza e licenze

### A1. Privacy TTS
- Correggere la dichiarazione assoluta che nessun testo viene trasmesso esternamente.
- Dichiarare che OCR e trattamento locale sono locali, mentre il testo fornito al TTS viene inviato a un servizio remoto quando la funzione è usata.
- Controllare metainfo, README, About/legal dialog e documentazione.
- Test di accettazione: descrizione coerente con il comportamento e comprensibile prima dell'uso di TTS.

### A2. Inventario licenze
- Inventariare tutti i moduli, gli asset e i modelli distribuiti.
- Controllare le licenze effettive nel pacchetto installato, non solo i metadati sorgente.
- Includere esplicitamente la licenza Apache-2.0 dei modelli tessdata, se applicabile alla versione inclusa.
- Rivedere i comandi di copia licenza che ignorano gli errori con `|| true`.
- Test di accettazione: inventario con versione, origine, licenza, file incluso e percorso per ogni componente.

### A3. Provenienza IA
- Il maintainer ricostruisce la provenienza del codice, della documentazione e del packaging che fanno parte del prodotto.
- Applicare la policy Flathub aggiornata e preparare la dichiarazione richiesta.
- Non inserire materiale assistito dall'IA nel manifesto di submission.
- Tenere questi appunti di audit separati dal repository dedicato alla submission e dichiararne la provenienza come già fatto in questo documento.

## Fase B — Manifesti, runtime e architetture

### B1. Runtime
- Verificare il runtime più recente ospitato da Flathub il giorno dell'invio.
- Allineare manifesti, CI e documentazione al runtime scelto.
- Test di accettazione: build pulita e avvio verificato con il runtime selezionato.

### B2. Architetture
- Buildare e provare almeno `x86_64` e `aarch64`.
- Investigare i percorsi `x86_64-linux-gnu` in `GI_TYPELIB_PATH` e `LD_LIBRARY_PATH`.
- Test di accettazione: nessun percorso hardcoded che impedisca l'esecuzione sull'architettura supportata; risultati salvati per entrambe.

### B3. Riproducibilità e sorgenti
- Valutare il pinning del codice applicativo a un commit verificato.
- Verificare tag, sorgenti e checksum di tutti i moduli.
- Test di accettazione: ogni sorgente remota è dichiarata e verificabile, senza download non dichiarati durante la build.

## Fase C — CI e qualità del pacchetto

### C1. Validatori obbligatori
- Rendere i controlli AppStream e desktop file gate espliciti della CI/release, senza dipendere dalla presenza casuale degli strumenti in Meson.
- Validare il metainfo finale compilato, non solo il template.
- Test di accettazione: la pipeline fallisce se i validatori mancano o segnalano errori.

### C2. Manifesto release
- Eseguire il generatore release in un ambiente controllato e validare il manifesto generato.
- Applicare `flatpak-builder-lint manifest` e gli altri controlli applicabili secondo la guida corrente.
- Verificare che il repository dedicato di submission abbia il manifesto all'interno della propria root.
- Test di accettazione: manifesto generato, lint pulito e build riuscita.

### C3. Build offline e dependency manifest
- Confermare il formato di dependency manifest richiesto per la strategia di build Python usata.
- Provare una build pulita senza accesso di rete nella fase build.
- Test di accettazione: tutte le dipendenze sono dichiarate, pinning/checksum presenti e build ripetibile.

### C4. Test funzionali
- OCR da immagine e acquisizione schermo.
- Screenshot portal su Wayland e fallback supportato su X11.
- Download modello, checksum errato, file troncato, timeout e interruzione.
- TTS, gestione errori e pulizia file audio.
- Avvio, desktop integration, notifiche, accessibilità e cronologia.
- Test su entrambi i target architetturali.
- Test di accettazione: risultati riproducibili e nessun flusso critico affidato al solo smoke test `--help`.

## Fase D — Sandbox e metadati

### D1. Permessi
- Documentare ogni `finish-args` in relazione a una funzionalità.
- Valutare portal per screenshot e accesso file, riducendo i permessi statici non indispensabili.
- Non rimuovere X11/Wayland/audio/DRI senza test di regressione.
- Test di accettazione: ogni permesso è motivato e i flussi di utilizzo restano funzionanti.

### D2. AppStream, desktop, screenshot e inglese
- Validare App ID, summary, descrizione, licenze, developer, release, launchable, content rating e screenshot.
- Verificare che le immagini corrispondano alla versione distribuita; evitare che cambi non revisionati su `main` modifichino gli screenshot pubblicati.
- Verificare completezza dell'inglese UI e compilazione gettext.
- Test di accettazione: validatori puliti e contenuti coerenti con la versione rilasciata.

## Gate finali prima della submission

Non considerare Anura pronta per la submission finché tutti i gate applicabili non sono documentati:

- [ ] Privacy/TTS descritti correttamente.
- [ ] Licenze e copyright verificati nel pacchetto finale.
- [ ] Provenienza IA valutata e dichiarazione predisposta dal maintainer.
- [ ] Runtime più recente confermato e buildato.
- [ ] Build e test su `x86_64` e `aarch64`.
- [ ] Manifesto e dependency manifest validi per la submission.
- [ ] Linter Flathub pulito.
- [ ] Build offline ripetibile.
- [ ] AppStream e desktop file validati obbligatoriamente.
- [ ] Permessi sandbox giustificati.
- [ ] Test OCR, download, screenshot e TTS eseguiti.
- [ ] Repository dedicato di submission preparato manualmente nel rispetto della policy IA.

## Fonti ufficiali

- [Flathub requirements](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub linter](https://docs.flathub.org/docs/for-app-authors/linter)
- [flatpak-builder-lint](https://github.com/flathub-infra/flatpak-builder-lint)
- [GNOME 51 release announcement](https://discourse.gnome.org/t/gnome-51-released/38820)
