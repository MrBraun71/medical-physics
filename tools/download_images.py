import json, os, re, ssl, urllib.request, urllib.parse, sys

TMP = os.path.join(os.environ['TEMP'], 'mp')
OUT = r'E:\MedPhys_Sito\assets\img'
os.makedirs(OUT, exist_ok=True)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

urls = set()

# media endpoints
for f in ['media1.json', 'media2.json', 'media.json']:
    p = os.path.join(TMP, f)
    if not os.path.exists(p):
        continue
    try:
        data = json.load(open(p, encoding='utf-8'))
    except Exception:
        continue
    if isinstance(data, list):
        for m in data:
            if isinstance(m, dict) and m.get('source_url'):
                urls.add(m['source_url'])

# images referenced in html files
imgre = re.compile(r'(?:src|href)=["\']([^"\']+\.(?:png|jpe?g|gif|svg))["\']', re.I)
html_files = [os.path.join(TMP, 'home.html')]
extract = os.path.join(TMP, 'extract')
if os.path.isdir(extract):
    html_files += [os.path.join(extract, f) for f in os.listdir(extract) if f.endswith('.html')]
for hf in html_files:
    try:
        txt = open(hf, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for m in imgre.findall(txt):
        if m.startswith('//'):
            m = 'https:' + m
        elif m.startswith('/'):
            m = 'https://medphys.ba.infn.it' + m
        elif m.startswith('./'):
            m = 'https://medphys.ba.infn.it/' + m[2:]
        elif not m.startswith('http'):
            m = 'https://medphys.ba.infn.it/' + m
        urls.add(m)

# srcset references
srcsetre = re.compile(r'srcset=["\']([^"\']+)["\']', re.I)
for hf in html_files:
    try:
        txt = open(hf, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for ss in srcsetre.findall(txt):
        for part in ss.split(','):
            u = part.strip().split(' ')[0]
            if u and u != '-':
                if u.startswith('//'):
                    u = 'https:' + u
                elif u.startswith('/'):
                    u = 'https://medphys.ba.infn.it' + u
                urls.add(u)

urls = sorted(u for u in urls if 'medphys.ba.infn.it' in u or u.startswith('http'))
print('Total candidate image urls:', len(urls))

manifest = {}
fails = []
for i, u in enumerate(urls):
    name = os.path.basename(urllib.parse.urlparse(u).path)
    name = urllib.parse.unquote(name)
    if not name:
        continue
    dest = os.path.join(OUT, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        manifest[u] = name
        continue
    try:
        req = urllib.request.Request(u, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
            data = r.read()
        with open(dest, 'wb') as fh:
            fh.write(data)
        manifest[u] = name
    except Exception as e:
        fails.append((u, str(e)))

json.dump(manifest, open(os.path.join(TMP, 'img_manifest.json'), 'w', encoding='utf-8'), indent=1)
print('Downloaded/available:', len(manifest), 'Failed:', len(fails))
for u, e in fails[:40]:
    print('  FAIL', u, '->', e)
