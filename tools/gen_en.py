import os, json, re

OUT = r'E:\MedPhys_Sito\assets\data'
pages = json.load(open(os.path.join(OUT, 'pages_en.json'), encoding='utf-8'))
meta = json.load(open(os.path.join(OUT, 'meta.json'), encoding='utf-8'))

def fix(h):
    h = h.lstrip('\ufeff\n\r ')
    # unwrap <p><div>..</div></p> invalid nesting
    h = re.sub(r'<p>(<div\b[\s\S]*?</div>)</p>', r'\1', h)
    h = re.sub(r'<p>\s*(<div\b[^>]*>)', r'\1', h)
    h = h.replace('</div></p>', '</div>')
    h = re.sub(r'(<div class="video-embed">.*?</div>)</p>', r'\1', h, flags=re.S)
    return h.strip()

pages = {k: fix(v) for k, v in pages.items()}

def js(obj):
    return json.dumps(obj, ensure_ascii=False).replace('</', '<\\/')

with open(os.path.join(OUT, 'pages_en.js'), 'w', encoding='utf-8') as f:
    f.write('window.MEDPHYS_EN = ' + js(pages) + ';\n')
    f.write('window.MEDPHYS_META = ' + js(meta) + ';\n')

print('written pages_en.js', os.path.getsize(os.path.join(OUT, 'pages_en.js')))
print('slugs:', len(pages))
