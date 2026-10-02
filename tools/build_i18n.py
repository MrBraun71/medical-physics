# -*- coding: utf-8 -*-
"""Genera assets/data/i18n.js.

I testi sono sorgente locale e fidato; i video pero' arrivano comunque da
copia-incolla, quindi l'URL passa dalla stessa validazione usata dagli altri
strumenti e il markup dell'iframe viene generato qui invece di essere
ricopiato a mano (era la ragione per cui restava privo di sandbox).
"""

import html
import json
import os
import re
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'data')

EMBED_HOST = 'https://www.youtube-nocookie.com/embed/'
IFRAME_SANDBOX = 'allow-scripts allow-same-origin allow-presentation allow-popups'
IFRAME_REFERRER = 'strict-origin-when-cross-origin'
ALLOWED_SCHEMES = ('https', 'mailto', 'tel')


def esc_attr(value):
    return html.escape(str(value or ''), quote=True)


def safe_url(value, kind='link'):
    """Allow-list di schemi; rifiuta javascript:, vbscript:, data: e file:."""
    raw = html.unescape(str(value or '')).strip()
    if not raw or any(ch.isspace() or ord(ch) < 32 for ch in raw):
        return None
    if raw.startswith('#'):
        return raw if kind == 'link' else None
    if kind == 'embed':
        return raw if raw.startswith(EMBED_HOST) else None
    if raw.lower().startswith(('javascript:', 'vbscript:', 'data:', 'file:')) or raw.startswith('//'):
        return None
    match = re.match(r'([a-zA-Z][a-zA-Z0-9+.-]*):', raw)
    if match:
        return raw if match.group(1).lower() in ALLOWED_SCHEMES else None
    return None if '..' in raw.split('/') else raw


def embed(url):
    """Markup dell'iframe video sull'host no-cookie, validando l'URL."""
    safe = safe_url(url, 'embed')
    if not safe:
        raise ValueError('URL video non ammesso: %r' % url)
    return ('<div class="video-embed"><iframe src="%s" title="video" loading="lazy"'
            ' allowfullscreen sandbox="%s" referrerpolicy="%s"></iframe></div>'
            % (esc_attr(safe), esc_attr(IFRAME_SANDBOX), esc_attr(IFRAME_REFERRER)))


def js(value):
    """Serializza in JSON bloccando la chiusura del tag <script>.

    Espone `<`, `>` e `&` come escape Unicode e separa U+2028/U+2029, che il
    parser JavaScript tratta come terminatori di riga e che dentro una stringa
    cambierebbero la struttura del file.
    """
    text = json.dumps(value, ensure_ascii=False)
    return (text.replace(chr(0x2028), '\\u2028')
                .replace(chr(0x2029), '\\u2029')
                .replace('<', '\\u003c')
                .replace('>', '\\u003e')
                .replace('&', '\\u0026'))


SYNC_IT = (
    "<p>Qui mostriamo il comportamento di sincronizzazione dinamica di due serie temporali attraverso la diagonale principale del loro Cross-Recurrence Plot (CRP).</p>"
    "<p>Anzitutto vengono generate due realizzazioni della dinamica del sistema di Lorenz. Il sistema di Lorenz \u00e8 un modello matematico semplificato della convezione atmosferica ed \u00e8 specificato da tre equazioni differenziali ordinarie:</p>"
    "<p>\\( \\frac{\\text{d}x}{\\text{d}t} = \\sigma (y - x)\\)<br>\n"
    "\\( \\frac{\\text{d}y}{\\text{d}t} = x (r - y) - y\\)<br>\n"
    "\\(\\frac{\\text{d}z}{\\text{d}t} = xy - bz\\)</p>"
    "<p>dove le tre componenti \\( x,y,z \\) sono proporzionali al tasso di convezione, alla variazione orizzontale di temperatura e alla variazione verticale di temperatura. Per \\( \\sigma = 10, b = 8/3, r = 28\\) il sistema mostra un comportamento caotico.<br>\n"
    "La figura seguente mostra l\u2019andamento temporale delle tre componenti del sistema per 2000 campioni e con i valori iniziali delle tre componenti \\( x_1(1)=10, y_1(1)=10, z_1(1)=10\\).</p>"
    "<p><img src=\"assets/img/lorenz.png\" alt=\"Serie temporali del sistema di Lorenz\" loading=\"lazy\"></p>"
    "<p>Abbiamo poi generato un secondo sistema di Lorenz con i valori iniziali delle tre componenti \\( x_2(1)=7, y_2(1)=10, z_2(1)=10\\).<br>\n"
    "Le due serie temporali \\( x_1(t) \\) e \\( x_2(t) \\) sono mostrate nella figura seguente.</p>"
    "<p><img src=\"assets/img/timeseries.png\" alt=\"Confronto delle due serie temporali\" loading=\"lazy\"><br>\n"
    "Il teorema di Takens \u00e8 stato utilizzato per ricostruire le traiettorie nello spazio delle fasi dei due sistemi a partire dalle serie temporali \\( x_1(t) \\) e \\( x_2(t)\\).<br>\n"
    "Per una generica osservazione temporale singola di un sistema \\( u(t) \\), la traiettoria \u00e8 espressa come:<br>\n"
    "\\( \\vec{x}_i = \\bigl( u_i,u_{i+\\tau},\\dots,u_{i+(m-1)\\tau} \\bigr)\\)<br>\n"
    "dove \\( m \\) \u00e8 la dimensione di embedding e \\( \\tau \\) \u00e8 il ritardo temporale.</p>"
    "<p>Per \\( m=3 \\) e \\( \\tau=8 \\), le traiettorie ricostruite appaiono come nella seguente demo:<br>"
    + embed('https://www.youtube-nocookie.com/embed/q525dTc20eQ') + "</p>"
    "<p>Dopo la ricostruzione delle traiettorie dinamiche dei due sistemi nello spazio delle fasi, \u00e8 possibile quantificare il loro comportamento interagente proiettando lo spazio delle fasi nei cross recurrence plot bidimensionali:</p>"
    "<p>\\( CR_{i,j}(\\epsilon) = \\Theta\\left(\\epsilon - ||\\vec{x_1}_i-\\vec{x_2}_j|| \\right) \\)</p>"
    "<p>dove \\(\\Theta\\) \u00e8 la funzione di Heaviside, \\(\\epsilon\\) \u00e8 una soglia di prossimit\u00e0, \\(N\\) \u00e8 il numero di stati considerati per ciascun sistema e \\(||\\cdot||\\) \u00e8 la funzione norma massima.<br>\n"
    "Per \\(\\epsilon=0.9\\) il CRP dei due sistemi appare come:</p>"
    "<p><img src=\"assets/img/crp.png\" alt=\"Cross Recurrence Plot\" loading=\"lazy\"></p>"
    "<p>La diagonale principale del CRP \u00e8 nota anche come Line of Synchronization (LOS). La presenza della LOS implica l\u2019identit\u00e0 degli stati dei due sistemi negli stessi intervalli temporali, quindi la sua struttura pu\u00f2 essere analizzata per estrarre informazioni sulla sincronizzazione delle due serie temporali.<br>\n"
    "Nel video seguente mostriamo le due serie temporali insieme ai valori della LOS: per ragioni di visualizzazione, la presenza di valori nella diagonale (entrate unitarie) \u00e8 visualizzata come punti neri positivi, mentre l\u2019assenza di valori (entrate nulle) \u00e8 mostrata come punti neri negativi.<br>"
    + embed('https://www.youtube-nocookie.com/embed/TIV7hmCNMwc') + "</p>"
)

IT = {"synchronization-demo": SYNC_IT}
ENX = {}


def main():
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, 'i18n.js')
    with open(path, 'w', encoding='utf-8') as handle:
        handle.write('window.MEDPHYS_IT = ' + js(IT) + ';\n')
        handle.write('window.MEDPHYS_EN_X = ' + js(ENX) + ';\n')
    print('i18n.js', os.path.getsize(path))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
