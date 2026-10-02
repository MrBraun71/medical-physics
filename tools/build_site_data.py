# -*- coding: utf-8 -*-
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'data')

ALLOWED_SCHEMES = ('http', 'https', 'mailto', 'tel')


def safe_url(value, kind='link'):
    """Normalizza un URL e ne blocca gli schemi pericolosi.

    Serve in particolare per il newsroom: la lista conteneva link in chiaro
    `http://`. `http` resta ammesso come schema per non perdere le voci, ma
    viene sempre promosso a `https` prima di finire nel dato pubblicato.
    """
    raw = str(value or '').strip()
    if not raw or any(ch.isspace() or ord(ch) < 32 for ch in raw):
        return ''
    if kind == 'link' and raw.startswith('#'):
        return raw
    match = re.match(r'([a-zA-Z][a-zA-Z0-9+.-]*):', raw)
    if match:
        scheme = match.group(1).lower()
        if scheme not in ALLOWED_SCHEMES:
            return ''
        if scheme == 'http':
            raw = 'https://' + raw[len('http://'):]
    return raw


def js(value):
    """Serializza in JSON bloccando la chiusura del tag <script>.

    Espone `<`, `>` e `&` come escape Unicode e separa U+2028/U+2029, che il
    parser JavaScript considera terminatori di riga.
    """
    return (json.dumps(value, ensure_ascii=False)
            .replace(chr(0x2028), '\\u2028')
            .replace(chr(0x2029), '\\u2029')
            .replace('<', '\\u003c')
            .replace('>', '\\u003e')
            .replace('&', '\\u0026'))

SITE = {
  "brand": {"en": "Medical Physics & Complex Systems", "it": "Fisica Medica e Sistemi Complessi"},
  "short": {"en": "Medical Physics", "it": "Fisica Medica"},
  "org": {"en": "University of Bari Aldo Moro \u00b7 INFN Bari", "it": "Universit\u00e0 di Bari Aldo Moro \u00b7 INFN Bari"},
  "logo": "assets/img/MedicalPhysics.png",
  "address": "Via E. Orabona 4, 70125 \u2013 Bari, Italy",
  "emails": ["roberto.bellotti@uniba.it", "sonia.tangaro@ba.infn.it"],
  "nav": [
    {"route": "home", "en": "Home", "it": "Home"},
    {"route": "research", "en": "Research", "it": "Ricerca"},
    {"route": "people", "en": "People", "it": "Persone"},
    {"route": "projects", "en": "Projects", "it": "Progetti"},
    {"route": "challenges", "en": "Challenges", "it": "Sfide"},
    {"route": "publications", "en": "Publications", "it": "Pubblicazioni"},
    {"route": "multimedia", "en": "Multimedia", "it": "Multimedia"},
    {"route": "join-us", "en": "Join Us", "it": "Unisciti a noi"},
    {"route": "courses", "en": "Courses", "it": "Corsi", "children": [
      {"route": "courses", "en": "Courses", "it": "Corsi"},
      {"route": "short-course", "en": "Short Course", "it": "Short Course"},
      {"route": "conference-slides", "en": "Conference slides", "it": "Slide dei convegni"},
      {"route": "pattern_recognition", "en": "Labs", "it": "Laboratori"}
    ]}
  ],
  "home": {
    "kicker": {"en": "University of Bari Aldo Moro \u00b7 INFN Bari", "it": "Universit\u00e0 di Bari Aldo Moro \u00b7 INFN Bari"},
    "title": {"en": "Medical Physics & Complex Systems", "it": "Fisica Medica e Sistemi Complessi"},
    "lead": {
      "en": "Research topics range from medical image analysis with machine learning techniques to complex network analysis applied to medical, environmental and genomic data.",
      "it": "I temi di ricerca spaziano dall\u2019analisi di immagini mediche con tecniche di machine learning all\u2019analisi di reti complesse applicata a dati medici, ambientali e genomici."
    },
    "para2": {
      "en": "Current research interests are in complex network analysis and deep learning models applied to medicine, physics, remote sensing and environmental data, developing machine learning algorithms also through distributed computing and storage architectures.",
      "it": "Gli interessi di ricerca attuali riguardano l\u2019analisi di reti complesse e modelli di deep learning applicati a medicina, fisica, telerilevamento e dati ambientali, sviluppando algoritmi di machine learning anche su architetture distribuite di calcolo e storage."
    },
    "para3": {
      "en": "The goal of the Medical Physics research activity is to improve the diagnosis of disease and the effectiveness of therapies by integrating physics, engineering and medicine.",
      "it": "L\u2019obiettivo dell\u2019attivit\u00e0 di ricerca in Fisica Medica \u00e8 migliorare la diagnosi delle malattie e l\u2019efficacia delle terapie integrando fisica, ingegneria e medicina."
    },
    "hero_img": "assets/img/cropped-Culture_of_rat_brain_cells_stained_with_antibody_to_MAP2_green_Neurofilament_red_and_DNA_blue-1.jpg"
  },
  "sections": {
    "research": {"en": "Research", "it": "Ricerca"},
    "people": {"en": "People", "it": "Persone"},
    "publications": {"en": "Publications", "it": "Pubblicazioni"},
    "challenges": {"en": "Challenges", "it": "Sfide"},
    "newsroom": {"en": "Newsroom", "it": "Rassegna stampa"},
    "projects": {"en": "Projects", "it": "Progetti"},
    "collaborators": {"en": "Collaborators", "it": "Collaboratori"}
  },
  "pub_notice": {
    "en": "\u00a9 2018\u20132026 Medical Physics group. The papers listed below are provided for personal use only and may not be reproduced without permission from the copyright holders.",
    "it": "\u00a9 2018\u20132026 Gruppo di Fisica Medica. I lavori elencati sono forniti esclusivamente per uso personale e non possono essere riprodotti senza autorizzazione dei titolari dei diritti."
  },
  "research": [
    {
      "slug": "brain", "img": "assets/img/www.maxpixel.net-Neurons-Brain-Cells-Brain-Brain-Structure-Network-1739997-500x310.jpg",
      "title": {"en": "Brain", "it": "Cervello"},
      "summary": {"en": "MRI-based methods for brain disease: multimodal registration, hippocampus segmentation and distributed computing workflows.", "it": "Metodi basati su MRI per le patologie cerebrali: registrazione multimodale, segmentazione dell\u2019ippocampo e workflow di calcolo distribuito."},
      "body": {
        "en": "<p>The application of magnetic resonance imaging (MRI) has undergone an unstoppable development over the last decades. Large datasets containing thousands of medical images are currently available to support clinical diagnosis, and this is particularly true for brain diseases. At the same time, increasingly sophisticated software and computationally intensive algorithms have been implemented to extract useful information from medical images. As a consequence, many medical image processing applications would greatly benefit from grids: run-time reduction, sharing of data collections and platform/hardware independent configurations are simple examples. With this goal we implement methods to exploit Grid \u2014 or more generally distributed computing infrastructures. Among the services produced there is a feasibility study for inter-subject multimodal registration and a segmentation algorithm workflow dedicated to the hippocampus. The workflow allows the end user to upload MRIs, which are registered with several ICBM templates and segmented with a classifier. The proposed approach can be useful even for large-scale studies or clinical trials.</p>",
        "it": "<p>L\u2019applicazione della risonanza magnetica (MRI) ha conosciuto negli ultimi decenni uno sviluppo inarrestabile. Grandi insiemi di dati contenenti migliaia di immagini mediche sono oggi disponibili a supporto della diagnosi clinica, e ci\u00f2 \u00e8 particolarmente vero per le patologie cerebrali. Allo stesso tempo sono stati implementati software sempre pi\u00f9 sofisticati e algoritmi computazionalmente intensivi per estrarre informazioni utili dalle immagini mediche. Di conseguenza molte applicazioni di elaborazione di immagini mediche trarrebbero grande vantaggio dalle grid: riduzione dei tempi di esecuzione, condivisione delle collezioni di dati e configurazioni indipendenti da piattaforma e hardware sono semplici esempi. Con questo obiettivo implementiamo metodi per sfruttare la Grid \u2014 o pi\u00f9 in generale infrastrutture di calcolo distribuito. Tra i servizi prodotti vi sono uno studio di fattibilit\u00e0 per la registrazione multimodale inter-soggetto e un workflow di segmentazione dedicato all\u2019ippocampo. Il workflow consente all\u2019utente di caricare MRI, che vengono registrate con diversi template ICBM e segmentate con un classificatore. L\u2019approccio proposto pu\u00f2 essere utile anche per studi su larga scala o trial clinici.</p>"
      }
    },
    {
      "slug": "lung", "img": "assets/img/xray-1476620_640-500x310.jpg",
      "title": {"en": "Lung", "it": "Polmone"},
      "summary": {"en": "Automated detection of small pulmonary nodules in CT lung scans, including participation in the Italung-CT screening trial.", "it": "Individuazione automatica di piccoli noduli polmonari nelle scansioni CT, inclusa la partecipazione allo studio di screening Italung-CT."},
      "body": {
        "en": "<p>The automated identification of small nodules in Computed Tomography (CT) lung scans represents an activity of our group. CT has been shown to be the best imaging modality for the detection of small pulmonary nodules, particularly after the introduction of helical technology. The first Italian Randomized Controlled Trial has recently started (Italung-CT) to study the potential impact of a screening-based low-dose helical CT on the high-risk population. In this framework our group develops automated approaches for the identification of small pulmonary nodules. Various approaches are developed and tested:</p><ol><li>detection of nodule candidates by means of a dot-enhancement filter;</li><li>detection of nodule candidates by means of region growing;</li><li>detection of non-pathological structures by means of an artificial life model.</li></ol>",
        "it": "<p>L\u2019identificazione automatica dei piccoli noduli nelle scansioni CT del polmone rappresenta un\u2019attivit\u00e0 del nostro gruppo. La CT si \u00e8 dimostrata la migliore modalit\u00e0 di imaging per l\u2019individuazione dei piccoli noduli polmonari, in particolare dopo l\u2019introduzione della tecnologia elicoidale. \u00c8 recentemente iniziato il primo studio randomizzato controllato italiano (Italung-CT) per studiare il potenziale impatto di una CT elicoidale a basso dosaggio basata su screening sulla popolazione ad alto rischio. In questo quadro il nostro gruppo sviluppa approcci automatici per l\u2019identificazione dei piccoli noduli polmonari. Sono sviluppati e testati diversi approcci:</p><ol><li>individuazione dei candidati nodulo mediante un filtro di enhancement dei punti;</li><li>individuazione dei candidati nodulo mediante region growing;</li><li>individuazione delle strutture non patologiche mediante un modello di vita artificiale.</li></ol>"
      }
    },
    {
      "slug": "breast", "img": "assets/img/mammography-500x310.jpg",
      "title": {"en": "Breast", "it": "Mammella"},
      "summary": {"en": "Computer-aided detection (CAD) systems for mammographic image analysis to support physicians\u2019 diagnosis.", "it": "Sistemi di diagnosi assistita dal computer (CAD) per l\u2019analisi di immagini mammografiche a supporto della diagnosi medica."},
      "body": {
        "en": "<p>The analysis of medical images has gathered, in recent years, growing interest from the scientific community working at the crossover point among physics, engineering and medicine. The development of computer-aided detection (CAD) systems for the automated search for pathologies could be very useful for the improvement of physicians\u2019 diagnosis. A typical example is the analysis of mammographic images, widely recognized as the only imaging modality for an early detection of breast neoplasia. Breast cancer is reported as the leading cause of woman cancer deaths in both the United States and Europe. At present, screening programs are the best known method for an early diagnosis in asymptomatic women, allowing a reduction of mortality. Screening programs are based on a double visual inspection of the mammographic images, since double reading increases diagnostic accuracy. From this point of view, the use of a CAD system could provide valuable assistance to the radiologist. In previous studies, our group proposed a CAD scheme based on ROI localization, feature extraction and neural network classification. Suspect regions were detected by searching for local intensity maxima in rings whose radius was increased until the average intensity decreased to a predefined fraction of the local maximum. The ROIs thus obtained were described in terms of statistical features such as average, variance, skewness and kurtosis of the intensity distributions at different fractions of the ROI radius. This scheme relied on a simplified and rough description of the ROI, modeled as a round region. An improvement was achieved by implementing a new edge-based segmentation algorithm where ROIs are defined by iso-intensity contours. We retained the improved version of the segmentation step and replaced the feature set with Haralick\u2019s one. The choice of texture-based features is justified by the successful application of such features to the detection of pathologies in medical image analysis. Comparing our approach with the previous one, two main aspects should be stressed: some algorithms lack automatic localization of the suspicious regions (using manually selected ROIs), while others that include a computerized ROI hunter lack a large and heterogeneous database to test performance in screening-like conditions. Both points should be taken into account in view of a completely automated CAD system assisting radiologists in a large-scale screening program. Our CAD meets both requirements as it fits into the more general framework of the MAGIC-5 Project (Medical Application on a Grid Infrastructure Connection), which focuses on the development of software tools for biomedical image analysis and their use on distributed image databases via GRID technologies. Image collection in a screening program intrinsically creates a distributed database, as it involves many hospitals and/or screening centers in different locations. The amount of data generated by such periodic examinations would be so large that concentrating it in a single computing center would not be efficient; in addition, it would grow linearly with time, and a full network transfer from the collection centers to a central site would likely saturate the available connections. Making the whole database available to authorized users, regardless of data distribution, would provide several advantages. The best way to tackle these demands is to use GRID services to manage distributed databases and allow real-time remote diagnosis, providing access to the full database from any site.</p>",
        "it": "<p>L\u2019analisi delle immagini mediche ha raccolto negli ultimi anni un interesse crescente da parte della comunit\u00e0 scientifica che opera all\u2019incrocio tra fisica, ingegneria e medicina. Lo sviluppo di sistemi di diagnosi assistita dal computer (CAD) per la ricerca automatica delle patologie potrebbe essere molto utile per migliorare la diagnosi dei medici. Un esempio tipico \u00e8 l\u2019analisi delle immagini mammografiche, ampiamente riconosciute come l\u2019unica modalit\u00e0 di imaging per la diagnosi precoce della neoplasia mammaria. Il tumore al seno \u00e8 la principale causa di morte per cancro nelle donne sia negli Stati Uniti sia in Europa. Attualmente i programmi di screening sono il metodo pi\u00f9 noto per una diagnosi precoce nelle donne asintomatiche, consentendo una riduzione della mortalit\u00e0. I programmi di screening si basano su una doppia lettura visiva delle immagini mammografiche, poich\u00e9 la doppia lettura aumenta l\u2019accuratezza diagnostica. Da questo punto di vista, l\u2019uso di un sistema CAD potrebbe fornire un valido supporto al radiologo. In studi precedenti il nostro gruppo ha proposto uno schema CAD basato sulla localizzazione delle ROI, l\u2019estrazione di caratteristiche e la classificazione con reti neurali. Le regioni sospette venivano individuate cercando i massimi locali di intensit\u00e0 in anelli il cui raggio cresceva finch\u00e9 l\u2019intensit\u00e0 media non diminuiva a una frazione predefinita del massimo locale. Le ROI cos\u00ec ottenute erano descritte tramite caratteristiche statistiche come media, varianza, simmetria e curtosi delle distribuzioni di intensit\u00e0 a diverse frazioni del raggio della ROI. Questo schema si basava su una descrizione semplificata e approssimativa della ROI, modellata come regione circolare. Un miglioramento \u00e8 stato ottenuto implementando un nuovo algoritmo di segmentazione basato sui bordi, in cui le ROI sono definite da contorni di iso-intensit\u00e0. Abbiamo mantenuto la versione migliorata della segmentazione e sostituito l\u2019insieme di caratteristiche con quelle di Haralick. La scelta di caratteristiche basate sulla texture \u00e8 giustificata dal successo di tali caratteristiche nell\u2019individuazione di patologie nell\u2019analisi di immagini mediche. Confrontando il nostro approccio con quello precedente, vanno sottolineati due aspetti principali: alcuni algoritmi mancano di una localizzazione automatica delle regioni sospette (usando ROI selezionate manualmente), mentre altri, che includono un \u2018cacciatore\u2019 automatico di ROI, non dispongono di un database ampio ed eterogeneo per testare le prestazioni in condizioni simili allo screening. Entrambi gli aspetti vanno considerati in vista di un sistema CAD completamente automatico a supporto dei radiologi in un programma di screening su larga scala. Il nostro CAD soddisfa entrambi i requisiti, inserendosi nel quadro pi\u00f9 generale del Progetto MAGIC-5 (Medical Application on a Grid Infrastructure Connection), incentrato sullo sviluppo di strumenti software per l\u2019analisi di immagini biomediche e sul loro uso su database distribuiti tramite tecnologie GRID. La raccolta di immagini in un programma di screening crea intrinsecamente un database distribuito, coinvolgendo molti ospedali e/o centri di screening in localit\u00e0 diverse. La quantit\u00e0 di dati generata da tali esami periodici sarebbe cos\u00ec grande che concentrarla in un singolo centro di calcolo non sarebbe efficiente; inoltre crescerebbe linearmente nel tempo e un trasferimento completo via rete dai centri di raccolta a un sito centrale saturerebbe probabilmente le connessioni disponibili. Rendere l\u2019intero database disponibile agli utenti autorizzati, indipendentemente dalla distribuzione dei dati, offrirebbe diversi vantaggi. Il modo migliore per affrontare queste esigenze \u00e8 usare i servizi GRID per gestire database distribuiti e consentire la diagnosi remota in tempo reale, offrendo accesso all\u2019intero database da qualsiasi sito.</p>"
      }
    },
    {
      "slug": "phase-contrast-phase-retrieval-imaging", "img": "assets/img/586px-Cheek_cell_phase_contrast-500x310.jpg",
      "title": {"en": "Phase Contrast / Phase Retrieval Imaging", "it": "Imaging a contrasto di fase / phase retrieval"},
      "summary": {"en": "Thomson-source phase-contrast and phase-retrieval imaging, and the Combined Mixed Approach (CMA) for phase-map reconstruction from X-ray images.", "it": "Imaging a contrasto di fase e phase retrieval con sorgenti Thomson, e l\u2019approccio Combined Mixed Approach (CMA) per la ricostruzione delle mappe di fase da immagini a raggi X."},
      "body": {
        "en": "<p>The group\u2019s activities were focused on studying the potential of Thomson imaging sources (TS) in terms of visibility of details in Phase Contrast (PC) and Phase Retrieval (PRI) images compared with the detail visibility in absorption images. A new analytical/numerical method, called Combined Mixed Approach (CMA), was developed for the reconstruction of phase maps from X-ray images. PRI allows a quantitative approach because the phase map is directly proportional to the electron density of the object and can therefore provide essential information on the internal structures of objects/tissues. Some preliminary experiments were performed at synchrotron sources with different samples, showing significant increases in image quality compared with X-ray absorption imaging.</p>",
        "it": "<p>Le attivit\u00e0 del gruppo si sono concentrate sullo studio delle potenzialit\u00e0 delle sorgenti di imaging Thomson (TS) in termini di visibilit\u00e0 dei dettagli nelle immagini a contrasto di fase (PC) e di phase retrieval (PRI) rispetto alla visibilit\u00e0 dei dettagli nelle immagini di assorbimento. \u00c8 stato sviluppato un nuovo metodo analitico/numerico, chiamato Combined Mixed Approach (CMA), per la ricostruzione delle mappe di fase da immagini a raggi X. Il PRI consente un approccio quantitativo poich\u00e9 la mappa di fase \u00e8 direttamente proporzionale alla densit\u00e0 elettronica dell\u2019oggetto e pu\u00f2 quindi fornire informazioni essenziali sulle strutture interne di oggetti/tesuti. Alcuni esperimenti preliminari sono stati condotti presso sorgenti di sincrotrone con diversi campioni, mostrando incrementi significativi della qualit\u00e0 dell\u2019immagine rispetto all\u2019imaging per assorbimento a raggi X.</p>"
      }
    }
  ],
}

# ---------------- PEOPLE ----------------
def person(slug, img, kw_en, kw_it, bio_en, bio_it, email=""):
    return {"slug": slug, "img": img, "keywords": {"en": kw_en, "it": kw_it},
            "bio": {"en": bio_en, "it": bio_it}, "email": email}

SITE["people"] = [
  person("roberto-bellotti", "assets/img/foto-rob.jpg",
    "Medical Physics, Spatio-temporal Data Mining",
    "Fisica Medica, Data Mining spazio-temporale",
    "Roberto Bellotti is full professor of applied physics at the University of Bari, Italy. His current research interests are in medical physics and spatio-temporal data mining by means of learning techniques and complex network analysis.",
    "Roberto Bellotti \u00e8 professore ordinario di fisica applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano la fisica medica e il data mining spazio-temporale mediante tecniche di apprendimento e analisi di reti complesse.",
    "roberto.bellotti@uniba.it"),
  person("nicola-amoroso", "assets/img/amoroso.jpg",
    "Complex Systems, Earth Observation, Decision Support Systems",
    "Sistemi complessi, Osservazione della Terra, Sistemi di supporto alle decisioni",
    "Nicola Amoroso is associate professor of applied physics at the University of Bari, Italy. His current research interests are in remote sensing, medical physics and medicinal chemistry by means of Artificial Intelligence and complex networks.",
    "Nicola Amoroso \u00e8 professore associato di fisica applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano il telerilevamento, la fisica medica e la chimica farmaceutica mediante intelligenza artificiale e reti complesse.",
    "nicola.amoroso@uniba.it"),
  person("loredana-bellantuono", "assets/img/imgonline-com-ua-resize-M4JCA518Kn.jpg",
    "Social Physics, Bioinformatics in Psychiatric Genetics, Network Inequality",
    "Fisica sociale, Bioinformatica in genetica psichiatrica, Disuguaglianza di rete",
    "Loredana Bellantuono is a tenure-track assistant professor in Applied Physics at the University of Bari, Italy. Her current research interests are in Social Physics, Bioinformatics, Neuroscience and Econophysics by means of complex networks and Artificial Intelligence.",
    "Loredana Bellantuono \u00e8 ricercatrice a tempo determinato (tenure-track) in Fisica Applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano la fisica sociale, la bioinformatica, le neuroscienze e l\u2019econofisica mediante reti complesse e intelligenza artificiale.",
    "loredana.bellantuono@ba.infn.it"),
  person("tommaso-maggipinto", "assets/img/imgonline-com-ua-resize-3wvMabJA5o.jpg",
    "Health Physics, Environment, Radiation Protection",
    "Fisica sanitaria, Ambiente, Radioprotezione",
    "Tommaso Maggipinto is an associate professor of applied physics at the University of Bari, Italy. His current research interests are in environmental and health physics by means of new emerging technologies and Artificial Intelligence techniques.",
    "Tommaso Maggipinto \u00e8 professore associato di fisica applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano la fisica ambientale e sanitaria mediante nuove tecnologie emergenti e tecniche di intelligenza artificiale.",
    "tommaso.maggipinto@uniba.it"),
  person("alfonso-monaco", "assets/img/imgonline-com-ua-resize-WrCTL7rkQCi7njDh.jpg",
    "Heterogeneous System Investigation, One Health Approach, Genomics Analysis",
    "Studio di sistemi eterogenei, Approccio One Health, Analisi genomica",
    "Alfonso Monaco is associate professor (tenure-track) in Applied Physics at the University of Bari, Italy. His current research interests are in life science, medical physics and genomics by means of Artificial Intelligence and complex networks.",
    "Alfonso Monaco \u00e8 professore associato (tenure-track) in Fisica Applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano le scienze della vita, la fisica medica e la genomica mediante intelligenza artificiale e reti complesse.",
    "alfonso.monaco@ba.infn.it"),
  person("sabina-tangaro", "assets/img/imgonline-com-ua-resize-TBwvszLapOKs.jpg",
    "Health Data, Medical Imaging, Connectivity",
    "Dati sanitari, Imaging medico, Connettivit\u00e0",
    "Prof. Sabina Tangaro is an associate professor of Applied Physics at the University of Bari. Her research activity includes complex networks, artificial intelligence and explainable machine learning models for health data and images.",
    "La prof.ssa Sabina Tangaro \u00e8 professoressa associata di Fisica Applicata presso l\u2019Universit\u00e0 di Bari. La sua attivit\u00e0 di ricerca comprende reti complesse, intelligenza artificiale e modelli di machine learning spiegabile per dati e immagini sanitari.",
    "sonia.tangaro@ba.infn.it"),
  person("ester-pantaleo", "assets/img/Ester_Pantaleo.png",
    "Genomics, Natural Language Processing, Earth Observation",
    "Genomica, Elaborazione del linguaggio naturale, Osservazione della Terra",
    "Ester Pantaleo is a researcher (RTT) at the University of Bari. Her research interests focus on applications of Artificial Intelligence to Medical Physics and Remote Sensing.",
    "Ester Pantaleo \u00e8 ricercatrice (RTT) presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca si concentrano sulle applicazioni dell\u2019intelligenza artificiale alla fisica medica e al telerilevamento.",
    "ester.pantaleo@uniba.it"),
  person("domenico-diacono", "assets/img/new_diacono.jpg",
    "Machine Learning, Explainable Artificial Intelligence",
    "Machine Learning, Intelligenza artificiale spiegabile",
    "Domenico Diacono is a senior technologist at INFN (National Institute for Nuclear Physics). His current work interests are in machine learning and explainable artificial intelligence.",
    "Domenico Diacono \u00e8 tecnologo senior presso l\u2019INFN (Istituto Nazionale di Fisica Nucleare). I suoi interessi attuali riguardano il machine learning e l\u2019intelligenza artificiale spiegabile."),
  person("marianna-la-rocca", "assets/img/imgonline-com-ua-resize-QCtIb7KnPokvX1.jpg",
    "Neurodegenerative Diseases, Pattern Recognition, Electrophysiology",
    "Malattie neurodegenerative, Pattern Recognition, Elettrofisiologia",
    "Marianna La Rocca is a research-track assistant professor in applied physics at the University of Bari, Italy. Her current research interests are in complex networks, artificial intelligence, image and signal processing, and quantitative and computational methods to study different neurological conditions.",
    "Marianna La Rocca \u00e8 ricercatrice (RTD-B) in fisica applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano reti complesse, intelligenza artificiale, elaborazione di immagini e segnali e metodi quantitativi e computazionali per lo studio di diverse condizioni neurologiche.",
    "marianna.larocca@uniba.it"),
  person("roberto-cilli", "assets/img/imgonline-com-ua-resize-V8zPA0Bl8yMRkBO.jpg",
    "Remote Sensing, Earth Observation, Spatial Data Analysis, Risk Assessment",
    "Telerilevamento, Osservazione della Terra, Analisi di dati spaziali, Valutazione del rischio",
    "Roberto Cilli is a research fellow of applied physics at the University of Bari, Italy. His current research interests are in remote sensing, natural disasters and spatial data analysis by means of Artificial Intelligence.",
    "Roberto Cilli \u00e8 assegnista di ricerca in fisica applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano il telerilevamento, i disastri naturali e l\u2019analisi di dati spaziali mediante intelligenza artificiale.",
    "roberto.cilli@uniba.it"),
  person("alessandro-fania", "assets/img/imgonline-com-ua-resize-THHJGzL9ztv.jpg",
    "One Health Approach, Remote Sensing, Air Quality Monitoring",
    "Approccio One Health, Telerilevamento, Monitoraggio della qualit\u00e0 dell\u2019aria",
    "Alessandro Fania is a PhD student in applied physics at the University of Bari, Italy. His research interest is remote sensing applied to One Health models by means of Artificial Intelligence and Complex Systems.",
    "Alessandro Fania \u00e8 dottorando in fisica applicata presso l\u2019Universit\u00e0 di Bari. Il suo interesse di ricerca \u00e8 il telerilevamento applicato a modelli One Health mediante intelligenza artificiale e sistemi complessi.",
    "alessandro.fania@uniba.it"),
  person("antonio-lacalamita", "assets/img/imgonline-com-ua-resize-SqqQ2fsF1Q2PzIzi.jpg",
    "Big Data Analytics, Bioinformatics, Biomedical Data Processing",
    "Big Data Analytics, Bioinformatica, Elaborazione di dati biomedici",
    "Antonio Lacalamita is a PhD student in applied physics at the University of Bari, Italy. His current research interests are the study and development of artificial intelligence and complex network techniques in order to analyze genomic data.",
    "Antonio Lacalamita \u00e8 dottorando in fisica applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano lo studio e lo sviluppo di tecniche di intelligenza artificiale e reti complesse per l\u2019analisi di dati genomici.",
    "antonio.lacalamita@uniba.it"),
  person("andrea-lo-sasso", "assets/img/imgonline-com-ua-resize-uiYtCtPwtw.jpg",
    "Breath Analysis, Rankings, Social Inequalities",
    "Analisi del respiro, Ranking, Disuguaglianze sociali",
    "Andrea Lo Sasso is a PhD candidate in applied physics at the University of Bari, Italy. He works on the implementation of Artificial Intelligence to standardize the breath analysis process and the employment of complex networks to detect socio-economic inequalities. His MSc is in theoretical physics and complex systems.",
    "Andrea Lo Sasso \u00e8 dottorando in fisica applicata presso l\u2019Universit\u00e0 di Bari. Si occupa dell\u2019implementazione di intelligenza artificiale per standardizzare il processo di analisi del respiro e dell\u2019uso di reti complesse per rilevare disuguaglianze socio-economiche. Ha conseguito una laurea magistrale in fisica teorica e sistemi complessi.",
    "andrea.losasso@uniba.it"),
  person("pierfrancesco-novielli", "assets/img/imgonline-com-ua-resize-oarJOvY31pc66IW.jpg",
    "Genomics, Bioinformatics, Microbiome",
    "Genomica, Bioinformatica, Microbioma",
    "Pierfrancesco Novielli is a PhD student at the University of Bari \u2013 Polytechnic University of Bari. His current research interests are in microbiome, human and plant genetics by means of Artificial Intelligence and complex networks.",
    "Pierfrancesco Novielli \u00e8 dottorando presso l\u2019Universit\u00e0 di Bari \u2013 Politecnico di Bari. I suoi interessi di ricerca attuali riguardano il microbioma e la genetica umana e vegetale mediante intelligenza artificiale e reti complesse.",
    "pierfrancesco.novielli@uniba.it"),
  person("donato-romano", "assets/img/imgonline-com-ua-resize-jpkMJsNuABl.jpg",
    "One Health, Georeferenced Data, Temporal Series",
    "One Health, Dati georeferenziati, Serie temporali",
    "Donato Romano is a PhD candidate in Sustainable Land Management at the University of Bari. His current research interests are in machine learning techniques and complex network analysis applied to environmental and human health data.",
    "Donato Romano \u00e8 dottorando in Gestione Sostenibile del Territorio presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano tecniche di machine learning e analisi di reti complesse applicate a dati ambientali e di salute umana.",
    "Donato.Romano@ba.infn.it"),
  person("silvano-quarto", "assets/img/imgonline-com-ua-resize-J22iLBXh1hylRBz.jpg",
    "Cybersecurity, Blockchain, Authentication",
    "Cybersicurezza, Blockchain, Autenticazione",
    "Silvano Quarto is a research fellow in Applied Physics at the University of Bari, Italy. His current research interests are in cybersecurity and blockchain technology by means of artificial intelligence.",
    "Silvano Quarto \u00e8 assegnista di ricerca in Fisica Applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano la cybersicurezza e la tecnologia blockchain mediante intelligenza artificiale.",
    "s.quarto4@studenti.uniba.it"),
  person("domenico-pomarico", "assets/img/domenico_pomarico.jpeg",
    "Quantum machine learning, Complex Systems, Multiomics, Earth Observation",
    "Quantum machine learning, Sistemi complessi, Multiomics, Osservazione della Terra",
    "Domenico Pomarico is a researcher in applied physics at the University of Bari, Italy. His current research interests span quantum machine learning, complex systems, multi-omics data analysis, and Earth Observation, with a focus on advanced computational methods for extracting and interpreting complex patterns in high-dimensional data.",
    "Domenico Pomarico \u00e8 un ricercatore di fisica applicata presso l'Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano il quantum machine learning, i sistemi complessi, l'analisi di dati multi-omics e l'Osservazione della Terra, con un focus su metodi computazionali avanzati per l'estrazione e l'interpretazione di pattern complessi in dati ad alta dimensionalit\u00e0.",
    "domenico.pomarico@uniba.it"),
  person("michele-magarelli", "assets/img/michele_magarelli.jpeg",
    "Agrifood, Biology, Microbiome",
    "Agroalimentare, Biologia, Microbioma",
    "Michele Magarelli is a Research Fellow at the University of Bari Aldo Moro, where he obtained his PhD in Sustainable Land Management. His current research interests include Artificial Intelligence, Explainable AI, Machine Learning, multi-omics and microbiome data analysis, with applications in the biomedical, agri-food, and environmental fields.",
    "Michele Magarelli \u00e8 assegnista di ricerca presso l'Universit\u00e0 degli Studi di Bari Aldo Moro, dove ha conseguito il dottorato in Gestione Sostenibile del Territorio. I suoi interessi di ricerca attuali includono Intelligenza Artificiale, AI Spiegabile, Machine Learning, analisi di dati multi-omics e del microbioma, con applicazioni nei campi biomedico, agroalimentare e ambientale.",
    "michele.magarelli@uniba.it"),
]

SITE["collaborators"] = [
  person("annamaria-demarinis-loiotile", "assets/img/imgonline-com-ua-resize-EGqFIMq6pbQF.jpg",
    "Intellectual Property Analytics, Technology Transfer, Healthcare 4.0",
    "Analisi della propriet\u00e0 intellettuale, Trasferimento tecnologico, Healthcare 4.0",
    "Chemist, responsible for the Third Mission Office at the University of Bari Aldo Moro. PhD student in \u201cIndustry 4.0\u201d at the University of Bari \u2013 Politecnico di Bari with research interest in Intellectual Property Analytics.",
    "Chimico, responsabile dell\u2019Ufficio Terza Missione dell\u2019Universit\u00e0 di Bari Aldo Moro. Dottoranda in \u201cIndustria 4.0\u201d presso l\u2019Universit\u00e0 di Bari \u2013 Politecnico di Bari con interesse di ricerca nell\u2019analisi della propriet\u00e0 intellettuale.",
    "annamaria.demarinis@uniba.it"),
  person("annarita-fanizzi", "assets/img/fanizzi2.jpg",
    "Breast Cancer, Multimodal Imaging, Biostatistics",
    "Tumore al seno, Imaging multimodale, Biostatistica",
    "Since July 2010, Annarita Fanizzi has been involved in a research project on the study and development of a support system for the diagnosis of breast cancer based on multimodal imaging at the Istituto Tumori \u201cGiovanni Paolo II\u201d in Bari. In 2011 she obtained a PhD in Statistics at the University of Bari \u201cA. Moro\u201d.",
    "Dal luglio 2010 Annarita Fanizzi \u00e8 impegnata in un progetto di ricerca per lo studio e lo sviluppo di un sistema di supporto alla diagnosi del tumore al seno basato su imaging multimodale presso l\u2019Istituto Tumori \u201cGiovanni Paolo II\u201d di Bari. Nel 2011 ha conseguito il dottorato in Statistica presso l\u2019Universit\u00e0 di Bari \u201cA. Moro\u201d."),
  person("federica-cuna", "assets/img/Federica.jpg",
    "Neuroscience, EEG, Brain Imaging",
    "Neuroscienze, EEG, Imaging cerebrale",
    "Federica Cuna is a research fellow in Applied Physics at the University of Bari. Her current research interests deal with Neuroscience by means of Machine Learning and Complex Networks.",
    "Federica Cuna \u00e8 assegnista di ricerca in Fisica Applicata presso l\u2019Universit\u00e0 di Bari. I suoi interessi di ricerca attuali riguardano le neuroscienze mediante machine learning e reti complesse.",
    "federica.cuna@le.infn.it"),
  person("raffaella-massafra", "assets/img/Foto_Raffaella-Massafra.jpg",
    "Biomedical Data Analysis, Machine Learning",
    "Analisi di dati biomedici, Machine Learning",
    "Dr. Raffaella Massafra has collaborated with the Medical Physics group at the University of Bari Aldo Moro since 2003. She has been a promoter in the development of methodologies for the analysis of biomedical data through machine learning.",
    "La dott.ssa Raffaella Massafra collabora con il gruppo di Fisica Medica dell\u2019Universit\u00e0 di Bari Aldo Moro dal 2003. \u00c8 stata promotrice dello sviluppo di metodologie per l\u2019analisi di dati biomedici mediante machine learning."),
  person("rosangela-errico", "assets/img/new_rosangela_errico2.png",
    "Image Registration, Image Segmentation",
    "Registrazione di immagini, Segmentazione di immagini",
    "Rosangela Errico graduated cum laude in Physics at the Universit\u00e0 degli Studi di Bari \u201cA. Moro\u201d in 2012. She is currently a postgraduate student at the School of Medical Physics of the Universit\u00e0 degli Studi di Genova. Her research activity deals with image registration and image segmentation.",
    "Rosangela Errico si \u00e8 laureata con lode in Fisica presso l\u2019Universit\u00e0 degli Studi di Bari \u201cA. Moro\u201d nel 2012. Attualmente \u00e8 specializzanda presso la Scuola di Specializzazione in Fisica Medica dell\u2019Universit\u00e0 degli Studi di Genova. La sua attivit\u00e0 di ricerca riguarda la registrazione e la segmentazione di immagini."),
  person("gianluca-sforza", "assets/img/new_Gian-13.png",
    "Medical Imaging, Computer Science",
    "Imaging medico, Informatica",
    "Gianluca Sforza is currently a post-doc research fellow at INFN, Bari Section. He joined the Medical Physics group in May 2017. After his master\u2019s degree in Computer Science in 2007 at the University of Bari \u201cAldo Moro\u201d, he attended the PhD school in Computer Science, focusing on techniques for image segmentation.",
    "Gianluca Sforza \u00e8 attualmente assegnista di ricerca post-doc presso la Sezione INFN di Bari. \u00c8 entrato nel gruppo di Fisica Medica nel maggio 2017. Dopo la laurea magistrale in Informatica nel 2007 presso l\u2019Universit\u00e0 di Bari \u201cAldo Moro\u201d, ha frequentato il dottorato in Informatica, concentrandosi su tecniche di segmentazione di immagini."),
  person("eufemia-lella", "assets/img/new_Eufemia_foto.png",
    "Medical Physics",
    "Fisica Medica",
    "Eufemia Lella is a PhD student in the Medical Physics group, Department of Physics, University of Bari.",
    "Eufemia Lella \u00e8 dottoranda nel gruppo di Fisica Medica, Dipartimento di Fisica, Universit\u00e0 di Bari.",
    "eufemia.lella@ba.infn.it"),
  person("andrea-tateo", "assets/img/new_a_tateo.png",
    "Applied Physics",
    "Fisica Applicata",
    "Andrea Tateo collaborated with the Medical Physics group from 2011 to 2020. He was a research fellow (2019\u20132020) and lecturer in Physics and Applied Physics at the University of Bari.",
    "Andrea Tateo ha collaborato con il gruppo di Fisica Medica dal 2011 al 2020. \u00c8 stato assegnista di ricerca (2019\u20132020) e titolare di insegnamenti di Fisica e Fisica Applicata presso l\u2019Universit\u00e0 di Bari."),
]

# ---------------- PROJECTS ----------------
def proj(slug, img, title_en, title_it, dur, abs_en, abs_it, period=""):
    return {"slug": slug, "img": img, "title": {"en": title_en, "it": title_it},
            "duration": dur, "period": period, "abstract": {"en": abs_en, "it": abs_it}}

SITE["projects"] = {"ongoing": [], "past": []}

SITE["projects"]["ongoing"].append(proj(
  "progetto-gunnebo-innovation-hub", "assets/img/gunnebo_logo_ok.png",
  "Gunnebo Innovation Hub", "Progetto Gunnebo Innovation Hub", "Jan 2021 \u2013 May 2024",
  "The project involves the implementation of technologies concerning the development of advanced image processing algorithms using Machine Learning and Artificial Intelligence technologies. The innovations implemented are aimed at authentication with biometric solutions for facial and voice recognition for digital locks on B2C (Business-to-Consumer) products.",
  "Il progetto prevede l\u2019implementazione di tecnologie relative allo sviluppo di algoritmi avanzati di elaborazione delle immagini mediante tecniche di Machine Learning e Intelligenza Artificiale. Le innovazioni introdotte sono finalizzate all\u2019autenticazione con soluzioni biometriche per il riconoscimento facciale e vocale per serrature digitali su prodotti B2C (Business-to-Consumer)."))

SITE["projects"]["ongoing"].append(proj(
  "tebaka-sistema-per-acquisizione-conoscenze-di-base-del-territorio", "assets/img/intro-tebaka-dta.png",
  "TEBAKA \u2013 Territory baseline knowledge acquisition system", "TEBAKA \u2013 Sistema per acquisizione conoscenze di base del territorio", "Nov 2020 \u2013 Apr 2024",
  "The basic objectives of the proposed industrial research project are: the structured acquisition of knowledge (representable through defined and experimentally validated models and algorithms/calculation codes) related to the conditions peculiar to the annual life cycle of agricultural crops of wheat, grapevine and olive and related significant land/environmental variables; the realization of an integrated multiscale system of satellite, airborne and ground-based (mobile and fixed) payloads/platforms and a mobile command/control center, for the management of systematic, targeted and specific observations of crops and related territories/environments; the definition and implementation of an environment, networked with the command/control center, for managing the storage of the large amounts of data acquired and their manipulation in order to build a machine learning system for predictive modeling and decision support in the domain of agricultural crops; the design of a service, distributed over the network, for growers to provide them with the correct information to support optimal management of their crops; the definition of the best methodology and observation missions at the various stages of the annual crop production cycle to optimize cost-effectiveness.",
  "Gli obiettivi di base del progetto di ricerca industriale proposto sono: l\u2019acquisizione strutturata di conoscenze (rappresentabili tramite modelli e algoritmi/codici di calcolo definiti e validati sperimentalmente) relative alle condizioni peculiari del ciclo di vita annuale delle colture agricole di grano, vite e olivo e alle relative variabili significative del territorio/ambiente; la realizzazione di un sistema multiscala integrato di payload/piattaforme satellitari, aeroportati e a terra (mobili e fissi) e di un centro mobile di comando/controllo, per la gestione di osservazioni sistematiche, mirate e specifiche delle colture e dei relativi territori/ambienti; la definizione e l\u2019implementazione di un ambiente, in rete con il centro di comando/controllo, per la gestione dell\u2019archiviazione delle grandi quantit\u00e0 di dati acquisiti e della loro manipolazione al fine di costruire un sistema di machine learning per la modellazione predittiva e il supporto decisionale nel dominio delle colture agricole; la progettazione di un servizio, distribuito sulla rete, per i coltivatori in grado di fornire loro, in modo semplice ed economicamente sostenibile, le informazioni corrette per supportare la gestione ottimale dei processi del ciclo produttivo annuale; la definizione della migliore metodologia e delle missioni di osservazione nelle varie fasi del ciclo produttivo annuale per ottimizzare il rapporto costo-efficacia."))

SITE["projects"]["past"].append(proj(
  "sapere-avviso-innolabs-soluzioni-innovative-per-problemi-di-rilevanza-sociale-dta-distretto-tecnologico-aerospaziale", "assets/img/intro-sapere-dta.png",
  "SAPERE \u2013 Innovative solutions for socially relevant problems", "SAPERE \u2013 Soluzioni innovative per problemi di rilevanza sociale", "Feb 2020 \u2013 Aug 2021",
  "The objective of the project was to define and develop innovative solutions, based on the use of images of the territory acquired by satellite and/or through sensors carried on remotely piloted aircraft, for the acquisition of information about the territory itself, its processing and distribution for the planning and management of the plans under the responsibility of municipal administrations. These solutions are tools to support both the administration and the freelancers who collaborate in the plan drafting and plan implementation verification phases. The project intends to facilitate and enrich the process of drafting and managing the Municipal Urban Plan, from the knowledge frameworks of the Preliminary Planning Document to the subsequent adoption of the PUG and its activation through the PUEs.",
  "L\u2019obiettivo del progetto era definire e sviluppare soluzioni innovative, basate sull\u2019uso di immagini del territorio acquisite da satellite e/o tramite sensori trasportati su aeromobili a pilotaggio remoto, per l\u2019acquisizione di informazioni sul territorio stesso, la loro elaborazione e distribuzione per la pianificazione e la gestione dei piani di competenza delle amministrazioni comunali. Tali soluzioni sono strumenti a supporto sia dell\u2019amministrazione sia dei professionisti che collaborano nelle fasi di redazione del piano e di verifica dell\u2019attuazione. Il progetto intende facilitare e arricchire il processo di redazione e gestione del Piano Urbanistico Generale, dai quadri conoscitivi del Documento Programmatico Preliminare alla successiva adozione del PUG e alla sua attivazione tramite i PUE."))

SITE["projects"]["past"].append(proj(
  "decision-data-driven-customer-service-innovation", "assets/img/decision.jpeg",
  "DECiSION \u2013 Data-drivEn Customer Service InnovatiON", "DECiSION \u2013 Data-drivEn Customer Service InnovatiON", "2018 \u2013 2020",
  "Data-drivEn Customer Service InnovatiON \u2013 POR Puglia FESR 2014-2020, Action 1.6, INNONETWORK call for support to R&D activities for the development of new sustainable technologies, new products and services \u2013 DECiSION project, grouping code BQS5153 (2018\u20132020). Researchers from the Department of Physics and the INFN Bari Section developed systems based on machine learning algorithms for the analysis of geolocated time series of territory deformation for early warning of water and sewerage networks. Support was also provided to the project through the ReCaS Datacenter.",
  "Data-drivEn Customer Service InnovatiON \u2013 POR Puglia FESR 2014-2020 \u2013 Azione 1.6 Bando INNONETWORK SOSTEGNO ALLE ATTIVIT\u00c0 DI R&S PER LO SVILUPPO DI NUOVE TECNOLOGIE SOSTENIBILI, DI NUOVI PRODOTTI E SERVIZI \u2013 progetto DECiSION codice raggruppamento: BQS5153 (2018-2020). I ricercatori del Dipartimento di Fisica e della sezione INFN di Bari hanno sviluppato sistemi basati su algoritmi di machine learning per l\u2019analisi di serie temporali geolocalizzate di deformazione del territorio per l\u2019early warning di reti idrico-fognarie. Inoltre \u00e8 stato fornito supporto al progetto attraverso il Datacenter ReCaS."))

SITE["projects"]["past"].append(proj(
  "person-pervasive-game-for-personalized-treatment-of-cognitive-and-functional-deficits-associated-with-chronic-and-neurodegenerative-diseases", "assets/img/Adobe-Scan-28-apr-2023-1.png",
  "PERSON \u2013 Pervasive game for personalized treatment of cognitive and functional deficits", "PERSON \u2013 Gioco pervasivo per il trattamento personalizzato dei deficit cognitivi e funzionali", "2016 \u2013 2017",
  "The PERSON project aims to achieve an ICT environment for diagnosis and therapy, based on a pervasive and innovative system, both for the early diagnosis of neurodegenerative diseases and to support personalized therapy processes in the case of diagnosed pathology. A new-generation pervasive game will be developed with which the user can interact. During the interaction the game will be able to diagnose, together with the doctor, the player\u2019s disease status and suggest therapeutic exercises in the form of a game, relieving symptoms of cognitive impairment and/or slowing the progression of disability. The continuous adaptation of the therapy to the patients\u2019 reactions will be implemented through wearable hardware (sensors and actuators) and algorithms for user profiling and adaptivity able to analyze the data and determine the treatment to be given. The algorithms developed in the PERSON project will be available and can be used on the PRISMA Cloud platform implemented on the RECAS Datacenter.",
  "Il progetto PERSON mira a realizzare un ambiente ICT per la diagnosi e la terapia, basato su un sistema pervasivo e innovativo, sia per la diagnosi precoce delle malattie neurodegenerative sia per supportare i processi di terapia personalizzata in caso di patologia diagnosticata. Sar\u00e0 sviluppato un gioco pervasivo di nuova generazione con cui l\u2019utente potr\u00e0 interagire. Durante l\u2019interazione il gioco sar\u00e0 in grado di diagnosticare, insieme al medico, lo stato della malattia del giocatore e suggerire esercizi terapeutici sotto forma di gioco, attenuando i sintomi del deficit cognitivo e/o rallentando la progressione della disabilit\u00e0. L\u2019adattamento continuo della terapia alle reazioni dei pazienti sar\u00e0 implementato tramite hardware indossabile (sensori e attuatori) e algoritmi di profilazione e adattivit\u00e0 dell\u2019utente in grado di analizzare i dati e determinare il trattamento da erogare. Gli algoritmi sviluppati nel progetto PERSON saranno disponibili e potranno essere utilizzati sulla piattaforma PRISMA Cloud implementata sul Datacenter RECAS."))

SITE["projects"]["past"].append(proj(
  "nextmr-advancing-magnetic-resonance-imaging-and-data-analysis", "assets/img/nextmr.png",
  "nextMR \u2013 advancing Magnetic Resonance Imaging and Data Analysis", "nextMR \u2013 advancing Magnetic Resonance Imaging and Data Analysis", "2015 \u2013 2017",
  "The nextMR proposal addresses a selected number of open problems in clinical research where the nontrivial use of MRI techniques and data analysis could be instrumental in the solution. While the key to the clinical questions is generally complex and involves other examinations (e.g. PET, neuropsychology, genetic and molecular data), the proponents use these complementary data to maximize the contribution of MRI-based information whenever possible. The research activity is divided into three intertwined branches: hardware, protocols and data analysis.",
  "La proposta nextMR affronta un numero selezionato di problemi aperti nella ricerca clinica in cui l\u2019uso non banale di tecniche MRI e di analisi dei dati potrebbe essere determinante per la soluzione. Poich\u00e9 la chiave delle domande cliniche \u00e8 generalmente complessa e coinvolge altri esami (ad es. PET, neuropsicologia, dati genetici e molecolari), i proponenti utilizzano questi dati complementari per massimizzare, ove possibile, il contributo delle informazioni basate su MRI. L\u2019attivit\u00e0 di ricerca \u00e8 suddivisa in tre rami interconnessi: hardware, protocolli e analisi dei dati."))

SITE["projects"]["past"].append(proj(
  "medical-imaging-for-neurodegenerative-diseases-mind", "assets/img/mind.png",
  "MIND \u2013 Medical Imaging for Neurodegenerative Diseases", "MIND \u2013 Medical Imaging for Neurodegenerative Diseases", "2012 \u2013 2013",
  "Until recently the segmentation of the hippocampus, i.e. its identification and separation from surrounding brain structures, was performed mainly manually or with semi-automated techniques, followed by manual editing. This is obviously time-consuming and subject to investigator variability, so a number of automated segmentation methods have been developed. In this project a fully automated pattern recognition system for accurate and reproducible segmentation of the hippocampus in structural Magnetic Resonance Imaging (MRI) is presented. The system has been validated on T1-weighted structural brain MR images. The proposed approach can be useful for large-scale research studies, in the first instance on Alzheimer\u2019s disease, where hippocampal volume is an important biomarker, but also on other brain disorders in which the hippocampus plays a relevant pathogenetic role.",
  "Fino a poco tempo fa la segmentazione dell\u2019ippocampo, cio\u00e8 la sua identificazione e separazione dalle strutture cerebrali circostanti, era eseguita principalmente manualmente o con tecniche semi-automatiche, seguite da editing manuale. Ci\u00f2 richiede molto tempo ed \u00e8 soggetto alla variabilit\u00e0 dell\u2019operatore, perci\u00f2 sono stati sviluppati diversi metodi di segmentazione automatica. In questo progetto viene presentato un sistema di pattern recognition completamente automatico per una segmentazione accurata e riproducibile dell\u2019ippocampo in risonanza magnetica strutturale (MRI). Il sistema \u00e8 stato validato su immagini MR cerebrali strutturali pesate in T1. L\u2019approccio proposto pu\u00f2 essere utile per studi su larga scala, in primo luogo sulla malattia di Alzheimer, dove il volume dell\u2019ippocampo \u00e8 un importante biomarcatore, ma anche su altri disturbi cerebrali in cui l\u2019ippocampo svolge un ruolo patogenetico rilevante."))

SITE["projects"]["past"].append(proj(
  "medical-applications-on-a-grid-infrastructure-connection-magic-5", "assets/img/www.maxpixel.net-Neurons-Brain-Cells-Brain-Brain-Structure-Network-1739997-500x310.jpg",
  "MAGIC-5 \u2013 Medical Applications on a Grid Infrastructure Connection", "MAGIC-5 \u2013 Medical Applications on a Grid Infrastructure Connection", "2007 \u2013 2012",
  "The MAGIC-5 Project aims at developing Computer Aided Detection (CAD) software for Medical Applications on distributed databases by means of a GRID Infrastructure Connection. The use of automatic systems for analyzing medical images is of paramount importance in screening programs, due to the huge amount of data to check. Examples are mammographies for breast cancer detection, Computed Tomography (CT) images for lung cancer analysis, and Positron Emission Tomography (PET) imaging for the early diagnosis of Alzheimer\u2019s disease. The need to acquire and analyze data stored in different locations requires a GRID approach of distributed computing systems and associated data management. GRID technologies allow remote image analysis and interactive online diagnosis, with a relevant reduction of the delays actually associated with screening programs. From this point of view, the MAGIC-5 collaboration can be seen as a group of distributed users sharing their resources to implement different Virtual Organizations (VO), each aiming at developing screening programs, tele-training, tele-diagnosis and epidemiologic studies for a particular pathology.",
  "Il progetto MAGIC-5 mira a sviluppare software di Computer Aided Detection (CAD) per applicazioni mediche su database distribuiti tramite una GRID Infrastructure Connection. L\u2019uso di sistemi automatici per l\u2019analisi di immagini mediche \u00e8 di fondamentale importanza nei programmi di screening, data l\u2019enorme quantit\u00e0 di dati da esaminare. Esempi sono le mammografie per l\u2019individuazione del tumore al seno, le immagini di tomografia computerizzata (CT) per l\u2019analisi del cancro ai polmoni e l\u2019imaging con tomografia a emissione di positroni (PET) per la diagnosi precoce della malattia di Alzheimer. La necessit\u00e0 di acquisire e analizzare dati archiviati in localit\u00e0 diverse richiede un approccio GRID di sistemi di calcolo distribuito e gestione associata dei dati. Le tecnologie GRID consentono l\u2019analisi remota delle immagini e la diagnosi interattiva online, con una riduzione rilevante dei ritardi attualmente associati ai programmi di screening. Da questo punto di vista la collaborazione MAGIC-5 pu\u00f2 essere vista come un gruppo di utenti distribuiti che condividono le proprie risorse per implementare diverse Virtual Organization (VO), ciascuna finalizzata a sviluppare programmi di screening, tele-formazione, tele-diagnosi e studi epidemiologici per una particolare patologia."))

SITE["projects"]["past"].append(proj(
  "beam-line-from-thomson-source-beats", "assets/img/586px-Cheek_cell_phase_contrast-500x310.jpg",
  "BEATS \u2013 BEAm line from Thomson Source", "BEATS \u2013 BEAm line from Thomson Source", "2008 \u2013 2012",
  "The group\u2019s activities were focused on studying the potential of Thomson imaging sources (TS) in terms of visibility of details in phase contrast (PC) and phase mapping (PRI) images compared with the detail visibility in absorption images. A new analytical/numerical method, called Combined Mixed Approach (CMA), was developed for the reconstruction of phase maps from X-ray images. PRI allows a quantitative approach because the phase map is directly proportional to the electron density of the object and can therefore provide essential information on the internal structures of objects/tissues. Some preliminary experiments were performed at synchrotron sources with different samples, showing significant increases in image quality compared with X-ray absorption imaging.",
  "Le attivit\u00e0 del gruppo si sono concentrate sullo studio delle potenzialit\u00e0 delle sorgenti di imaging Thomson (TS) in termini di visibilit\u00e0 dei dettagli nelle immagini a contrasto di fase (PC) e di mappatura di fase (PRI) rispetto alla visibilit\u00e0 dei dettagli nelle immagini di assorbimento. \u00c8 stato sviluppato un nuovo metodo analitico/numerico, chiamato Combined Mixed Approach (CMA), per la ricostruzione delle mappe di fase da immagini a raggi X. Il PRI consente un approccio quantitativo poich\u00e9 la mappa di fase \u00e8 direttamente proporzionale alla densit\u00e0 elettronica dell\u2019oggetto e pu\u00f2 quindi fornire informazioni essenziali sulle strutture interne di oggetti/tesuti. Alcuni esperimenti preliminari sono stati condotti presso sorgenti di sincrotrone con diversi campioni, mostrando incrementi significativi della qualit\u00e0 dell\u2019immagine rispetto all\u2019imaging per assorbimento a raggi X."))

# ---------------- CHALLENGES ----------------
def chal(slug, img, title_en, title_it, desc_en, desc_it, url):
    return {"slug": slug, "img": img, "title": {"en": title_en, "it": title_it},
            "desc": {"en": desc_en, "it": desc_it}, "url": url}

SITE["challenges"] = [
  chal("mci-challenge", "assets/img/mci-e1537816970354.png",
    "MCI Challenge", "MCI Challenge",
    "A machine learning neuroimaging challenge for automated diagnosis of Mild Cognitive Impairment.",
    "Una sfida di neuroimaging con machine learning per la diagnosi automatica del deterioramento cognitivo lieve (MCI).",
    "https://www.kaggle.com/c/mci-prediction"),
  chal("preterm-birth-prediction-microbiome-dream-challenge", "assets/img/Preterm-birth-copia-scaled.jpg",
    "Preterm Birth Prediction \u2013 Microbiome DREAM Challenge", "Preterm Birth Prediction \u2013 Microbiome DREAM Challenge",
    "A machine learning challenge for the prediction of high-risk preterm births using microbiome data.", 
    "Una sfida di machine learning per la previsione dei parti pretermine ad alto rischio utilizzando dati del microbioma.",
    "https://www.synapse.org/#!Synapse:syn26133770/wiki/612541"),
  chal("mtop2016", "assets/img/MTOP-e1537711435958.png",
    "mTOP 2016", "mTOP 2016",
    "Mild Traumatic Brain Injuries (mTOP) in MICCAI 2016 \u2013 winner.",
    "Mild Traumatic Brain Injuries (mTOP) in MICCAI 2016 \u2013 vincitore.",
    "https://tbichallenge.wordpress.com/"),
  chal("dream1", "assets/img/challenge_alzheimers.jpg",
    "DREAM Challenge #1", "DREAM Challenge #1",
    "Alzheimer\u2019s Disease Big Data DREAM Challenge #1, organized by Sage Bionetworks (USA), over 500 scientist participants.",
    "Alzheimer\u2019s Disease Big Data DREAM Challenge #1, organizzato da Sage Bionetworks (USA), oltre 500 scienziati partecipanti.",
    "https://www.synapse.org/#!Synapse:syn2290704/wiki/60828"),
  chal("caddementia", "assets/img/caddementia-e1537711475200.png",
    "MICCAI CADDementia Challenge", "MICCAI CADDementia Challenge",
    "Challenge on Computer-Aided Diagnosis of Dementia based on structural MRI data, in MICCAI CADDementia, organized by the Biomedical Imaging Group Rotterdam, Erasmus MC, Rotterdam, The Netherlands.",
    "Sfida sulla diagnosi assistita dal computer della demenza basata su dati MRI strutturali, in MICCAI CADDementia, organizzata dal Biomedical Imaging Group Rotterdam, Erasmus MC, Rotterdam, Paesi Bassi.",
    "https://caddementia.grand-challenge.org/"),
  chal("mlc", "assets/img/caddementia-e1537711475200.png",
    "MICCAI MLC Challenge", "MICCAI MLC Challenge",
    "Machine Learning Challenge: predicting binary and continuous phenotypes from structural brain MRI data, in MICCAI MLC, organized by the Laboratory for Computational Imaging Biomarkers, Harvard Medical School (Boston, USA) \u2013 winner.",
    "Machine Learning Challenge: previsione di fenotipi binari e continui da dati MRI cerebrali strutturali, in MICCAI MLC, organizzata dal Laboratory for Computational Imaging Biomarkers, Harvard Medical School (Boston, USA) \u2013 vincitore.",
    "https://www.nmr.mgh.harvard.edu/lab/laboratory-computational-imaging-biomarkers/miccai-2014-machine-learning-challenge"),
  chal("anode09", "assets/img/anode-e1537712100743.png",
    "ANODE 09", "ANODE 09",
    "Comparing and combining algorithms for computer-aided detection of pulmonary nodules in computed tomography scans, ANODE 09, organized by the Image Sciences Institute, University Medical Center Utrecht, The Netherlands.",
    "Confronto e combinazione di algoritmi per la diagnosi assistita dal computer dei noduli polmonari in scansioni di tomografia computerizzata, ANODE 09, organizzata dall\u2019Image Sciences Institute, University Medical Center Utrecht, Paesi Bassi.",
    "https://anode09.grand-challenge.org/"),
]

# ---------------- PUBLICATIONS ----------------
SITE["publications"] = [
  {"slug": "journal-papers", "en": "Journal papers", "it": "Articoli su rivista", "desc": {"en": "Peer-reviewed articles published in international journals.", "it": "Articoli con revisione paritaria pubblicati su riviste internazionali."}},
  {"slug": "book-chapters", "en": "Book chapters", "it": "Capitoli di libro", "desc": {"en": "Contributions published as chapters in scientific books.", "it": "Contributi pubblicati come capitoli in volumi scientifici."}},
  {"slug": "refereed-proceedings", "en": "Refereed proceedings", "it": "Atti di convegno con revisione", "desc": {"en": "Papers published in refereed conference proceedings.", "it": "Lavori pubblicati in atti di convegno con revisione."}},
]

# ---------------- JOIN US ----------------
SITE["join_us"] = {
  "intro": {
    "en": "We welcome motivated students interested in medical physics, artificial intelligence, complex networks and data science. The following master\u2019s degree thesis titles are currently available.",
    "it": "Accogliamo con piacere studenti motivati interessati a fisica medica, intelligenza artificiale, reti complesse e data science. Sono attualmente disponibili i seguenti titoli di tesi di laurea magistrale."
  },
  "col_title": {"en": "Master Degree Thesis titles", "it": "Titoli di tesi di laurea magistrale"},
  "col_sup": {"en": "Supervisors", "it": "Relatori"},
  "theses": [
    {"t": {"en": "Functional connectivity study to predict/characterize post-traumatic epilepsy", "it": "Studio di connettivit\u00e0 funzionale per predire/caratterizzare l\u2019epilessia post-traumatica"}, "s": "Dott.ssa Marianna La Rocca, Prof. Nicola Amoroso"},
    {"t": {"en": "fNIRS and EEG connectivity to study the effects of migraine therapies", "it": "Connettivit\u00e0 fNIRS ed EEG per studiare gli effetti delle terapie per l\u2019emicrania"}, "s": "Dott.ssa Marianna La Rocca, Prof. Roberto Bellotti"},
    {"t": {"en": "Acquisition and processing of imaging data for the study of brain dynamics", "it": "Acquisizione ed elaborazione di dati di imaging per lo studio della dinamica cerebrale"}, "s": "Prof. Sonia Tangaro, Prof. Roberto Bellotti"},
    {"t": {"en": "Explainable Artificial Intelligence for microbiome data analysis for new disease biomarker identification", "it": "Intelligenza artificiale spiegabile per l\u2019analisi di dati del microbioma per l\u2019identificazione di nuovi biomarcatori di malattia"}, "s": "Prof. Sonia Tangaro, Prof. Roberto Bellotti"},
    {"t": {"en": "A comparison of classical and tensor network machine learning for medical image classification", "it": "Confronto tra machine learning classico e a tensor network per la classificazione di immagini mediche"}, "s": "Dott. Monaco, Dott. Domenico Pomarico"},
    {"t": {"en": "eXplainable Artificial Intelligence on Raman spectra of thyroid samples supports early diagnosis of carcinoma", "it": "Intelligenza artificiale spiegabile su spettri Raman di campioni tiroidei a supporto della diagnosi precoce del carcinoma"}, "s": "Dott.ssa Loredana Bellantuono, Dott. Alfonso Monaco"},
    {"t": {"en": "A complex network framework to quantify the resilience of infrastructures with respect to natural disasters", "it": "Un framework di reti complesse per quantificare la resilienza delle infrastrutture rispetto ai disastri naturali"}, "s": "Dott.ssa Loredana Bellantuono, Prof. Roberto Bellotti"}
  ]
}

# ---------------- COURSES / PROTECTED ----------------
SITE["courses"] = {
  "items": [
    {"en": "Pattern Recognition \u2013 Prof. Roberto Bellotti", "it": "Pattern Recognition \u2013 Prof. Roberto Bellotti"}
  ]
}
SITE["protected"] = {
  "short-course": {"title": {"en": "Short Course", "it": "Short Course"}},
  "conference-slides": {"title": {"en": "Conference slides", "it": "Slide dei convegni"}},
  "pattern_recognition": {"title": {"en": "Labs", "it": "Laboratori"}}
}
SITE["protected_msg"] = {
  "en": "This content is password protected. To view it please enter your password below.",
  "it": "Questo contenuto \u00e8 protetto da password. Per visualizzarlo inserisci la tua password qui sotto."
}

# ---------------- NEWSROOM ----------------
NEWS = [
  ("Comune di Bari", "logo_comune_bari.png", "http://www.comune.bari.it/-/il-sindaco-consegna-a-roberto-bellotti-il-riconoscimento-dell-amministrazione-comunale-per-le-sue-importanti-ricerche"),
  ("CB Insights", "cbi_logo_marketing.png", "https://www.cbinsights.com/research/alzheimers-disease-artificial-intelligence-detection/"),
  ("The Times", "times-white-small-f4ad00a748.png", "https://www.thetimes.co.uk/article/ai-can-identify-alzheimer-s-a-decade-before-symptoms-appear-9b3qdrrf7"),
  ("Famiglia Cristiana", "famiglia_cristiana.png", "http://m.famigliacristiana.it/articolo/alzheimer-e-l-algoritmo-che-lo-predice.htm"),
  ("Corriere della Sera", "corriere_della_sera.png", "http://www.corriere.it/cronache/17_settembre_21/grazie-un-algoritmo-macchina-scoprira-l-alzheimer-dieci-anni-prima-ricerca-fisica-95138e2e-9e3b-11e7-a6ea-abd1a52d72e1.shtml"),
  ("Tanta Salute", "tanta_salute.png", "http://www.tantasalute.it/articolo/alzheimer-diagnosi-10-anni-prima-con-l-intelligenza-artificiale/65785/"),
  ("la Repubblica", "repubblica.png", "http://www.repubblica.it/salute/ricerca/2017/09/20/news/alzheimer_l_intelligenza_artificiale_per_scovare_la_malattia_10_anni_prima-176018356/"),
  ("Newsweek", "Newsweek.png", "https://www.newsweek.com/alzheimers-test-artificial-intelligence-spots-symptoms-years-doctors-668373"),
  ("Fast Company", "fastcompany.png", "https://www.fastcompany.com/40470639/scientists-say-ai-can-predict-alzheimers-a-decade-before-symptoms-show"),
  ("BT", "BT_mark_4col_rev_80x46.png", "http://home.bt.com/tech-gadgets/tech-news/ai-could-spot-alzheimers-in-mri-scans-up-to-a-decade-before-symptoms-show-11364213607927"),
  ("Breitbart", "breitbart.png", "https://www.breitbart.com/tech/2017/09/20/researchers-develop-a-i-that-can-detect-alzheimers-a-decade-before-visible-symptoms/amp/"),
  ("Health Imaging", "logo-HI.png", "http://www.healthimaging.com/topics/imaging-informatics/ai-detects-brain-changes-related-alzheimer%E2%80%99s-10-years-symptoms-appear"),
  ("Chief Observer", "chiefObserver.png", "http://chiefobserver.com/2017/09/ai-turns-out-to-be-the-most-powerful-tool-for-detecting-alzheimers-disease-at-an-early-stage/"),
  ("Daily Express", "express.png", "https://www.express.co.uk/news/uk/856694/alzheimers-disease-breakthrough-artificial-Intelligence-indentify-dementia/amp"),
  ("The Sun", "sun.png", "https://www.thesun.co.uk/news/4503707/artificial-intelligence-can-pick-up-alzheimers-10-years-before-symptoms/amp/"),
  ("Power Hour Nation", "powerHourNation.png", "https://powerhournation.com/artificial-intelligence-now-predicting-alzheimers/"),
  ("Tecnologia e Ricerca", "tecnologiaericerca.png", "http://www.tecnologiaericerca.com/2017/09/19/lotta-allalzheimer-uno-studio-ne-dimostra-la-diagnosi-dieci-anni-prima/"),
  ("Il Mattino", "ilmattino.png", "http://www.ilmattino.it/tecnologia/scienza/alzheimer_intelligenza_artificiale-3248905.html"),
  ("NZ Herald", "nzherald.co_.nz_.png", "http://www.nzherald.co.nz/technology/news/article.cfm?c_id=5&objectid=11923628"),
  ("Adnkronos", "logo-top.gif", "https://www.adnkronos.com/salute/medicina/2017/09/18/intelligenza-artificiale-prevede-alzheimer-anni-prima_O7yvmc9kJy203v72gkrDTM_amp.html"),
  ("Tom\u2019s Hardware", "tom.png", "https://www.tomshw.it/ia-italiana-ci-dira-se-10-anni-avremo-alzheimer-88350"),
  ("Il Fatto Quotidiano", "ilFattoQuotidiano.png", "http://www.ilfattoquotidiano.it/2017/09/18/alzheimer-con-lintelligenza-artificiale-si-puo-diagnosticare-dieci-anni-prima/3863485/"),
  ("Corriere del Mezzogiorno", "corriere_del_mezzogiorno.png", "http://corrieredelmezzogiorno.corriere.it/bari/salute/17_settembre_18/diagnosi-precoce-dell-alzheimer-l-intelligenza-artificiale-defa1c92-9c5b-11e7-85de-930379838927.shtml"),
  ("La Gazzetta del Mezzogiorno", "GdM_Nuova_Testata_rid_new_2.jpg", "http://www.lagazzettadelmezzogiorno.it/news/home/930710/l-alzheimer-10-anni-prima-grazie-ad-algoritmo-intelligente.html"),
  ("BariToday", "bariToday.png", "http://www.baritoday.it/cronaca/alzheimer-scoperta-universita-bari-intelligenza-artificiale.html"),
  ("The Week", "theWeek.png", "http://www.theweek.co.uk/88443/ai-can-detect-alzheimer-s-a-decade-before-symptoms-show"),
  ("HuffPost", "huffpost.png", "https://m.huffpost.com/uk/entry/uk_59bfaa1ae4b0edff971d74fb/amp"),
  ("The Indian Express", "indian-express-logo.png", "https://indianexpress.com/article/technology/science/new-ai-system-can-predict-alzheimers-10-years-in-advance-4849747/lite/"),
  ("Tech Times", "techTimes.png", "https://www.techtimes.com/amp/articles/213578/20170918/ai-arrives-as-the-newest-and-most-powerful-weapon-for-early-alzheimers-disease-detection.htm"),
  ("IFLScience", "iflscience_logo.png", "http://www.iflscience.com/health-and-medicine/ai-can-detect-early-signs-of-alzheimers-almost-a-decade-before-symptoms-develop/"),
  ("Immortal News", "immortal-news.png", "https://www.immortal.org/34937/ai-can-detect-early-symptoms-alzheimers/"),
  ("Engadget", "engaget.png", "https://www.engadget.com/amp/2017/09/17/ai-alzheimers-early-detection/"),
  ("Daily Mail", "dailyMail.gif", "https://www.dailymail.co.uk/sciencetech/article-4889722/amp/AI-spot-signs-Alzheimer-s-DECADE-doctors.html"),
  ("Digital Trends", "digitalTrends.png", "https://www.digitaltrends.com/cool-tech/ai-alzheimers-italy-diagnosis/"),
  ("Wired Italia", "wired.png", "https://www.wired.it/scienza/medicina/2017/09/15/alzheimer-diagnosi-precoce/"),
  ("New Scientist", "newScientist.png", "https://www.newscientist.com/article/2147472-ai-spots-alzheimers-brain-changes-years-before-symptoms-emerge/"),
  ("Barletta News", "logo-barletta_news-magazine-160x90.png", "http://www.barlettanews.it/alzheimer-intervista-al-prof-roberto-bellotti/"),
]
# Il newsroom passa dalla normalizzazione: nessun http:// in chiaro raggiunge
# il dato pubblicato, e un URL con schema non ammesso verrebbe scartato.
def news_item(entry):
    name, image, url = entry
    safe = safe_url(url)
    if not safe:
        print('  scartato (URL non ammesso):', name, '|', url)
    return {"name": name, "img": "assets/img/" + image, "url": safe}


SITE["newsroom"] = [news_item(entry) for entry in NEWS]


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, 'site-data.js'), 'w', encoding='utf-8') as fh:
        fh.write('window.MEDPHYS_SITE = ' + js(SITE) + ';\n')

    print('site-data.js', os.path.getsize(os.path.join(OUT, 'site-data.js')))
    print('people', len(SITE['people']), 'collab', len(SITE['collaborators']),
          'proj', len(SITE['projects']['ongoing']), len(SITE['projects']['past']),
          'chal', len(SITE['challenges']), 'news', len(SITE['newsroom']))
    print('newsroom http in chiaro:', sum(1 for n in SITE['newsroom'] if n['url'].startswith('http://')))
    print('newsroom scartati:', sum(1 for n in SITE['newsroom'] if not n['url']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
