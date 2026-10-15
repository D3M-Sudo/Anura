# Rapporto di Analisi Comparativa REA per Anura (TASK REA-ANALYSIS)

**Stato Finale:** `COMPLETED`
**Data ed Ora:** 15 Ottobre 2026 - 11:05 UTC
**Agente Esecutore:** Jules
**Branch Anura Analizzato:** `feat/history-v2-expandable-rows`
**Applicazioni Target Analizzate:**
- **gImageReader** (v3.4.x - C++/GTKmm & Qt)
- **OCRFeeder** (v0.8.x - Python/PyGObject/GTK3/GooCanvas)

---

## 1. Obiettivo dell'Analisi

L'obiettivo di questo studio comparativo svolto con il supporto metodologico e gli strumenti di **REA (Reverse Engineer Anything)** è analizzare l'architettura ed i pattern di progettazione di due note applicazioni open-source di OCR su Linux (**gImageReader** e **OCRFeeder**), al fine di individuare soluzioni tecniche e pattern riutilizzabili per l'evoluzione dell'applicazione **Anura** (con focus specifico sul branch `feat/history-v2-expandable-rows`).

---

## 2. Sintesi delle Architetture Target

### 2.1 gImageReader (`~/analisi-rea-anura/targets/gimagereader`)
* **Stack Tecnologico:** C++17, GTKmm 3/4, GtkSourceView, Tesseract C++ API.
* **Componenti Chiave:**
  - `SourceManager` / `FileTreeModel`: Gestione gerarchica dei file immagine e PDF multipagina tramite `Gtk::TreeModel`.
  - `OutputEditorText` / `OutputBuffer`: Editor di output basato su `GtkSourceView` con gestione avanzata del testo estratto, supporto all'inserimento batch (Append, Cursor, Replace) ed al tracciamento delle modifiche (Undo/Redo).
  - `hocr/*`: Gestione strutturata di blocchi di testo e layout HOCR con esportazione diretta in PDF/ODT.

### 2.2 OCRFeeder (`~/analisi-rea-anura/targets/ocrfeeder`)
* **Stack Tecnologico:** Python 3, PyGObject (GTK3), GooCanvas, Engine OCR plurali (Tesseract, CADDET).
* **Componenti Chiave:**
  - `PagesIconView`: Visualizzazione ad icone (`Gtk.IconView`) basata su `Gtk.ListStore` per la gestione ed anteprima rapida delle pagine/scansioni acquisite.
  - `BoxesArea` (`GooCanvas.Canvas`): Interfaccia grafica interattiva per la selezione, il ridimensionamento ed il riconoscimento selettivo delle regioni d'interesse (OCR boxes).
  - `layoutAnalysis`: Algoritmo di segmentazione del layout per l'identificazione automatica di colonne, blocchi di testo ed immagini.

---

## 3. Confronto con Anura (`feat/history-v2-expandable-rows`)

| Caratteristica | Anura (`feat/history-v2-expandable-rows`) | gImageReader | OCRFeeder |
| :--- | :--- | :--- | :--- |
| **Architettura UI** | GTK4 / Libadwaita (`Adw.ActionRow`, `Adw.PreferencesPage`) | GTKmm / Qt (`Gtk::TreeView`, `GtkSourceView`) | GTK3 / GooCanvas (`Gtk.IconView`, Canvas) |
| **Gestione Storico/Pagine** | `HistoryPage` con righe espandibili interattive (`Adw.ActionRow`) e ricerca live | `FileTreeModel` (albero file/pagine a pannello laterale) | `PagesIconView` (griglia icone/miniature in sidebar) |
| **Espansione & Anteprima** | Reveler / Textview espandibile direttamente nella riga dello storico con limiti di altezza e scroll interno | Finestra/Buffer di output separato affiancato (`OutputEditorText`) | Riquadro di testo espandibile e pannello proprieta per singola box |
| **Feedback e Accessibilità** | WCAG 2.4 AA, sync dynamic tooltips e `Gtk.AccessibleProperty.LABEL` | Tooltip classici GTK | Nessuna ottimizzazione specifica WCAG/AccessibleProperty |

---

## 4. Pattern Architetturali Riusabili per Anura

1. **Gestione del Testo Espanso e Batch Processing (Ispirato da gImageReader `OutputEditorText`):**
   - *Pattern:* In `OutputEditorText`, la gestione delle modifiche al testo estratto avviene separando la logica di buffer (`OutputBuffer`) dalla rappresentazione visiva.
   - *Applicazione per Anura:* Nella riga espansa della cronologia (`HistoryPage`), mantenere un'area di testo scrollabile con stime trasparenti di altezza minima/massima (`_EXPANDED_TEXT_MAX_HEIGHT`) e integrare azioni veloci di copia/ricerca senza riorganizzare il layout dell'interfaccia.

2. **Anteprima Visiva ed Asincronismo (Ispirato da OCRFeeder `PagesIconView` & `asyncworker`):**
   - *Pattern:* OCRFeeder carica le miniature ed elabora il layout in thread asincroni per evitare di bloccare il main loop GTK.
   - *Applicazione per Anura:* Mantenere asincrona l'espansione e la lettura dettagliata degli elementi dello storico tramite `GLib.idle_add` e callback non bloccanti.

3. **Accessibilità Dinamica e HIG GNOME Moderno (Integrazione Custom Anura):**
   - *Differenziazione:* Rispetto a gImageReader e OCRFeeder (che utilizzano widget GTK3/GTKmm tradizionali), Anura sfrutta Libadwaita 1.5+. L'integrazione di `Adw.ActionRow` con pulsanti d'azione piatti e feedback dinamico sul clipboard rappresenta una soluzione tecnologicamente più moderna e pienamente conforme alle linee guida GNOME HIG.

---

## 5. Conclusioni

L'analisi svolta evidenzia che l'approccio adottato in **Anura** per il branch `feat/history-v2-expandable-rows` (righe di cronologia espandibili ed interattive basate su Libadwaita) garantisce un'esperienza utente notevolmente più fluida e nativa rispetto alle soluzioni basate su `TreeView` tradizionali (gImageReader) o `IconView` (OCRFeeder). I pattern di estrazione del testo ed asincronismo identificati nelle target apps confermano la solidità del design correntemente implementato in Anura.
