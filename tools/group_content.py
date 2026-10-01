import os, re, glob, json

d = os.path.join(os.environ['TEMP'], 'mp', 'extract')
out = os.path.join(os.environ['TEMP'], 'mp', 'groups')
os.makedirs(out, exist_ok=True)

def load(fn):
    txt = open(os.path.join(d, fn), encoding='utf-8').read()
    title = re.search(r'TITLE: (.*)', txt)
    slug = re.search(r'SLUG: (.*)', txt)
    body = re.sub(r'^<!--.*?-->\s*', '', txt, flags=re.S)
    body = re.sub(r'<!-- TITLE:.*?-->', '', txt)
    body = re.sub(r'<!-- SLUG:.*?-->', '', body)
    body = re.sub(r'<!-- PARENT:.*?-->', '', body)
    body = re.sub(r'<!-- LINK:.*?-->', '', body).strip()
    # strip tags to readable text
    text = re.sub(r'<script.*?</script>', ' ', body, flags=re.S | re.I)
    text = re.sub(r'<style.*?</style>', ' ', text, flags=re.S | re.I)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.I)
    text = re.sub(r'</(p|div|li|h[1-6]|tr)>', '\n', text, flags=re.I)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&#8217;', "'")
    text = text.replace('&#8211;', '-').replace('&hellip;', '...').replace('&#039;', "'")
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)
    return title.group(1).strip() if title else fn, slug.group(1).strip() if slug else fn, text.strip()

files = sorted(os.listdir(d))
groups = {
 'people': ['roberto-bellotti','nicola-amoroso','loredana-bellantuono','tommaso-maggipinto','alfonso-monaco','sabina-tangaro','ester-pantaleo','domenico-diacono','marianna-la-rocca','roberto-cilli','alessandro-fania','antonio-lacalamita','andrea-lo-sasso','pierfrancesco-novielli','donato-romano','silvano-quarto','annamaria-demarinis-loiotile','federica-cuna','annarita-fanizzi','rosangela-errico','gianluca-sforza','eufemia-lella','andrea-tateo','raffaella-massafra'],
 'projects': ['projects','ongoing-projects','past-projects','nextmr-advancing-magnetic-resonance-imaging-and-data-analysis','medical-imaging-for-neurodegenerative-diseases-mind','person-pervasive-game-for-personalized-treatment-of-cognitive-and-functional-deficits-associated-with-chronic-and-neurodegenerative-diseases','decision-data-driven-customer-service-innovation','sapere-avviso-innolabs-soluzioni-innovative-per-problemi-di-rilevanza-sociale-dta-distretto-tecnologico-aerospaziale','tebaka-sistema-per-acquisizione-conoscenze-di-base-del-territorio','progetto-gunnebo-innovation-hub','medical-applications-on-a-grid-infrastructure-connection-magic-5','beam-line-from-thomson-source-beats'],
 'challenges': ['mci-challenge','preterm-birth-prediction-microbiome-dream-challenge','mtop2016','dream1','caddementia','mlc','anode09'],
 'publications': ['pubblication','journal-papers','57x','book-chapters','refereed-proceedings','journal-papers','72__x'],
 'other': ['courses','747__x','short-course','conference-slides','join-us','multimedia','privary-cookie-policy','disattivazione-dei-cookies-sui-browser','synchronization-demo'],
}

by_slug = {}
for f in files:
    if f.endswith('.html') and '__' in f:
        idpart, slug = f.split('__', 1)
        slug = slug[:-5]
        by_slug.setdefault(slug, f)

def slugify(s):
    return s

for gname, slugs in groups.items():
    parts = []
    for s in slugs:
        if s in by_slug:
            t, sl, body = load(by_slug[s])
            parts.append(f"\n\n===== {t} ({sl}) =====\n{body}")
    open(os.path.join(out, gname + '.txt'), 'w', encoding='utf-8').write(''.join(parts))
    print(gname, len(parts))
