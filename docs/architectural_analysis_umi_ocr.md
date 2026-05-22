# Analisi Comparativa e Proposta Architetturale: Anura vs Umi-OCR

Questo documento presenta un'analisi comparativa tra il codebase di Anura e quello di Umi-OCR, focalizzandosi su punti di miglioramento strutturale, ottimizzazione della memoria e gestione asincrona delle risorse.

---

### 1. Tabella Comparativa Sintetica

| Caratteristica | Anura (Stato Attuale) | Umi-OCR (Benchmark) | Differenza Chiave |
| :--- | :--- | :--- | :--- |
| **Gestione Asincrona** | Threading atomico via `AtomicTaskManager`. Slot singolo con versioning. | Architettura a **Code (Queue)** basata su `multiprocessing` e `asyncio`. | Umi-OCR gestisce code batch massive; Anura privilegia l'integrità del task singolo e la fluidità della GUI tramite task versioning. |
| **Pre-processing** | Pipeline basata su **Pillow (PIL)**: LUT ottimizzate, filtri mediani e thresholding adattivo manuale. | Pipeline basata su **OpenCV**: algoritmi di binarizzazione (Sauvola/Niblack), deskewing e denoising avanzato. | Umi-OCR garantisce una maggiore accuratezza su testi distorti o con scarso contrasto grazie alla potenza computazionale di OpenCV. |
| **Post-processing** | Pattern **"Magics"**: Chain of Responsibility che seleziona il trasformatore in base a punteggi probabilistici (Tesseract layout). | **Paragraph Reconstruction**: Algoritmi geometrici complessi per fondere linee basandosi sulla prossimità spaziale e semantica. | Anura è più agile nel riconoscere tipologie di dati (URL/Email), ma Umi-OCR è superiore nella ricostruzione strutturale di documenti multi-colonna. |

---

### 2. Proposta di Cambiamento Strutturale (Architettura Logica)

#### A. Atomic Task Manager (Gestore Task Atomico)
Modulo `AtomicTaskManager` basato su un design pattern **Atomic Executor with Versioning**:
- **Logica**: Utilizzo di un `ThreadPoolExecutor` con un singolo worker (`max_workers=1`) e un sistema di `TaskID` incrementali per invalidare i task obsoleti.
- **Vantaggio**: Previene la "thread explosion" e risolve le race conditions sulla UI. Ogni nuova richiesta cancella la precedente, assicurando che solo l'ultimo risultato aggiorni la GUI.
- **Impatto GUI**: Massima reattività del desktop Cinnamon/GNOME. La GUI delega l'elaborazione pesante e valida i risultati in arrivo tramite il versioning, garantendo coerenza visiva.

#### B. Pipeline di Pre-processing "Filter Chain"
Evoluzione del modulo `TextPreprocessor` verso una struttura modulare a filtri:
- **Logica**: Implementare una catena di filtri (`Filter Chain`) dove ogni passaggio (Denoise, Deskew, Thresholding) è un modulo indipendente e configurabile.
- **Ottimizzazione**: Introduzione della **"ROI Detection" (Region of Interest)**. Utilizzando analisi geometriche preliminari, il pre-processing viene applicato solo alle aree che contengono effettivamente del testo, riducendo drasticamente il consumo di CPU e memoria.

#### C. Post-processing: Structural Reconstructor
Evolvere il sistema "Magics" integrando una logica di ricostruzione geometrica:
- **Logica**: Sfruttare i metadati di layout forniti da `pytesseract.image_to_data` (coordinate bounding box) per calcolare la distanza euclidea tra i blocchi di testo.
- **Perché**: La decisione di unire due righe in un paragrafo deve basarsi sulla loro prossimità spaziale nell'immagine originale, non solo sull'ordine sequenziale del testo estratto. Questo approccio risolve in modo definitivo il problema delle "linee spezzate".

---

### 3. Impatto sui Vincoli di Sistema

#### A. Analisi Dipendenze (OpenCV vs NumPy)
Per mantenere la leggerezza del pacchetto Flatpak e la compatibilità con sandbox Linux:
- **Scelta consigliata**: Potenziare l'uso di **NumPy** per le operazioni di calcolo matriciale (binarizzazione, contrasto) evitando l'inclusione della libreria OpenCV completa (che aumenterebbe il peso del pacchetto di ~50MB).
- **Alternativa**: Inclusione di `opencv-python-headless` solo se i filtri di denoising avanzati diventano critici per la precisione.

#### B. Ottimizzazione Memoria
- L'approccio a pool controllato dell'orchestratore garantisce che l'occupazione di memoria (I/O) rimanga entro limiti prevedibili, impedendo picchi di RAM durante l'elaborazione di immagini ad alta risoluzione o file multipli.

#### C. Compatibilità Sandbox
L'architettura proposta non richiede nuovi permessi `xdg-desktop-portal` o accessi hardware diretti, garantendo la continuità del supporto per distribuzioni moderne come Linux Mint 22/23.
