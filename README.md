# Sito Web Medical Physics and Complex Systems (INFN Bari & UniBa)

Sito istituzionale **statico** del gruppo Medical Physics and Complex Systems (Università degli Studi di Bari Aldo Moro · INFN Bari).
Nessun framework, nessuna dipendenza, nessun passo di build obbligatorio: solo HTML, CSS e JavaScript vanilla.

---

## 1. Architettura

Il sito è una **single-page application** con routing basato su `location.hash`.
`index.html` contiene un `<div id="app">` vuoto: tutto il contenuto viene generato a runtime da `assets/js/app.js`, che legge i dati da variabili globali e si ridisegna a ogni cambio di rotta.

```text
index.html
   │  carica 4 script in quest'ordine
   ├─► assets/data/site-data.js   →  window.MEDPHYS_SITE   (struttura e contenuti brevi, bilingui)
   ├─► assets/data/pages_en.js    →  window.MEDPHYS_EN     (HTML delle pagine lunghe, inglese)
   │                                window.MEDPHYS_META   (titoli e link delle pagine)
   ├─► assets/data/i18n.js        →  window.MEDPHYS_IT     (traduzioni italiane, override)
   │                                window.MEDPHYS_EN_X   (override inglese)
   └─► assets/js/app.js           →  legge le globali, renderizza in #app, gestisce #/rotta
```

La lingua scelta viene salvata in `localStorage` (`medphys_lang`) e riproiettata su ogni pagina.

### Rotte disponibili

| Rotta | Pagina | Contenuto |
|---|---|---|
| `#/home` | Home | hero, sezioni, notizie in evidenza |
| `#/research` | Ricerca | indice delle linee di ricerca |
| `#/<slug>` | Linea di ricerca | es. `#/brain`, `#/breast`, `#/lung` |
| `#/people` | Persone | griglia dello staff |
| `#/<slug-persona>` | Persona | es. `#/roberto-bellotti` |
| `#/projects` | Progetti | ongoing + past |
| `#/ongoing-projects`, `#/past-projects` | Progetti | stesse griglie, filtrate |
| `#/<slug-progetto>` | Progetto | dettaglio progetto |
| `#/challenges` | Sfide | competizioni |
| `#/<slug-sfida>` | Sfida | dettaglio + link esterno |
| `#/publications` | Pubblicazioni | categorie |
| `#/<slug-categoria>` | Categoria | es. `#/journal-papers`, `#/book-chapters` |
| `#/multimedia`, `#/join-us`, `#/courses` | Varie | pagine lunghe |
| `#/short-course`, `#/conference-slides`, `#/pattern_recognition` | Risorse | protette da password |

Il router è in `assets/js/app.js:311`. Le rotte non riconosciute mostrano una pagina 404.

---

## 2. Struttura dei file

```text
MedPhys_Sito/
├── index.html                    # unico file HTML: carica CSS + 4 script
│
├── assets/
│   ├── css/
│   │   └── style.css             # tutto il design (variabili CSS, layout, responsive)
│   ├── data/                     # ← I DATI DEL SITO (vedi sezione 4)
│   │   ├── site-data.js          # window.MEDPHYS_SITE   — nav, home, people, projects,
│   │   │                         #   research, challenges, pubblicazioni, corsi, notizie
│   │   ├── pages_en.js           # window.MEDPHYS_EN     — corpo HTML delle pagine lunghe
│   │   ├── pages_en.json         # copia JSON leggibile usata come sorgente da tools/gen_en.py
│   │   ├── i18n.js               # window.MEDPHYS_IT / MEDPHYS_EN_X — override di traduzione
│   │   └── meta.json             # titoli/link delle pagine (sorgente di tools/gen_en.py)
│   ├── img/                      # logo, foto, loghi giornali, grafici (~250 file)
│   └── js/
│       └── app.js                # renderer + router + header/footer condivisi
│
├── tools/                        # script Python di migrazione (non servono a far funzionare il sito)
│   ├── build_site_data.py        # genera site-data.js
│   ├── build_i18n.py             # genera i18n.js
│   ├── gen_en.py                 # genera pages_en.js da pages_en.json + meta.json
│   ├── clean_content.py          # pulizia HTML importato dal vecchio sito
│   ├── group_content.py          # raggruppamento pagine per slug
│   └── download_images.py        # download delle immagini del vecchio sito
│
├── nuovo_sito.md                 # specifiche e analisi del progetto
└── README.md                     # questa guida
```

---

## 3. Come visualizzare il sito in locale

Non serve installare Node.js, PHP, un database o un server.

1. **Doppio clic su `index.html`**: funziona, perché gli script sono caricati come file normali (nessun modulo ES, nessuna `fetch`).
2. Oppure, se preferisci un server locale per evitare sorprese col browser:
   ```bash
   python -m http.server 8000
   ```
   poi apri `http://localhost:8000`.

> **Attenzione alla cache.** Dopo ogni modifica a `assets/data/*.js` fai un **hard refresh** (`Ctrl+F5` / `Cmd+Shift+R`): altrimenti il browser continua a servire la vecchia versione degli script e sembra che la modifica non sia stata applicata.

---

## 4. Mini guida: aggiungere e aggiornare i contenuti

### 4.0 Prima di tutto — due regole da conoscere

**Regola 1: quasi tutto il contenuto sta in `site-data.js`, non in HTML.**
Non cercare pagine `people.html` o `publications.html`: non esistono. Le schede, le griglie e i menu sono generati da array JSON.

**Regola 2: i file in `assets/data/` sono JSON scritti tutto su una riga.**
Per leggerli e modificarli senza dolori, apri il file in VS Code e usa **Shift+Alt+F** (*Format Document*): il JSON diventa indentato e leggibile. **Ricontrolla la sintassi prima di salvare** — una virgola o una graffa di troppo rompe l'intero sito (che resta bianco, senza errori evidenti).

> I file `.js` in `assets/data/` sono stati generati una volta dagli script in `tools/`. Per l'aggiornamento ordinario si modifica **direttamente il `.js`**: gli script Python servono solo per re-importare il vecchio sito e hanno percorsi assoluti scritti dentro, quindi funzionano solo sulla macchina originale.

---

### 4.1 Aggiungere una persona (staff)

In `assets/data/site-data.js`, dentro l'array `"people"`:

```json
{
  "slug": "mario-rossi",
  "img": "assets/img/mario_rossi.jpg",
  "keywords": {
    "en": "Medical Imaging, Deep Learning",
    "it": "Imaging Medico, Deep Learning"
  },
  "bio": {
    "en": "Mario Rossi is a PhD student…",
    "it": "Mario Rossi è dottorando…"
  },
  "email": "mario.rossi@uniba.it"
}
```

Regole:
- `slug` **obbligatorio e obbligatoriamente `nome-cognome` in minuscolo con trattini**: il nome mostrato viene ricavato dal slug (`nameOf()` in `app.js:150`). `mario-rossi` → "Mario Rossi".
- `img`, `keywords`, `bio` obbligatori; `email` opzionale.
- Metti la foto in `assets/img/` **prima** di inserire il riferimento.
- Collocare la persona in `people` (mostrata nella pagina) o in `collaborators` (non mostrata in `#/people`).

Non serve creare una pagina: la scheda personale è generata automaticamente da `renderPerson()`.

### 4.2 Aggiungere una pubblicazione

Le pubblicazioni sono organizzate in due livelli.

**a) Se è una categoria nuova** (es. "Conference papers"), nell'array `"publications"`:

```json
{
  "slug": "conference-papers",
  "en": "Conference papers",
  "it": "Articoli a convegno",
  "desc": {
    "en": "Peer-reviewed conference contributions.",
    "it": "Contributi a convegno con revisione paritaria."
  }
}
```

**b) Se la categoria esiste già**, il singolo articolo va nel corpo HTML della pagina, in `assets/data/pages_en.js`, dentro `window.MEDPHYS_EN["journal-papers"]`:

```html
<li class="pub-item">
  <span class="pub-authors">Rossi M., Bellotti R.</span>
  <span class="pub-title">"Titolo dell'articolo."</span>
  <span class="pub-journal">Nome Rivista, 12(3), 45-67, 2026.</span>
  <div>
    <a href="https://doi.org/10.xxxx/xxxx" target="_blank" rel="noopener" class="pub-doi-badge">DOI: 10.xxxx/xxxx</a>
  </div>
</li>
```

`window.MEDPHYS_META` nello stesso file serve al titolo della pagina: se crei una pagina nuova, aggiungi anche lì la voce con `title`, `link` e `fn`.

### 4.3 Aggiungere una notizia in home

Nell'array `"newsroom"`:

```json
{ "name": "Testata giornalistica", "img": "assets/img/logo_testata.png", "url": "https://…" }
```

Le prime voci dell'array sono quelle in evidenza in home.

### 4.4 Aggiungere una linea di ricerca

Nell'array `"research"`:

```json
{
  "slug": "nuova-linea",
  "img": "assets/img/immagine.jpg",
  "title": { "en": "New line", "it": "Nuova linea" },
  "summary": { "en": "Short description…", "it": "Descrizione breve…" },
  "body": { "en": "<p>Testo lungo in HTML…</p>", "it": "<p>Testo lungo…</p>" }
}
```

- `slug`, `img`, `title`, `summary` obbligatori.
- `body` è opzionale: **se lo ometti**, la pagina prende il contenuto da `pages_en.js` usando lo stesso slug.
- Appare automaticamente in `#/research` e nel menu laterale delle pagine di dettaglio.

### 4.5 Aggiungere un progetto

In `site-data.js`, dentro `"projects"` → `"ongoing"` oppure `"past"`:

```json
{
  "slug": "progetto-acronimo",
  "img": "assets/img/logo_progetto.png",
  "title": { "en": "ACRONYM", "it": "ACRONYM" },
  "duration": "Jan 2026 – Dec 2029",
  "period": "",
  "abstract": { "en": "Descrizione…", "it": "Descrizione…" }
}
```

### 4.6 Modificare contatti, intestazione e footer

Tutto in `site-data.js`, chiavi iniziali:

| Cosa | Chiave |
|---|---|
| Nome del gruppo | `brand`, `short`, `org` |
| Logo | `logo` |
| Indirizzo | `address` |
| Email | `emails` (array) |
| Voci del menu | `nav` |
| Titoli delle sezioni | `sections` |
| Testi della home | `home` |
| Avviso sulle pubblicazioni | `pub_notice` |

Le voci del menu sono `{ "route": "…", "en": "…", "it": "…" }`; per un menu a tendina aggiungi `children: [{ "route": "…", "en": "…", "it": "…" }]`.

Il footer invece è nel codice: `footer()` in `assets/js/app.js:61`. Testi, crediti e link si modificano lì (i crediti e la lingua corrente sono alla riga 81-87).

### 4.7 Traduzioni EN/IT

Tre meccanismi, da scegliere in base al tipo di contenuto:

1. **Testi brevi** (titoli, etichette, riassunti): scrivi l'oggetto con `en` e `it` nello stesso campo di `site-data.js`.
2. **Pagine lunghe in italiano**: `assets/data/i18n.js`, dentro `window.MEDPHYS_IT`, con lo **slug della pagina** come chiave. Ha la priorità su tutto quando la lingua è IT.
3. **Override della versione inglese**: `window.MEDPHYS_EN_X` nello stesso file.

```js
window.MEDPHYS_IT = {
  "synchronization-demo": "<p>Testo in italiano…</p>"
};
```

Ogni oggetto `{ "en": …, "it": … }` viene risolto da `t()` (`app.js:12`): **se manca `it`, viene mostrato `en`**.

---

## 5. Aggiungere una pagina nuova

1. Scrivi il corpo HTML in `assets/data/pages_en.js`:
   ```js
   window.MEDPHYS_EN = {
     "nuova-pagina": "<p>Contenuto…</p>"
   };
   ```
2. Aggiungi il titolo in `window.MEDPHYS_META` (stesso file):
   ```js
   "nuova-pagina": { "title": "Nuova pagina", "link": "…", "fn": "…" }
   ```
3. Aggiungi la voce di menu in `nav` (`site-data.js`).
4. Se la pagina ha bisogno di una struttura dedicata (tabelle, griglie custom), aggiungi il caso nel router di `app.js:311`.

Il resto è automatico: se nessun caso del router corrisponde, `renderBase()` (`app.js:289`) mostra la pagina con il contenuto da `pages_en.js` / `i18n.js`.

---

## 6. Strumenti in `tools/`

Script Python usati per la migrazione dal vecchio sito WordPress. **Non servono per far funzionare il sito** e non vanno eseguiti per l'aggiornamento dei contenuti.

| Script | Funzione |
|---|---|
| `build_site_data.py` | genera `site-data.js` |
| `build_i18n.py` | genera `i18n.js` |
| `gen_en.py` | genera `pages_en.js` da `pages_en.json` + `meta.json`, ripulendo l'HTML |
| `clean_content.py` | ripulisce l'HTML importato |
| `group_content.py` | raggruppa le pagine per slug |
| `download_images.py` | scarica le immagini dal vecchio sito |

**Attenzione:** contengono percorsi assoluti (`E:\MedPhys_Sito\…`) e leggono da `%TEMP%\mp`. Prima di eseguirli, correggi `OUT` e gli `import`.

---

## 7. Messa online

Il sito è pronto per qualsiasi web server statico: basta caricare **tutta** la cartella (root del progetto, non solo `index.html`).

- **Linux / Apache / Nginx** — copia il contenuto in una directory pubblica, es. `/var/www/html/medphys/`.
- **GitLab Pages / GitHub Pages** — committa i file nel branch principale; nessuna configurazione di build richiesta.
- **Nginx** — se in futuro aggiungerai URL puliti senza `#`, serve un `try_files $uri /index.html;`.

---

## 8. Note operative

- **Aggiornare l'anno del copyright** — è automatico: `new Date().getFullYear()` in `footer()`.
- **Lingua predefinita** — `lang = "en"` in `app.js:9`.
- **File generati su una riga sola** — se un file in `assets/data/` diventa illeggibile, riformattalo con VS Code (*Format Document*) invece di riscriverlo a mano.
- **Diagnostica** — se il sito resta bianco, il problema è quasi sempre una virgola mancante in `site-data.js`. Controlla la console del browser (F12).
