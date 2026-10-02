# Manuale operativo — Sito *Medical Physics & Complex Systems* (UniBa / INFN Bari)

Documento di riferimento per chi deve **leggere, modificare o estendere** il sito.
Copre in modo puntuale ogni file del progetto e le procedure passo-passo per
intervenire su ciascuna sezione, inclusa l'aggiunta di **nuove schede** (voci di
menu) e di **nuove pagine**.

> Documento complementare a `README.md` (panoramica rapida) e a `nuovo_sito.md`
> (specifiche di progetto e piano di ricostruzione dal vecchio sito WordPress).

---

## 0. Dieci secondi di orientamento

| Cosa vuoi sapere | Dove guardare |
|---|---|
| Come si rende una pagina | §3 |
| Com'è fatto il sito | §1 Architettura |
| Cosa contiene ogni file | §2 Descrizione dei file |
| **Come aggiungere contenuti senza reintrodurre XSS** | **§2.1b CSP, §2.3b sanitizer, §2.4 regola 7** |
| **Perché non posso eseguire `build_site_data.py`** | **§2.10 avvertenza** |
| Come aggiungere una persona / pubblicazione / progetto | §5 |
| Come aggiungere una nuova scheda di menu o pagina | §6 |
| Come cambiare colori, font, spaziature | §7 |
| Il sito resta bianco / un link non funziona | §8 Diagnostica |
| Come pubblicarlo online | §9 Deploy |

Tre regole da non dimenticare:

1. **Non esistono pagine HTML per ogni sezione.** Non cercare `people.html`,
   `projects.html`, `publications.html`: non esistono e non servono. Tutto il
   contenuto è in `assets/data/site-data.js` e `assets/data/pages_en.js`.
2. **I file in `assets/data/*.js` sono JSON su una riga sola.** Aprili in VS Code
   e usa `Shift+Alt+F` prima di modificarli.
3. **Una virgola o una graffa di troppo rompe tutto il sito** (che resta bianco,
   senza messaggi di errore evidenti). Riformatta e ricontrolla sempre prima di salvare.

Quattro regole **di sicurezza**:

4. **Niente HTML grezzo nei dati.** Il contenuto di `MEDPHYS_EN`, `MEDPHYS_IT` e
   `MEDPHYS_EN_X` passa dal sanitizer, ma la forma canonica va rispettata:
   allow-list di tag e classi (§2.3b). Se serve una classe nuova, aggungila
   lì e in `style.css`, non a caso.
5. **Niente stile o gestore inline.** La CSP li blocca. Le classi nuove vanno in
   `style.css`, i gestori in `app.js` con `addEventListener`.
6. **Link esterni solo `https:`.** E con `target="_blank"` sempre accompagnato da
   `rel="noopener noreferrer"`.
7. **Aggiungere una risorsa nuova?** Se la carichi da `index.html`, aggiungila
   anche alla lista di copia del workflow (§2.11).

---

## 1. Architettura

Sito **statico**, senza framework, senza dipendenze, senza build step.
È una *single-page application* con routing basato su `location.hash`.

```text
index.html
   │  carica 5 script, in quest'ordine preciso
   ├─► assets/data/site-data.js   →  window.MEDPHYS_SITE    (dati: nav, home, persone,
   │                                                     progetti, ricerca, sfide,
   │                                                     pubblicazioni, corsi, newsroom)
   ├─► assets/data/pages_en.js    →  window.MEDPHYS_EN      (corpo HTML delle pagine lunghe)
   │                                window.MEDPHYS_META    (titolo + link di ogni pagina)
   ├─► assets/data/i18n.js        →  window.MEDPHYS_IT     (override/pagine in italiano)
   │                                window.MEDPHYS_EN_X    (override della versione inglese)
   ├─► assets/js/sanitize.js      →  window.MedPhysSanitize  (OBBLIGATORIO: vedi §2.3b)
   └─► assets/js/app.js           →  legge le globali, disegna dentro #app, gestisce #/rotta
```

`index.html` contiene solo un `<div id="app"></div>` vuoto: a runtime `app.js`
sostituisce quel contenuto con `header + main + footer` a ogni cambio di rotta.

La lingua scelta viene salvata in `localStorage` (chiave `medphys_lang`) e
riproiettata su tutte le pagine. Default: `en` (`app.js:9`).

### Catena di rendering di una rotta

```text
cambio #hash  →  render()  (app.js:311)
                  ├─ routeSlug()            app.js:306   estrae lo slug dall'hash
                  ├─ confronto in cascata con findResearch / findPerson / findProject /
                  │  findChallenge / findPublication  (app.js:14-23)
                  ├─ funzione di rendering  (renderHome, renderPerson, renderBase, …)
                  │    └─ t()  app.js:12    risolve {"en":…, "it":…} nella lingua corrente
                  │    └─ basePage() app.js:25  IT[slug] → ENX[slug] → EN[slug]
                  └─ app.innerHTML = header() + <main> + footer()   app.js:332
```

### Mappa completa delle rotte

| Rotta (`#/…`) | Renderer (riga in `app.js`) | Sorgente dei dati | Visibilità nel menu |
|---|---|---|---|
| `home` | `renderHome()` :184 | `SITE.home`, `SITE.research`, `SITE.people`, `SITE.publications`, `SITE.challenges`, `SITE.newsroom` | Home |
| `research` | `renderResearchIndex()` :254 | `SITE.research` | Research |
| `brain`, `lung`, `breast`, `phase-contrast-phase-retrieval-imaging` | `renderResearch(slug)` :265 | `SITE.research[].body` (o `EN[slug]`) | Research |
| `people` | `renderPeople()` :277 | `SITE.people` | People |
| *qualsiasi slug persona* | `renderPerson(slug)` :285 | `SITE.people` + `SITE.collaborators` | — |
| `projects`, `ongoing-projects`, `past-projects` | `renderProjects()` :311 | `SITE.projects.{ongoing,past}` | Projects |
| *qualsiasi slug progetto* | `renderProject(slug)` :324 | `SITE.projects` | — |
| `challenges` | `renderChallenges()` :339 | `SITE.challenges` | Challenges |
| *qualsiasi slug sfida* | `renderChallenge(slug)` :351 | `SITE.challenges` | — |
| `publications`, `pubblication` | `renderPublications()` :366 | `SITE.publications` | Publications |
| `journal-papers`, `book-chapters`, `refereed-proceedings` | `renderPublication(slug)` :377 | `EN[slug]` / `IT[slug]` / `ENX[slug]` | — |
| `join-us` | `renderJoin()` :384 | `SITE.join_us` | Join Us |
| `courses` | `renderCourses()` :395 | `SITE.courses.items` | Courses |
| `short-course`, `conference-slides`, `pattern_recognition` | `renderProtected(slug)` :404 | `SITE.protected` (form password) | sottovoci di Courses |
| `multimedia`, `privary-cookie-policy`, `disattivazione-dei-cookies-sui-browser`, `synchronization-demo`, qualunque altro slug presente in `EN`/`IT`/`ENX` | `renderBase(slug)` :420 | `EN`/`IT`/`ENX` + `META` | Multimedia (gli altri reachable da link/footer) |
| qualunque altro slug | `notFound()` :432 | — | — |

Rotte attive senza codice dedicato, perché risolte da `renderBase`:
`multimedia`, `privary-cookie-policy` (link nel footer, `app.js:172`),
`disattivazione-dei-cookies-sui-browser`, `synchronization-demo`.

---

## 2. Descrizione dei file

Albero reale del progetto (con dimensioni e ruolo):

```text
MedPhys_Sito/
├── index.html                        763 B    unico file HTML (28 righe)
├── manuale.md                    (questo)   manuale operativo
├── README.md                     12.982 B    guida rapida
├── nuovo_sito.md                 17.525 B    specifiche e piano del progetto
│
├── assets/
│   ├── css/
│   │   └── style.css             13.179 B    tutto il design (198 righe)
│   ├── js/
│   │   ├── sanitize.js          (nuovo)     window.MedPhysSanitize — filtro obbligatorio
│   │   └── app.js                           renderer + router
│   ├── data/                              ← I DATI DEL SITO
│   │   ├── site-data.js           72.924 B    window.MEDPHYS_SITE
│   │   ├── pages_en.js           131.457 B    window.MEDPHYS_EN + MEDPHYS_META
│   │   ├── pages_en.json         239.787 B    sorgente leggibile di MEDPHYS_EN
│   │   ├── meta.json              11.494 B    sorgente di MEDPHYS_META
│   │   └── i18n.js                 3.750 B    window.MEDPHYS_IT + MEDPHYS_EN_X
│   └── img/                     251 file     17,2 MB (123 png, 115 jpg, 10 jpeg, 3 gif)
│
├── tools/                                  ← script di migrazione (non servono al sito)
│   ├── build_site_data.py                  genera site-data.js
│   ├── build_i18n.py                       genera i18n.js
│   ├── clean_content.py                    pulisce l'HTML del vecchio sito
│   ├── gen_en.py                           genera pages_en.js
│   ├── group_content.py                    raggruppa pagine per slug
│   └── download_images.py                  scarica le immagini
│
├── robots.txt                              permette il sito, vieta tools/ e .github/
├── vulnerabilita.md                        le 15 segnalazioni e il loro stato
│
├── .well-known/
│   └── security.txt                        contatto per le segnalazioni (RFC 9116)
│
└── .github/
    ├── dependabot.yml                      aggiornamento settimanale delle action
    └── workflows/
        └── pages.yml                       deploy: compone _site/ e lo pubblica
```

---

### 2.1 `index.html`

28 righe. Non contiene contenuto: è solo il *guscio* che monta il sito.

| Riga | Contenuto |
|---|---|
| 2 | `<html lang="en">` — valore aggiornato a runtime da `setLang()` |
| 6 | `<title>Medical Physics & Complex Systems</title>` — **sovrascritto** a ogni rotta da `document.title` in `app.js` (diventa `Titolo — Brand`) |
| 7 | meta description (SEO). Da aggiornare se cambia la descrizione del gruppo |
| 9-11 | **Content-Security-Policy** (vedi §2.1b) |
| 12 | meta `referrer`: `strict-origin-when-cross-origin` |
| 14 | favicon: `assets/img/cropped-586px-Cheek_cell_phase_contrast-1.jpg` |
| 15 | unico foglio di stile: `assets/css/style.css` |
| 18 | `<div id="app"></div>` — punto di innesto di tutto il sito |
| 19-21 | `<noscript>` in italiano: con JavaScript disabilitato la pagina resta vuota, quindi si dice cosa fare |
| 22-26 | i 5 script, **in quest'ordine**: `site-data.js` → `pages_en.js` → `i18n.js` → `sanitize.js` → `app.js`. Riordinarli rompe il sito (`sanitize.js` deve precedere `app.js`, che dipende da `MedPhysSanitize`) |

> **Nessuno stile inline e nessun gestore inline.** La CSP (`style-src 'self'`)
> bloccherebbe `style="..."` e `onsubmit="..."`. Se serve una classe, si aggiunge
> in `style.css`; se serve un gestore, si collega in `app.js` con
> `addEventListener`.

---

### 2.1b Content-Security-Policy

La meta CSP in `index.html` (riga 12) vale per l'intera pagina:

```text
default-src 'self'; script-src 'self'; style-src 'self';
img-src 'self' data:; font-src 'self'; connect-src 'self';
frame-src https://www.youtube-nocookie.com; object-src 'none';
base-uri 'self'; form-action 'none'
```

Cosa implica, in pratica:

- **Nessun `eval`, nessun handler inline**: per questo il form password (§5.10)
  usa `event.preventDefault()` e non `onsubmit="return false"`.
- **`form-action 'none'`**: nessun form può inviare dati. È voluto, perché l'unico
  form del sito è cosmetico.
- **`frame-src` ammette solo `www.youtube-nocookie.com`**: i video *devono* stare su
  quell'host, altrimenti il browser li blocca.
- **`img-src 'self' data:`**: le immagini devono essere locali. Tutte quelle
  referenziate lo sono; non introdurre CDN esterni senza rivalutare la CSP.

**Due direttive non sono applicabili da `<meta>`:** `frame-ancestors` e `sandbox`
valgono solo come header HTTP. Con GitHub Pages non si possono impostare header
custom, quindi il sito è pubblicato senza protezione da *clickjacking*: se in
fatto si ospita altrove (Apache/Nginx), aggiungere
`X-Frame-Options: DENY` o `Content-Security-Policy: frame-ancestors 'none'`.

---

### 2.2 `assets/css/style.css`

209 righe, unico foglio di stile, senza preprocessori né framework.
Blocchi, in ordine:

| Righe | Blocco | Contenuto |
|---|---|---|
| 1-19 | `:root` | le **variabili CSS** del tema (colori, raggi, ombre, larghezza max, font) |
| 20-33 | reset/base | `box-sizing`, `scroll-behavior`, `body`, `img`, link, `.container`, `.skip` (accessibilità) |
| 35-56 | Header | `.site-header` (sticky, sfondo sfocato), `.brand`, `.main-nav`, `.nav-drop`/`.dropdown` (menu a tendina), `.lang` (selettore EN/IT), `.menu-toggle` ( hamburger mobile) |
| 58-72 | Hero | `.hero`, `.hero-bg`, gradiente sovrapposizione, `.kicker`, `.btn-primary`, `.btn-ghost` |
| 74-86 | Sezioni | `.section`, `.section.alt` (sfondo alternato), `.section.dark` (sezione scura), `.section-head` con occhiello + titolo + sottotitolo |
| 88-104 | Griglie e card | `.grid` + varianti `.cols-2/.cols-3/.cols-4` (auto-fit responsive), `.card`, `.thumb`, `.body`, `.more` |
| 106-113 | Persone | `.person`, `.person .ph` (foto quadrata), `.person .pb` |
| 115-119 | Newsroom | `.news-grid` (loghi testate), `.news-item` (grayscale → colori all'hover) |
| 121-160 | Pagine di dettaglio | `.page-hero`, `.crumbs`, `.prose` (tutto il contenuto HTML libero: `h2/h3/ul/ol/table/blockquote/img`), `.figure-inline`, `.detail-layout` (2 colonne), `.aside-card`, `.person-hero`, `.tag`, `.video-embed`, `.notice`, `.lock` |
| 162-166 | Pubblicazioni | `.pub-list`, `.pub-entry` |
| 168-181 | Footer | `.site-footer`, `.footer-grid`, `.footer-brand`, `.copyright`, `.footer-lang` |
| 183-185 | Back to top | `.to-top` — **definito ma mai usato** da `app.js` |
| 187-198 | Mobile | unico media query `@media (max-width:960px)`: menu a schermo intero, dropdown statico, riduzione padding hero |

Variabili principali (`:root`):

```css
--ink / --ink-soft / --muted   testo principale, testo secondario, testo attenuato
--line / --bg / --bg-alt       bordi, sfondo bianco, sfondo alternato
--brand / --brand-2 / --brand-ink   ciano istituzionale (toni con cui ricolorare il sito)
--accent                        ambra: pulsanti e sottolineature dei titoli
--dark                          fondo scuro (footer, sezione newsroom)
--radius / --radius-sm          arrotondamento card / piccoli elementi
--shadow / --shadow-lg          ombre
--maxw:1180px                   larghezza massima contenuto
--sans                          font system (Segoe UI → system-ui → Roboto → …)
```

Classi **presenti nel CSS ma non usate** né da `app.js` né dai dati:
`.to-top` e `.crumbs-back`. Si possono usare in futuro oppure rimuovere.

`.pub-entry` esiste nel CSS e nell'allow-list del sanitizer, ma il contenuto
delle pubblicazioni è **prosa** (`<p>`, `<em>`, `<ul>` dentro `.prose.pub-list`):
si può usare se un giorno si vuole una scheda per articolo.

---

### 2.3 `assets/js/app.js`

363 righe, IIFE con `"use strict"`, nessuna dipendenza esterna.
È l'unico file che "disegna" il sito.

| Righe | Funzione | Cosa fa |
|---|---|---|
| 3-8 | lettura delle globali | `MEDPHYS_SITE`, `MEDPHYS_EN`, `MEDPHYS_META`, `MEDPHYS_IT`, `MEDPHYS_EN_X`, elemento `#app` |
| 9-10 | lingua | default `en`, ripresa da `localStorage("medphys_lang")` in un `try/catch` |
| 12 | `t(o)` | **il resolver bilingue**: accesso a `o[lang]` / `o.en` con guardia anti prototype-pollution (`S.hasSlug`) |
| 13 | `pageOf(d, slug)` | lettura da un dizionario con la stessa guardia |
| 14-23 | helper dati | `allPeople()` (people+collaborators), `allProjects()`, `findPerson/findProject/findChallenge/findResearch/findPublication(slug)` |
| 25-29 | `basePage(slug)` | **catena delle traduzioni**: `IT[slug]` → `ENX[slug]` → `EN[slug]` → `""` |
| 31-33 | `external(url)` | link esterno con `target=_blank rel="noopener noreferrer"`, URL validato |
| **40-44** | **helper di output sicuro** | `e()` = escape testo, `a()` = escape attributo, **`rich()` = unico punto di passaggio per l'HTML ricco**, `media()` = URL immagine validato, `link()` = URL di destinazione validato. **Tutto ciò che arriva dai dati deve passare da qui** |
| 36-58 | `header(route)` | logo+brand, menu da `SITE.nav` (con dropdown se `children`), selettore lingua, bottone hamburger, link "Skip to content" |
| 61-88 | `footer()` | logo, indirizzo, email da `SITE.emails`, link di navigazione, colonna "Risorse", copyright con anno automatico `new Date().getFullYear()`, crediti, selettore lingua |
| **445-449** | `routeSlug()` | `location.hash` → slug, validato con `S.isValidSlug()`: rifiuta nomi di proprietà pericolosi (`__proto__`, `constructor`, …) e slug che non corrispondono a `^[a-z0-9]+([-_][a-z0-9]+)*$` |
| **455** | **l'unico sink** | `template.innerHTML = html;` — non esistono altri `innerHTML` in tutto il file, e ciò che vi finisce è stato passato da `rich()`/`a()`/`e()` |
| 533 | form password | `addEventListener("submit", …, event.preventDefault())` — la CSP vieta `form-action` e i gestori inline |
| 91-135 | `renderHome()` | hero + 6 sezioni nell'ordine: research → people → publications → challenges → projects → newsroom |
| 137-142 | `sectionWrap(id, titleKey, inner, cls)` | involucro standard di sezione (occhiello = `SITE.short`, titolo da `SITE.sections`) |
| 144-149 | `staffGrid(list)` | griglia `.grid.cols-4` di card persona |
| 150-152 | `nameOf(slug)` | **"roberto-bellotti" → "Roberto Bellotti"**: il nome viene ricavato dallo slug |
| 155-159 | `pageHero(title, sub, crumb)` | testata di pagina con breadcrumb |
| 161-168 | `renderResearchIndex()` | griglia a 2 colonne delle linee di ricerca |
| 170-179 | `renderResearch(slug)` | `body` di `site-data.js` se presente, altrimenti `basePage(slug)`; colonna laterale con tutte le linee |
| 181-185 | `renderPeople()` | solo `SITE.people` (i collaboratori **non** vengono mostrati in griglia) |
| 187-198 | `renderPerson(slug)` | foto, keywords, **tag** ricavati dividendo `keywords` sulle virgole, bio, email |
| 200-204 | `projectCard(p)` | card progetto, abstract troncato a 150 caratteri |
| 206-213 | `renderProjects()` | due sezioni: ongoing (chiaro) + past (`.alt`) |
| 215-225 | `renderProject(slug)` | immagine, abstract, `dl` con Duration e **Status** (calcolato verificando se lo slug è in `past`) |
| 227-235 | `renderChallenges()` | griglia card sfide |
| 237-245 | `renderChallenge(slug)` | descrizione + bottone "Apri la sfida" verso `c.url` |
| 247-254 | `renderPublications()` | griglia categorie di pubblicazioni |
| 256-261 | `renderPublication(slug)` | `pub_notice` + `basePage(slug)` dentro `.prose.pub-list` |
| 263-270 | `renderJoin()` | tabella tesi da `SITE.join_us.theses` (titolo tradotto + supervisori) |
| 272-276 | `renderCourses()` | lista puntata da `SITE.courses.items` |
| 278-287 | `renderProtected(slug)` | blocco `.lock` con titolo, messaggio e **form password non funzionante** (`onsubmit="return false"`, nessun controllo) |
| 289-298 | `renderBase(slug)` | pagina generica: titolo da `META[slug].title` (o `nameOf(slug)`) + corpo da `basePage(slug)`; aggiunge il banner "official notice" sulle due pagine cookie |
| 300-303 | `notFound()` | pagina 404 con link alla home |
| 306-309 | `routeSlug()` | *spostato: vedi riga 445 sopra* |
| **311-336** | **`render()`** | **il router**: cascata di `if/else` (vedi mappa rotte in §1); scrive `header + main + footer` in `#app`, imposta `document.title`, scrolla a 0, richiama `bindShell()` |
| 338-351 | `bindShell()` | eventi: apertura menu mobile, chiusura al click sui link, bottoni lingua (`[data-setlang]`) |
| 353-358 | `setLang(l)` | salva in `localStorage`, aggiorna `<html lang>`, ridisegna |
| 360-362 | bootstrap | `hashchange` → `render()`; se l'hash è vuoto imposta `#/home`; prima render |

> Se `MedPhysSanitize` non è definito, `app.js` **si ferma e mostra un avviso**
> invece di rendere la pagina: meglio una pagina di errore che un rendering
> senza protezione. Se in console compare quell'avviso, il caricamento di
> `sanitize.js` è rotto (ordine sbagliato in `index.html`, oppure file mancante).

---

### 2.3b `assets/js/sanitize.js` — il punto di controllo obbligatorio

Espone `window.MedPhysSanitize` (ed è importabile come modulo CommonJS, così i
test lo possono usare senza un browser). **Nessuna dipendenza esterna.**

È l'unico punto in cui l'HTML proveniente dai dati viene filtrato. Non è un
pre-filtro: **ricostruisce** il markup da zero a partire da un allow-list di tag,
attributi e classi. Un tag non ammesso viene rimosso; se è pericoloso
(`script`, `style`, `iframe` non consentito, `object`, `embed`, `form`, …) viene
rimosso anche tutto il suo contenuto.

API pubblica:

| Funzione | Cosa fa |
|---|---|
| `escapeHtml(s)` / `escapeAttr(s)` | codifica testo e attributi; `&` viene codificato **prima**, così `&lt;` non può essere "rianimato" |
| `safeUrl(u, kind)` | `kind` = `link`, `media`, `embed`. Ammette solo `https:`, `mailto:`, `tel:`, percorsi relativi e ancore; per `embed` **solo** `https://www.youtube-nocookie.com/embed/…`. Rifiuta `javascript:`, `vbscript:`, `data:`, `file:` e i protocol-relative |
| `sanitizeRichHtml(html)` | il filtro completo, con allow-list di tag/attributi/classi e codifica delle entità prima dell'analisi |
| `isValidSlug(s)` / `hasSlug(obj, k)` | validazione degli slug e accesso sicuro ai dizionari |
| `decodeEntities(s)` | usato dai test per confrontare il testo visibile |

Dettagli che contano:

- **Classi ammesse**: solo `video-embed` e `pub-entry`. Ogni altra classe nel
  contenuto viene scartata.
- **Iframe**: riscritti su `youtube-nocookie.com`, con `sandbox`, `referrerpolicy`
  e `rel="noopener noreferrer"`. Un `<iframe>` con altro host viene **rimosso**.
- **Codice caratteri**: i tag sono confrontati in minuscolo, così `<ScRiPt>` non
  sfugge al filtro.
- **Ordine**: `sanitize.js` va caricato **prima** di `app.js`.

Quando aggiungi contenuto, non serve (e non si deve) disattivare nulla: se una
cosa viene rimossa, il modo corretto è correggere il dato, non allargare
l'allow-list.

---

### 2.4 `assets/data/site-data.js` — `window.MEDPHYS_SITE`

**È il file dei dati del sito.** JSON su una riga, preceduto da
`window.MEDPHYS_SITE = ` e chiuso da `;`. Contiene `</` scritto come `<\/`
(obbligatorio: evita che il browser interpreti la sequenza come fine script).

Schema completo, chiave per chiave:

| Chiave | Tipo | N. | Contenuto / uso |
|---|---|---|---|
| `brand` | `{en,it}` | — | Nome esteso del gruppo. Usato in header (riga 2 del brand), footer, `<title>` |
| `short` | `{en,it}` | — | Nome breve ("Medical Physics"). Occhiello delle sezioni, `<title>` di default |
| `org` | `{en,it}` | — | Affiliazione, sotto il brand |
| `logo` | stringa | 1 | Percorso del logo mostrato nel footer (`MedicalPhysics.png`) |
| `address` | stringa | 1 | Indirizzo, mostrato nel footer |
| `emails` | array di stringhe | 2 | Email istituzionali, resi cliccabili nel footer |
| `nav` | array | 9 | **Menu principale.** Voce = `{route,en,it}`; con `children:[…]` diventa menu a tendina. L'ultima voce (`courses`) ha 4 figli |
| `home` | oggetto | 6 | `kicker`, `title`, `lead`, `para2`, `para3` (tutti `{en,it}`) + `hero_img` (immagine di sfondo). `para3` **non è renderizzato** da `renderHome()` |
| `sections` | oggetto | 7 | Titoli bilingui delle sezioni: `research`, `people`, `publications`, `challenges`, `newsroom`, `projects`, `collaborators`. Chiave inesistente → fallback sul nome della sezione (`app.js:138`) |
| `pub_notice` | `{en,it}` | — | Avviso legale sopra l'elenco pubblicazioni (home e pagina categoria) |
| `research` | array | 4 | **Linee di ricerca**: `brain`, `lung`, `breast`, `phase-contrast-phase-retrieval-imaging`. Chiavi: `slug`, `img`, `title`, `summary`, `body` (entrambi `{en,it}`) |
| `people` | array | 18 | **Staff mostrato** in `#/people`. Chiavi: `slug`, `img`, `keywords`, `bio` ( `{en,it}` ), `email` |
| `collaborators` | array | 8 | Collaboratori: hanno scheda individuale raggiungibile ma **non compaiono in griglia** |
| `projects` | oggetto | 2+7 | `ongoing` (2) e `past` (7). Chiavi: `slug`, `img`, `title` (`{en,it}`), `duration`, `period`, `abstract` (`{en,it}`) |
| `challenges` | array | 7 | `slug`, `img`, `title` (`{en,it}`), `desc` (`{en,it}`), `url` |
| `publications` | array | 3 | **Categorie** di pubblicazioni: `journal-papers`, `book-chapters`, `refereed-proceedings`. Chiavi: `slug`, `en`, `it`, `desc` (`{en,it}`) |
| `join_us` | oggetto | 4 | `intro`, `col_title`, `col_sup` (tutti `{en,it}`) + `theses`: array di 7 voci `{t:{en,it}, s:"supervisori"}` |
| `courses` | oggetto | 1 | `items`: array di 1 voce `{en,it}` (corso Pattern Recognition) |
| `protected` | oggetto | 3 | Pagine con richesta password: `short-course`, `conference-slides`, `pattern_recognition`. Ciascuna con `title` (`{en,it}`) |
| `protected_msg` | `{en,it}` | — | Testo sopra il campo password |
| `newsroom` | array | 37 | Rassegna stampa: `{name, img, url}`; **le prime voci sono le prime loghi in home** |

Esempio reale (persona):

```json
{
  "slug": "roberto-bellotti",
  "img": "assets/img/foto-rob.jpg",
  "keywords": { "en": "Medical Physics, Spatio-temporal Data Mining",
                "it": "Fisica Medica, Data Mining spazio-temporale" },
  "bio": { "en": "Roberto Bellotti is full professor…",
           "it": "Roberto Bellotti è professore ordinario…" },
  "email": "roberto.bellotti@uniba.it"
}
```

> Attenzione: il **nome mostrato non è nei dati**, è derivato dallo slug da
> `nameOf()` (`app.js:150`). Cambiare lo slug cambia anche il nome visualizzato,
> e i nomi con doppio nome (`andrea-lo-sasso`) diventano "Andrea Lo Sasso".

---

### 2.5 `assets/data/pages_en.js` — `window.MEDPHYS_EN` + `window.MEDPHYS_META`

Un unico file con **due** assegnazioni:

```js
window.MEDPHYS_EN  = { "slug": "<html>", … };   // 62 slug, ~131 KB
window.MEDPHYS_META = { "slug": {"title":…,"link":…,"fn":…}, … };
```

- `MEDPHYS_EN` = corpo HTML delle pagine "lunghe". È HTML **libero**: quasi tutte
  le classi del CSS sono state rimosse in fase di pulizia, quindi il contenuto
  viene stilato solo dalle regole di `.prose` (`h1..h4`, `p`, `ul/ol/li`,
  `table/th/td`, `blockquote`, `img`, `a`).
- `MEDPHYS_META` = metadati: `title` (titolo mostrato, usato da `renderBase`),
  `link` (URL del vecchio sito, **informativo**), `fn` (nome file sorgente
  dell'estrazione, **informativo**).

Stato reale dei 62 slug (verificato rispetto al router):

| Stato | Slug |
|---|---|
| **Usati** da `renderPublication` | `journal-papers`, `book-chapters`, `refereed-proceedings` |
| **Usati** da `renderBase` | `multimedia`, `privary-cookie-policy`, `disattivazione-dei-cookies-sui-browser`, `synchronization-demo` |
| **Fallback** (valgono solo se in `site-data.js` manca `body` nella linea di ricerca) | `brain`, `lung`, `breast`, `phase-contrast-phase-retrieval-imaging` |
| **Superati** dai dati (presenti ma mai letti) | tutti gli slug persona, tutti gli slug progetto, tutti gli slug sfida, `join-us`, `courses`, `projects` |
| **Vuoti** (`""`, quindi il router cade in 404 se raggiunti) | `people`, `homepage`, `pubblication`, `short-course`, `conference-slides`, `pattern_recognition` |

Convenzioni osservate nel contenuto delle pubblicazioni:

```html
<p><em>Titolo dell'articolo</em></p>
<p>Autori, in ordine</p>
<p>Rivista, anno; vol(num): pagine. doi:10.xxxx/yyyy</p>
```

Non esistono classi `pub-item`/`pub-authors`: il README le descrive come
convenzione possibile, ma il CSS effettivamente usato è `.pub-list`.

Problemi noti del contenuto in questo file:

- I `<iframe>` di YouTube **non** hanno la classe `video-embed`
  (la conversione l'aveva prevista, ma il file è stato poi rigenerato/ripulito):
  in `#/multimedia` i video si vedono alla dimensione nativa 300×150.
  Fix:wrappare ogni `iframe` in `<div class="video-embed">…</div>` (vedi §7.3).
- 10 immagini citate (`crp.png`, `lorenz.png`, `mind.png`, `nextmr.png`,
  `decision.jpeg`, `gunnebo_logo_ok.png`, …) sono tutte presenti in
  `assets/img/`: i riferimenti sono corretti.

---

### 2.6 `assets/data/pages_en.json`

240 KB, **JSON pretty-printed** (indentazione a 1 spazio). È la sorgente leggibile
usata da `tools/gen_en.py` per rigenerare `pages_en.js`. Non viene caricata dal
browser.
Per l'aggiornamento ordinario **non serve toccarlo**: si modifica `pages_en.js`.

---

### 2.7 `assets/data/meta.json`

11 KB, JSON pretty-printed. Sorgente di `window.MEDPHYS_META`: 62 voci
`{title, link, fn}`. Come sopra: usare `pages_en.js` per le modifiche.

---

### 2.8 `assets/data/i18n.js` — `window.MEDPHYS_IT` + `window.MEDPHYS_EN_X`

3,7 KB, due assegnazioni:

- `MEDPHYS_IT` — **1 solo slug**: `synchronization-demo` (testo italiano completo
  di quella pagina). È il meccanismo per le pagine lunghe in italiano.
- `MEDPHYS_EN_X` — **oggetto vuoto**: predisposto per gli override della versione
  inglese (ha la priorità su `MEDPHYS_EN` quando la lingua è `en`).

Effetto della catena (`basePage()`, `app.js:25-29`):

| Lingua | Ordine di risoluzione |
|---|---|
| `it` | `MEDPHYS_IT[slug]` → `MEDPHYS_EN[slug]` |
| `en` | `MEDPHYS_EN_X[slug]` → `MEDPHYS_EN[slug]` |

Il file in italiano contiene formule LaTeX (`\( … \)`) che **non vengono
renderizzate**: non c'è MathJax/KaTeX nel sito.

---

### 2.9 `assets/img/`

251 file, 17,2 MB (123 `.png`, 115 `.jpg`, 10 `.jpeg`, 3 `.gif`).

Contenuti:

- **Logo e testate**: `MedicalPhysics.png`, favicon `cropped-586px-…jpg`.
- **Ritratti dello staff**: `foto-rob.jpg`, `new_diacono.jpg`, `new_lombardi_angela.png`, …
- **Logo dei progetti**: usati nelle card di `#/projects`.
- **Immagini delle linee di ricerca** e delle sfide.
- **Loghi delle testate giornalistiche** (37) per la sezione newsroom.
- **Varianti responsive WordPress** (68 file, es. `nextmr-320x103.png`,
  `Preterm-birth-copia-768x177.jpg`): **non usate** dal sito, sono residui
  dell'estrazione. Candidates per una pulizia futura.

Regole:

- I percorsi nei dati sono **relativi alla root del sito**: `assets/img/…`.
  Non usare percorsi assoluti né cartelle esterne.
- Metti il file in `assets/img/` **prima** di referenziarlo nei dati.
- Tutti i riferimenti attuali sono stati verificati: **nessuna immagine mancante**.

---

### 2.10 `tools/` — script di migrazione (non servono al sito)

Il sito **non ha bisogno** di alcuno di questi script per funzionare o essere
aggiornato. Servono solo per re-importare il vecchio sito WordPress
(`medphys.ba.infn.it`).

**Non contengono più percorsi assoluti**: la cartella di destinazione è derivata
dalla posizione dello script (`ROOT = dirname(dirname(abspath(__file__)))`), quindi
funzionano su qualsiasi checkout e su qualsiasi sistema operativo. L'unico posto
ancora legato a Windows è la sorgente dei dati grezzi, `%TEMP%\mp` (su Linux
`/tmp/mp`), che va procurato a parte.

Tutti condividono due regole di sicurezza:

- **URL**: `safe_url()` ammette solo `https:`, `mailto:`, `tel:` e percorsi
  relativi. `javascript:`, `vbscript:`, `data:`, `file:` e i protocol-relative
  vengono rifiutati. Gli URL YouTube sull'host con cookie vengono **riscritti**
  su `youtube-nocookie.com`, non scartati (altrimenti il prossimo
  rigeneramento perderebbe tutti i video).
- **Serializzazione**: i file `.js` vengono prodotti con `<`, `>`, `&` esposti
  come `\u003c`, `\u003e`, `\u0026` e con U+2028/U+2029 separati. Un `</script>`
  nel dato non può chiudere il tag che lo contiene.

| Script | Cosa fa | Input → Output |
|---|---|---|
| `download_images.py` | Scarica le immagini del vecchio sito (media REST + `src`/`srcset` negli HTML). **Verifica TLS attiva**, allow-list di un solo host (`medphys.ba.infn.it`), scrittura confinata in `assets/img/`, tetto di 20 MB per file, controllo del `Content-Type`. Genera il manifest `img_manifest.json` | `%TEMP%\mp` → `assets/img/` |
| `clean_content.py` | Ripulisce l'HTML importato: rimuove script/style/commenti e span vuoti, riscrive `<img>` verso `assets/img/` con `alt` codificato, converte gli iframe YouTube in sandbox su `nocookie`, converte i link interni in `href="#/slug"`, lascia solo gli attributi utili, elimina paragrafi vuoti | `%TEMP%\mp\extract\*.html` → `pages_en.json` + `meta.json` |
| `group_content.py` | Raggruppa e ripulisce in testo le pagine per gruppo tematico, per facilitare la riscrittura dei contenuti | `%TEMP%\mp\extract` → `%TEMP%\mp\groups\*.txt` |
| `build_site_data.py` | Contiene, hard-coded, **tutti i dati** di `site-data.js` e lo serializza. Gli URL del newsroom passano da `safe_url()`, che promuove `http://` a `https://` | dict Python → `site-data.js` |
| `build_i18n.py` | Definisce la versione italiana di `synchronization-demo` e scrive il file. L'iframe è **generato** dalla funzione `embed()`, non copiato a mano | dict Python → `i18n.js` |
| `gen_en.py` | Applica le correzioni finali all'HTML (`<p><div>…</div></p>` non valido) e serializza in `pages_en.js` | `pages_en.json` + `meta.json` → `pages_en.js` |

**Avvertenza importante:** il workflow normale è **modificare direttamente il
`.js`**, non eseguire i generatori. `build_site_data.py` è stato allineato al
dato pubblicato (18 persone, 37 notizie, nessun URL scartato) e non è più
distruttivo, ma resta una copia: **se modifichi `site-data.js` a mano, lo script
diventa di nuovo obsoleto**. Prima di eseguirlo, verifica con

```bat
python -c "import importlib.util,io,json;s=importlib.util.spec_from_file_location('b','tools/build_site_data.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);raw=io.open('assets/data/site-data.js',encoding='utf-8').read();print(len(m.SITE['people']),len(json.loads(raw[len('window.MEDPHYS_SITE = '):].strip().rstrip(';'))['people']))"
```

che i conteggi coincidono. Nota che l'output dello script scrive `&` come
`\u0026`: è un escaping più conservativo, semanticamente identico, quindi il
diff risulta grande ma non cambia nulla di visibile.

---

### 2.11 `.github/workflows/pages.yml`

Deploy automatico su GitHub Pages. Si attiva su push a `main` o manualmente
(`workflow_dispatch`).

- **Le action sono fissate a un commit SHA completo** (non a un tag): un tag
  spostabile diventerebbe un vettore di esecuzione arbitraria. Il tag è
  conservato nel commento a destra. `dependabot.yml` li aggiorna ogni settimana.
- **Permessi minimi dichiarati**: `contents: read`, `pages: write`,
  `id-token: write`.
- **Non si pubblica la radice del repository.** Il passo *Assemble the published
  directory* copia in `_site/` **solo** `index.html`, `assets/`, `robots.txt` e
  `.well-known/security.txt`, poi crea `_site/.nojekyll` e verifica con un
  controllo negativo che `tools/`, `.github/` e i documenti interni non siano
  dentro. L'upload usa `path: _site`.

La directory `_site/` è un artefatto di build: è in `.gitignore` e non va
committata.

> **Attenzione:** se aggiungi in `index.html` un nuovo file da pubblicare (un
> favicon, un font, un `.json`), devi **aggiungerlo anche alla lista di copia**
> del workflow, altrimenti funziona in locale e sparisce in produzione.

---

### 2.12 File di igiene del repository

| File | A cosa serve |
|---|---|
| `.gitignore` | Esclude `_site/`, `__pycache__/`, i JSON intermedi e i file di log |
| `robots.txt` | Permette il sito, vieta `/tools/` e `/.github/` |
| `.well-known/security.txt` | Contatto per le segnalazioni di vulnerabilità (RFC 9116). **Contiene una data `Expires`: va rinnovata almeno ogni anno** |
| `.github/dependabot.yml` | Aggiornamento settimanale delle action GitHub |
| `vulnerabilita.md` | Le 15 segnalazioni del 2026-10-02 e il loro stato di risoluzione |

---

### 2.13 `README.md` e `nuovo_sito.md`

- **`README.md`** — guida rapida d'ingresso: architettura, rotte, struttura file,
  mini-guida contenuti, sezione "aggiungere una pagina", tool, deploy, note.
  È più conciso di questo manuale: se i due divergono, **vale il codice**, e per
  i dettagli questo file.
- **`nuovo_sito.md`** — documento di progetto *pre-implementazione*: analisi del
  sito originale, elenco delle 11 sezioni del menu WordPress, struttura proposta,
  piano operativo, manuale per l'operatore, vantaggi rispetto a un CMS, piano di
  deploy. **Descrive un'architettura multi-pagina che non è stata implementata**:
  il sito finale è una SPA single-file come descritto qui. Utile come storico e
  come elenco dei contenuti da migrare.

---

## 3. Come si rende una pagina (esempio: `#/brain`)

1. `app.js` legge `location.hash` → `routeSlug()` restituisce `brain`.
2. Nel router: `findResearch("brain")` trova l'oggetto in `SITE.research`.
3. `renderResearch("brain")` chiama `t(r.title)` → "Brain"; il corpo è
   `t(r.body)` (presente in `site-data.js`, quindi `basePage()` non viene chiamato).
4. `pageHero()` stampa titolo, sommario e breadcrumb verso `#/research`.
5. La colonna laterale elenca tutte le linee di ricerca come link.
6. `render()` scrive header + main + footer in `#app`, imposta
   `document.title = "Brain — Medical Physics & Complex Systems"`.

---

## 4. Modifiche globali (non dipendono dalla sezione)

### 4.1 Nome gruppo, logo, indirizzo, email
`site-data.js` → chiavi iniziali:

| Voce | Chiave |
|---|---|
| Nome esteso | `brand` |
| Nome breve (occhielli sezioni) | `short` |
| Affiliazione | `org` |
| Logo del footer | `logo` |
| Indirizzo | `address` |
| Email (array, anche 1 solo) | `emails` |

```json
"emails": ["roberto.bellotti@uniba.it", "nuovo.indirizzo@infn.it"]
```

### 4.2 Testi del footer
Il footer è **hard-coded** in `app.js:61-88`. Si modificano:

- colonna "Navigate" — generata da `SITE.nav` (nessun codice da toccare);
- colonna "Risorse" — testi e link scritti a mano (`app.js:74-80`);
- crediti e copyright — `app.js:81-87` (l'anno è automatico);
- logo, indirizzo, email — da `site-data.js`.

### 4.3 Lingua predefinita
`app.js:9` → `var lang = "en";`. Attenzione: se l'utente ha già visitato il sito,
`localStorage` sovrascrive il default (per testare, svuota i dati del browser).

### 4.4 Colori e stile
Tutto in `style.css:1-19`. Per un re-branding bastano le variabili `--brand`,
`--brand-2`, `--brand-ink`, `--accent`, `--dark`.

---

## 5. Modifiche sezione per sezione

> Prefazione comune a tutte le sezioni:
> 1. Apri `assets/data/site-data.js` in VS Code.
> 2. `Shift+Alt+F` per riformattare (diventa leggibile).
> 3. Cerca la chiave con Ctrl+F, modifica, salva.
> 4. **Ctrl+F5** nel browser (hard refresh: senza, resta la cache degli script).
> 5. Se il sito diventa bianco: hai rotto il JSON → F12 → Console per l'errore.

---

### 5.1 Aggiungere una persona (nuova scheda personale)

Nel blocco `"people"` di `site-data.js`, aggiungi un oggetto:

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

- `slug` **obbligatorio**, obbligatoriamente `nome-cognome` in minuscolo con
  trattini: il nome mostrato è generato dal slug (`nameOf()`, `app.js:150`).
  `mario-rossi` → "Mario Rossi".
- `img`, `keywords`, `bio` obbligatori; `email` opzionale.
- Metti la foto in `assets/img/` **prima** di referenziarla.
- Usa la **virgola** come separatore in `keywords`: ogni pezzo diventa un tag
  colorato nella scheda (`app.js:189`).
- **Nessuna pagina da creare**: la scheda è generata da `renderPerson()`, e la
  rotta `#/mario-rossi` funziona automaticamente.
- Per un **collaboratore** (scheda raggiungibile ma **fuori** dalla griglia di
  `#/people`) inserisci l'oggetto nel blocco `"collaborators"` invece di `"people"`.

**Rimuovere una persona**: elimina l'intero oggetto da `people` (o `collaborators`).
Non serve toccare `pages_en.js` (le vecchie pagine persona lì presenti non sono
più usate).

**Ordine in griglia**: l'ordine è quello dell'array. Per raggruppare per ruolo,
basta riordinare gli oggetti (non esiste ancora una separazione per ruolo).

---

### 5.2 Linee di ricerca

Nel blocco `"research"`:

```json
{
  "slug": "nuova-linea",
  "img": "assets/img/immagine.jpg",
  "title": { "en": "New line", "it": "Nuova linea" },
  "summary": { "en": "Short description…", "it": "Descrizione breve…" },
  "body": {
    "en": "<p>Testo lungo in HTML…</p>",
    "it": "<p>Testo lungo…</p>"
  }
}
```

- `slug`, `img`, `title`, `summary` obbligatori.
- `body` è **opzionale**: se lo ometti, la pagina prende il contenuto da
  `MEDPHYS_EN[slug]` in `pages_en.js` (stesso slug).
- Appare automaticamente in `#/research`, in home e nel menu laterale delle pagine
  di dettaglio.
- Il sommario del sottotitolo in `renderResearchIndex()` è scritto fisso nel
  codice ("Four research lines…", `app.js:162`): se le linee non sono più 4,
  correggi quella frase.

---

### 5.3 Progetti

In `site-data.js` → `projects` → `ongoing` **oppure** `past`:

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

- Lo stato (Ongoing/Completed) **non si dichiara**: `renderProject()` lo deduce
  verificando in quale dei due array lo slug si trova (`app.js:223`).
- Nell'array giusto, finisce nella sezione giusta di `#/projects`.
- Il testo esteso del progetto, se serve, si inserisce in
  `MEDPHYS_EN[slug]` (ma attenzione: `renderProject()` **non** chiama `basePage()`,
  quindi un corpo aggiunto lì **non verrebbe mostrato**; per un testo esteso serve
  una modifica al renderer, vedi §6.4).

---

### 5.4 Sfide (challenges)

Nel blocco `"challenges"`:

```json
{
  "slug": "nuova-sfida",
  "img": "assets/img/logo_sfida.png",
  "title": { "en": "Challenge name", "it": "Nome sfida" },
  "desc": { "en": "Breve descrizione…", "it": "Breve descrizione…" },
  "url": "https://sito-esterno.org/challenge"
}
```

`url` è l'unico campo obbligatorio in assoluto: è il link del bottone
"Apri la sfida" (`app.js:244`).

---

### 5.5 Pubblicazioni

Le pubblicazioni sono su **due livelli**.

**a) Creare una categoria nuova** (es. "Conference papers") — nell'array
`"publications"`:

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

Compare subito in `#/publications` e in home. La rotta `#/conference-papers` è
riconosciuta da `findPublication()` e resa da `renderPublication()`.

**b) Aggiungere un articolo a una categoria esistente** — in `pages_en.js`, dentro
`window.MEDPHYS_EN["journal-papers"]`, in fondo alla stringa, seguendo lo stile
in uso:

```html
<p><em>"Titolo dell'articolo."</em></p>
<p>Rossi M., Bellotti R.</p>
<p>Nome Rivista, 12(3), 45-67, 2026. doi:10.xxxx/xxxx</p>
<p><a href="https://doi.org/10.xxxx/xxxx" target="_blank" rel="noopener">doi:10.xxxx/xxxx</a></p>
```

Regole pratiche:

- le chiavi (`"journal-papers"`, ecc.) sono **case-sensitive** e devono combaciare
  con lo `slug` in `SITE.publications`;
- l'HTML è **inline** nella stringa JSON: niente righe nuove non escape
  (`\n`), niente apici doppi non escape, e ogni `</` va scritto `<\/`;
- per la versione italiana della pagina usa `MEDPHYS_IT` in `i18n.js` con lo
  **stesso slug** come chiave.

---

### 5.6 Join Us (tesi di laurea)

`site-data.js` → `join_us`:

```json
"theses": [
  {
    "t": { "en": "Titolo della tesi", "it": "Titolo della tesi" },
    "s": "Dott.ssa Marianna La Rocca, Prof. Nicola Amoroso"
  }
]
```

- `t` = titolo tradotto (finisce nella prima colonna), `s` = supervisori
  (seconda colonna, testo semplice).
- Anche `intro`, `col_title`, `col_sup` sono `{en,it}` e si modificano lì.
- L'elenco completo in `#/join-us` è **solo** questo array: le voci in
  `MEDPHYS_EN["join-us"]` non vengono mostrate.

---

### 5.7 Corsi

`site-data.js` → `courses` → `items`: array di oggetti `{en, it}` resi come
`<ul>`. Esempio attuale: `"Pattern Recognition – Prof. Roberto Bellotti"`.

---

### 5.8 Notizie in home (newsroom)

Nell'array `"newsroom"`:

```json
{ "name": "Testata giornalistica", "img": "assets/img/logo_testata.png", "url": "https://…" }
```

- L'ordine dell'array è l'ordine di visualizzazione; le prime voci sono in evidenza.
- Il logo viene mostrato in scala di grigi e torna a colori all'hover
  (`.news-item`).
- `url` si apre in nuova scheda.
- Per aggiungere news *testuali* (con data e estratto) servono una nuova sezione
  o una pagina nuova: vedi §6.

---

### 5.9 Pagine lunghe (multimedia, cookie policy, demo)

Metodo generale (`renderBase`), valido per qualsiasi pagina senza struttura dedicata:

1. In `pages_en.js`, dentro `window.MEDPHYS_EN`, aggiungi
   `"nuova-pagina": "<p>Contenuto…</p>"`.
2. Nello stesso file, dentro `window.MEDPHYS_META`, aggiungi
   `"nuova-pagina": { "title": "Nuova pagina", "link": "", "fn": "" }`
   (se ometti `META`, il titolo viene derivato dallo slug → "Nuova Pagina").
3. In `i18n.js`, dentro `window.MEDPHYS_IT`, aggiungi `"nuova-pagina": "<p>…</p>"`
   se vuoi la versione italiana.
4. Per vederla nel menu, aggiungi la voce in `nav` (§6.2). Altrimenti è
   raggiungibile solo via link diretto `#/nuova-pagina`.

Contenuti ammessi: `h1..h4`, `p`, `ul/ol/li`, `strong/em`, `table`, `blockquote`,
`img` con percorso in `assets/img/`, `a`, `iframe`.

**Multimedia** in particolare: contiene solo `<div><iframe …></div>` (YouTube).
Vedi §7.3 per la correzione delle dimensioni.

---

### 5.10 Pagine protette da password

`site-data.js` → `protected`:

```json
"protected": {
  "short-course": { "title": { "en": "Short Course", "it": "Short Course" } },
  "conference-slides": { "title": { "en": "Conference slides", "it": "Slide dei convegni" } },
  "pattern_recognition": { "title": { "en": "Labs", "it": "Laboratori" } }
}
```

- Aggiungere una chiave qui basta per far comparire il blocco con password.
- **Attenzione:** la protezione è **solo cosmetica**. Il form chiama
  `event.preventDefault()` e non confronta nulla: qualunque visitatore vede
  comunque la pagina "bloccata", e il contenuto, se presente in `MEDPHYS_EN`,
  sarebbe comunque scaricabile dal browser. Non inserire dati riservati.
- Se serve una protezione vera, va messa **fuori dal sito**: i file servono dal
  server, e `form-action 'none'` nella CSP impedisce al form di inviare
  qualcosa. Le opzioni realistiche sono togliere `MEDPHYS_EN[slug]` dal dato
  pubblicato, oppure servire quella pagina da un percorso con autenticazione
  (basic auth del server, o un proxy che chieda le credenziali).

---

## 6. Aggiungere una nuova scheda / sezione

Ci sono **cinque scenari**, dal più semplice al più invasivo.

---

### 6.1 Scenario A — Nuova scheda che riusa un renderer esistente

Il caso più comune: una nuova scheda di pubblicazione, un nuovo gruppo di persone,
una nuova scheda di progetto. **Non serve toccare `app.js`.**

Esempio: creare `#/awards`.

| Passo | Azione |
|---|---|
| 1 | Copia in `site-data.js` il blocco `awards: [ … ]` con gli elementi (`slug`, `img`, `title`, `desc`, `url`) |
| 2 | Aggiungi la voce in `nav` (§6.2) |
| 3 | Se vuoi una anteprima in home, aggiungi la sezione in `renderHome()` (`app.js:134`) |
| 4 | Per la pagina di dettaglio, o usi `renderBase` (aggiungi lo slug in `MEDPHYS_EN`) oppure aggiungi `findAward()` + `renderAward()` (§6.4) |

Verifica: hard refresh, apri `#/awards`, controlla breadcrumb e link di ritorno.

---

### 6.2 Scenario B — Nuova voce di menu che punta a una pagina generica

Per una pagina "semplicemente lunga" (testo, immagini, tabelle, video) servono
**3 modifiche, tutte in file di dati**:

```text
1) assets/data/site-data.js  →  array "nav": aggiungi la voce
2) assets/data/pages_en.js   →  window.MEDPHYS_EN["nuova-pagina"] = "<p>…</p>"
3) assets/data/pages_en.js   →  window.MEDPHYS_META["nuova-pagina"] = { "title": "…", "link": "", "fn": "" }
   (facoltativo) assets/data/i18n.js → window.MEDPHYS_IT["nuova-pagina"] = "<p>…</p>"
```

La voce di menu, forma semplice (link diretto):

```json
{ "route": "nuova-pagina", "en": "New page", "it": "Nuova pagina" }
```

La voce di menu, forma con **sottovoci** (menu a tendina):

```json
{
  "route": "sezione",
  "en": "Section",
  "it": "Sezione",
  "children": [
    { "route": "pagina-1", "en": "Page 1", "it": "Pagina 1" },
    { "route": "pagina-2", "en": "Page 2", "it": "Pagina 2" }
  ]
}
```

Note:

- `route` = lo **slug** che segue `#/`. Deve combaciare con la chiave in
  `MEDPHYS_EN`/`MEDPHYS_IT`.
- La voce padre rimane comunque cliccabile e porta a `#/<route-padre>`
  (deve esistere anche quella pagina, altrimenti 404).
- La voce viene evidenziata automaticamente se `route` (o uno dei `children`)
  è uguale alla rotta corrente (`app.js:42`).
- Il footer riceve automaticamente anche le voci di primo livello (`app.js:62`).

Verifica: la nuova voce compare in header **e** in footer, la pagina si apre, il
menu è evidenziato, e le sottovoci funzionano sia in desktop (hover) sia in
mobile (sotto 960 px il dropdown diventa lista statica).

---

### 6.3 Scenario C — Nuova sezione in home

In `renderHome()` (`app.js:91-135`), la sequenza è:

```js
return hero + research + people + pubs + challenges + projects + news;
```

Aggiungi il tuo blocco e inseriscilo nella stringa:

```js
var awards = sectionWrap("awards-preview", "awards", /* … */, "alt");
return hero + research + people + pubs + challenges + projects + awards + news;
```

`sectionWrap(id, titleKey, inner, cls)` (`app.js:137`):

| Parametro | Significato |
|---|---|
| `id` | id HTML della `<section>` (ancora, utile per i link) |
| `titleKey` | chiave in `SITE.sections` per il titolo (aggiungila in `sections`) |
| `inner` | HTML interno (usa `.grid.cols-2/3/4` + `.card`, o `.grid` + `.person`) |
| `cls` | `""`, `"alt"` (sfondo alternato) o `"dark"` (sezione scura) |

Esempio minimo, riusando una griglia:

```js
var awards = sectionWrap("awards", "awards",
  '<div class="grid cols-3">' + (SITE.awards || []).map(function (a) {
    return '<a class="card" href="#/' + a.slug + '"><div class="thumb contain"><img src="' + a.img + '" alt=""></div>' +
      '<div class="body"><h3>' + t(a.title) + "</h3><p>" + t(a.desc) + "</p></div></a>";
  }).join("") + "</div>", "alt");
```

Aggiungi anche `"awards": { "en": "Awards", "it": "Premi" }` in `SITE.sections`.

Verifica: la sezione appare tra projects e newsroom, con lo sfondo giusto e la
sponsione del menu non rotta.

---

### 6.4 Scenario D — Nuova pagina con struttura dedicata

Serve quando la pagina ha bisogno di tabelle, filtri, sidebar, dati propri.
**Qui si tocca `app.js`.** Procedura in 5 passi:

1. **Dati** — aggiungi il blocco in `site-data.js` (es. `SITE.awards`).
2. **Funzione di rendering** — copia lo scheletro di una funzione esistente.
   Il modello più adatto è `renderChallenge()` (`app.js:237`):

```js
function renderAwards(slug) {
  var a = (SITE.awards || []).filter(function (x) { return x.slug === slug; })[0];
  if (!a) return notFound();
  return pageHero(t(a.title), t(a.desc), '<a href="#/awards">' + t(SITE.sections.awards) + "</a>") +
    '<section class="section"><div class="container"><div class="detail-layout"><div>' +
    '<div class="prose"><p>' + t(a.body) + "</p></div>" +
    '<aside class="aside-card"><h3>' + t({ en: "Details", it: "Dettagli" }) + "</h3><dl>" +
    "<dt>Year</dt><dd>" + a.year + "</dd></dl></aside></div></div></section>";
}
```

   Blocchi riutilizzabili: `pageHero(title, sub, crumb)` (`:155`),
   `sectionWrap(...)` (`:137`), `t({en,it})` (`:12`), `notFound()` (`:300`),
   `.detail-layout` + `.aside-card` per il layout a due colonne.

3. **Indice** — una funzione `renderAwardsIndex()` con `.grid.cols-3` e `.card`,
   se vuoi una pagina di elenco separata da `#/<slug>`.

4. **Router** — inserisci i casi **prima** di `renderBase`, nel punto giusto
   della cascata (`app.js:311`):

```js
else if (r === "awards") html = renderAwardsIndex();
else if (findAward(r)) { html = renderAwards(r); title = t(findAward(r).title); }
```

   + l'helper `findAward(slug)` accanto agli altri `find*` (`app.js:19-23`).

5. **Menu** — aggiungi la voce in `SITE.nav` (§6.2).

Attenzione all'**ordine della cascata**: i casi `if/else` sono valutati in
sequenza, quindi i confronti generici (`findResearch`, `findPerson`, …) vengono
prima di quelli espliciti. Due slug non possono coincidere, e uno slug generico
non deve "rubare" la rotta di una sezione.

---

### 6.5 Scenario E — Nuova scheda in una sezione a griglia (persone, progetti, sfide, pubblicazioni)

Per "aggiungere una scheda" nel senso di **card/voce** dentro una sezione esistente:

| Sezione | File | Blocco | Chiavi minime |
|---|---|---|---|
| Persone | `site-data.js` | `people` (o `collaborators`) | `slug`, `img`, `keywords`, `bio`, `email` |
| Progetti | `site-data.js` | `projects.ongoing` / `projects.past` | `slug`, `img`, `title`, `duration`, `abstract` |
| Sfide | `site-data.js` | `challenges` | `slug`, `img`, `title`, `desc`, `url` |
| Categorie di pubblicazioni | `site-data.js` | `publications` | `slug`, `en`, `it`, `desc` |
| Articoli | `pages_en.js` | `MEDPHYS_EN["<categoria>"]` | HTML |
| Tesi | `site-data.js` | `join_us.theses` | `t`, `s` |
| Corsi | `site-data.js` | `courses.items` | `en`, `it` |
| Notizie | `site-data.js` | `newsroom` | `name`, `img`, `url` |

In tutti i casi: **slug univoco** (nessuna duplicazione, altrimenti la rotta va
alla prima occorrenza) e **immagine prima del riferimento**.

---

### 6.6 Checklist di verifica (da eseguire a ogni modifica)

1. Aprire la console del browser (F12): nessun errore rosso.
2. Hard refresh (`Ctrl+F5` / `Cmd+Shift+R`).
3. Controllare la rotta diretta: digitare l'hash nell'indirizzo e verificare che
   non compaia la pagina 404.
4. Verificare che la voce di menu esista **sia** in header **sia** in footer.
5. Verificare entrambe le lingue (pulsanti EN/IT in alto a destra): i testi
   brevi devono cambiare, e i testi senza `it` devono mostrare l'inglese.
6. Verificare il ritorno dalla pagina di dettaglio (breadcrumb e/o back).
7. Controllare la console per immagini rotte (tab *Network*, filtro *Img*).
8. Controllare il sito a 380 px di larghezza (menu hamburger attivo).

---

## 7. Personalizzazione grafica

### 7.1 Cambiare i colori
Solo `style.css:1-19`. Per esempio un blu istituzionale:

```css
--brand:#004481; --brand-2:#0e7490; --brand-ink:#083344;
```

### 7.2 Larghezza e tipografia
```css
--maxw:1180px;   /* larghezza massima del contenuto */
--sans: "Segoe UI", system-ui, …;
```

### 7.3 Classi CSS disponibili per i contenuti HTML

| Classe | Effetto |
|---|---|
| `.container` | centratura con larghezza massima |
| `.section` / `.section.alt` / `.section.dark` | sezione con padding / sfondo alternato / sfondo scuro |
| `.section-head` (+ `.eyebrow`, `h2`, `p`) | occhiello + titolo con sottolineatura ambra |
| `.grid.cols-2/.cols-3/.cols-4` | griglia responsive |
| `.card` (+ `.thumb`, `.thumb.contain`, `.body`, `.more`) | card con immagine, testo, link "leggi di più" |
| `.person` (+ `.ph`, `.pb`) | card persona quadrata |
| `.prose` | contenuto HTML libero (stili di `h2/h3/ul/table/blockquote/img`) |
| `.detail-layout` + `.aside-card` | due colonne: contenuto + sidebar |
| `.tag`, `.tags` | etichette colorate |
| `.notice` | riquadro avviso (giallo) |
| `.lock` | riquadro password |
| `.video-embed` | contenitore 16:9 per YouTube (`position:relative; padding-bottom:56.25%`) |
| `.figure-inline` | riquadro immagine con bordo arrotondato |
| `.crumbs-back` | link "torna indietro" (definito, non usato) |

### 7.4 I video YouTube (multimedia e altre pagine)

I video devono stare tre cose:

1. sull'host **`www.youtube-nocookie.com`** — `frame-src` nella CSP ammette solo
   quello, e `clean_content.py` riscrive automaticamente l'host con cookie;
2. con `sandbox` e `referrerpolicy` — li aggiunge il sanitizer, ma è bene
   scriverli già così nei dati, così il file è corretto anche senza passare da
   `app.js`;
3. dentro un `<div class="video-embed">`, altrimenti l'iframe si vede alla
   dimensione nativa 300×150.

La forma canonica, che il sanitizer accetta e lascia invariata:

```html
<div class="video-embed"><iframe src="https://www.youtube-nocookie.com/embed/ID"
  title="video" loading="lazy" allowfullscreen
  sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
  referrerpolicy="strict-origin-when-cross-origin"></iframe></div>
```

> Attenzione a `sandbox` + `allow-same-origin` insieme: la combinazione è
> necessaria qui perché YouTube non funziona senza, ed è sicura **solo** perché
> il contenuto caricato è di origine esterna (`youtube-nocookie.com`), non del
> nostro stesso dominio. Se un giorno si ospitasse video propri, non usare
> quell'attributo.

---

## 8. Diagnostica

| Sintomo | Causa quasi certa | Rimedio |
|---|---|---|
| Pagina interamente bianca | JSON non valido in un file di `assets/data/` (virgola o graffa mancante) | F12 → Console, trovare `SyntaxError`; riformattare con `Shift+Alt+F` e ricontrollare |
| Il sito mostra la versione vecchia | Cache degli script | Hard refresh `Ctrl+F5`; in alternativa aprire con Incognito |
| `#/…` porta alla pagina 404 | Lo slug non è in nessun array né in `MEDPHYS_EN`/`IT`/`ENX`, oppure è duplicato | Verificare che `route` nella `nav`, lo `slug` nei dati e la chiave in `MEDPHYS_EN` coincidano |
| Voce di menu evidenziata anche su un'altra pagina | Due `route` uguali, o una voce con `children` che contiene la rotta corrente | Controllare `app.js:42` |
| Traduzione italiana assente | Manca `it` nell'oggetto `{en,it}` | Aggiungerlo: `t()` ripiega su `en` (`app.js:12`) |
| Immagine non mostrata | Percorso errato o file assente | I percorsi sono relativi alla root: `assets/img/…`; verificare che il file esista |
| Testo in italiano non disponibile su una pagina lunga | Manca la voce in `MEDPHYS_IT` | Aggiungerla in `i18n.js` con lo stesso slug |
| Le formule matematiche appaiono come codice | Non c'è un renderer LaTeX | Aggiornare il testo in parole semplici, oppure caricare KaTeX/MathJax in `index.html` |
| Il copyright ha l'anno sbagliato | Non dovrebbe succedere: è automatico | Verificare che il sistema abbia la data giusta |
| Password accettata/non accettata | Il form è cosmetico: chiama `preventDefault()` e non confronta nulla | Non è un problema: per una protezione vera serve il server (§5.10) |
| La pagina resta bianca con un avviso in console | `MedPhysSanitize` non è definito: `sanitize.js` non è stato caricato | Controllare che `sanitize.js` venga prima di `app.js` in `index.html` (§2.1) |
| Un video YouTube non si vede | L'iframe non è su `youtube-nocookie.com`, quindi la CSP lo blocca | Riscrivere l'host come in §7.4 |
| Un'immagine non si vede solo in produzione | Il file è in `assets/` ma non è nella lista di copia del workflow | Aggiungerlo al passo *Assemble the published directory* (§2.11) |

---

## 9. Deploy

Il sito è pronto per qualsiasi server statico: basta caricare **tutta** la
cartella (non solo `index.html`).

- **GitHub Pages**: il workflow `.github/workflows/pages.yml` pubblica
  automaticamente a ogni push su `main` (o manualmente da *Actions*).
  Serve aver abilitato *Settings → Pages → Source: GitHub Actions*.
  Viene pubblicata la directory `_site/`, non il repository (§2.11).
- **Apache / Nginx / host INFN**: copia in una directory pubblica
  (`/var/www/html/medphys/`) **solo** `index.html`, `assets/`, `robots.txt`,
  `.well-known/`. Permessi tipici: `chmod 644` sui file, `755` sulle cartelle.
  **Aggiungi gli header di sicurezza**: su Apache, per esempio

  ```apache
  Header always set X-Content-Type-Options "nosniff"
  Header always set Referrer-Policy "strict-origin-when-cross-origin"
  Header always set Content-Security-Policy "frame-ancestors 'none'"
  ```

  Su GitHub Pages gli header custom non sono disponibili, quindi l'ultimo si
  può solo ottenere altrove (§2.1b).
- **Anteprima locale**: doppio clic su `index.html`, oppure
  `python -m http.server 8000` e poi `http://localhost:8000`.

Prima di pubblicare: hard refresh, controllo su entrambe le lingue, verifica delle
immagini (tab *Network*), controllo a 380 px e a 1440 px di larghezza, e prova
delle rotte dirette (`#/brain`, `#/people`, `#/join-us`, …).

---

## 10. Glossario

| Termine | Significato in questo progetto |
|---|---|
| **slug** | Identificativo breve di una voce: la parte di `#/` che segue il cancelletto. Deve essere univoco |
| **scheda** | Una voce cliccabile di un elenco (persona, progetto, sfida, pubblicazione, notizia) |
| **rotta** | L'hash `#/slug`, gestito da `render()` |
| **renderer** | Funzione in `app.js` che produce l'HTML di un tipo di pagina |
| **globali** | Variabili window create dai file in `assets/data` e lette da `app.js` |
| **bilinguale** | Oggetto `{"en": …, "it": …}` risolto da `t()` |
| **hard-coded** | Testo scritto direttamente in `app.js`, non modificabile dai dati |