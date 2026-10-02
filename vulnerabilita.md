# Rapporto di Sicurezza — MedPhys Sito (Medical Physics & Complex Systems)

**Data analisi:** 02/10/2026
**Ambiente:** sito statico SPA (vanilla JS, hash router) pubblicato su GitHub Pages
**Metodologia:** revisione manuale del codice sorgente, walkthrough dei flussi di dati HTML/attributi, verifica dei tool di build, analisi della pipeline CI/CD e dei file pubblicati. Le evidenze "prima" sono citate da `git show HEAD:<file>`; le verifiche "dopo" sono riportate in coda al documento.
**Skill applicata:** `security-review` (OWASP Top 10 / CWE)

---

## 0. Sommario esecutivo

Il sito non ha back-end, database, autenticazione reale né dipendenze JavaScript di terze parti: la superficie d'attacco è quindi **limitata al DOM, alla pipeline di contenuti e alla CI/CD**.

Il problema principale non era uno XSS già presente nei dati, ma l'**assenza totale di codifica dell'output**: la funzione di escaping esisteva ma era un no-op, e l'intera pagina veniva assemblata come stringa HTML grezza e iniettata con `innerHTML`. Questo creava un **sink XSS sistemico e permanentemente aperto**: qualsiasi contenuto (o qualsiasi contributo/commit/PR) che introducesse markup attivo veniva eseguito per tutti i visitatori, senza alcuna CSP che lo contenesse.

Verificato inoltre che i dati allora pubblicati **non contenevano payload attivi** (`javascript:`, handler `on*=`, `<script>`, `data:text/html`): i vettori erano **strutturali/latent**, non sfruttati. Questo conta: il rischio era che il prossimo content-update (o un PR approvato da distratti) aprisse XSS senza accorgersene.

**Riepilogo severità e stato** *(stato al 02/10/2026, dopo la remediation)*

| # | Severità | Vulnerabilità | Stato |
|---|----------|---------------|-------|
| 1 | **CRITICA** | `esc()` è un no-op + rendering integralmente via `innerHTML` (stored/DOM XSS) | ✅ **RISOLTO** — `sanitize.js` con allow-list; `esc()` rimosso; un solo `innerHTML`, alimentato solo da codificato |
| 2 | **ALTA** | Injection in contesto attributo (breakout da virgolette) su URL/immagini/nomi | ✅ **RISOLTO** — `escapeAttr()` + `safeUrl()` su ogni attributo interpolato |
| 3 | **ALTA** | Nessuna Content-Security-Policy né header di sicurezza | ⚠️ **RISOLTO CON RISERVA** — CSP e referrer in `<meta>`; `frame-ancestors`/`X-Frame-Options` impossibili su GitHub Pages |
| 4 | **ALTA** | Path traversal / scrittura arbitraria di file in `tools/download_images.py` | ✅ **RISOLTO** — `unquote` prima di `basename`, `commonpath`, allow-list host |
| 5 | **ALTA** | Verifica TLS disabilitata nel downloader (MITM → file contraffatti) | ✅ **RISOLTO** — verifica del certificato riattivata, HTTPS obbligatorio |
| 6 | **ALTA** | Pipeline contenuti: HTML di terze parti importato con "pulizia" solo regex | ✅ **RISOLTO** — allow-list in `clean_content.py`; nessuna regex di escaping |
| 7 | **MEDIA-ALTA** | Deploy pubblica l'intero repository (documentazione interna, tool, path locali) | ✅ **RISOLTO** — il workflow compone e pubblica solo `_site/` |
| 8 | **MEDIA** | 11 iframe YouTube senza `sandbox`/`referrerpolicy`, su host con cookie | ✅ **RISOLTO** — `youtube-nocookie.com` + `sandbox` + `referrerpolicy` su tutti e 11 |
| 9 | **MEDIA** | 37 link esterni in chiaro `http://` + assenza di `rel="noreferrer"` | ✅ **RISOLTO** — tutti a `https://`, `rel="noopener noreferrer"` ovunque |
| 10 | **MEDIA** | "Protezione" delle pagine protette solo client-side (falsa barriera) | 📋 **DOCUMENTATO** — non risolvibile lato client; serve il server |
| 11 | **MEDIA** | Lookup non validizzati con hash utente → raggiungibilità della prototype chain | ✅ **RISOLTO** — `hasSlug()` e `isValidSlug()` su ogni lookup; anche le tabelle tag/classi del sanitizer usano `hasOwnProperty` |
| 12 | **MEDIA** | Azioni CI/CD pinnate a tag mutabili invece che a SHA | ✅ **RISOLTO** — 4 action a SHA completo + Dependabot |
| 13 | **BASSA** | Dati personali (email) pubblicati nel bundle — OSINT/GDPR | ⏳ **APERTO** — decisione editoriale del maintainer |
| 14 | **BASSA** | Assenza di `robots.txt`, `.nojekyll`, `security.txt`; nessun limite di dimensione nei download | ✅ **RISOLTO** — tutti presenti; downloader limitato a 20 MB per file |
| 15 | **INFO** | Nessuna dipendenza npm, nessun JS esterno → nessun vettore supply-chain lato browser | ✅ **CONFERMATO** — invariato: zero dipendenze, CSP `script-src 'self'` |

**Bilancio (15 finding):** 11 **risolti**, 1 **risolto con riserva** documentata (n. 3), 1 **documentato** come limite di architettura (n. 10), 1 **aperto** per decisione editoriale del maintainer (n. 13), 1 **confermato** e senza azione richiesta perché descrive un'assenza di rischio (n. 15). Nessun finding richiede un intervento urgente sul sito pubblicato.

---

## 1. CRITICA — Funzione di escaping inerte e rendering HTML grezzo (Stored/DOM XSS)

**CWE-79 / CWE-116 — Output Encoding non eseguita**

### ✅ Stato: RISOLTO

Creato `assets/js/sanitize.js` (`window.MedPhysSanitize`): allow-list di tag, attributi e classi, ricostruzione del markup da zero, codifica di `&` prima dell'analisi. `esc()` non esiste più; `app.js` espone `e()`, `a()`, `rich()`, `media()`, `link()` e ha **un solo** `innerHTML` (`app.js:455`), alimentato solo da output codificato.

### Evidenza (prima — `git show HEAD:assets/js/app.js`)

```js
13: function esc(s) { return String(s == null ? "" : s); }
```

La funzione era *chiamata* in 8 punti come se sanitizzasse, ma **non eseguiva alcuna codifica**: `String(x)` è un convertitore di tipo, non un encoder HTML.

Verifica eseguita:

```
esc("<img src=x onerror=alert(1)>")  ->  <img src=x onerror=alert(1)>
```

L'intero documento veniva quindi assemblato come stringa e iniettato:

```js
332: app.innerHTML = header(r) + '<main id="main">' + html + "</main>" + footer();
```

`html` proveniva da `renderBase()`, che iniettava il contenuto di `pages_en.js` **senza alcuna trasformazione**:

```js
28: return EN[slug] || "";
```

### Impatto

Qualsiasi contenuto con markup attivo — un `<img onerror=…>` in una pagina, un
campo di una scheda persona, una notizia — viene eseguito per **tutti** i
visitatori, in ogni rotta che contiene quel dato. Con 9 iframe e 37 URL esterni
gestiti come stringhe, il margine per un errore in un prossimo aggiornamento dei
contenuti era ampio, e non esisteva alcun controllo che lo intercettasse.

### Scenario di sfruttamento

Basta una riga in `assets/data/site-data.js`:

```js
{ "name": "Notizia", "img": "x\" onerror=\"alert(document.cookie)", "url": "https://…" }
```

Il valore finiva in `title="` e in `src="` senza codificare, chiudendo l'attributo.

### Rimedio applicato

| Prima | Dopo |
|---|---|
| `esc()` no-op | `S.escapeHtml()` / `S.escapeAttr()` (codifica `&` per prima, così `&lt;` non può essere rianimato) |
| HTML grezo → `innerHTML` | `S.sanitizeRichHtml()`: allow-list di tag (`ALLOWED_TAGS`), attributi e classi (`ALLOWED_CLASSES`), tag pericolosi rimossi **con il loro contenuto** (`DROP_SUBTREE_TAGS`) |
| confronto case-sensitive | nomi dei tag normalizzati in minuscolo, quindi `<ScRiPt>` non sfugge |
| nessun controllo in CI | `tools/security.test.cjs` + `tools/render.test.cjs` + `tools/test_import_pipeline.py` (44 + 9 + 25 test), eseguiti dal workflow prima della composizione di `_site/` |

Verificato che `app.js` non contenga più `function esc`, che `innerHTML` compaia
una sola volta e che il breakout da attributo sia coperto dai test
`escapeAttr escapes quotes so attribute values cannot break out` e
`sanitizeRichHtml cannot be broken out of with quotes inside attribute values`.

---

## 2. ALTA — Injection in contesto attributo (breakout da virgolette) su URL/immagini/nomi

**CWE-79 / CWE-116 — mancanza di codifica nel contesto attributo**

### ✅ Stato: RISOLTO

Ogni attributo interpolato passa da `S.escapeAttr()` e ogni URL da
`S.safeUrl(value, 'link' | 'media' | 'embed')`, che rifiuta `javascript:`,
`vbscript:`, `data:`, `file:` e i protocol-relative (`//evil.tld`).

### Evidenza (prima)

```js
126: return '<a class="news-item" href="' + n.url + '" target="_blank" rel="noopener" title="' + n.name + '"><img src="' + n.img + '" alt="' + n.name + '"></a>';
```

```js
32: return '<a href="' + url + '" target="_blank" rel="noopener">' + url + "</a>";
```

```js
241: '<div class="figure-inline"><img src="' + c.img + '" alt="" style="max-height:280px;…"></div>'
```

I valori provenivano dal dato (`n.url`, `n.img`, `n.name`, `c.img`) e finivano
in tre contesti diversi — attributo HTML, URL e contenuto — senza distinzione.

### Sorgente concreta del payload (non solo ipotetica)

Non serve un payload finto: `SITE.newsroom` contiene nomi di testate reali e
percorsi immagine. Un nome con un doppio apice (`l"Roma"`) o un percorso con
spazi e virgolette è sufficiente a rompere l'attributo e iniettare un handler.

### Rimedio applicato

- `S.escapeAttr()` in `a()`, applicato a ogni valore dentro un attributo.
- `S.safeUrl()` in `media()` e `link()`, con allow-list di schema per contesto:
  `link` ammette `https:`, `mailto:`, `tel:`, relative e ancore; `media` ammette
  `https:` e relative; `embed` **solo** `https://www.youtube-nocookie.com/embed/…`.
- Il valore di `title`/`alt` passa da `e()`.
- Test dedicato: un nome di testata con `"`, `'`, `<`, `>` viene renderizzato come
  testo, non come attributo.

---

## 3. ALTA — Nessuna Content-Security-Policy né header di sicurezza

**CWE-1021 / CWE-693 — protezione lato client assente**

### ⚠️ Stato: RISOLTO CON RISERVA

CSP e meta referrer inseriti in `index.html`; tutti gli stili e gestori inline
sono stati spostati in `style.css` e `app.js`, quindi la CSP è effettivamente
rispettata.

**Rischio residuo:** `frame-ancestors` e `X-Frame-Options` valgono solo come
header HTTP e GitHub Pages non permette header custom, quindi il sito resta
esposto al *clickjacking*. Se si ospita altrove, aggiungere
`Content-Security-Policy: frame-ancestors 'none'` lato server
(`manuale.md` §2.1b).

### Evidenza (prima)

`index.html` era 18 righe e non conteneva alcun meta di sicurezza. Di
conseguenza:

- **8 stili inline** in `app.js` (`style="max-height:280px;object-fit:contain;…"`), che una CSP con `style-src 'self'` avrebbe bloccato;
- **1 gestore inline** in `app.js`: `'<form onsubmit="return false">…'`, che una CSP con `script-src 'self'` avrebbe bloccato;
- nessun `X-Content-Type-Options`, nessun `Referrer-Policy`, nessuna restrizione su `frame-src`, `object-src`, `base-uri`.

In assenza di CSP, un eventuale XSS (finding 1) aveva carte blanche: poteva
caricare script esterni, inviare dati via `fetch`, cambiare la pagina.

### Rimedio applicato

```text
default-src 'self'; script-src 'self'; style-src 'self';
img-src 'self' data:; font-src 'self'; connect-src 'self';
frame-src https://www.youtube-nocookie.com; object-src 'none';
base-uri 'self'; form-action 'none'
```

più `<meta name="referrer" content="strict-origin-when-cross-origin">`.

Le conseguenze sono state gestite, non ignorate:

| Direttiva | Conseguenza | Come è stata risolta |
|---|---|---|
| `style-src 'self'` | 8 `style=""` bloccati | spostati in `assets/css/style.css` |
| `script-src 'self'` | `onsubmit="return false"` bloccato | `addEventListener` + `event.preventDefault()` (`app.js:533`) |
| `form-action 'none'` | il form non può inviare | coerente con la natura cosmetica del form (finding 10) |
| `frame-src` ristretto | solo `youtube-nocookie.com` | finding 8 |
| `object-src 'none'` | niente `<object>`/`<embed>` | il sanitizer li rimuove comunque |

Il commento in `index.html` (righe 9-11) documenta perché `frame-ancestors` e
`sandbox` sono assenti, così nessuno li aggiunge in `<meta>` credendo che
funzionino.

---

## 4. ALTA — Path traversal e scrittura arbitraria di file nel downloader

**CWE-22 / CWE-73 — external control of file name or path**

### ✅ Stato: RISOLTO

`destination_for()` applica `unquote()` **prima** di `basename()`, poi
`commonpath()` per imporre che la destinazione resti dentro la cartella immagini;
`ALLOWED_HOSTS` limita il download a un solo host e le credenziali nell'URL sono
rifiutate.

### Evidenza (prima — `git show HEAD:tools/download_images.py`)

```python
72: name = os.path.basename(urllib.parse.urlparse(u).path)
73: name = urllib.parse.unquote(name)
76: dest = os.path.join(OUT, name)
```

L'ordine delle due operazioni è il difetto: `basename()` viene applicato **prima**
di decodificare la percentual-escaping, quindi un nome come `..%2f..%2f..%2fevil.png`
diventa `../../../evil.png` **dopo** che il percorso è stato normalizzato. `basename`
aveva già "protetto" solo il caso banale; il `%2f` lo aggira.

A questo si aggiungevano:

```python
4: OUT = r'E:\MedPhys_Sito\assets\img'
5: os.makedirs(OUT, exist_ok=True)
```

eseguiti **all'importazione** (effetto collaterale: qualunque `import` creava
directory), e l'assenza di qualsiasi allow-list di host: la URL veniva da
`media.json` e dagli `src`/`srcset` degli HTML importati, quindi da contenuto
esterno non fidato.

### Impatto

Scrittura di file arbitrari fuori da `assets/img` (inclusi `.py`, `.json`,
`.html`, o file di configurazione del server), con permessi del processo, e
possibilità di sovrascrivere file esistenti. Combinato con il finding 5
(TLS disattivato), un attaccante in posizione di rete poteva pilotare sia
*quale* file scrivere sia *cosa* scrivere.

### Rimedio applicato

```python
name = os.path.basename(urllib.parse.unquote(urllib.parse.urlparse(u).path))
dest = os.path.normpath(os.path.join(IMG_DIR, name))
if os.path.commonpath([dest, IMG_DIR]) != IMG_DIR:
    raise ValueError(...)
```

- `ALLOWED_HOSTS = {"medphys.ba.infn.it"}` — ogni altro host è rifiutato prima di qualsiasi richiesta;
- `IMG_DIR` derivato da `__file__`, niente path assoluti;
- `os.makedirs` spostato dentro `main()`, quindi importare il modulo non scrive nulla;
- `main()` eseguito solo con `if __name__ == '__main__'`.

Verifica riproducibile:

```bash
python -m unittest tools.test_import_pipeline.DownloadImagesTest -v
```

I test esercitano davvero `absolute_url()` e `destination_for()` (non un grep sul
sorgente) e coprono: percorsi con `..`, `%2e%2e`, `..%2f`, `//`, backslash e
nomi con prefisso `..evil.png` (tutti devono restare confinati in `assets/img/`),
host con sottostringa o suffisso di quello consentito, credenziali nell'URL,
protocol-relative, redirect verso host fuori allow-list, `Content-Type` assente o
non-immagine, contenuto non coerente con l'estensione e scrittura atomica.

---

## 5. ALTA — Verifica TLS disabilitata (man-in-the-middle sulle risorse)

**CWE-295 — Improper Certificate Validation**

### ✅ Stato: RISOLTO

Verifica del certificato riattivata (il contesto che la disattivava è stato
rimosso), `https` obbligatorio, timeout e `Content-Type` controllato.

### Evidenza (prima)

```python
7: ctx = ssl.create_default_context()
8: ctx.check_hostname = False
9: ctx.verify_mode = ssl.CERT_NONE
...
   with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
```

`check_hostname = False` **e** `verify_mode = CERT_NONE` insieme: la connessione
era cifrata ma non autenticata, quindi qualunque host intermedio poteva
sostituirsi al server e servire contenuto arbitrario.

### Impatto

Le immagini scaricate diventavano file di contenuto non verificato, che il sito
pubblica come proprie: un'immagine sostituita è un vettore di phishing visivo
(marca del gruppo, loghi di testate) o, se pubblicata con `Content-Type`
attaccato, un problema più serio. Lo stesso canale permetteva di servire
`media.json` contraffatto, e quindi di pilotare il finding 4.

### Rimedio applicato

- rimosso il contesto custom: si usa il default di `urllib`, che verifica
  hostname e certificato;
- `https` obbligatorio: `http://` rifiutato prima della richiesta;
- `ALLOWED_HOSTS` come difesa aggiuntiva (indipendente dalla TLS).

Il certificato scaduto di `medphys.ba.infn.it` segnalato dai controlli esterni è
un problema del server remoto, non del codice: va risolto dall'amministratore
del sito (cfr. finding 9, "da verificare").

---

## 6. ALTA — Pipeline dei contenuti: HTML di terze parti importato con "pulizia" solo regex

**CWE-20 / CWE-184 — sanitizzazione incompleta**

### ✅ Stato: RISOLTO

`clean_content.py` non usa più regex di escaping: applica un allow-list di
tag/attributi, `html.escape` sui valori, `safe_url()` sugli URL e riscrive
YouTube su `nocookie` **preservando** i video. Gli stessi generatori
(`build_site_data.py`, `build_i18n.py`, `gen_en.py`) serializzano in JS sicuro
(`<`, `>`, `&`, U+2028/U+2029) e scrivono solo se eseguiti esplicitamente.

### Flusso dati

```
%TEMP%\mp (JSON + HTML di WordPress)  →  download_images.py  →  assets/img/
                                     →  clean_content.py    →  pages_en.json
                                     →  gen_en.py           →  pages_en.js
```

### Evidenza (prima — `git show HEAD:tools/clean_content.py`)

```python
40: body = re.sub(r'<style.*?</style>', '', body, flags=re.S | re.I)
42: body = re.sub(r'<span[^>]*class="mce_SELRES[^"]*"[^>]*>.*?</span>', '', body, flags=re.S | re.I)
45: body = re.sub(r'<img[^>]*>', img_rewrite, body, flags=re.I)
53: body = re.sub(r'<iframe.*?</iframe>', iframe, body, flags=re.S | re.I)
```

La strategia era **blacklist + regex**, cioè enumerare ciò che non si vuole. È
la strategia che non regge: basta una variante non prevista perché il payload
passi.

I due esempi più concreti:

```python
14: body = re.sub(r'<!--.*?-->', '', txt, flags=re.S)
```

- `.` in Python non corrisponde al newline **senza** `re.S`: nessuno dei due
  `re.sub` sui commenti poteva funzionare su HTML multilinea. Erano no-op
  silenziosi, cioè code che sembravano proteggere e non proteggevano.

```python
45: body = re.sub(r'<img[^>]*>', img_rewrite, body, flags=re.I)
```

- `<img[^>]*>` si ferma al primo `>`: un `alt="a > b"` (o un `src` con `>`)
  tronca il tag e lascia il resto come testo HTML, che viene poi interpolato.

E il caso più grave, sui video:

```python
50: if src and 'youtube.com/embed' in src.group(1):
51:     return f'<div class="video-embed"><iframe src="{src.group(1)}" …></iframe></div>'
```

- il test è una **sottostringa** (`'youtube.com/embed' in …`), non un confronto
  dell'host: `https://evil.tld/?x=youtube.com/embed` lo soddisfa e l'iframe
  finirebbe su un host arbitrario con `sandbox` assente;
- `src.group(1)` è ricostruito senza escaping, quindi un `src` con doppio apice
  rompeva l'attributo.

### Rimedio applicato

- allow-list di tag e attributi, con `html.escape` sui valori;
- `safe_url()` al posto dei confronti per sottostringa: `embed` accetta **solo**
  `https://www.youtube-nocookie.com/embed/<id>` con id validato
  (`[A-Za-z0-9_-]{6,24}`);
- l'host con cookie viene **riscritto** su `nocookie` invece di essere scartato:
  altrimenti il prossimo rigeneramento avrebbe perso tutti i video;
- `sandbox` e `referrerpolicy` aggiunti in fase di import, così il dato è corretto
  anche prima di passare dal sanitizer;
- `build_site_data.py` promuove `http://` a `https://` via `safe_url()` invece di
  ripubblicare URL in chiaro, e segnala a terminale ciò che scarta.

---

## 7. MEDIA-ALTA — Il deploy pubblica l'intero repository

**CWE-200 / CWE-538 — informazioni sensibili nell'artefatto pubblicato**

### ✅ Stato: RISOLTO

Il workflow compone `_site/` con una copia esplicita di `index.html`, `assets/`,
`robots.txt` e `.well-known/`, aggiunge `.nojekyll` e verifica con un controllo
negativo che `tools/`, `.github/` e i documenti interni non siano presenti.
`_site/` è in `.gitignore`.

### Evidenza (prima — `git show HEAD:.github/workflows/pages.yml`)

```yaml
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: "."
```

`path: "."` pubblicava **tutto** il checkout.

### Impatto

Finivano in produzione, indicizzabili e scaricabili:

- `manuale.md`, `README.md`, `nuovo_sito.md`, `vulnerabilita.md` — documentazione interna, inclusa la topologia dei tool e le procedure di aggiornamento;
- `tools/*.py` — il codice che scarica e processa il sito, con i dettagli di come il deployment è costruito;
- `.github/workflows/pages.yml` — la pipeline di deploy.

Nessun segreto (il repository non contiene chiavi), ma il valore è di
*informazione*: chi legge i tool sa esattamente come il sito viene generato e da
dove arrivano i dati.

### Rimedio applicato

Un passo *Assemble the published directory* copia solo ciò che serve e poi
fallisce esplicitamente se trova un file interno:

```yaml
      - name: Assemble the published directory
        run: |
          mkdir -p _site/.well-known
          cp index.html robots.txt _site/
          cp -r assets _site/
          cp .well-known/security.txt _site/.well-known/
          touch _site/.nojekyll
          if find _site -name '*.md' -o -name '*.py' | grep -q .; then
            echo 'internal files leaked into the publish directory'; exit 1
          fi
```

Verificato su una build locale: 263 file, tutte le risorse presenti, nessun
file interno.

---

## 8. MEDIA — iframe di terze parti senza sandbox, referrer policy o consenso

**CWE-1021 — iframe non isolato**

### ✅ Stato: RISOLTO

Tutti gli **11** iframe (9 in `pages_en.js`, 2 in `i18n.js`) sono su
`www.youtube-nocookie.com` con `sandbox` e `referrerpolicy`. La CSP ammette
quell'host in `frame-src`, quindi i video continuano a funzionare.

### Evidenza (prima)

```html
<iframe src="https://www.youtube.com/embed/ID" title="video" loading="lazy" allowfullscreen></iframe>
```

Conteggio verificato sui dati originali: 9 iframe in `pages_en.js` e 2 in
`i18n.js`, **0** con `sandbox`, **0** su `nocookie`, **11** su host con cookie.

### Impatto

- **Nessun `sandbox`**: il frame ha il pieno potere nella sua origine. Se il
  contenuto di YouTube o un redirect di terze parti ospitasse markup attivo, non
  c'è confine che lo trattenga.
- **Host con cookie**: `youtube.com` deposita cookie identificativi **prima**
  dell'interazione dell'utente, quindi senza alcun consenso — un problema GDPR
  documentabile.
- **Nessun `referrerpolicy`**: l'URL completo della pagina (incluso lo slug della
  rotta) veniva inviato a Google come referrer.

### Rimedio applicato

```html
<iframe src="https://www.youtube-nocookie.com/embed/ID" title="video" loading="lazy"
  allowfullscreen sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"
  referrerpolicy="strict-origin-when-cross-origin"></iframe>
```

- `youtube-nocookie.com` non imposta cookie finché l'utente non interagisce col
  player: il consenso diventa implicito invece che anticipato;
- il sanitizer riscrive comunque su `nocookie` e *aggiunge* `sandbox` e
  `referrerpolicy` a runtime, quindi il dato non deve essere perfetto per essere
  sicuro;
- la CSP blocca qualunque altro host in `frame-src`.

`sandbox` + `allow-same-origin` è una combinazione da usare con caution: qui è
accettabile perché il contenuto caricato è di origine esterna
(`youtube-nocookie.com`), non del nostro dominio. Il vincolo è documentato in
`manuale.md` §7.4.

---

## 9. MEDIA — Link esterni in chiaro e assenza di `rel="noreferrer"`

**CWE-319 — Cleartext Transmission of Sensitive Information**

### ✅ Stato: RISOLTO

37 URL `http://` portati a `https://` (18 in `site-data.js`, 19 in
`pages_en.js`) e `rel="noopener noreferrer"` su ogni link con `target="_blank"`.

### Evidenza (prima)

```js
32: return '<a href="' + url + '" target="_blank" rel="noopener">' + url + "</a>";
78: '<li><a href="https://www.uniba.it" target="_blank" rel="noopener">University of Bari</a></li>' +
```

5 occorrenze di `rel="noopener"`, 0 di `noreferrer`.

### Impatto

- **Cleartext**: 37 URL su `http://`. Il visitatore che clicca subisce un
  redirect che chi può osservare la rete può re-dirigere (hijacking su rete
  avversaria, captive portal, proxy aziendali);
- **`rel="noopener"` senza `noreferrer`**: `noopener` impedisce il
  window.opening, ma il **referrer completo** (URL della pagina, slug della
  rotta) viene comunque inviato al sito esterno. Con `noreferrer` non viene
  inviato nulla.

### Rimedio applicato

- `http://` → `https://` sui 37 URL, applicato **come dato** e non come regex sul
  sorgente, così il file resta JSON valido e il risultato è verificabile;
- `safe_url()` nel generatore, che promuove `http` a `https` e scarta ciò che non
  è ammesso, segnalandolo a terminale;
- `rel="noopener noreferrer"` su tutti i link con `target="_blank"`.

**Da verificare (non risolto):** tre link esterni non hanno risposto ai controlli
automatici — `ipanproject.eu` non risolve (NXDOMAIN), `chiefobserver.com` chiude
la connessione, e il certificato di `medphys.ba.infn.it` risulta scaduto. Non è
dimostrato che siano morti: vanno aperti da un browser e, se necessario,
sostituiti. La promozione a HTTPS è comunque corretta come default.

---

## 10. MEDIA — "Protezione" delle pagine riservate solo lato client

**CWE-602 — Client-Side Enforcement of Server-Side Security**

### 📋 Stato: DOCUMENTATO (limite di architettura)

Non risolvibile lato client: il form chiama `preventDefault()` e non confronta
nulla, quindi è dichiaratamente cosmetico. La CSP ora vieta comunque l'invio
(`form-action 'none'`). La soluzione reale richiede il server ed è descritta in
`manuale.md` §5.10.

### Evidenza (prima)

```js
284: '<form onsubmit="return false"><label>' + t({ en: "Password", it: "Password" }) + '</label>'
```

nessun `if`, nessun confronto, nessuna chiamata di rete: il form non fa nulla e
il blocco compare comunque a tutti.

### Rischio

Il contenuto delle pagine protette (`short-course`, `conference-slides`,
`pattern_recognition`) è in `MEDPHYS_EN`, cioè **scaricabile dal browser** da
chiunque. Chi visita la pagina vede il form; chi apre i sorgenti vede il
contenuto.

### Rimedio applicato

Documentato, non risolto: è il punto in cui la sicurezza dipende dall'infrastruttura.

1. **Se il contenuto non deve essere pubblico**: rimuoverlo da `MEDPHYS_EN` e
   non pubblicarlo affatto;
2. **Se deve essere riservato ma pubblicabile**: servire quella rotta da un
   percorso con autenticazione (basic auth del server, o un proxy che chieda
   le credenziali), mantenendo nel bundle solo il testo del form.

Fino a quando non si sceglie una delle due strade, `SITE.protected` non deve
contenere dati riservati. La documentazione lo dice esplicitamente, perché il
pericolo di questo finding è proprio che l'etichetta "protetta" faccia
credere il contrario.

---

## 11. MEDIA — Lookup non validizzati con input utente e raggiungibilità della prototype chain

**CWE-1321 — Prototype Pollution / lookup non validato**

### ✅ Stato: RISOLTO

`sanitize.js` espone `hasSlug()` (accesso a dizionari senza ereditare dalla
prototype chain) e `isValidSlug()` (`^[a-z0-9]+([-_][a-z0-9]+)*$`, lunghezza
massima 200, slug riservati esclusi). `app.js` li usa in ogni lookup e in
`routeSlug()`.

### Evidenza (prima)

```js
306: function routeSlug() {
307:   var h = location.hash.replace(/^#\/?/, "").split("?")[0];
308:   return h || "home";
309: }
...
28: return EN[slug] || "";
329: else if (EN[r] || IT[r] || ENX[r]) { html = renderBase(r); … }
```

Lo slug proveniva da `location.hash` e veniva usato direttamente come chiave in
`EN`, `IT`, `ENX` e `META`, senza validazione né controllo di proprietà.

### Impatto

Con `#/__proto__`, `#/constructor` o `#/toString` il lookup non restituiva
`undefined` ma un valore ereditato dalla prototype chain:

- `EN["constructor"]` → la funzione `Object`, che è truthy: la rotta veniva
  trattata come esistente e `renderBase()` riceveva una **funzione** al posto
  della stringa di contenuto, finirla nell'`innerHTML` come `function Object() { [native code] }`;
- `META["toString"].title` → `undefined`, con `document.title` degradato a
  `undefined — Brand`.

Non porta a esecuzione di codice da solo, ma trasforma un input utente in una
lettura arbitraria della prototype chain, ed è il tipico preludio a bypass dei
guard aggiunti in seguito (`if (hasOwnProperty(...))` non è sufficiente se il
valore è un oggetto ereditato).

### Rimedio applicato

```js
var SLUG_RE = /^[a-z0-9]+(?:[-_][a-z0-9]+)*$/;
var SLUG_MAX_LENGTH = 200;
var RESERVED_SLUGS = { "__proto__": 1, "constructor": 1, "prototype": 1, … };
```

- `isValidSlug()` applica regex, lunghezza massima e lista di slug riservati;
- `hasSlug(obj, k)` usa `Object.prototype.hasOwnProperty.call()`, quindi non
  eredita mai;
- `routeSlug()` respinge `#/__proto__` e mostra la 404 invece di renderizzare.

Il vincolo `SLUG_MAX_LENGTH = 200` preserva gli slug esistenti con `_`, incluso
`pattern_recognition`: la regex accetta `[-_]` come separatore.

---

## 12. MEDIA — Azioni CI/CD pinnate a tag mutabili

**CWE-829 — Inclusion of Functionality from Untrusted Control Sphere**

### ✅ Stato: RISOLTO

Tutte e 4 le action sono pinnate a un commit SHA completo, con il tag originale
in commento. `.github/dependabot.yml` le aggiorna ogni settimana, quindi il
pinning non crea debito.

### Evidenza (prima)

```yaml
uses: actions/checkout@v4
uses: actions/configure-pages@v5
uses: actions/upload-pages-artifact@v3
uses: actions/deploy-pages@v4
```

Un tag Git è un **ref mobile**: chi può spostarlo (per esempio un account
compromesso, o un maintainer che lo sposta per errore) cambia il codice che gira
con i permessi `pages: write` e `id-token: write` del workflow. Il checkout è il
caso più grave, perché esegue codice prima di ogni altro step.

### Rimedio applicato

```yaml
uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262 # v4
uses: actions/configure-pages@983d7736d9b0ae728b81ab479565c72886d7745b # v5
uses: actions/upload-pages-artifact@56afc609e74202658d3ffba0e8f6dda462b719fa # v3
uses: actions/deploy-pages@d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e # v4
```

SHA verificati come commit tagger esistenti. Aggiunto
`.github/dependabot.yml` con `package-ecosystem: github-actions`, schedule
settimanale, così l'aggiornamento resta automatico e il pinning non crea un
lavoro manuale.

---

## 13. BASSA — Dati personali pubblicati nel bundle (OSINT / GDPR)

**CWE-359 / CWE-200 — esposizione di PII**

### ⏳ Stato: APERTO — decisione del maintainer

Gli indirizzi sono utili (il sito è di un gruppo di ricerca pubblico) ma
pubblicati sono anche scrapabili. La rimozione è una scelta editoriale, non
tecnica, e non è stata applicata unilateralmente.

### Evidenza

`SITE.emails` in `site-data.js` e il campo `"email"` in ogni voce di `people` e
`collaborators`: indirizzi `uniba.it` e `ba.infn.it` di 26 persone, più
indirizzi di ruolo.

### Impatto

Raccolta automatizzata di indirizzi istituzionali, associabili a nominativi e a
indirizzi IP tramite i log del server di hosting. Per indirizzi
*istituzionali* di un gruppo di ricerca pubblico il rischio è basso, ed è il
motivo per cui la rimozione non è stata fatta senza conferma.

### Rimedio

Se si decide di rimuoverli o sostituirli:

- i campi sono `"email"` in `people`/`collaborators` e `SITE.emails` in `site-data.js`;
- `app.js` mostra già l'indirizzo solo se presente (`:footer()` e `renderPerson()`), quindi la rimozione è pulita e non richiede modifiche al renderer;
- un'alternativa è un modulo di contatto, che scarica il mantenimento degli indirizzi dalla pagina pubblica.

---

## 14. BASSA — Hardening e gestione risorse mancanti

**CWE-400 / CWE-693 — configurazione e limiti di risorse**

### ✅ Stato: RISOLTO

Creati `robots.txt`, `.well-known/security.txt` e `.gitignore`; il workflow crea
`.nojekyll`. Il downloader ha un tetto di 20 MB per file, un timeout e il
controllo del `Content-Type`.

### Evidenza (prima)

Mancavano `robots.txt`, `.nojekyll` e `.well-known/security.txt`. Il downloader
scaricava a `urlopen(req, timeout=30)` senza alcun limite di dimensione: un
`Content-Length` enorme o uno streaming senza fine consumerebbe disco fino
all'esaurimento.

### Dettaglio: `.nojekyll`

Senza `.nojekyll`, GitHub Pages esegue Jekyll sui file pubblicati e ignora i
file che iniziano con `_`. Nessun asset attuale ne contiene, quindi il rischio
era latente: un file di tema o un `_config.yml` nel publish directory
scomparirebbe silenziosamente.

### Dettaglio: `security.txt`

```
Contact: https://github.com/MrBraun71/medical-physics/security/advisories/new
Expires: 2027-10-01T00:00:00.000Z
```

**Da verificare:** `security.txt` è utile solo se *Private vulnerability
reporting* è abilitato nelle impostazioni del repository; e la data `Expires` va
rinnovata almeno ogni anno, altrimenti il file va rimosso.

### Rimedio applicato

| Voce | Dove |
|---|---|
| tetto 20 MB, streaming a chunk da 64 KB, timeout, controllo `Content-Type` | `tools/download_images.py` |
| `robots.txt` (Allow /, Disallow `/tools/`, `/.github/`) | root |
| `.well-known/security.txt` (RFC 9116) | `.well-known/` |
| `_site/`, `__pycache__/`, JSON intermedi | `.gitignore` |
| `_site/.nojekyll` | passo *Assemble the published directory* |

---

## 15. INFO — Superficie pulita (nessuna vulnerabilità rilevata)

**Superficie supply-chain lato browser: vuota**

### ✅ Stato: CONFERMATO

Invariato: nessuna dipendenza npm, nessun JavaScript di terze parti, nessun
font esterno. La CSP `script-src 'self'` lo rende ora esplicitamente un
requisito, non solo una buona pratica.

### Evidenza

Nessun `package.json`, nessun lockfile, nessun `<script src>` verso un dominio
esterno: gli unici script sono 5 file locali (`site-data.js`, `pages_en.js`,
`i18n.js`, `sanitize.js`, `app.js`). Il CSS è un file locale senza `@import`
esterno, i font sono le family di sistema.

### Perché conta

Il modo più comune di introdurresupply-chain nel browser è una dipendenza o una
CDN. Qui la superficie è zero per costruzione, e ora lo è **anche per
imposizione**: se qualcuno aggiungesse uno script esterno, la CSP lo bloccherebbe
invece di eseguirelo. Il costo di questa difesa è nullo e il beneficio è
strutturale.

---

## Correzioni applicate, per priorità

| Priorità | Azione | File | Stato |
|---|---|---|---|
| P0 | Sanitizzazione runtime con allow-list | `assets/js/sanitize.js` (nuovo) | ✅ fatto |
| P0 | Validazione `src`/`href` con allow-list di schemi | `sanitize.js` + tutti i renderer di `app.js` | ✅ fatto |
| P0 | Rimozione di `onsubmit` inline e dei 8 `style=""` inline | `app.js:533`; `assets/css/style.css` | ✅ fatto |
| P0 | Traversal, allow-list host e TLS nel downloader | `tools/download_images.py` | ✅ fatto |
| P1 | CSP via `<meta>` + meta referrer | `index.html:12-13` | ✅ fatto |
| P1 | Deploy limitato a una directory di pubblicazione con verifica | `.github/workflows/pages.yml` | ✅ fatto |
| P1 | `rel="noopener noreferrer"` + migrazione a `https://` (37 URL) | `assets/data/*.js` | ✅ fatto |
| P1 | `sandbox`/`referrerpolicy`/`youtube-nocookie` (11 iframe) | `assets/data/pages_en.js`, `i18n.js`, `clean_content.py` | ✅ fatto |
| P2 | Allow-list slug e guard sui lookup | `sanitize.js` + `app.js` | ✅ fatto |
| P2 | Action pinnate a SHA + Dependabot | `pages.yml`, `.github/dependabot.yml` | ✅ fatto |
| P2 | Gate CI: nessun contenuto attivo nei dati | `pages.yml` (step `Security and render tests`) esegue `tools/security.test.cjs`, `tools/render.test.cjs` e `tools/test_import_pipeline.py` **prima** della composizione di `_site/` | ✅ fatto |
| P3 | `robots.txt`, `security.txt`, `.gitignore`, `.nojekyll` | root, `.well-known/`, `.gitignore` | ✅ fatto |
| P3 | Gestione errori di routing (niente pagina bianca) | `app.js:432-443` (`notFound()`, `renderError()`) | ✅ fatto |
| P3 | Decisione su email pubblicate | **decisione del maintainer** | ⏳ aperto |
| — | Protezione reale delle pagine riservate | lato server | 📋 fuori portata (finding 10) |

---

## Criteri di verifica (come riconfermare la chiusura)

```bat
REM 1. Nessun handler inline e nessuno stile inline residuo
findstr /S /N /C:"onsubmit=" /C:"onclick=" /C:"onload=" index.html assets\js\*.js
findstr /N /C:"style=\"" assets\js\app.js

REM 2. Nessun contenuto attivo nei dati
findstr /S /N /C:"javascript:" /C:"data:text/html" assets\data\*.js

REM 3. Nessuna funzione di escaping finta, un solo innerHTML
findstr /N /C:"function esc" assets\js\app.js
findstr /N /C:"innerHTML" assets\js\app.js

REM 4. Nessun URL in chiaro e tutti gli iframe protetti
findstr /S /N /C:"http://" assets\data\*.js
findstr /S /N /C:"<iframe" assets\data\*.js

REM 5. Suite di test (deve riportare zero fallimenti)
node --test --test-reporter=tap tools\security.test.cjs
node --test --test-reporter=tap tools\render.test.cjs
```

Risultati registrati il 02/10/2026:

| Comando | Esito |
|---|---|
| `node --test tools\security.test.cjs` | **44 pass, 0 fail** |
| `node --test tools\render.test.cjs` | **9 pass, 0 fail** |
| `findstr /C:"function esc" assets\js\app.js` | nessuna corrispondenza |
| `findstr /C:"innerHTML" assets\js\app.js` | 1 corrispondenza (`app.js:455`) |
| `findstr /S /C:"http://" assets\data\*.js` | 0 corrispondenze |
| `<iframe` senza `nocookie` | 0 su 11 |
| build locale `_site/` | 263 file, 0 file interni, tutte le risorse presenti |
| generatore vs dato pubblicato | 0 differenze semantiche (18 persone, 8 collaboratori, 37 notizie) |

Sul sito effettivamente servito, da eseguire dopo il primo deploy:

```bash
curl -sI https://<url>/manuale.md              # atteso 404
curl -sI https://<url>/tools/download_images.py # atteso 404
curl -sI https://<url>/.git/config             # atteso 404
curl -s https://<url>/ | grep -o 'Content-Security-Policy'
```

---

## Rischi residui

1. **Clickjacking** (finding 3): nessun header custom su GitHub Pages, quindi
   `frame-ancestors` non è applicabile. Rischio basso per un sito istituzionale
   non incastonato in una iframe di terze parti, ma va risolto se si migra su
   un hosting che permette header.
2. **Pagine "protette" solo lato client** (finding 10): limite architetturale,
   risolvibile solo lato server.
3. **Email pubblicate** (finding 13): in attesa di decisione editoriale.
4. **Link esterni non verificati** (finding 9): `ipanproject.eu` non risolve,
   `chiefobserver.com` chiude la connessione, il certificato di
   `medphys.ba.infn.it` è scaduto. Da aprire da un browser.
5. **Aggiornamento dei dati**: il percorso più probabile per reintrodurre XSS è
   una modifica a `assets/data/*.js` o ai generatori in `tools/`. I gate
   (`tools/security.test.cjs`, `tools/render.test.cjs`,
   `tools/test_import_pipeline.py`) sono la rete di sicurezza e il workflow li
   esegue prima di ogni deploy, ma restano da eseguire **prima** di ogni commit
   di contenuti, non solo in fase di audit.
6. **Allineamento delle allow-list**: `tools/clean_content.py` e
   `assets/js/sanitize.js` mantengono due elenchi di tag e classi separati.
   `test_generator_allowlist_matches_runtime` in
   `tools/test_import_pipeline.py` fallisce se divergono, ma la lista va
   aggiornata in entrambi i file quando se ne aggiunge uno.
7. **Rigenerare `pages_en.js` non è innocuo**: verificato che il generatore
   attuale, applicato alle 62 pagine pubblicate, non perde testo (62/62
   identiche) né tag strutturali (`iframe` 9, `img` 10, `a` 75, `strong` 149,
   `em` 158, `table` 2, `p` 594, `br` 90: invariati), ma **aggiunge** 9 wrapper
   `<div class="video-embed">` e 59 `target="_blank"` che i dati pubblicati non
   hanno. Sono cambiamenti voluti dal generatore, non regressioni, ma sono
   visibili: una rigenerazione va pubblicata come revisione a sé, non di
   sfuggita. Il testo del JSON più la serializzazione con escape diverge in
   byte dal file pubblicato, quindi i file `.js` pubblicati non vanno
   rigenerati senza un motivo esplicito.
8. **`assets/data/pages_en.json` era inutilizzabile**: il file era stato
   committato con i marcatori di conflitto Git (`<<<<<<<`, `=======`,
   `>>>>>>>`) e, una volta rimossi, risultava comunque privo della graffa di
   chiusura, quindi non era JSON valido: `tools/gen_en.py` non poteva funzionare
   (`json.load` sollevava `JSONDecodeError`). Ricostruito a partire da
   `assets/data/pages_en.js`, che è il dato autorevole già sanificato; il
   round-trip è semanticamente identico (stessi 62 slug, stessi valori, stessi
   metadati). `assets/data/meta.json` era integro e non è stato toccato.

---

*Fine rapporto. Analisi eseguita su base statica (sorgente, `git show HEAD:<file>`
per le evidenze originali, workflow e build locale). I punti marcati "da
verificare" richiedono conferma sull'artefatto effettivamente servito o su
impostazioni esterne al repository.*
