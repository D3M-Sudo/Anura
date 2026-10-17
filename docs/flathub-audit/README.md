# Anura — audit di preparazione a Flathub

**Stato:** audit documentale in corso, non approvazione alla submission  
**Baseline esaminata:** branch `testing`, commit `ceeb66c9b0c4b5b81357e7924de7601584a5883e`  
**Versione applicativa esaminata:** `0.2.0`  
**Ultimo aggiornamento:** 2026-10-17

## Scopo e limiti

Questa cartella raccoglie le evidenze, i rilievi e il piano di verifica emersi durante l'audit pre-Flathub di Anura. È documentazione di lavoro per i maintainer: non è il repository di submission Flathub e non sostituisce una build, un test pratico o la validazione ufficiale.

L'analisi fin qui è principalmente statica. Non sono stati installati strumenti, compilati manifesti Flatpak o eseguiti test su host reali durante questa fase. I rilievi distinguono fatti verificati, rischi da provare e aspetti che richiedono conferma.

## Indice

- [Rapporto dei rilievi](./FINDINGS.md) — registro dei findings, evidenze e priorità.
- [Manifesti, dipendenze e licenze](./MANIFEST-DEPENDENCIES-LICENSES.md) — struttura dei manifesti, sorgenti, dipendenze, licenze e riproducibilità.
- [Piano di chiusura](./REMEDIATION-PLAN.md) — ordine operativo e gate da superare prima della submission.
- [Priorità operative](./PRIORITIES.md) — ordine raccomandato, criteri di completamento e decisioni che richiedono il maintainer.

## Baseline e metodo

La baseline è stata identificata come `testing@ceeb66c9b0c4b5b81357e7924de7601584a5883e`. Le conclusioni non vanno automaticamente attribuite a commit successivi: ripetere i controlli dopo cambiamenti rilevanti.

Le fonti pubbliche normative principali consultate sono:

- Flathub — [Requirements](https://docs.flathub.org/docs/for-app-authors/requirements)
- Flathub — [Runtimes](https://docs.flathub.org/docs/for-app-authors/runtimes)
- Flathub — [Submission](https://docs.flathub.org/docs/for-app-authors/submission)
- Flathub — [Linter](https://docs.flathub.org/docs/for-app-authors/linter)
- Flathub infrastructure — [flatpak-builder-lint](https://github.com/flathub-infra/flatpak-builder-lint)
- GNOME — [GNOME 51 released](https://discourse.gnome.org/t/gnome-51-released/38820)
- Tesseract — [tessdata_fast](https://github.com/tesseract-ocr/tessdata_fast) e [tessdata README](https://github.com/tesseract-ocr/tessdata)
- gTTS — [API documentation](https://gtts.readthedocs.io/en/stable/module.html)

Le policy e i runtime cambiano: ricontrollare le fonti ufficiali immediatamente prima della submission. La documentazione generale sui runtime conferma che deve essere usata una versione ospitata da Flathub e che la versione più recente al momento dell'invio è un requisito; non abbiamo concluso dalla sola pagina runtime che GNOME 51 sia sicuramente il ramo più recente ospitato. Questo va verificato direttamente prima di scegliere il target.

## Provenienza di questi documenti

Questi appunti di audit sono stati redatti con assistenza IA sulla base di ispezioni del repository e fonti pubbliche. Non costituiscono codice dell'applicazione né un manifesto di submission. Il maintainer deve valutare se e quali parti di questa documentazione rientrino nel materiale dell'applicazione o del packaging da dichiarare secondo la policy Flathub corrente. La cartella di audit non va copiata automaticamente nel repository di submission. Il manifesto destinato alla submission deve essere preparato nel rispetto delle regole Flathub e non deve contenere materiale generato o assistito dall'IA.

## Convenzioni

- **Confermato:** supportato da file o metadati effettivamente ispezionati.
- **Rischio da verificare:** indicazione plausibile che richiede build, test o ulteriore evidenza.
- **Non verificato:** nessuna conclusione positiva o negativa può essere tratta.
- **Bloccante:** non procedere alla submission finché il punto non è risolto o esplicitamente valutato dal maintainer.
