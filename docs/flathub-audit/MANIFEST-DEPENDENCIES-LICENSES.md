# Manifesti, dipendenze e licenze

**Baseline:** `testing@ceeb66c9b0c4b5b81357e7924de7601584a5883e`

## Manifesti e flusso release

Il repository mantiene due manifesti:

- `flatpak/io.github.d3msudo.anura.local.json`: fonte di verità per build locali e automazioni di dipendenza; usa la directory di lavoro come sorgente Anura.
- `flatpak/io.github.d3msudo.anura.json`: manifesto generato per la release; non deve essere modificato a mano.

Secondo `flatpak/README.md`, `build-aux/release.sh` copia i moduli dal manifesto locale, sostituisce la sorgente del modulo Anura con il repository Git e il tag della release e rimuove chiavi locali. Lo script esegue controlli di coerenza dei manifesti, tessdata e copertura delle dipendenze.

Il manifesto di release attuale specifica:

- App ID: `io.github.d3msudo.anura`
- Runtime e SDK: GNOME 50
- Sorgente Anura: repository Git e tag `v0.2.0`
- 23 moduli (conteggio statico riportato durante l'audit)
- nessuna restrizione esplicita con `only-arches` / `skip-arches`

Non modificare manualmente il manifesto generato. Correzioni al flusso release vanno progettate a partire dal manifesto locale e dallo script generatore.

## Build Python e dipendenze

`pyproject.toml` richiede Python `>=3.12` e dichiara queste dipendenze runtime:

- `gtts`
- `loguru`
- `pillow`
- `psutil`
- `pytesseract`
- `requests`
- `zxing-cpp`

Il file `uv.lock` è presente. I moduli Flatpak Python usano in diversi casi `pip3 install --no-deps --no-build-isolation --prefix=/app`, con artefatti locali e checksum. Questa scelta può favorire build offline e controllate, ma non è stata provata end-to-end in questo audit.

### Controlli necessari

1. Verificare che ogni dipendenza runtime e di build sia dichiarata nel manifesto e che nessun build step tenti di accedere alla rete.
2. Verificare che gli artefatti siano disponibili e i checksum corretti.
3. Verificare i backend di build richiesti dai pacchetti (per esempio `scikit-build-core`, `pybind11`, `packaging`, `pathspec` o altri moduli presenti nel manifesto).
4. Verificare che il manifesto finale generato sia valido e passi `flatpak-builder-lint manifest`.
5. Eseguire una build pulita offline per dimostrare che le sorgenti dichiarate siano sufficienti.
6. Chiarire se la submission richiede un dependency manifest Python separato per la modalità di packaging effettivamente scelta. Non assumere che `uv.lock` sostituisca automaticamente un manifest richiesto da Flathub.

## Modelli OCR / tessdata

Il manifesto include almeno i modelli inglese e italiano di `tessdata_fast`, tag `4.1.0`, con SHA-256 dichiarati:

| File | SHA-256 |
|---|---|
| `eng.traineddata` | `7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2` |
| `ita.traineddata` | `b8f89e1e785118dac4d51ae042c029a64edb5c3ee42ef73027a6d412748d8827` |

Il modulo tessdata scarica i dati da `tesseract-ocr/tessdata_fast`. Il progetto Tesseract dichiara licenza Apache-2.0 per i dati. Nel manifesto esaminato non è stato individuato un passaggio che installi esplicitamente il file di licenza del modulo tessdata sotto la directory licenze dell'app.

La configurazione dei modelli scaricabili è inoltre registrata in `anura/data/tessdata_checksums.json`, con repository, tag, conteggio file e identificatori Git blob. `build-aux/check_tessdata_consistency.py` confronta la configurazione con i manifesti Flatpak. `build-aux/generate_tessdata_checksums.py` usa GitHub API per raccogliere hash e dimensioni, e fallisce se la tree è troncata o non contiene i modelli attesi.

### Valutazione integrità

La revisione statica di `anura/services/language/download_manager.py` ha individuato:

- rifiuto del download se manca il checksum;
- limiti sulla dimensione annunciata e sulla quantità effettivamente trasferita;
- verifica della dimensione attesa quando il server la dichiara;
- verifica dell'hash Git blob prima di installare;
- installazione atomica con `os.replace()`;
- rimozione del file temporaneo nel percorso di cleanup.

È una progettazione difensiva. Resta da testare con download reali, errori di rete, file troncati, checksum errato, esaurimento spazio e build senza rete. Gli hash SHA-256 dei modelli inclusi nel pacchetto e gli identificatori Git blob dei modelli scaricati sono meccanismi distinti.

## Licenze dei moduli e installazione

Alcuni comandi nei moduli Python cercano i file di licenza nei metadata installati e copiano il primo file che corrisponde a `*icense*`. Questi comandi terminano con `|| true`, perciò la build può proseguire anche se non è stata trovata una licenza.

Questo comportamento non dimostra che le licenze manchino tutte; dimostra che il successo della build non è una verifica sufficiente della loro presenza.

### Inventario da completare

Per ogni modulo e asset incluso, registrare:

| Campo | Controllo richiesto |
|---|---|
| Nome e versione | Identità univoca del componente |
| URL sorgente e revisione | URL, tag/commit/versione e checksum |
| Licenza dichiarata | Licenza del componente, non dedotta soltanto dal nome |
| File licenza incluso | Percorso effettivo nel pacchetto finale |
| Copyright / NOTICE | Inclusione dove richiesta |
| Esito | Verificato, mancante o da chiarire |

Verificare in particolare librerie native, moduli Python, utility incluse (fra cui `scrot`), dati tessdata, icone, font e altre risorse distribuite. La posizione richiesta per le licenze va confrontata con la policy Flathub corrente, inclusa la directory `$FLATPAK_DEST/share/licenses/$FLATPAK_ID`.

## Sorgente applicativa, tag e riproducibilità

Il manifesto usa `v0.2.0` senza pinning esplicito a commit. I metadati GitHub esaminati riportavano il tag non firmato e non immutabile.

Questo non prova una violazione normativa, ma un tag mobile può ridurre la riproducibilità. Valutare il pinning al commit verificato nel manifesto di submission e documentare come viene aggiornato durante una release. Non modificare la procedura esistente senza verificare l'impatto su `build-aux/release.sh` e sui controlli di coerenza.

## Permessi statici da rivedere

I permessi attualmente osservati comprendono:

- `--share=network`
- `--share=ipc`
- `--socket=x11`, `--socket=wayland`, `--socket=pulseaudio`
- `--device=dri`
- accesso read-only a `xdg-pictures`, `xdg-download`, `xdg-desktop`, `xdg-documents`
- talk name per accessibility, portal desktop e notifiche
- `TESSDATA_PREFIX=/app/share/tessdata`

La rete è plausibilmente necessaria per TTS remoto e download dei modelli. Per ogni altro permesso serve collegare il requisito alla funzionalità che lo usa. Valutare accesso tramite portal per file e screenshot dove disponibile; testare il fallback X11 senza concedere accessi più ampi del necessario.

## Fonti

- [Flathub requirements](https://docs.flathub.org/docs/for-app-authors/requirements)
- [Flathub linter](https://docs.flathub.org/docs/for-app-authors/linter)
- [gTTS API](https://gtts.readthedocs.io/en/stable/module.html)
- [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast)
- [Tesseract tessdata README](https://github.com/tesseract-ocr/tessdata)
