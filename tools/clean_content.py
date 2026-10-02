"""Ripulisce le pagine HTML esportate dal sito originale e produce i dati.

Ogni valore che arriva dal sorgente viene trattato come non fidato: gli URL
passano per un allow-list di schemi e ogni attributo ricostruito viene codificato
con html.escape. Prima, l'hrefveniva ricopiato cosi' com'era nell'output
generato (uno `javascript:` nel sorgente restava un `javascript:` nel dato
pubblicato) e l'alt delle immagini finiva in un attributo non codificato.
"""

import html
import json
import os
import re
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'data')
TMP = os.path.join(os.environ.get('TEMP') or os.environ.get('TMP') or tempfile.gettempdir(), 'mp')
EX = os.path.join(TMP, 'extract')

SITE_BASE = 'https://medphys.ba.infn.it'
EMBED_HOST = 'https://www.youtube-nocookie.com/embed/'
IFRAME_SANDBOX = 'allow-scripts allow-same-origin allow-presentation allow-popups'
IFRAME_REFERRER = 'strict-origin-when-cross-origin'
IMG_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp')

LINK_SCHEMES = ('https', 'mailto', 'tel')

# Riscontro di assets/js/sanitize.js: il generatore non deve emettere tag che il
# runtime scarterebbe, altrimenti il markup si perde senza alcun errore. Le
# liste sono copiate dal runtime e il test tools/test_import_pipeline.py
# segnala ogni divergenza fra le due.
ALLOWED_TAGS = frozenset({
    'a', 'abbr', 'b', 'blockquote', 'br', 'caption', 'div', 'em', 'figcaption',
    'figure', 'h1', 'h2', 'h3', 'h4', 'hr', 'i', 'iframe', 'img', 'li', 'ol',
    'p', 'span', 'strong', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
    'thead', 'tr', 'ul',
})

# Tag il cui contenuto viene scartato interamente a runtime.
DROP_SUBTREE_TAGS = frozenset({
    'script', 'style', 'object', 'applet', 'svg', 'math', 'template',
    'noscript', 'form', 'frameset', 'frame', 'base', 'link', 'meta', 'title',
    'head', 'canvas', 'audio', 'video', 'source', 'track',
})

# Tag vuoti, riscontro di VOID_TAGS in assets/js/sanitize.js. Sono in
# DROP_SUBTREE_TAGS ma non hanno contenuto: cercare un tag di chiusura che non
# esiste li farebbe consumare tutto il resto del documento.
VOID_TAGS = frozenset({
    'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
    'meta', 'param', 'source', 'track', 'wbr',
})

# Tag su cui il runtime ammette l'attributo class (TAG_ATTRS in sanitize.js).
# Su qualsiasi altro tag la classe verrebbe scartata a runtime, quindi qui non
# deve nemmeno essere emessa: regenerare non deve cambiare il dato pubblicato.
CLASS_ALLOWED_TAGS = frozenset({
    'div', 'p', 'span', 'figure', 'figcaption', 'blockquote',
})

# attributi di testo ammessi dal runtime, per tag
TEXT_ATTR_TAGS = {
    'a': ('title',),
    'img': ('title',),
    'iframe': ('title',),
    'table': ('summary',),
}

ALLOWED_CLASSES = frozenset({'video-embed', 'pub-entry', 'video-card', 'video-desc'})

# Il runtime accetta colspan/rowspan solo se sono 1-3 cifre decimali.
SPAN_RE = re.compile(r'^[0-9]{1,3}$')

# Un tag puo' contenere '>' dentro un attributo quotato: senza questo accorgimento
# il tag verrebbe troncato al '>' interno e il resto finirebbe nel testo.
QUOTED_ATTR = r'(?:[^>"\']|"[^"]*"|\'[^\']*\')*'

# I tag vuoti che il runtime scarta sono rimossi come markup singolo: non hanno
# contenuto, quindi non si puo' cercare un tag di chiusura che arriverebbe a
# cancellare il resto della pagina. Solo quelli in DROP_SUBTREE_TAGS: `img`,
# `br` e `hr` sono void ma ammessi, e restano al passaggio successivo.
VOID_DROP_TAGS = DROP_SUBTREE_TAGS & VOID_TAGS
VOID_DROP_RE = re.compile(
    r'</?(?:%s)\b%s>' % ('|'.join(sorted(VOID_DROP_TAGS)), QUOTED_ATTR), re.I)


def find_tag_end(raw):
    """Indice del '>' che chiude il tag, ignorando quelli dentro gli attributi.

    `raw.find('>')` non basta: un href come `x?a=1>2` o un title come `t>u`
    contengono '>' legittimi, e troncarci il tag lascerebbe dentro il testo
    l'attributo per intero, producendo markup malformato.
    """
    quote = None
    for index, char in enumerate(raw):
        if quote:
            if char == quote:
                quote = None
        elif char in '"\'':
            quote = char
        elif char == '>':
            return index
    return -1

# Scarti annotati durante l'ultima esecuzione: se un tag ammesso dal generatore
# non lo fosse nel runtime, il dato si perderebbe senza lasciare traccia.
DROPPED_TAGS = {}

# href scartati per schema non ammesso, per lo stesso motivo: il testo del
# collegamento resta, il link no, e senza un conteggio la perdita sarebbe
# silenziosa. Chiave = schema trovato, non l'URL intero.
REJECTED_LINKS = {}


def slug_or_url(raw):
    """Chiave di conteggio per uno href scartato: lo schema, non l'URL.

    L'URL completo renderebbe il report illeggibile e non aggregabile; lo
    schema basta a capire perche' il link e' andato perso.
    """
    match = re.match(r'([a-zA-Z][a-zA-Z0-9+.-]*):', raw or '')
    return match.group(1).lower() + ':' if match else 'senza schema'


def apply_runtime_allowlist(body):
    """Rimuove i tag che il runtime scarterebbe, annotando ogni scarto.

    Coerente con sanitize.js: i DROP_SUBTREE vengono eliminati col contenuto,
    gli altri vengono privati del tag mantenendo il testo interno. Ogni scarto
    viene contato, cosi' una divergenza fra le due allow-list è visibile invece
    di manifestarsi come contenuto sparito a runtime.
    """
    def note(name):
        DROPPED_TAGS[name] = DROPPED_TAGS.get(name, 0) + 1

    def drop_subtree(match):
        note(match.group('name').lower())
        return ''

    def keep_or_unwrap(match):
        raw = match.group(0)
        name = match.group('name').lower()
        if name in ALLOWED_TAGS:
            return raw
        note(name)
        if raw.startswith('</') or raw.endswith('/>'):
            # Chiusura o tag vuoto: non c'e' contenuto da preservare.
            return ''
        # Apertura: si scarta il tag e si mantiene il testo interno.
        end = find_tag_end(raw)
        return raw[end + 1:] if end >= 0 else ''

    # I tag vuoti in DROP_SUBTREE_TAGS si rimuovono come markup singolo: non
    # hanno contenuto, quindi non si puo' cercare un tag di chiusura che
    # arriverebbe a cancellare il resto della pagina.
    def drop_void(match):
        for name in re.findall(r'</?([A-Za-z][A-Za-z0-9-]*)', match.group(0)):
            if name.lower() in DROP_SUBTREE_TAGS:
                note(name.lower())
        return ''

    body = VOID_DROP_RE.sub(drop_void, body)

    for name in sorted(DROP_SUBTREE_TAGS - VOID_TAGS):
        body = re.sub(r'<(?P<name>%s)\b[^>]*>.*?(?:</(?P=name)\s*>|$)' % name,
                      drop_subtree, body, flags=re.S | re.I)

    body = re.sub(r'<(/?)(?P<name>\w+)\b%s>' % QUOTED_ATTR,
                  keep_or_unwrap, body, flags=re.I)
    return body


def keep_class(attrs, tag):
    """Ricostruisce l'attributo class filtrato dalla stessa allow-list del runtime.

    Senza questo, il wrapper dei video perderebbe la classe usata dal CSS e
    la perdita sarebbe silenziosa: il file si rigenererebbe "correttamente" ma
    con il layout rotto.

    `tag` limita la conservazione ai tag su cui il runtime ammette davvero la
    classe: su `b`, `li` o `table` verrebbe scartata, quindi rigenerare non deve
    nemmeno emetterla.
    """
    if tag not in CLASS_ALLOWED_TAGS:
        return ''
    match = re.search(r'class=["\']([^"\']*)["\']', attrs or '')
    if not match:
        return ''
    kept = [token for token in html.unescape(match.group(1)).split()
            if token in ALLOWED_CLASSES]
    return ' class="%s"' % esc_attr(' '.join(kept)) if kept else ''


def keep_text_attrs(attrs, tag):
    """Preserva gli attributi di testo ammessi dal runtime per quel tag.

    `title` su link/immagini e `summary` sulle tabelle verrebbero scartati a
    runtime se il generatore non li emettesse, perderli qui cambierebbe il dato
    pubblicato al prossimo rigeneramento.
    """
    keep = ''
    for name in TEXT_ATTR_TAGS.get(tag, ()):
        match = re.search(r'%s=["\']([^"\']*)["\']' % name, attrs or '')
        if match and match.group(1).strip():
            keep += ' %s="%s"' % (name, esc_attr(html.unescape(match.group(1))))
    return keep


def esc_attr(value):
    """Codifica un valore destinato a un attributo (incluse le virgolette)."""
    return html.escape(str(value or ''), quote=True)


def safe_url(value, kind='link'):
    """Restituisce l'URL solo se lo schema e' ammesso, altrimenti None.

    Il controllo e' fatto sulla stringa *decodificata*: `&#106;avascript:` e
    `java\tscript:` non devono passare come se fossero innocui.
    """
    raw = html.unescape(str(value or '')).strip()
    # Spazi e caratteri di controllo non hanno posto in un URL.
    if not raw or any(ch.isspace() or ord(ch) < 32 for ch in raw):
        return None
    # Il browser risolve il backslash come se fosse '/', quindi `https:\evil.tld`
    # punta a un altro origin pur senza schema esplicito: il runtime lo rifiuta
    # e il generatore deve essere piu' severo, non piu' permissivo.
    if '\\' in raw:
        return None

    if raw.startswith('#'):
        return raw if kind == 'link' else None

    if kind == 'embed':
        if raw.startswith(EMBED_HOST):
            return raw
        # Gli embed arrivano dal sito originale sull'host con cookie: si
        # riscrivono, non si scartano.
        if raw.startswith('https://www.youtube.com/embed/'):
            return to_no_cookie(raw)
        return None

    lowered = raw.lower()
    if lowered.startswith(('javascript:', 'vbscript:', 'data:', 'file:')):
        return None
    if raw.startswith('//'):
        return None  # protocol-relative: eredita il contesto, non e' una scelta esplicita

    match = re.match(r'([a-zA-Z][a-zA-Z0-9+.-]*):', raw)
    if match:
        return raw if match.group(1).lower() in LINK_SCHEMES else None

    # Percorsi relativi ammessi, senza sequenze di risalita.
    if raw.startswith('/') or not raw:
        if '..' in raw.split('/'):
            return None
        return raw
    return None if '..' in raw.split('/') else raw


def slug_from_link(link):
    match = re.match(r'https?://medphys\.ba\.infn\.it/([^/?#]+)/?$', link or '')
    return match.group(1) if match else None


def image_tag(src, alt, title=''):
    """Ricostruisce un <img> con nome confinato e alt codificato."""
    name = os.path.basename(html.unescape(src).split('?')[0].replace('\\', '/'))
    if not name or os.path.splitext(name)[1].lower() not in IMG_EXTENSIONS:
        return ''
    if name in ('.', '..'):
        return ''
    # L'alt arriva dal sorgente con le entita' gia' codificate: senza
    # unescape prima dell'escape si pubblicherebbe "&amp;amp;" a schermo.
    # Anche title va conservato: il runtime lo ammette sulle immagini.
    return ('<img src="assets/img/%s" alt="%s" loading="lazy"%s>'
            % (esc_attr(name), esc_attr(html.unescape(alt)),
               (' title="%s"' % esc_attr(html.unescape(title))) if title.strip() else ''))


def embed_tag(src):
    """Ricostruisce l'iframe YouTube sull'host no-cookie e in sandbox.

    L'host originale viene riscritto invece di scartato: rifiutare
    `www.youtube.com` farebbe perdere tutti i video al prossimo
    rigeneramento, che e' esattamente il motivo per cui il markup era rimasto
    privo di hardening.
    """
    url = safe_url(src, 'embed')
    if not url:
        return ''
    return ('<div class="video-embed"><iframe src="%s" title="video" loading="lazy"'
            ' allowfullscreen sandbox="%s" referrerpolicy="%s"></iframe></div>'
            % (esc_attr(url), esc_attr(IFRAME_SANDBOX), esc_attr(IFRAME_REFERRER)))


def to_no_cookie(url):
    """Trasforma un URL embed YouTube nell'equivalente sull'host no-cookie."""
    if url.startswith('https://www.youtube.com/embed/'):
        return EMBED_HOST + url[len('https://www.youtube.com/embed/'):]
    return url


def read_meta(filename):
    # `utf-8-sig` rimuove il BOM: `str.strip()` non lo considera whitespace,
    # quindi senza questo ogni pagina inizierebbe con U+FEFF e una pagina senza
    # corpo diventerebbe '\ufeff' invece di stringa vuota.
    with open(os.path.join(EX, filename), encoding='utf-8-sig') as handle:
        text = handle.read()
    title = re.search(r'TITLE: (.*?) -->', text)
    slug = re.search(r'SLUG: (.*?) -->', text)
    link = re.search(r'LINK: (.*?) -->', text)
    body = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    return (html.unescape(title.group(1).strip()) if title else filename,
            slug.group(1).strip() if slug else '',
            link.group(1).strip() if link else '',
            body.strip('﻿\n\r '))


def clean(body):
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S | re.I)
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S | re.I)
    body = re.sub(r'<span[^>]*class="mce_SELRES[^"]*"[^>]*>.*?</span>', '', body, flags=re.S | re.I)
    body = re.sub(r'<span[^>]*>\s*</span>', '', body, flags=re.S | re.I)

    # Immagini: il tag originale viene rimpiazzato da uno ricostruito.
    def image(match):
        tag = match.group(0)
        src = re.search(r'src=["\']([^"\']+)["\']', tag)
        if not src:
            return ''
        alt = re.search(r'alt=["\']([^"\']*)["\']', tag)
        title = re.search(r'title=["\']([^"\']*)["\']', tag)
        return image_tag(src.group(1), alt.group(1) if alt else '',
                         title.group(1) if title else '')

    body = re.sub(r'<img\b%s>' % QUOTED_ATTR, image, body, flags=re.I)

    # Iframe: solo YouTube, sull'host no-cookie e in sandbox.
    def iframe(match):
        found = re.search(r'src=["\']([^"\']+)["\']', match.group(0))
        if not found:
            return ''
        return embed_tag(found.group(1))

    body = re.sub(r'<iframe.*?</iframe>', iframe, body, flags=re.S | re.I)

    # Ancore: URL validato, testo mantenuto.
    def anchor(match):
        tag = match.group(0)
        href = re.search(r'href=["\']([^"\']+)["\']', tag)
        # Il '>' che chiude il tag va cercato fuori dagli attributi: un href o un
        # title possono contenerne uno, e usarlo per tagliare lascerebbe dentro
        # il testo il resto dell'attributo.
        end = find_tag_end(tag)
        closing = re.search(r'</a\s*>\s*$', tag, re.I)
        if end < 0 or not closing:
            return ''
        label = tag[end + 1:closing.start()]
        if not href:
            return label
        # Il runtime ammette title sui link: rigenerare senza riportarlo
        # cambierebbe il dato pubblicato (perdita di tooltip e di contesto).
        opening = tag[:end + 1]
        title = keep_text_attrs(opening, 'a')
        raw = html.unescape(href.group(1))
        if 'medphys.ba.infn.it' in raw or raw.startswith('/'):
            slug = slug_from_link(raw if raw.startswith('http') else SITE_BASE + raw)
            if slug and slug not in ('', 'wp-json'):
                return '<a href="#/%s"%s>%s</a>' % (esc_attr(slug), title, label)
            return label
        safe = safe_url(raw, 'link')
        if not safe:
            # Testo conservato, collegamento perso: si conta cosi' che la
            # perdita resti visibile invece di emergere solo a runtime, dove
            # il link verrebbe comunque scartato.
            REJECTED_LINKS[slug_or_url(raw)] = REJECTED_LINKS.get(slug_or_url(raw), 0) + 1
            return label
        if safe.startswith('#'):
            return '<a href="%s"%s>%s</a>' % (esc_attr(safe), title, label)
        # target non viene inventato: si riporta solo se il sorgente lo chiedeva
        # esplicitamente. Aggiungerlo a ogni link esterno cambierebbe il dato
        # pubblicato al prossimo rigeneramento e imporrebbe a ogni visitatore
        # una scheda nuova. Quando c'e', rel=noopener mantiene la protezione
        # dal tabnabbing; su mailto e tel non ha senso aprire una scheda.
        blank = ''
        wanted = re.search(r'target=["\']([^"\']*)["\']', opening)
        if (wanted and wanted.group(1).strip().lower() == '_blank'
                and safe.startswith('https:')):
            blank = ' target="_blank" rel="noopener noreferrer"'
        return '<a href="%s"%s%s>%s</a>' % (esc_attr(safe), title, blank, label)

    body = re.sub(r'<a\b.*?</a>', anchor, body, flags=re.S | re.I)

    # Gli attributi superstiti vengono ricostruiti e codificati uno per uno.
    def strip_attrs(match):
        tag = match.group(1).lower()
        attrs = match.group(2) or ''
        keep = ''
        if tag == 'a':
            href = re.search(r'href=["\']([^"\']*)["\']', attrs)
            if href:
                safe = safe_url(html.unescape(href.group(1)), 'link')
                if safe:
                    keep = ' href="%s"' % esc_attr(safe)
                    keep += keep_text_attrs(attrs, tag)
                    # Il runtime ammette target con validazione esplicita:
                    # perderlo qui cambierebbe il comportamento dei link
                    # esterni al prossimo rigeneramento.
                    target = re.search(r'target=["\']([^"\']*)["\']', attrs)
                    value = (target.group(1).strip().lower() if target else '')
                    if value in ('_blank', '_self'):
                        keep += ' target="%s"' % value
                        if value == '_blank':
                            keep += ' rel="noopener noreferrer"'
        elif tag == 'img':
            src = re.search(r'src=["\']([^"\']*)["\']', attrs)
            alt = re.search(r'alt=["\']([^"\']*)["\']', attrs)
            keep = (' src="%s"' % esc_attr(src.group(1)) if src else '') \
                + (' alt="%s"' % esc_attr(html.unescape(alt.group(1))) if alt else '') \
                + ' loading="lazy"'
            keep += keep_text_attrs(attrs, tag)
        elif tag == 'iframe':
            src = re.search(r'src=["\']([^"\']*)["\']', attrs)
            if src:
                embed = to_no_cookie(safe_url(html.unescape(src.group(1)), 'embed'))
                if embed:
                    keep = (' src="%s" title="video" loading="lazy" allowfullscreen'
                            ' sandbox="%s" referrerpolicy="%s"'
                            % (esc_attr(embed), esc_attr(IFRAME_SANDBOX), esc_attr(IFRAME_REFERRER)))
        elif tag in ('td', 'th'):
            for name in ('colspan', 'rowspan'):
                value = re.search(name + r'=["\']([^"\']*)["\']', attrs)
                # Stessa validazione del runtime: un valore non numerico
                # verrebbe scartato in pagina, quindi non si emette.
                if value and SPAN_RE.match(value.group(1).strip()):
                    keep += ' %s="%s"' % (name, esc_attr(value.group(1).strip()))
        elif tag == 'table':
            keep += keep_text_attrs(attrs, tag)
        # La classe dei wrapper video e' ciò che il CSS usa per il layout:
        # senza questa riga una rigenerazione la perderebbe in silenzio.
        keep += keep_class(attrs, tag)
        return '<%s%s>' % (tag, keep)

    body = re.sub(r'<(\w+)(\s%s)?>' % QUOTED_ATTR, strip_attrs, body)

    # Ultimo controllo: nessun tag fuori dall'allow-list del runtime può
    # sopravvivere nel dato, e ogni scarto viene contato. Senza questo passaggio
    # un tag ammesso qui ma rifiutato da sanitize.js (o il suo contenuto, per i
    # DROP_SUBTREE) sparirebbe a runtime senza alcun segnale nel repository.
    body = apply_runtime_allowlist(body)

    for _ in range(4):
        body = re.sub(r'<p>\s*</p>', '', body)
        body = re.sub(r'<div>\s*</div>', '', body)

    # La compressione dei vuoti riguarda solo i vuoti che contengono un newline,
# cioe' l'indentazione usata per impaginare il sorgente. Applicarla a ogni
# `><` cancellava anche gli spazi significativi fra elementi inline
# ("<b>grasso</b> <b>altro</b>" diventava "grassoaltro").
    body = re.sub(r'>[ \t]*\r?\n[ \t\r\n]*<', '><', body)
    body = re.sub(r'\n\s*\n+', '\n', body).strip()
    return body


def main():
    os.makedirs(OUT, exist_ok=True)
    # Uscire con successo senza aver scritto nulla lascerebbe i dati alla
    # versione precedente (o assenti) e la CI continuerebbe a verde: un import
    # fallito deve fermarsi, non passare inosservato.
    if not os.path.isdir(EX):
        raise SystemExit('nessuna estruzione trovata in %s: eseguire prima '
                         'l\'estrazione degli archivi' % EX)

    pages = {}
    meta = {}
    for filename in sorted(os.listdir(EX)):
        if not filename.endswith('.html') or '__' not in filename:
            continue
        title, slug, link, body = read_meta(filename)
        if not slug:
            continue
        cleaned = clean(body)
        if slug not in meta or len(cleaned) > len(pages.get(slug, '')):
            meta[slug] = {'title': title, 'link': link, 'fn': filename}
            pages[slug] = cleaned

    if not pages:
        raise SystemExit('nessuna pagina estratta da %s: i dati non verrebbero '
                         'rigenerati' % EX)

    with open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8') as handle:

        json.dump(meta, handle, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, 'pages_en.json'), 'w', encoding='utf-8') as handle:
        json.dump(pages, handle, ensure_ascii=False, indent=1)

    print('pages:', len(pages))
    if DROPPED_TAGS:
        print('tag scartati per non essere ammessi dal runtime:')
        for name, count in sorted(DROPPED_TAGS.items(), key=lambda kv: -kv[1]):
            print('  DROP', name, count)
    else:
        print('tag scartati: nessuno')
    if REJECTED_LINKS:
        print('href scartati per schema non ammesso:')
        for scheme, count in sorted(REJECTED_LINKS.items(), key=lambda kv: -kv[1]):
            print('  DROP', scheme, count)
    else:
        print('href scartati: nessuno')
    for slug in ['brain', 'lung', 'breast', 'phase-contrast-phase-retrieval-imaging',
                 'roberto-bellotti', 'mci-challenge', 'multimedia', 'join-us']:
        print('---', slug, len(pages.get(slug, '')))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
