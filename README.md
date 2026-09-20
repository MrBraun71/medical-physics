# Sito Web Medical Physics and Complex Systems (INFN Bari & UniBa)

Sito web istituzionale statico e modulare a **pagine singole**, realizzato **senza l'uso di alcun plugin esterno**.

---

## Struttura dei File

```text
Medical Physics/
├── index.html                  # Home page
├── people.html                 # Staff, docenti, ricercatori e dottorandi
├── research.html               # 5 Linee di ricerca principali
├── projects.html               # Progetti finanziati (TEBAKA, PERSON, MAGIC-5, ReCaS)
├── publications.html           # Pubblicazioni con filtro di ricerca istantaneo vanilla
├── challenges.html             # Competizioni internazionali (DREAM Challenge, LUNA16)
├── courses.html                # Corsi didattici, short courses e seminari
├── conference-slides.html      # Tabella archivio slide e relazioni a congressi
├── multimedia.html             # Galleria multimediale HTML5 nativa
├── newsroom.html               # Bacheca avvisi, bandi e notizie
├── join-us.html                # Proposte tesi, posizioni aperte e contatti
│
├── assets/
│   ├── css/
│   │   └── style.css           # Foglio di stile CSS3 nativo (100% responsive, zero framework)
│   ├── js/
│   │   └── main.js             # Script vanilla per menu mobile e filtro pubblicazioni
│   ├── images/
│   │   ├── logo-infn.svg       # Logo vettoriale INFN Sezione di Bari
│   │   └── logo-uniba.svg      # Logo vettoriale Università degli Studi di Bari
│   └── docs/                   # Cartella per ospitare PDF di bandi, slide e dispense
│
├── nuovo_sito.md               # Documento di specifiche e analisi originale
└── README.md                   # Questa guida rapida
```

---

## Come Visualizzare il Sito in Locale

1. Non è necessario installare Node.js, PHP, database o server complessi.
2. Fai semplicemente **doppio clic su `index.html`** con un qualsiasi browser web (Google Chrome, Microsoft Edge, Mozilla Firefox, Apple Safari).
3. Il sito è completamente funzionante anche **offline** (senza connessione a Internet).

---

## Come Aggiornare i Contenuti (Manuale Operatore)

Tutte le pagine sono suddivise con commenti HTML espliciti che indicano con chiarezza dove iniziare e dove terminare le modifiche.

### 1. Inserire un nuovo membro dello staff (`people.html`)
Apri `people.html` con un editor di testo (es. Blocco Note, VS Code, Notepad++) e copia/incolla questo blocco nella sezione appropriata:

```html
<article class="person-card">
  <div class="person-avatar">NR</div>
  <div class="person-info">
    <h3 class="person-name">Dott. Nome Cognome</h3>
    <p class="person-role">Dottorando di Ricerca</p>
    <p class="person-email">✉ <a href="mailto:nome.cognome@uniba.it">nome.cognome@uniba.it</a></p>
    <p class="person-keywords">
      <strong>Aree di ricerca:</strong> Neuroimaging, Deep Learning, Brain Networks.
    </p>
  </div>
</article>
```

### 2. Aggiungere una pubblicazione (`publications.html`)
Apri `publications.html`, individua l'elenco `pub-list` e aggiungi:

```html
<li class="pub-item">
  <span class="pub-authors">Cognome N., Bellotti R., Tangaro S.</span>
  <span class="pub-title">"Titolo dell'articolo scientifico."</span>
  <span class="pub-journal">Nome Rivista Internazionale, Volume(Numero), Pagine, Anno.</span>
  <div>
    <a href="https://doi.org/10.xxxx/xxxx" target="_blank" rel="noopener" class="pub-doi-badge">DOI: 10.xxxx/xxxx</a>
  </div>
</li>
```

### 3. Pubblicare una nuova notizia (`newsroom.html`)
Apri `newsroom.html` e inserisci in cima:

```html
<article class="card">
  <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
    <span class="card-badge">Categoria Notizia</span>
    <time datetime="2026-10-01" style="font-size: 0.85rem; color: var(--color-text-muted); font-weight: 600;">1 Ottobre 2026</time>
  </div>
  <h2 class="card-title" style="font-size: 1.3rem;">Titolo della notizia o avviso</h2>
  <p class="card-text">
    Testo descrittivo dell'annuncio o bando...
  </p>
  <div style="margin-top: 14px;">
    <a href="assets/docs/allegato.pdf" class="btn btn-outline btn-sm">Scarica Allegato &rarr;</a>
  </div>
</article>
```

---

## Messa Online sul Server INFN

Il sito è pronto per essere distribuito su qualsiasi web server:
- **Server Linux / Apache / Nginx**: Caricare l'intero contenuto della cartella nella directory pubblica del web server (es. `/var/www/html/medphys/`).
- **GitLab Pages INFN**: È sufficiente committare i file nel branch principale di un repository GitLab con configurazione standard per siti statici.
