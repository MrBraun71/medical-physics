# -*- coding: utf-8 -*-
"""Converte i JSON intermedi in pages_en.js, il file caricato a runtime.

Il contenuto e' gia' stato ripulito da clean_content.py, quindi qui non si
toccano i link: la protezione utile e' sulla serializzazione, che espone `<`
come escape Unicode perche' una sequenza `</script>` nel dato non possa chiudere
il tag che lo contiene.
"""

import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'data')


def js(value):
    """JSON sicuro da inserire dentro un tag <script>."""
    return (json.dumps(value, ensure_ascii=False)
            .replace(chr(0x2028), '\\u2028')
            .replace(chr(0x2029), '\\u2029')
            .replace('<', '\\u003c')
            .replace('>', '\\u003e')
            .replace('&', '\\u0026'))


def fix(html):
    html = html.lstrip('\ufeff\n\r ')
    # Annida <p><div>..</div></p>, che non e' markup valido.
    html = re.sub(r'<p>(<div\b[\s\S]*?</div>)</p>', r'\1', html)
    html = re.sub(r'<p>\s*(<div\b[^>]*>)', r'\1', html)
    html = html.replace('</div></p>', '</div>')
    html = re.sub(r'(<div class="video-embed">.*?</div>)</p>', r'\1', html, flags=re.S)
    return html.strip()


def main():
    with open(os.path.join(OUT, 'pages_en.json'), encoding='utf-8') as handle:
        pages = json.load(handle)
    with open(os.path.join(OUT, 'meta.json'), encoding='utf-8') as handle:
        meta = json.load(handle)

    pages = {slug: fix(value) for slug, value in pages.items()}

    with open(os.path.join(OUT, 'pages_en.js'), 'w', encoding='utf-8') as handle:
        handle.write('window.MEDPHYS_EN = ' + js(pages) + ';\n')
        handle.write('window.MEDPHYS_META = ' + js(meta) + ';\n')

    print('written pages_en.js', os.path.getsize(os.path.join(OUT, 'pages_en.js')))
    print('slugs:', len(pages))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
