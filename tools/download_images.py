"""Scarica le immagini referenziate dal sito e le deposita in assets/img.

Il file era nato come script usa-e-getta: verificava il contenuto scaricato
senza fidarsi di nulla. In particolare disattivava la verifica TLS, ricavava il
nome del file con basename() *prima* di decodificare l'URL (permettendo
`%2e%2e%2f` di uscire dalla cartella di destinazione) e accettava qualunque
host contenesse la sottostringa `medphys.ba.infn.it` nell'URL.

Ora la destinazione e' derivata dalla posizione dello script, il download e'
consentito solo verso host in allow-list, e ogni scrittura viene confinata e
limitata. Il manifest prodotto ha lo stesso formato di prima.
"""

import json
import os
import re
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(ROOT, 'assets', 'img')
TMP = os.path.join(os.environ.get('TEMP') or os.environ.get('TMP') or tempfile.gettempdir(), 'mp')

# Un solo host: il sito da cui proviene il materiale originale.
ALLOWED_HOSTS = frozenset({'medphys.ba.infn.it'})
SITE_BASE = 'https://medphys.ba.infn.it'

# Limiti di dimensione: senza tetto, un endpoint che restituisce un file
# enorme esaurisce memoria e disco.
MAX_BYTES = 20 * 1024 * 1024
CHUNK = 64 * 1024
TIMEOUT = 30
MAX_REDIRECTS = 3

ALLOWED_CONTENT_TYPES = ('image/png', 'image/jpeg', 'image/gif', 'image/webp')
ALLOWED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.webp')

# Prime byte di ciascun formato: l'estensione e' un'indicazione, non una prova.
# Senza questo controllo un file HTML servito come .png finirebbe pubblicato
# come <img> (e su alcuni browser come documento navigabile).
#
# GIF: il prefisso e' `GIF8` perche' esistono due versioni del formato, 87a e
# 89a, e quella diffusa (GIF89a) non iniziarebbe con `GIF87a`.
MAGIC = {
    '.png': b'\x89PNG\r\n\x1a\n',
    '.jpg': b'\xff\xd8\xff',
    '.jpeg': b'\xff\xd8\xff',
    '.gif': b'GIF8',
    '.webp': b'RIFF',
}

# WebP e' un contenitore RIFF: `RIFF` da solo accetterebbe anche un WAV o un
# AVI, quindi si verifica anche il tag del formato all'offset 8.
MAGIC_AT_OFFSET = {
    '.webp': (8, b'WEBP'),
}


def matches_magic(head, extension):
    """True se i byte iniziali sono coerenti con l'estensione del file."""
    extension = extension.lower()
    signature = MAGIC.get(extension)
    if signature is None:
        return True
    if not head.startswith(signature):
        return False
    offset_tag = MAGIC_AT_OFFSET.get(extension)
    if offset_tag is None:
        return True
    offset, tag = offset_tag
    return head[offset:offset + len(tag)] == tag

IMG_RE = re.compile(r'(?:src|href)=["\']([^"\']+\.(?:png|jpe?g|gif|webp))["\']', re.I)
SRCSET_RE = re.compile(r'srcset=["\']([^"\']+)["\']', re.I)
MEDIA_FILES = ('media1.json', 'media2.json', 'media.json')

# urllib segue i redirect per default. Senza questo opener un URL consentito
# puo' rimandare il download a un host interno (SSRF) aggirando ALLOWED_HOSTS,
# che viene verificato solo sull'URL iniziale.
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _opener(context):
    """Opener senza redirect e con la verifica TLS del chiamante."""
    return urllib.request.build_opener(
        NoRedirect, urllib.request.HTTPSHandler(context=context))


def absolute_url(candidate):
    """Ricostruisce un URL https assoluto, o None se non e' utilizzabile."""
    candidate = (candidate or '').strip()
    if not candidate:
        return None
    if candidate.startswith('//'):
        candidate = 'https:' + candidate
    elif candidate.startswith('/'):
        candidate = SITE_BASE + candidate
    elif candidate.startswith('./'):
        candidate = SITE_BASE + '/' + candidate[2:]
    elif not candidate.startswith('http'):
        candidate = SITE_BASE + '/' + candidate.lstrip('./')

    try:
        parts = urllib.parse.urlsplit(candidate)
    except ValueError:
        return None
    if parts.scheme != 'https':
        return None
    host = (parts.hostname or '').lower()
    # confronto esatto sull'host: una sottostringa nell'URL non autorizza nulla
    if host not in ALLOWED_HOSTS:
        return None
    if parts.username or parts.password:
        return None
    return urllib.parse.urlunsplit(parts)


def destination_for(url):
    """Nome di destinazione confinato in IMG_DIR, o None se non e' scrivibile.

    Il nome va decodificato *prima*: con basename() applicato all'URL grezzo,
    un `%2e%2e%2f` decodificato dopo avrebbe ricomposto un percorso di
    uscita dalla cartella.
    """
    path = urllib.parse.unquote(urllib.parse.urlsplit(url).path)
    name = os.path.basename(path.replace('\\', '/'))
    if not name or name in ('.', '..'):
        return None
    if os.path.splitext(name)[1].lower() not in ALLOWED_EXTENSIONS:
        return None
    dest = os.path.abspath(os.path.join(IMG_DIR, name))
    if os.path.commonpath([dest, os.path.abspath(IMG_DIR)]) != os.path.abspath(IMG_DIR):
        return None
    return dest


def collect_urls():
    urls = set()

    for name in MEDIA_FILES:
        path = os.path.join(TMP, name)
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8') as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            continue
        if not isinstance(data, list):
            continue
        for item in data:
            if isinstance(item, dict) and item.get('source_url'):
                urls.add(item['source_url'])

    html_files = [os.path.join(TMP, 'home.html')]
    extract = os.path.join(TMP, 'extract')
    if os.path.isdir(extract):
        html_files += [os.path.join(extract, f) for f in sorted(os.listdir(extract))
                       if f.lower().endswith('.html')]

    for path in html_files:
        try:
            with open(path, encoding='utf-8', errors='ignore') as handle:
                text = handle.read()
        except OSError:
            continue
        candidates = IMG_RE.findall(text)
        for entry in SRCSET_RE.findall(text):
            for part in entry.split(','):
                piece = part.strip().split(' ')[0]
                if piece and piece != '-':
                    candidates.append(piece)
        for candidate in candidates:
            urls.add(candidate)

    resolved = set()
    for candidate in urls:
        url = absolute_url(candidate)
        if url:
            resolved.add(url)
    return sorted(resolved)


def fetch(url, dest, context):
    """Scarica con tetto di dimensione, controllo del tipo e scrittura atomica.

    Scrive in `dest + '.part'` e rinomina solo a download completo: un'interruzione
    non puo' lasciare un .png troncato che un passo successivo scambierebbe per
    un'immagine completa. Il file parziale viene rimosso in ogni caso di errore,
    perche' `_site/` pubblica l'intera directory `assets/`.

    I redirect sono seguiti a mano e riverificati a ogni hop: `urlopen` li
    seguirebbe in automatico e ALLOWED_HOSTS controllerebbe solo il primo URL,
    lasciando un 302 verso un host interno come vettore SSRF.
    """
    headers = {'User-Agent': 'medphys-importer/1.0'}
    partial = dest + '.part'
    opener = _opener(context)

    try:
        return _fetch_inner(url, dest, partial, headers, opener)
    finally:
        # Un .part lasciato sul disco verrebbe pubblicato con il resto di
        # assets/, e un'immagine troncata cosi' sembrerebbe completa.
        if os.path.exists(partial):
            os.remove(partial)


def _fetch_inner(url, dest, partial, headers, opener):
    current = url
    head = b''
    total = 0
    for hop in range(MAX_REDIRECTS + 1):
        request = urllib.request.Request(current, headers=headers)
        try:
            response = opener.open(request, timeout=TIMEOUT)
        except urllib.error.HTTPError as exc:
            if exc.code not in (301, 302, 303, 307, 308) or hop >= MAX_REDIRECTS:
                raise
            location = exc.headers.get('Location')
            if not location:
                raise
            target = absolute_url(urllib.parse.urljoin(current, location))
            if target is None:
                raise ValueError('redirect verso host non consentito: %s' % location)
            current = target
            exc.close()
            continue

        with response:
            declared = (response.headers.get('Content-Length') or '').strip()
            if declared.isdigit() and int(declared) > MAX_BYTES:
                raise ValueError('immagine oltre %d byte' % MAX_BYTES)

            # Content-Type assente non e' un "pass": e' un'assenza di
            # informazione, e su questo canale si decide di rifiutare.
            content_type = (response.headers.get('Content-Type') or '').split(';')[0].strip().lower()
            if content_type not in ALLOWED_CONTENT_TYPES:
                raise ValueError('tipo non atteso: %s' % (content_type or 'assente'))

            total = 0
            with open(partial, 'wb') as handle:
                while True:
                    chunk = response.read(CHUNK)
                    if not chunk:
                        break
                    if len(head) < 16:
                        head += chunk[:16 - len(head)]
                    total += len(chunk)
                    if total > MAX_BYTES:
                        raise ValueError('immagine oltre %d byte' % MAX_BYTES)
                    handle.write(chunk)

            # Una connessione che si chiude a meta' non solleva alcuna
            # eccezione: il ciclo finisce semplicemente. Senza questo confronto
            # il file troncato passerebbe il controllo dei magic byte (che
            # guardano solo i primi byte) e verrebbe pubblicato come valido,
            # con i download successivi che lo scarterebno come "gia' presente".
            if declared.isdigit() and total != int(declared):
                raise ValueError('risposta troncata: %d byte su %d attesi'
                                 % (total, int(declared)))

    if not matches_magic(head, os.path.splitext(dest)[1]):
        raise ValueError("contenuto non coerente con l'estensione")

    os.replace(partial, dest)
    return total


def main():
    os.makedirs(IMG_DIR, exist_ok=True)
    # Verifica TLS attiva: e' il punto del download da host esterni.
    context = ssl.create_default_context()

    urls = collect_urls()
    print('Total candidate image urls:', len(urls))

    manifest = {}
    failures = []
    for url in urls:
        dest = destination_for(url)
        if dest is None:
            failures.append((url, 'percorso di destinazione non valido'))
            continue
        if os.path.exists(dest) and os.path.getsize(dest) > 0:
            manifest[url] = os.path.basename(dest)
            continue
        try:
            fetch(url, dest, context)
            manifest[url] = os.path.basename(dest)
        except Exception as exc:  # noqa: BLE001 - l'import non deve fermarsi
            failures.append((url, str(exc)))

    os.makedirs(TMP, exist_ok=True)
    with open(os.path.join(TMP, 'img_manifest.json'), 'w', encoding='utf-8') as handle:
        json.dump(manifest, handle, indent=1)

    print('Downloaded/available:', len(manifest), 'Failed:', len(failures))
    for url, error in failures[:40]:
        print('  FAIL', url, '->', error)
    # Il manifesto contiene quasi sempre le immagini gia' in archivio, quindi
    # legare il fallimento a `not manifest` nasconderebbe anche un import in cui
    # tutti i download sono falliti: l'esito deve dipendere dai soli fallimenti.
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
