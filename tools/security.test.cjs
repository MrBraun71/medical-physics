'use strict';

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.resolve(__dirname, '..');
const p = (...parts) => path.join(ROOT, ...parts);
const read = (...parts) => fs.readFileSync(p(...parts), 'utf8');

// The sanitizer must exist and be requireable from Node (dual UMD export) so the
// exact same code path that ships to the browser is what the tests exercise.
const S = require(p('assets', 'js', 'sanitize.js'));

// ---------------------------------------------------------------------------
// 1. HTML escaping (replaces the no-op esc() of app.js)
// ---------------------------------------------------------------------------

test('escapeHtml neutralises every HTML metacharacter', () => {
  assert.strictEqual(S.escapeHtml('<img src=x onerror=alert(1)>'),
    '&lt;img src=x onerror=alert(1)&gt;');
  assert.strictEqual(S.escapeHtml('a & b'), 'a &amp; b');
  assert.strictEqual(S.escapeHtml('"'), '&quot;');
  assert.strictEqual(S.escapeHtml("'"), '&#39;');
});

test('escapeHtml escapes ampersands before entities so they cannot be revived', () => {
  // &lt;script&gt; must not become a live tag after the browser re-parses it.
  assert.strictEqual(S.escapeHtml('&lt;script&gt;alert(1)&lt;/script&gt;'),
    '&amp;lt;script&amp;gt;alert(1)&amp;lt;/script&amp;gt;');
});

test('escapeHtml coerces non-string input instead of throwing', () => {
  assert.strictEqual(S.escapeHtml(null), '');
  assert.strictEqual(S.escapeHtml(undefined), '');
  assert.strictEqual(S.escapeHtml(0), '0');
  assert.strictEqual(S.escapeHtml({ a: 1 }), '[object Object]');
});

test('escapeAttr escapes quotes so attribute values cannot break out', () => {
  assert.strictEqual(S.escapeAttr('a" onload="alert(1)'),
    'a&quot; onload=&quot;alert(1)');
});

// ---------------------------------------------------------------------------
// 2. URL allow-list (blocks javascript:, data:, protocol-relative, control chars)
// ---------------------------------------------------------------------------

test('safeUrl rejects script-bearing schemes for links', () => {
  for (const bad of [
    'javascript:alert(1)',
    'JaVaScRiPt:alert(1)',
    '  javascript:alert(1)',
    '\tjavascript:alert(1)',
    'java\tscript:alert(1)',
    'java\nscript:alert(1)',
    '\u0000javascript:alert(1)',
    'vbscript:msgbox(1)',
    'data:text/html,<script>alert(1)</script>',
    'data:text/html;base64,PHNjcmlwdD4=',
  ]) {
    assert.strictEqual(S.safeUrl(bad, 'link'), null, `expected null for ${JSON.stringify(bad)}`);
  }
});

test('safeUrl keeps legitimate link targets', () => {
  assert.strictEqual(S.safeUrl('https://example.com/a?b=1#c', 'link'), 'https://example.com/a?b=1#c');
  assert.strictEqual(S.safeUrl('mailto:info@example.com', 'link'), 'mailto:info@example.com');
  assert.strictEqual(S.safeUrl('tel:+3901234567', 'link'), 'tel:+3901234567');
  assert.strictEqual(S.safeUrl('#section-3', 'link'), '#section-3');
  assert.strictEqual(S.safeUrl('/pages/istruzione.html', 'link'), '/pages/istruzione.html');
  assert.strictEqual(S.safeUrl('assets/img/logo.png', 'link'), 'assets/img/logo.png');
});

test('safeUrl refuses plaintext http and protocol-relative URLs', () => {
  assert.strictEqual(S.safeUrl('http://example.com/a', 'link'), null);
  assert.strictEqual(S.safeUrl('http://example.com/a', 'media'), null);
  assert.strictEqual(S.safeUrl('//evil.example/x', 'link'), null);
});

test('safeUrl rejects script schemes hidden behind character entities', () => {
  // Il browser decodifica le entita' leggendo l'attributo: questi payload
  // arrivano al controllo dello schema come se fossero testo letterale.
  for (const bad of [
    'jav&#x09;ascript:alert(1)',
    'jav&#9;ascript:alert(1)',
    'jav&#x0A;ascript:alert(1)',
    'jav&#x0D;ascript:alert(1)',
    '&Tab;javascript:alert(1)',
    '&NewLine;javascript:alert(1)',
    '&#0000106;avascript:alert(1)',
    'javascript&colon;alert(1)',
    '&#106;avascript:alert(1)',
  ]) {
    assert.strictEqual(S.safeUrl(bad, 'link'), null, `link: expected null for ${JSON.stringify(bad)}`);
    assert.strictEqual(S.safeUrl(bad, 'media'), null, `media: expected null for ${JSON.stringify(bad)}`);
    assert.strictEqual(S.safeUrl(bad, 'embed'), null, `embed: expected null for ${JSON.stringify(bad)}`);
  }
});

test('safeUrl rejects backslashes that the browser would resolve cross-origin', () => {
  for (const bad of [
    '\\evil.example\\x',
    '/\\evil.example/x',
    'https:\\evil.example',
    'https:\\/\\/evil.example',
    'https&#x3a;\\evil.example',
  ]) {
    assert.strictEqual(S.safeUrl(bad, 'link'), null, `expected null for ${JSON.stringify(bad)}`);
    assert.strictEqual(S.safeUrl(bad, 'media'), null, `media: expected null for ${JSON.stringify(bad)}`);
  }
});

test('safeUrl returns the URL the browser will see, not a double-escaped one', () => {
  assert.strictEqual(
    S.safeUrl('https://example.com/?a=1&amp;b=2', 'link'),
    'https://example.com/?a=1&b=2'
  );
  // Nessuna regressione sui percorsi senza entita'.
  assert.strictEqual(S.safeUrl('https://example.com/a?b=1#c', 'link'), 'https://example.com/a?b=1#c');
});

test('safeUrl for media allows https and relative paths but not data URIs', () => {
  assert.strictEqual(S.safeUrl('https://cdn.example.com/a.png', 'media'), 'https://cdn.example.com/a.png');
  assert.strictEqual(S.safeUrl('/assets/img/a.png', 'media'), '/assets/img/a.png');
  assert.strictEqual(S.safeUrl('assets/img/a.png', 'media'), 'assets/img/a.png');
  assert.strictEqual(S.safeUrl('data:image/png;base64,iVBOR', 'media'), null);
});

test('safeUrl for embeds only accepts the youtube-nocookie embed origin', () => {
  assert.ok(S.safeUrl('https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ', 'embed'));
  assert.strictEqual(S.safeUrl('https://www.youtube.com/embed/dQw4w9WgXcQ', 'embed'), null);
  assert.strictEqual(S.safeUrl('https://evil.example/embed/x', 'embed'), null);
  assert.strictEqual(S.safeUrl('javascript:alert(1)', 'embed'), null);
});

// ---------------------------------------------------------------------------
// 3. Target / rel hardening
// ---------------------------------------------------------------------------

test('isExternalUrl only treats absolute http(s) URLs as external', () => {
  assert.strictEqual(S.isExternalUrl('https://example.com'), true);
  assert.strictEqual(S.isExternalUrl('http://example.com'), true);
  assert.strictEqual(S.isExternalUrl('/pages/x.html'), false);
  assert.strictEqual(S.isExternalUrl('#top'), false);
  assert.strictEqual(S.isExternalUrl('mailto:a@b.it'), false);
  assert.strictEqual(S.isExternalUrl('assets/img/a.png'), false);
});

test('relAttrs adds noopener noreferrer for external targets', () => {
  assert.strictEqual(S.relAttrs('https://example.com'), 'noopener noreferrer');
  assert.strictEqual(S.relAttrs('/pages/x.html'), '');
});

// ---------------------------------------------------------------------------
// 4. Prototype-pollution-safe slug handling
// ---------------------------------------------------------------------------

test('isValidSlug accepts the documented slug alphabet only', () => {
  assert.ok(S.isValidSlug('istruzione'));
  assert.ok(S.isValidSlug('radiazioni-terapeutiche'));
  assert.ok(S.isValidSlug('imaging'));
  for (const bad of ['constructor', '__proto__', 'toString', '../../etc/passwd', 'a b', '', 'a/b', 'x?y']) {
    assert.strictEqual(S.isValidSlug(bad), false, `expected invalid: ${bad}`);
  }
});

test('every slug published in the data survives slug validation', () => {
  // Regressione: la validazione dello slug non deve invalidare i link gia'
  // pubblicati (es. #/pattern_recognition, che usa il trattino basso). Il valore
  // viaggia solo come fragment e come chiave: non e' mai un percorso.
  const routes = new Set();
  const collect = (value) => {
    if (Array.isArray(value)) { value.forEach(collect); return; }
    if (value && typeof value === 'object') {
      if (typeof value.slug === 'string') routes.add(value.slug);
      Object.values(value).forEach(collect);
    }
  };
  const site = loadDataBundle(['assets', 'data', 'site-data.js']);
  collect(site.MEDPHYS_SITE);
  Object.keys(loadDataBundle(['assets', 'data', 'pages_en.js']).MEDPHYS_EN).forEach((k) => routes.add(k));
  Object.keys(loadDataBundle(['assets', 'data', 'i18n.js']).MEDPHYS_IT).forEach((k) => routes.add(k));
  assert.ok(routes.size > 20, `expected the real route set, found ${routes.size}`);
  for (const route of routes) {
    assert.ok(S.isValidSlug(route), `published route must stay reachable: ${route}`);
  }
});

test('hasSlug never resolves inherited Object.prototype members', () => {
  assert.strictEqual(S.hasSlug({ istruzione: {} }, 'istruzione'), true);
  assert.strictEqual(S.hasSlug({ istruzione: {} }, 'toString'), false);
  assert.strictEqual(S.hasSlug({ istruzione: {} }, 'constructor'), false);
  assert.strictEqual(S.hasSlug({ istruzione: {} }, 'valueOf'), false);
  assert.strictEqual(S.hasSlug({ istruzione: {} }, '__proto__'), false);
  assert.strictEqual(S.hasSlug({}, 'hasOwnProperty'), false);
});

// ---------------------------------------------------------------------------
// 5. Rich-content sanitizer
// ---------------------------------------------------------------------------

test('sanitizeRichHtml keeps the real editorial markup', () => {
  const input = '<h2>Titolo</h2><p><strong>Grassetto</strong> e <em>corsivo</em>.</p>'
    + '<ul><li>uno</li><li>due</li></ul><table><thead><tr><th>a</th></tr></thead>'
    + '<tbody><tr><td colspan="2">b</td></tr></tbody></table>';
  assert.strictEqual(S.sanitizeRichHtml(input), input);
});

test('sanitizeRichHtml drops script blocks together with their content', () => {
  assert.strictEqual(S.sanitizeRichHtml('<p>a</p><script>alert(1)</script><p>b</p>'), '<p>a</p><p>b</p>');
  assert.strictEqual(S.sanitizeRichHtml('<script>alert(1)</script>'), '');
  assert.strictEqual(S.sanitizeRichHtml('<SCRIPT SRC=//evil.example/x.js></SCRIPT>ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<style>body{display:none}</style>ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<object data="evil.swf">x</object>ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<embed src="evil.swf">ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<svg><script>alert(1)</script></svg>ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<math><mtext>x</mtext></math>ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<template><img src=x onerror=alert(1)></template>ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<noscript><img src=x onerror=alert(1)></noscript>ok'), 'ok');
});

test('sanitizeRichHtml strips every event handler attribute', () => {
  assert.strictEqual(S.sanitizeRichHtml('<p onclick="alert(1)">testo</p>'), '<p>testo</p>');
  assert.strictEqual(S.sanitizeRichHtml('<p ONMOUSEOVER=alert(1)>testo</p>'), '<p>testo</p>');
  assert.strictEqual(S.sanitizeRichHtml('<img src="https://a/b.png" onerror="alert(1)">'),
    '<img src="https://a/b.png">');
  assert.strictEqual(S.sanitizeRichHtml('<div onpointerover=alert(1) onfocus=alert(2)>x</div>'), '<div>x</div>');
});

test('sanitizeRichHtml removes javascript: and data: URL attributes', () => {
  assert.strictEqual(S.sanitizeRichHtml('<a href="javascript:alert(1)">clic</a>'), '<a>clic</a>');
  assert.strictEqual(S.sanitizeRichHtml('<img src="javascript:alert(1)">'), '<img>');
  assert.strictEqual(S.sanitizeRichHtml('<img src="data:text/html,<script>alert(1)</script>">'), '<img>');
  assert.strictEqual(S.sanitizeRichHtml('<a href="  javascript:alert(1)">clic</a>'), '<a>clic</a>');
});

test('sanitizeRichHtml hardens external links with rel noopener noreferrer', () => {
  assert.strictEqual(S.sanitizeRichHtml('<a href="https://example.com" target="_blank">x</a>'),
    '<a href="https://example.com" target="_blank" rel="noopener noreferrer">x</a>');
  // rel is overwritten even if the content already carries a bogus one
  assert.strictEqual(S.sanitizeRichHtml('<a href="https://example.com" rel="opener">x</a>'),
    '<a href="https://example.com" rel="noopener noreferrer">x</a>');
  // internal links stay untouched
  assert.strictEqual(S.sanitizeRichHtml('<a href="/pages/x.html">x</a>'), '<a href="/pages/x.html">x</a>');
});

test('sanitizeRichHtml rewrites YouTube iframes to the no-cookie host and sandboxes them', () => {
  const out = S.sanitizeRichHtml('<div class="video-embed">'
    + '<iframe src="https://www.youtube.com/embed/bWlGZdmzpLU?rel=0" title="Video" loading="lazy" allowfullscreen></iframe>'
    + '</div>');
  assert.match(out, /src="https:\/\/www\.youtube-nocookie\.com\/embed\/bWlGZdmzpLU\?rel=0"/);
  assert.match(out, /sandbox="allow-scripts allow-same-origin allow-presentation allow-popups"/);
  assert.match(out, /referrerpolicy="strict-origin-when-cross-origin"/);
  assert.match(out, /loading="lazy"/);
  assert.match(out, /title="Video"/);
  assert.doesNotMatch(out, /youtube\.com/);
  assert.doesNotMatch(out, /allowfullscreen/);
});

test('sanitizeRichHtml removes iframes that are not YouTube embeds', () => {
  assert.strictEqual(S.sanitizeRichHtml('<iframe src="https://evil.example/x"></iframe>ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<iframe srcdoc="<script>alert(1)</script>"></iframe>ok'), 'ok');
  assert.strictEqual(S.sanitizeRichHtml('<iframe src="//evil.example/x"></iframe>ok'), 'ok');
});

test('sanitizeRichHtml keeps only allow-listed CSS classes', () => {
  assert.strictEqual(S.sanitizeRichHtml('<div class="video-embed">x</div>'), '<div class="video-embed">x</div>');
  assert.strictEqual(S.sanitizeRichHtml('<div class="evil-lookalike">x</div>'), '<div>x</div>');
  assert.strictEqual(S.sanitizeRichHtml('<div class="video-embed something-else">x</div>'),
    '<div class="video-embed">x</div>');
});

test('sanitizeRichHtml drops non-allow-listed tags but keeps their text', () => {
  assert.strictEqual(S.sanitizeRichHtml('<form action="/x"><input name="a"></form>testo'), 'testo');
  assert.strictEqual(S.sanitizeRichHtml('<marquee>testo</marquee>'), 'testo');
  assert.strictEqual(S.sanitizeRichHtml('<button onclick="alert(1)">clic</button>'), 'clic');
  assert.strictEqual(S.sanitizeRichHtml('<details><summary>info</summary>testo</details>'), 'infotesto');
});

test('sanitizeRichHtml cannot be broken out of with quotes inside attribute values', () => {
  const payload = '<a href="https://ok.example/" title="a&quot; onmouseover=&quot;alert(1)">x</a>';
  const out = S.sanitizeRichHtml(payload);
  assert.doesNotMatch(out, /onmouseover="alert/);
  assert.match(out, /title="a&quot; onmouseover=&quot;alert\(1\)"/);
});

test('sanitizeRichHtml escapes stray angle brackets instead of emitting broken markup', () => {
  assert.strictEqual(S.sanitizeRichHtml('a < b'), 'a &lt; b');
  assert.strictEqual(S.sanitizeRichHtml('5 > 3'), '5 &gt; 3');
  assert.strictEqual(S.sanitizeRichHtml('<p>a</p><'), '<p>a</p>&lt;');
  assert.strictEqual(S.sanitizeRichHtml('<!-- comment -->testo'), 'testo');
  assert.strictEqual(S.sanitizeRichHtml('<!DOCTYPE html>testo'), 'testo');
});

test('sanitizeRichHtml drops comments that could hide conditional payloads', () => {
  assert.strictEqual(S.sanitizeRichHtml('<!--[if IE]><script>alert(1)</script><![endif]-->x'), 'x');
});

test('sanitizeRichHtml is idempotent', () => {
  const input = '<h2>T</h2><p><strong>a</strong></p><ul><li>x</li></ul>';
  const once = S.sanitizeRichHtml(input);
  assert.strictEqual(S.sanitizeRichHtml(once), once);
});

test('sanitizeRichHtml handles empty and non-string input safely', () => {
  assert.strictEqual(S.sanitizeRichHtml(''), '');
  assert.strictEqual(S.sanitizeRichHtml(null), '');
  assert.strictEqual(S.sanitizeRichHtml(undefined), '');
});

// ---------------------------------------------------------------------------
// 6. Static policy checks on the shipped source
// ---------------------------------------------------------------------------

const DATA_FILES = [
  ['assets', 'data', 'pages_en.js'],
  ['assets', 'data', 'i18n.js'],
  ['assets', 'data', 'site-data.js'],
];

test('index.html ships a strict CSP meta without unsafe-eval', () => {
  const html = read('index.html');
  const csp = html.match(/<meta[^>]+http-equiv=["']Content-Security-Policy["'][^>]*>/i);
  assert.ok(csp, 'index.html must declare a CSP via meta');
  const policy = csp[0];
  assert.match(policy, /default-src 'self'/);
  assert.doesNotMatch(policy, /unsafe-eval/);
  assert.doesNotMatch(policy, /unsafe-inline/);
  assert.match(policy, /frame-src/);
});

test('index.html declares a referrer policy', () => {
  const html = read('index.html');
  assert.match(html, /<meta[^>]+name=["']referrer["'][^>]+content=["']strict-origin-when-cross-origin["']/i);
});

test('no inline event-handler attributes anywhere in the shipped front-end', () => {
  const files = [['index.html'], ['assets', 'js', 'app.js'], ['assets', 'js', 'sanitize.js'], ...DATA_FILES];
  // Rimuove i letterali (singoli, doppi e backtick) per evitare falsi positivi
  // sui valori di testo, poi cerca handler davanti a un segno di uguale.
  const stripLiterals = (src) => src
    .replace(/(["'`])(?:\\.|(?!\1)[^\\])*\1/g, '""')
    .replace(/\\u[0-9a-fA-F]{4}/g, '');
  for (const f of files) {
    const hits = stripLiterals(read(...f)).match(/\son[a-z]+\s*=/gi);
    assert.strictEqual(hits, null, `${f.join('/')} contains inline handler(s): ${hits}`);
  }
});

test('no inline style attributes and no onsubmit pseudo-protocol in app.js', () => {
  const src = read('assets', 'js', 'app.js');
  const stripped = src.replace(/["'][^"']*["']/g, '""');
  assert.strictEqual(stripped.match(/\sstyle\s*=\s*["']/i), null);
  assert.doesNotMatch(src, /onsubmit/i);
});

test('app.js no longer ships a no-op esc() and routes rich content through the sanitizer', () => {
  const src = read('assets', 'js', 'app.js');
  assert.doesNotMatch(src, /function esc\s*\(/);
  // Un solo punto di applicazione del sanitizer (il chokepoint `rich()`), piu'
  // un chiamante per ogni sink di contenuto ricco.
  const sanitizerCalls = src.match(/sanitizeRichHtml\(/g) || [];
  assert.strictEqual(sanitizerCalls.length, 1, 'the sanitizer should live in exactly one chokepoint');
  const richCalls = (src.match(/\brich\(/g) || []).length - 1; // -1 = definizione
  assert.ok(richCalls >= 3, `expected a rich() call per rich-content sink, found ${richCalls}`);
  // Un solo punto di scrittura nel DOM: il resto della UI e' testo/attributi
  // codificati, quindi nessun altro percorso puo' iniettare markup grezzo.
  const sinks = src.match(/innerHTML\s*=/g) || [];
  assert.strictEqual(sinks.length, 1, `expected exactly one sanitised DOM sink, found ${sinks.length}`);
});

test('app.js guards every language dictionary lookup with hasOwnProperty', () => {
  const src = read('assets', 'js', 'app.js');
  assert.doesNotMatch(src, /\bEN\[\s*(?:lang|route|slug)/);
  assert.match(src, /hasSlug\(/);
});

test('published data carries no plaintext-http links and only sandboxed YouTube iframes', () => {
  for (const f of DATA_FILES) {
    const src = read(...f);
    const offenders = src.match(/http:\/\//g) || [];
    assert.strictEqual(offenders.length, 0, `${f.join('/')} still contains ${offenders.length} http:// URL(s)`);
    const iframes = src.match(/<iframe[^>]*>/gi) || [];
    for (const tag of iframes) {
      // Nel sorgente gli attributi sono dentro una stringa JS, quindi le
      // virgolette possono essere escaped: si accetta la forma attesa e quella
      // effettiva del file.
      assert.match(tag, /sandbox=\\?"/, `iframe without sandbox: ${tag}`);
      assert.match(tag, /referrerpolicy=\\?"/, `iframe without referrerpolicy: ${tag}`);
      assert.match(tag, /youtube-nocookie\.com/, `iframe not on the no-cookie host: ${tag}`);
    }
  }
});

test('download_images.py verifies TLS and confines writes to the image directory', () => {
  const src = read('tools', 'download_images.py');
  assert.doesNotMatch(src, /CERT_NONE/);
  assert.doesNotMatch(src, /check_hostname\s*=\s*False/);
  assert.match(src, /ALLOWED_HOSTS|ALLOWED_HOST/);
  assert.match(src, /commonpath|resolve\(\).*relative_to|startswith\(IMG_DIR/);
  assert.match(src, /MAX_/);
});

test('content generators escape interpolated text and validate link schemes', () => {
  for (const f of [['tools', 'clean_content.py'], ['tools', 'build_i18n.py']]) {
    const src = read(...f);
    assert.match(src, /html\.escape|escape_html|safe_url|sanitize/, `${f.join('/')} lacks escaping/validation`);
  }
});

test('the Pages workflow publishes a curated directory, not the repository', () => {
  const src = read('.github', 'workflows', 'pages.yml');
  const pathLine = src.match(/^\s*path:\s*(.+)$/m);
  assert.ok(pathLine, 'pages.yml must declare an upload path');
  assert.notStrictEqual(pathLine[1].trim().replace(/^['"]|['"]$/g, ''), '.',
    'uploading the repository root would publish source, tooling and dotfiles');
  assert.match(src, /\.nojekyll/);
  assert.match(src, /permissions:/);
  // every pinned action must be pinned to a full 40-character commit SHA
  const uses = src.match(/uses:\s*([^\s#]+)/g) || [];
  for (const u of uses) {
    assert.match(u, /@[0-9a-f]{40}$/, `action not pinned to a SHA: ${u}`);
  }
});

test('repository hygiene files are present', () => {
  assert.ok(fs.existsSync(p('robots.txt')), 'robots.txt missing');
  assert.ok(fs.existsSync(p('.well-known', 'security.txt')), 'security.txt missing');
  assert.ok(fs.existsSync(p('.gitignore')), '.gitignore missing');
  const gitignore = read('.gitignore');
  assert.match(gitignore, /_site\//);
  assert.match(gitignore, /__pycache__/);
});

test('dependabot keeps the pinned GitHub Actions current', () => {
  const src = read('.github', 'dependabot.yml');
  assert.match(src, /package-ecosystem:\s*"github-actions"/);
  assert.match(src, /directory:\s*"\/"/);
});

// ---------------------------------------------------------------------------
// 7. Regression tests driven by the real shipped content
// ---------------------------------------------------------------------------

function loadDataBundle(file) {
  const vm = require('node:vm');
  const sandbox = { window: {} };
  vm.createContext(sandbox);
  vm.runInContext(read(...file), sandbox, { filename: file.join('/') });
  return sandbox.window;
}

function collectStrings(value, out) {
  if (typeof value === 'string') {
    out.push(value);
  } else if (Array.isArray(value)) {
    value.forEach((v) => collectStrings(v, out));
  } else if (value && typeof value === 'object') {
    Object.keys(value).forEach((k) => collectStrings(value[k], out));
  }
  return out;
}

const RICH_BUNDLES = [
  { file: ['assets', 'data', 'pages_en.js'], keys: ['MEDPHYS_EN'] },
  { file: ['assets', 'data', 'i18n.js'], keys: ['MEDPHYS_IT', 'MEDPHYS_EN_X'] },
];

test('sanitising the real corpus loses no visible text', () => {
  // Il sanitizer normalizza di proposito (entita' numeriche, `rel` sugli
  // esterni): quindi il confronto e' sul testo visibile, non sui byte.
  const visibleText = (html) => S.decodeEntities(html.replace(/<[^>]*>/g, '')).replace(/\s+/g, ' ').trim();
  let checked = 0;
  for (const { file, keys } of RICH_BUNDLES) {
    const win = loadDataBundle(file);
    for (const key of keys) {
      for (const body of collectStrings(win[key], [])) {
        assert.strictEqual(visibleText(S.sanitizeRichHtml(body)), visibleText(body),
          `${file.join('/')} :: ${key} :: la sanificazione ha perso testo`);
        checked += 1;
      }
    }
  }
  assert.ok(checked > 20, `expected a meaningful corpus, sanitised only ${checked} strings`);
});

test('sanitising the real corpus is idempotent', () => {
  for (const { file, keys } of RICH_BUNDLES) {
    const win = loadDataBundle(file);
    for (const key of keys) {
      for (const body of collectStrings(win[key], [])) {
        const once = S.sanitizeRichHtml(body);
        assert.strictEqual(S.sanitizeRichHtml(once), once,
          `${file.join('/')} :: ${key} :: sanificazione non idempotente`);
      }
    }
  }
});

test('sanitising the real corpus cannot introduce an executable construct', () => {
  for (const { file, keys } of RICH_BUNDLES) {
    const win = loadDataBundle(file);
    for (const key of keys) {
      for (const body of collectStrings(win[key], [])) {
        const clean = S.sanitizeRichHtml(body);
        assert.doesNotMatch(clean, /<\s*script/i, 'script survived sanitisation');
        assert.doesNotMatch(clean, /\son[a-z]+\s*=/i, 'event handler survived sanitisation');
        assert.doesNotMatch(clean, /javascript\s*:/i, 'javascript: URL survived sanitisation');
        assert.doesNotMatch(clean, /data\s*:\s*text\/html/i, 'data:text/html survived sanitisation');
      }
    }
  }
});

test('every external URL in the shipped data is https and carries rel hardening', () => {
  const win = loadDataBundle(['assets', 'data', 'site-data.js']);
  const urls = collectStrings(win.MEDPHYS_SITE, [])
    .filter((s) => /^https?:\/\//i.test(s));
  assert.ok(urls.length > 0, 'expected external URLs in site-data.js');
  for (const u of urls) {
    assert.match(u, /^https:\/\//i, `plaintext http URL in data: ${u}`);
  }
});
