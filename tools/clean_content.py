import os, re, json, html

TMP = os.path.join(os.environ['TEMP'], 'mp')
EX = os.path.join(TMP, 'extract')
OUT = r'E:\MedPhys_Sito\assets\data'
os.makedirs(OUT, exist_ok=True)

# slugs that are "real" site pages (from REST title/link)
def read_meta(fn):
    txt = open(os.path.join(EX, fn), encoding='utf-8').read()
    t = re.search(r'TITLE: (.*?) -->', txt)
    s = re.search(r'SLUG: (.*?) -->', txt)
    l = re.search(r'LINK: (.*?) -->', txt)
    body = re.sub(r'<!--.*?-->', '', txt, flags=re.S)
    return (html.unescape(t.group(1).strip()) if t else fn,
            s.group(1).strip() if s else '',
            l.group(1).strip() if l else '',
            body.strip())

def slug_from_link(link):
    m = re.match(r'https?://medphys\.ba\.infn\.it/([^/?#]+)/?$', link)
    return m.group(1) if m else None

def img_rewrite(m):
    tag = m.group(0)
    src = re.search(r'src=["\']([^"\']+)["\']', tag)
    alt = re.search(r'alt=["\']([^"\']*)["\']', tag)
    if not src:
        return ''
    u = src.group(1)
    name = os.path.basename(u.split('?')[0])
    name = html.unescape(name)
    new = f'<img src="assets/img/{name}" alt="{alt.group(1) if alt else ""}" loading="lazy">'
    return new

def clean(body):
    # remove scripts/styles/comments
    body = re.sub(r'<!--.*?-->', '', body, flags=re.S)
    body = re.sub(r'<script.*?</script>', '', body, flags=re.S | re.I)
    body = re.sub(r'<style.*?</style>', '', body, flags=re.S | re.I)
    # remove spans with only bookmark junk
    body = re.sub(r'<span[^>]*class="mce_SELRES[^"]*"[^>]*>.*?</span>', '', body, flags=re.S | re.I)
    body = re.sub(r'<span[^>]*>\s*</span>', '', body, flags=re.S | re.I)
    # images
    body = re.sub(r'<img[^>]*>', img_rewrite, body, flags=re.I)
    # iframes: keep youtube, drop others
    def iframe(m):
        s = m.group(0)
        src = re.search(r'src=["\']([^"\']+)["\']', s)
        if src and 'youtube.com/embed' in src.group(1):
            return f'<div class="video-embed"><iframe src="{src.group(1)}" title="video" loading="lazy" allowfullscreen></iframe></div>'
        return ''
    body = re.sub(r'<iframe.*?</iframe>', iframe, body, flags=re.S | re.I)
    # anchors internal
    def anchor(m):
        s = m.group(0)
        href = re.search(r'href=["\']([^"\']+)["\']', s)
        txt = re.search(r'>(.*?)</a>', s, re.S)
        if not href:
            return txt.group(1) if txt else ''
        h = html.unescape(href.group(1))
        label = txt.group(1) if txt else h
        if 'medphys.ba.infn.it' in h or h.startswith('/'):
            slug = slug_from_link(h if h.startswith('http') else 'https://medphys.ba.infn.it' + h)
            if slug and slug not in ('', 'wp-json'):
                return f'<a href="#/{slug}">{label}</a>'
            return label
        if h.startswith('#'):
            return f'<a href="{h}">{label}</a>'
        return f'<a href="{h}" target="_blank" rel="noopener">{label}</a>'
    body = re.sub(r'<a\b.*?</a>', anchor, body, flags=re.S | re.I)
    # strip attributes except href on a, src/alt on img, colspan/rowspan on td/th
    def strip_attrs(m):
        tag = m.group(1).lower()
        attrs = m.group(2)
        keep = ''
        if tag == 'a':
            h = re.search(r'href=["\']([^"\']*)["\']', attrs)
            if h:
                keep = f' href="{h.group(1)}"'
        elif tag == 'img':
            s = re.search(r'src=["\']([^"\']*)["\']', attrs)
            a = re.search(r'alt=["\']([^"\']*)["\']', attrs)
            keep = (f' src="{s.group(1)}"' if s else '') + (f' alt="{a.group(1)}"' if a else '') + ' loading="lazy"'
        elif tag == 'iframe':
            s = re.search(r'src=["\']([^"\']*)["\']', attrs)
            keep = (f' src="{s.group(1)}"' if s else '') + ' title="video" loading="lazy" allowfullscreen'
        elif tag in ('td', 'th'):
            for a in ('colspan', 'rowspan'):
                v = re.search(a + r'=["\']([^"\']*)["\']', attrs)
                if v:
                    keep += f' {a}="{v.group(1)}"'
        return f'<{tag}{keep}>'
    body = re.sub(r'<(\w+)((?:\s[^>]*)?)>', strip_attrs, body)
    # remove empty paragraphs/divs
    for _ in range(4):
        body = re.sub(r'<p>\s*</p>', '', body)
        body = re.sub(r'<div>\s*</div>', '', body)
    # collapse whitespace between block tags but preserve text
    body = re.sub(r'>\s+<', '><', body)
    body = re.sub(r'\n\s*\n+', '\n', body).strip()
    return body

pages = {}
meta = {}
for fn in os.listdir(EX):
    if not fn.endswith('.html') or '__' not in fn:
        continue
    title, slug, link, body = read_meta(fn)
    if not slug:
        continue
    c = clean(body)
    if slug not in meta or len(c) > len(pages.get(slug, '')):
        meta[slug] = {'title': title, 'link': link, 'fn': fn}
        pages[slug] = c

json.dump(meta, open(os.path.join(OUT, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(pages, open(os.path.join(OUT, 'pages_en.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('pages:', len(pages))
for k in ['brain','lung','breast','phase-contrast-phase-retrieval-imaging','roberto-bellotti','mci-challenge','multimedia','join-us']:
    print('---', k, len(pages.get(k, '')))
