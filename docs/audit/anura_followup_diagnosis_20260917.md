# Anura — Diagnosi di follow-up (dati VM del 16-17 settembre)

Analizzati tutti i log dello zip + le tue osservazioni manuali. Due bug ora hanno una causa **confermata al 100%** con prove dirette (codice + screenshot + file su disco che si incrociano), uno è stato **ristretto** con un dato nuovo importante, e ho verificato con certezza le due domande sui fix già fatti.

## TTS — confermato risolto
Non l'hai più segnalato ed è confermato dal log reale di `dopo-tts-reale.txt`: `generate` → `Setting state to PLAYING` in ~3 secondi, poi pausa/resume/stop tutti puliti. Il fix del ramo ha funzionato, niente da fare qui.

---

## #2 — Lingue che "spariscono" cambiando qualità: **causa trovata, con prove dirette**

Il tuo sospetto era giusto. Tre prove che si incastrano esattamente:

1. **Codice** (`cache_manager.py`): ogni qualità ha una sua sottocartella —
   ```python
   def _get_model_quality_dir(self, quality=None):
       ...
       if quality == "best": return base_dir / "tessdata_best"
       if quality == "standard": return base_dir / "tessdata"
       return base_dir  # "fast"
   ```
   `get_downloaded_codes()` scansiona **solo** la cartella della qualità **attualmente selezionata**, mai le altre.

2. **File reali nello zip** — lo confermano alla lettera:
   ```
   .../tessdata/lit.traineddata              ← cartella base (fast)
   .../tessdata/tessdata/fra.traineddata     ← sottocartella "standard"
   ```
   Entrambi coesistono tranquillamente sul disco. **Nessun file viene mai cancellato** — la tua osservazione "i dati persistono" era corretta.

3. **Il vero bug — cache non invalidata al cambio qualità**: il tuo screenshot mostra "Model Quality: Standard" con "Spagnolo" ancora nella lista, anche se Spagnolo è stato scaricato in "Best". Nel codice:
   ```python
   def _on_model_quality_changed(self, combo, _param):
       ...
       self.settings.set_string("tessdata-model", model)
       self.load_languages()   # ← NON invalida la cache di CacheManager
   ```
   `load_languages()` ricarica solo la lista base; il filtro che decide cosa mostrare come "installato" chiama `get_downloaded_codes()` **senza `force=True`** — se la cache non è stata invalidata (cosa che succede solo su download/rimozione, mai su cambio qualità), la lista resta quella della qualità precedente. Ecco perché "non cambia mai" mostrando lingue che in realtà appartengono a un'altra qualità.

**Root cause completo, in una frase**: cambiare il selettore di qualità in Preferenze scrive la nuova impostazione ma non invalida la cache di `CacheManager`, quindi la lista mostrata resta quella scansionata l'ultima volta (a un'altra qualità) — mentre a runtime l'OCR vero cercherebbe comunque nella cartella *corretta* per la qualità attuale, quindi selezionare "Spagnolo" con qualità Standard probabilmente fallirebbe silenziosamente perché il file è altrove.

**Fix (non applicato)**: `_on_model_quality_changed` deve chiamare `get_language_manager().invalidate_cache()` (o `get_downloaded_codes(force=True)`) prima di `load_languages()`. Bonus da considerare: la UI potrebbe anche mostrare esplicitamente "3 lingue in Standard, 1 in Best" invece di nascondere del tutto la distinzione — ma quello è un miglioramento, non il bug.

---

## #6 — Editor esterno: causa finalmente isolata con la traccia D-Bus grezza

La cattura con `dbus-monitor` ha dato la risposta decisiva. La chiamata vera e propria:
```
method call ... interface=org.freedesktop.portal.OpenURI; member=OpenFile
   string "x11:3200005"
   file descriptor  (inode: 183)
   array [ handle_token: "gtk..." ]
```
e la risposta, **1.8 millisecondi dopo**:
```
signal ... interface=org.freedesktop.portal.Request; member=Response
   uint32 2
   array [ ]
```
`2` nel protocollo XDG Portal significa "l'interazione è terminata in altro modo" (fallimento generico), e l'array dei risultati è **vuoto** — il portale stesso non fornisce nessun dettaglio in più. Anura e GTK non stanno nascondendo niente: è `xdg-desktop-portal-gtk` a rispondere così, quasi istantaneamente, senza spiegare perché. Questo esclude definitivamente: rete, demone non attivo, nessuna app di default (tutte e tre già escluse prima), e adesso anche qualunque cosa lato Anura — il fallimento è tutto dentro il backend del portale.

Nota anche cosa **manca** dalla traccia: nessuna chiamata a `org.freedesktop.portal.Documents` prima di `OpenFile` — quindi non è nemmeno il document portal a essere coinvolto qui (Anura passa un file descriptor diretto, non un percorso che richieda l'export via document portal).

**Perché**: `Gtk.FileLauncher` (l'API usata da Anura) non ha *nessun* modo di passare un suggerimento sul tipo di contenuto — ho controllato la documentazione ufficiale, la sua superficie API è solo `new/launch/launch_finish/get_file` più un paio di opzioni introdotte in versioni successive (nessuna riguarda il tipo di contenuto). Quindi il portale deve indovinare da solo il tipo del file avendo **solo un file descriptor, senza nome né estensione** — e ho trovato un bug report quasi identico (NixOS/nixpkgs#279434): `OpenFile` che fallisce sempre con lo stesso codice "2", specificamente per il metodo basato su file descriptor (non per `OpenURI` basato su stringa), risolto in quel caso a un problema di come xdg-desktop-portal risale dal file descriptor al percorso reale sull'host. È un difetto documentato di questa classe di portale, non qualcosa di specifico ad Anura.

**Test decisivo per isolare Anura dal sistema**, da lanciare su host (non serve Flatpak):
```bash
python3 -c "
import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib

def on_launched(launcher, result, loop):
    try:
        print('OK:', launcher.launch_finish(result))
    except GLib.Error as e:
        print(f'FALLITO: dominio={e.domain} codice={e.code} msg={e.message}')
    loop.quit()

def on_activate(app):
    with open('/tmp/test-launcher.txt', 'w') as f:
        f.write('prova')
    launcher = Gtk.FileLauncher.new(Gio.File.new_for_path('/tmp/test-launcher.txt'))
    loop = GLib.MainLoop()
    launcher.launch(None, None, on_launched, loop)
    GLib.timeout_add_seconds(10, loop.quit)
    loop.run()
    app.quit()

app = Gtk.Application(application_id='com.test.filelaunchertest')
app.connect('activate', on_activate)
app.run(None)
"
```
Se fallisce anche così, fuori da Flatpak, da un'app GTK4 minimale che non ha nulla a che fare con Anura — è confermato al 100% un bug/limite di questa installazione di `xdg-desktop-portal-gtk`, non di Anura. A quel punto le strade realistiche sono: aggiornare il pacchetto se esiste una versione più recente su MX, segnalarlo upstream, oppure — lato Anura — intercettare questo fallimento specifico e offrire un fallback pragmatico (mostrare il percorso del file esportato con un pulsante "copia percorso", invece di continuare a tentare un lancio che su questo sistema non funzionerà mai).

---

## #3 (nuovo) — Spinner assente per lo screenshot: causa trovata

Confrontando `get_screenshot()` con `process_file()`/il flusso "incolla immagine" in `window.py`:
- `process_file()` e `_on_paste_from_clipboard_texture()` chiamano esplicitamente `self.welcome_page.show_spinner()` prima di avviare l'OCR.
- `get_screenshot()` **non lo chiama mai** — non gli è mai servito, perché prima del fix #5/#8 la finestra restava nascosta per tutta la durata dell'OCR (lo spinner sarebbe stato invisibile comunque).

Con la finestra che ora riappare subito dopo lo scatto (il fix che abbiamo fatto), questo buco è diventato visibile: la finestra torna su ma senza spinner, mentre gli altri flussi ce l'hanno. **Fix (non applicato)**: aggiungere `self.welcome_page.show_spinner()` nello stesso punto in cui la finestra viene ripresentata dopo lo scatto (il percorso legato al segnale `capture-finished`) — lo spegnimento a fine OCR dovrebbe già funzionare da solo, dato che è lo stesso meccanismo usato dagli altri flussi.

---

## #4 (nuovo) — Icona "Match Case" rotta: causa trovata

`data/ui/extracted_page.blp`:
```
ToggleButton search_case_btn {
  icon-name: "format-text-capitalize-symbolic";
  ...
}
```
Ho controllato il tema Adwaita installato: **quell'icona non esiste, da nessuna parte** — non è una svista di battitura recuperabile, proprio non c'è un'icona con quel nome nel tema. Per questo GTK mostra il placeholder generico che vedi nello screenshot.
Non c'è nemmeno un nome standard universale per "match case" nel set Adwaita (l'ho verificato) — altri progetti GTK4 per questo bundlano una propria SVG invece di affidarsi al tema di sistema. **Opzioni (non applicate)**: (a) bundlare un'icona propria "Aa" nel repo (pattern comune, es. sotto `data/icons/`), o (b) sostituire con un'etichetta testuale "Aa" nel bottone invece di un'icona.

---

## #5 — Verifiche dirette sul codice (le tue due domande)

- **Copia semplice nella History**: **non implementata**. `history_page.py` non ha nessuna azione di copia — solo il commento di copyright contiene la parola "Copyright". Il ramo ha prodotto solo `docs/planning/history-v2-interactive-rows.md`, un documento di pianificazione, nessun codice.
- **Riduzione a icona nella barra (X → tray)**: **non implementata**. Zero riferimenti a tray/appindicator/StatusNotifier in tutto il repo. Coerente con la decisione presa insieme: quella feature è stata deliberatamente rimandata a un ramo separato, mai iniziato.

Nessuna delle due è "sparita" da un fix precedente: semplicemente non sono mai state scritte, come da piano.
