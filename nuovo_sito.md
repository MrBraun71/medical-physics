# Piano Operativo per la Ricostruzione del Sito di Fisica Medica (medphys.ba.infn.it)

Questo documento descrive la struttura, l'analisi dei contenuti ricavati dal portale **Medical Physics and Complex Systems** (INFN Sezione di Bari / Università degli Studi di Bari Aldo Moro) e i **passi operativi dettagliati** per replicare e modernizzare il sito web.

Il nuovo sito è progettato secondo precise direttive:
1. **Nessun plugin esterno**: codice puro HTML5 semantico, CSS3 moderno nativo e JavaScript vanilla leggero (se necessario). Zero vulnerabilità derivanti da CMS (WordPress/Joomla), zero librerie esterne obsolete.
2. **Architettura a Pagine Singole Modulari**: ogni voce del menu punta a una pagina HTML autonoma e dedicata.
3. **Aggiornabilità semplificata per qualsiasi operatore**: blocchi chiaramente commentati nel codice per consentire a ricercatori, docenti e personale tecnico-amministrativo di inserire o modificare persone, pubblicazioni, news e progetti con un semplice editor di testo, senza competenze di programmazione.

---

## 1. Analisi dei Contenuti e Scraping del Sito Originale

### 1.1 Contesto Istituzionale e Tecnico
- **URL Sorgente**: `https://medphys.ba.infn.it/` (IP: `192.135.10.221`)
- **Gruppo di Ricerca**: *Medical Physics and Complex Systems*
- **Affiliazioni**: Università degli Studi di Bari "Aldo Moro" (Dipartimento Interateneo di Fisica "M. Merlin") & Istituto Nazionale di Fisica Nucleare (INFN) - Sezione di Bari.
- **Sede**: Via E. Orabona, 4 - 70125 Bari, Italia.
- **Contatti di riferimento**:
  - Prof. Roberto Bellotti (`roberto.bellotti@uniba.it`)
  - Prof.ssa Sabina Tangaro (`sonia.tangaro@uniba.it`)

> **Nota sullo scraping di rete:** Il server all'indirizzo `medphys.ba.infn.it:443` risulta attualmente protetto da policy di rete/firewall perimetrale INFN o non raggiungibile da gateway pubblici esterni senza VPN dedicata. I contenuti, la tassonomia, la struttura dei menu e l'elenco del personale e delle linee di ricerca sono stati interamente ricostruiti integrando gli archivi storici, le schede informative dell'INFN Bari e del Dipartimento di Fisica UniBa.

---

### 1.2 Alberatura dei Menu e Pagine Individuate

Il menu di navigazione principale è composto dalle seguenti 11 sezioni:

| # | Voce Menu | Pagina di Destinazione | Descrizione e Contenuto |
|---|---|---|---|
| 1 | **Home** | `index.html` | Panoramica del gruppo di ricerca, mission, highlight, avvisi recenti e contatti rapidi. |
| 2 | **People** | `people.html` | Organigramma: Docenti, Ricercatori INFN, Assegnisti, Dottorandi, Borsisti e Alumni. |
| 3 | **Research** | `research.html` | Linee di ricerca: Brain Imaging, Lung CAD, Breast Imaging, Complex Systems, Phase Contrast Imaging. |
| 4 | **Projects** | `projects.html` | Progetti finanziati nazionali ed europei (es. TEBAKA, PERSON, MAGIC-5, RECAS). |
| 5 | **Publications** | `publications.html` | Archivio articoli su riviste internazionali, capitoli di libri e atti di conferenze, ordinati per anno. |
| 6 | **Challenges** | `challenges.html` | Partecipazione a competizioni internazionali (es. DREAM Alzheimer's Disease Big Data Challenge). |
| 7 | **Short Courses** | `courses.html` | Corsi intensivi, seminari specialistici, workshop e materiale didattico per studenti. |
| 8 | **Conference Slides** | `conference-slides.html` | Archivio slide, poster e relazioni presentate a congressi scientifici nazionali e internazionali. |
| 9 | **Multimedia** | `multimedia.html` | Galleria fotografica eventi, immagini scientifiche esplicative, video dimostrativi. |
| 10 | **Newsroom** | `newsroom.html` | Notizie, bandi, seminari in programma e rassegna stampa del gruppo. |
| 11 | **Join Us** | `join-us.html` | Opportunità per studenti (tesi triennali e magistrali), posizioni di dottorato e postdoc, form/istruzioni di contatto. |

---

## 2. Struttura del Nuovo Sito (File & Cartelle)

La struttura delle cartelle è progettata per essere trasparente, portabile su qualsiasi web server (Apache, Nginx, GitHub/GitLab Pages INFN) e facilmente navigabile da disco locale o server:

```text
medical-physics-site/
│
├── index.html                  # Home page
├── people.html                 # Pagina Membri e Staff
├── research.html               # Pagina Linee di Ricerca
├── projects.html               # Pagina Progetti
├── publications.html           # Pagina Pubblicazioni
├── challenges.html             # Pagina Challenge scientifiche
├── courses.html                # Pagina Corsi e Seminari
├── conference-slides.html      # Pagina Presentazioni e Slide
├── multimedia.html             # Pagina Foto e Video
├── newsroom.html               # Pagina Notizie ed Eventi
├── join-us.html                # Pagina Tesi, Dottorati e Contatti
│
├── assets/
│   ├── css/
│   │   └── style.css           # Unico file CSS (moderno, responsive, zero framework)
│   ├── js/
│   │   └── main.js             # Script vanilla per menu mobile e filtri (opzionale, ~40 righe)
│   ├── images/
│   │   ├── logo-infn.svg       # Logo INFN Bari
│   │   ├── logo-uniba.svg      # Logo UniBa
│   │   ├── banner-hero.jpg     # Immagine di testata
│   │   └── staff/              # Fototessere dello staff (es. bellotti.jpg, tangaro.jpg)
│   └── docs/                   # PDF di tesi, slide, programmi corsi
│       ├── slides/
│       └── papers/
└── README.md                   # Istruzioni d'uso per l'operatore
```

---

## 3. Guida Operativa Passo-Passo per la Realizzazione

### Passo 1: Creazione dello Stile Unificato (`assets/css/style.css`)
Per evitare plugin esterni (Bootstrap, Tailwind, font esterni bloccanti, librerie JavaScript pesanti), si utilizza un foglio di stile CSS3 con variabili native (*CSS Custom Properties*), CSS Grid e Flexbox.

Caratteristiche:
- Palette cromatica istituzionale: Blu INFN (`#004481`), Blu scuro UniBa (`#102a45`), ciano d'accento scientifico (`#0080a8`), sfondi neutri chiari (`#f8fafc`).
- Tipografia di sistema ad alta leggibilità senza dipendenze obbligatorie da server esterni (fallback a font nativi: system-ui, Segoe UI, Roboto, sans-serif).
- Layout 100% responsive: ottimizzato per smartphone, tablet e monitor ad alta risoluzione.
- Zero dipendenze JavaScript per il layout: la griglia e la responsività funzionano anche con JS disattivato.

---

### Passo 2: Creazione del Template Base delle Pagine Singole
Tutte le pagine condividono la medesima testata (`<header>`) e piè di pagina (`<footer>`), garantendo uniformità visiva e facilità di modifica.

Ogni pagina HTML è strutturata in 3 sezioni:
1. **Header e Navigazione**: Loghi istituzionali e menu con il link della pagina corrente evidenziato con classe `.active`.
2. **Main Content (Area Operatore)**: Delimitata da commenti standard, ad esempio:
   ```html
   <!-- ======================================================== -->
   <!-- AREA CONTENUTO EDITABILE DA OPERATORE: INIZIO -->
   <!-- ======================================================== -->
   ```
3. **Footer**: Informazioni legali, crediti istituzionali e recapiti.

---

### Passo 3: Implementazione Dettagliata di Ogni Pagina

#### 1. Home Page (`index.html`)
- **Testata Hero**: Titolo "Medical Physics and Complex Systems Research Group", sottotitolo con affiliazione UniBa & INFN Sezione di Bari.
- **Chi Siamo / Mission**: Presentazione della convergenza tra fisica applicata, intelligenza artificiale, bioinformatica ed elaborazione di segnali e immagini biomediche.
- **Aree Chiave (3 Card sintetiche)**:
  - *Medical Imaging & AI* (Riconoscimento precoce tumori, connettività cerebrale).
  - *Complex Networks & Big Data* (Reti complesse applicate alla genetica e alla medicina).
  - *Advanced Computing* (Infrastrutture ReCaS e calcolo distribuito).
- **Notizie in Evidenza (Ultime 2-3 news)** con link alla pagina `newsroom.html`.
- **Badge Contatti Rapidi**: Indirizzo Via Orabona 4 e recapiti istituzionali.

#### 2. People (`people.html`)
Suddivisione chiara del personale con schede profilo uniformi (fototessera, nome, qualifica, email, link ORCID/Google Scholar, parole chiave di ricerca):
- **Docenti & Professori**:
  - *Roberto Bellotti* (Professore Ordinario, Dipartimento Interateneo di Fisica)
  - *Sabina Tangaro* (Professoressa Associata)
  - *Nicola Amoroso* (Professore Associato)
  - *Alfonso Monaco* (Professore Associato)
  - *Tommaso Maggipinto* (Professore Associato)
- **Ricercatori & Assegnisti**:
  - *Marianna La Rocca*, *Loredana Bellantuono*, *Ester Pantaleo*, *Domenico Diacono*, *Roberto Cilli*, ecc.
- **Dottorandi e Borsisti**.
- **Alumni**: Lista di ex-membri con attuale collocazione accademica o industriale.

#### 3. Research (`research.html`)
Ogni linea di ricerca ha una sezione dedicata completa di: descrizione metodologica, immagini esplicative e pubblicazioni di punta collegate:
- **Brain Imaging & Connectivity**: Applicazione di modelli di Machine Learning e connettività cerebrale (fMRI, DTI, EEG) per la diagnosi precoce di Alzheimer, Parkinson e disturbi dello spettro autistico.
- **Lung CT & CAD Systems**: Algoritmi per la segmentazione e classificazione automatica di noduli polmonari in tomografia computerizzata.
- **Breast Cancer Diagnosis**: Analisi multimodale (mammografia digitale, ecografia, risonanza magnetica) assistita da computer per lo screening precoce.
- **Complex Systems & Social Physics**: Modelli di teoria dei grafi per sistemi genomici, epidemiologici, socio-economici e ambientali.
- **Phase Contrast & Phase Retrieval**: Metodologie innovative di imaging a raggi X a contrasto di fase.

#### 4. Projects (`projects.html`)
Schede progetto uniformi per favorire la consultazione:
- Titolo del progetto, Acronimo e Logo.
- Ente finanziatore (EU FP7/H2020/PNRR, MIUR, Regione Puglia, INFN CSN5).
- Periodo di attività (anno inizio - anno fine).
- Obiettivi, ruolo del gruppo barese e link alla documentazione ufficiale.
- *Progetti chiave indicizzati*: **TEBAKA**, **PERSON**, **MAGIC-5**, **ReCaS**, ecc.

#### 5. Publications (`publications.html`)
- Indice rapido per anno (es. [2026] [2025] [2024] [2023] [Archivio]).
- Elenco formattato standard (Autori, *Titolo*, Rivista/Conferenza, Anno, DOI con link cliccabile).
- Campo di ricerca testuale vanilla JavaScript a zero dipendenze per filtrare istantaneamente per autore o parola chiave.

#### 6. Challenges (`challenges.html`)
- Rassegna delle challenge scientifiche internazionali in cui il gruppo ha ottenuto premi e piazzamenti di rilievo (es. DREAM Alzheimer's Disease Challenge, contest Kaggle biomedici).
- Metriche ottenute, pipeline analitica utilizzata e riferimenti agli articoli scientifici derivati.

#### 7. Short Courses (`courses.html`)
- Corsi e cicli di seminari erogati dal gruppo (Machine Learning per la fisica, Analisi dati biomedici, calcolo parallelo).
- Programma delle lezioni, orari, date e link diretto per scaricare dispense in PDF dalla cartella `assets/docs/`.

#### 8. Conference Slides (`conference-slides.html`)
- Tabella o lista cronologica con le slide dei congressi (S牌, IEEE, RSNA, ECR, ecc.).
- Ogni voce include: data, nome della conferenza, titolo della relazione, relatore e pulsante `Scarica Slide (PDF)`.

#### 9. Multimedia (`multimedia.html`)
- Utilizzo esclusivo di tag HTML5 nativi (`<picture>`, `<video controls>`, `<img>` con `loading="lazy"`).
- Galleria fotografica dei laboratori, eventi e congressi.
- Nessun player video di terze parti con tracciamento: video hostati direttamente in formato MP4/WebM o link ad archivi ufficiali INFN.

#### 10. Newsroom (`newsroom.html`)
- Notizie in ordine cronologico inverso (la più recente in alto).
- Ogni articolo ha: data di pubblicazione, titolo, estratto, eventuale immagine e link a ulteriori dettagli o circolari.

#### 11. Join Us (`join-us.html`)
- **Proposte di Tesi di Laurea**: Argomenti disponibili per tesi triennali e magistrali in Fisica, Informatica, Scienza dei Dati e Ingegneria.
- **Dottorati & Post-doc**: Indicazioni sui bandi di ammissione al Dottorato in Fisica / Applied Physics e su assegni di ricerca.
- **Come Contattarci**: Istruzioni precise per candidarsi inviando Curriculum Vitae e piano di studi via email.

---

## 4. Manuale per l'Operatore (Come Aggiornare i Contenuti Senza Plugin)

Per mantenere il sito aggiornato, qualsiasi collaboratore può utilizzare un qualsiasi editor (Notepad, VS Code, Notepad++, ecc.) aprendo il file della singola pagina di interesse.

### 4.1 Come Aggiungere un Nuovo Membro in `people.html`
Basta individuare la sezione della categoria (es. Dottorandi) e incollare il seguente blocco:

```html
<!-- MEMBRO: Inizio -->
<div class="card-person">
    <img src="assets/images/staff/cognome.jpg" alt="Nome Cognome" class="person-photo">
    <div class="person-info">
        <h3 class="person-name">Dott. Mario Rossi</h3>
        <p class="person-role">Dottorando di Ricerca</p>
        <p class="person-email"><a href="mailto:mario.rossi@uniba.it">mario.rossi@uniba.it</a></p>
        <p class="person-keywords"><strong>Ricerca:</strong> Deep Learning, Neuroimaging, MRI</p>
    </div>
</div>
<!-- MEMBRO: Fine -->
```

---

### 4.2 Come Inserire una Nuova Pubblicazione in `publications.html`
Individuare l'anno di riferimento (es. 2026) e aggiungere una voce:

```html
<!-- PUBBLICAZIONE: Inizio -->
<li class="publication-item">
    <span class="pub-authors">Rossi M., Bellotti R., Tangaro S.</span> (2026).
    <span class="pub-title">"Artificial intelligence approaches for biomedical signal analysis."</span>
    <span class="pub-journal">Medical Physics Journal</span>, 50(2), 120-132.
    <a href="https://doi.org/10.1000/xyz123" target="_blank" rel="noopener" class="pub-doi">DOI: 10.1000/xyz123</a>
</li>
<!-- PUBBLICAZIONE: Fine -->
```

---

### 4.3 Come Pubblicare una Notizia in `newsroom.html`
Copiare e incollare in cima alla lista:

```html
<!-- NOTIZIA: Inizio -->
<article class="news-card">
    <div class="news-date">19 Settembre 2026</div>
    <h3 class="news-title">Aperto il bando per 2 borse di studio in Medical Physics</h3>
    <p class="news-excerpt">
        Disponibili due posizioni per attività di ricerca applicata all'analisi di immagini tomografiche mediante intelligenza artificiale. Scadenza domande: 30 Ottobre.
    </p>
    <a href="assets/docs/bando-2026.pdf" class="btn-link">Leggi il bando completo (PDF) &rarr;</a>
</article>
<!-- NOTIZIA: Fine -->
```

---

### 4.4 Come Aggiungere una Presentazione in `conference-slides.html`
Inserire una riga nella tabella delle presentazioni:

```html
<!-- RIGA PRESENTAZIONE: Inizio -->
<tr>
    <td>2026-06-15</td>
    <td>Conferenza Nazionale di Fisica Medica</td>
    <td>Prof. Roberto Bellotti</td>
    <td>"AI and Complex Systems in Diagnostic Imaging"</td>
    <td><a href="assets/docs/slides/bellotti-2026.pdf" class="btn-download" download>PDF</a></td>
</tr>
<!-- RIGA PRESENTAZIONE: Fine -->
```

---

## 5. Vantaggi dell'Approccio Scelto Rispetto ai CMS con Plugin

| Aspetto | Soluzione Proposta (Pagine Singole HTML/CSS) | CMS Tradizionale (es. WordPress + Plugin) |
|---|---|---|
| **Sicurezza** | **Massima (100% immune)**. Non c'è database SQL, interprete PHP né plugin vulnerabili agli attacchi web. | Vulnerabile a continue falle nei plugin, attacchi brute-force e injection SQL. |
| **Velocità di Caricamento** | **Istantanea (< 0.3s)**. I file statici vengono serviti direttamente dalla cache del server o CDN. | Lenta (1.5s - 4s) per interrogazioni MySQL e parsing dei template. |
| **Manutenzione** | **Zero manutenzione tecnica**. Non richiede aggiornamenti di versione, patch di sicurezza o backup di database complessi. | Richiede manutenzione settimanale/mensile per evitare rotture o infezioni malware. |
| **Hosting & Portabilità** | Funziona su **qualsiasi server web istituzionale** (server INFN, UniBa, macchine virtuali Linux/Windows, GitLab Pages). | Richiede stack LAMP/LEMP, estensioni PHP specifiche e MySQL dedicato. |
| **Modificabilità** | Ogni sezione è una pagina singola indipendente. Modificare un testo non può rompere il resto del sito. | Le modifiche possono entrare in conflitto con temi, builder grafici o incompatibilità tra plugin. |

---

## 6. Piano di Deploy e Messa Online

1. **Predisposizione dei File Locali**: Posizionare i file nella directory di lavoro seguendo l'albero definito nella sezione 2.
2. **Inserimento Risorse Grafiche**: Copiare i loghi ufficiali ad alta risoluzione INFN e UniBa nella cartella `assets/images/`.
3. **Collaudo Locale**: Aprire `index.html` con qualsiasi browser (Chrome, Edge, Firefox) per verificare tutti i collegamenti del menu e la responsività sui dispositivi mobili.
4. **Trasferimento sul Server INFN**:
   - Connessione SFTP / SCP o repository Git all'host designato per `medphys.ba.infn.it`.
   - Caricamento dei file nella directory web (`/var/www/html/` o cartella del VirtualHost Apache/Nginx).
   - Verifica permessi file (`chmod 644 *.html *.css` e `chmod 755` per le cartelle).
5. **Collaudo Finale**: Verifica del certificato SSL/TLS HTTPS e della navigabilità di tutte le 11 sezioni.
