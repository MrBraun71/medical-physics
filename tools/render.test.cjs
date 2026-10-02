'use strict';

/* Test di rendering: verificano che l'hardening non abbia rotto il sito.
 *
 * security.test.cjs dimostra che i dati non fidati vengono sanificati; questi
 * test dimostrano che, dopo la riscrittura, ogni route continua a produrre una
 * pagina reale (header, main, footer) e che un valore malevolo resta inerte
 * nel DOM finale. E' la rete di sicurezza contro regressioni di funzionalita'.
 */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { makeWindow } = require('./dom-shim.cjs');

const ROOT = path.resolve(__dirname, '..');
const p = (...parts) => path.join(ROOT, ...parts);
const read = (...parts) => fs.readFileSync(p(...parts), 'utf8');

const APP_FILES = ['assets/data/site-data.js', 'assets/data/pages_en.js', 'assets/data/i18n.js',
  'assets/js/sanitize.js', 'assets/js/app.js'].map((f) => p(f));

function boot(hash) {
  const { app } = makeWindow(APP_FILES, { hash });
  return app.innerHTMLSerialized;
}

/* Tutte le route raggiungibili, piu' i casi limite del router. */
function publishedRoutes() {
  const files = {
    'assets/data/site-data.js': 'MEDPHYS_SITE',
    'assets/data/pages_en.js': 'MEDPHYS_EN',
    'assets/data/i18n.js': 'MEDPHYS_IT',
  };
  const routes = new Set();
  for (const [file, key] of Object.entries(files)) {
    const sandbox = { window: {} };
    vm.createContext(sandbox);
    vm.runInContext(read(...file.split('/')), sandbox, { filename: file });
    const collect = (value) => {
      if (Array.isArray(value)) { value.forEach(collect); return; }
      if (value && typeof value === 'object') {
        if (typeof value.slug === 'string') routes.add(value.slug);
        Object.values(value).forEach(collect);
      }
    };
    collect(sandbox.window[key]);
    // Solo i dizionari di pagine espongono chiavi-slung: in MEDPHYS_SITE le
    // stringhe sono valori (logo, address, ...), non route.
    if (key !== 'MEDPHYS_SITE') {
      for (const k of Object.keys(sandbox.window[key] || {})) {
        if (typeof sandbox.window[key][k] === 'string' && sandbox.window[key][k].trim()) routes.add(k);
      }
    }
  }
  return [...routes];
}

const ROUTES = publishedRoutes();
const EXPECT_404 = ['constructor', '__proto__', 'toString', 'NON-ESISTE', '../../etc/passwd'];

test('publishedRoutes finds the real route set', () => {
  assert.ok(ROUTES.length > 50, `expected the shipped routes, found ${ROUTES.length}`);
});

test('every published route renders a complete page', () => {
  for (const route of ROUTES) {
    const html = boot('#/' + route);
    assert.ok(html.startsWith('<a class="skip"'), `${route}: header mancante`);
    assert.ok(html.includes('<main id="main">'), `${route}: main mancante`);
    assert.ok(html.includes('<footer class="site-footer">'), `${route}: footer mancante`);
    assert.ok(html.length > 1000, `${route}: pagina sospettosamente vuota (${html.length} byte)`);
    assert.doesNotMatch(html, /could not be rendered|non e' stato possibile renderizzarla/,
      `${route}: render di primo livello fallito`);
  }
});

test('unknown and hostile hashes fall through to 404 instead of rendering data', () => {
  for (const route of EXPECT_404) {
    const html = boot('#/' + route);
    assert.match(html, /Page not found|Pagina non trovata/, `${route}: atteso 404`);
  }
});

test('no rendered route leaks an executable construct', () => {
  for (const route of ROUTES) {
    const html = boot('#/' + route);
    assert.doesNotMatch(html, /<script(?![^>]*src=)/i, `${route}: script inline`);
    assert.doesNotMatch(html, /\son[a-z]+\s*=\s*["']/i, `${route}: handler inline`);
    assert.doesNotMatch(html, /\sstyle\s*=\s*["']/i, `${route}: stile inline`);
    assert.doesNotMatch(html, /href="javascript:/i, `${route}: URL javascript:`);
    assert.doesNotMatch(html, /="http:\/\//i, `${route}: URL in chiaro`);
  }
});

test('every YouTube embed reaches the DOM sandboxed and on the no-cookie host', () => {
  let iframes = 0;
  for (const route of ROUTES) {
    const html = boot('#/' + route);
    for (const tag of html.match(/<iframe[^>]*>/gi) || []) {
      iframes += 1;
      assert.match(tag, /sandbox=/, `${route}: iframe senza sandbox`);
      assert.match(tag, /referrerpolicy=/, `${route}: iframe senza referrerpolicy`);
      assert.match(tag, /youtube-nocookie\.com/, `${route}: iframe non spostato su nocookie`);
    }
  }
  assert.ok(iframes > 0, 'il corpus dovrebbe contenere almeno un embed');
});

test('external links open in a new tab with rel hardening', () => {
  for (const route of ROUTES) {
    const html = boot('#/' + route);
    for (const tag of html.match(/<a\b[^>]*>/gi) || []) {
      if (!/target="_blank"/.test(tag)) continue;
      assert.match(tag, /rel="noopener noreferrer"/, `${route}: target=_blank senza rel`);
    }
  }
});

test('a hostile data value stays inert text in the rendered DOM', () => {
  const env = makeWindow(APP_FILES.slice(0, 3), { hash: '#/home' });
  const w = env.window;
  // Ogni foglia testuale e' un dizionario {en, it}: si avvelena la voce 'en'.
  w.MEDPHYS_SITE.home.kicker.en = '<script>alert(1)</script>';
  w.MEDPHYS_SITE.home.title.en = '"><script>alert(2)</script>';
  w.MEDPHYS_SITE.home.lead.en = '"><img src=x onerror=alert(3)>';
  w.MEDPHYS_SITE.home.para2.en = 'javascript:alert(4)';
  w.MEDPHYS_SITE.publications[0].en = '<script>alert(5)</script>';
  w.window.run(p('assets/js/sanitize.js'));
  w.window.run(p('assets/js/app.js'));
  const html = env.app.innerHTMLSerialized;

  assert.doesNotMatch(html, /<script>alert\(\d\)<\/script>/i);
  assert.doesNotMatch(html, /<img[^>]*\bonerror/i);
  assert.doesNotMatch(html, /<[a-zA-Z][^>]*\son[a-z]+\s*=\s*["']?/i);
  assert.doesNotMatch(html, /href="javascript:/i);
  // Il testo resta leggibile, ma codificato.
  assert.match(html, /&lt;script&gt;alert\(1\)&lt;\/script&gt;/);
  assert.match(html, /&quot;&gt;&lt;script&gt;alert\(2\)&lt;\/script&gt;/);
});

test('the sanitizer is required: without it the page is not rendered at all', () => {
  // Se il sanitizer non e' presente il sito deve restare vuoto, non rendersi
  // markup grezzo: e' il fail-safe dell'hardening.
  const env = makeWindow(APP_FILES.slice(0, 3), { hash: '#/home' });
  env.window.run(p('assets/js/app.js'));
  assert.equal(env.app.innerHTMLSerialized.length, 0);
  assert.match(env.app.textContent, /Errore di configurazione/);
});

test('the language switcher re-renders in place instead of reloading', () => {
  const env = makeWindow(APP_FILES, { hash: '#/home' });
  const before = env.app.innerHTMLSerialized;
  assert.ok(before.length > 1000);
  assert.match(before, /Explore research/);

  const buttons = env.app.querySelectorAll('[data-setlang]');
  assert.ok(buttons.length >= 2, 'mancano i pulsanti di lingua');
  buttons[1].dispatch('click', { preventDefault() {} });

  const after = env.app.innerHTMLSerialized;
  assert.notEqual(after, before, 'il cambio lingua non ha prodotto un nuovo render');
  assert.match(after, /Esplora la ricerca/, 'il testo italiano non e\' comparso');
  assert.strictEqual(env.window.document.documentElement.lang, 'it');
  assert.strictEqual(env.window.localStorage.getItem('medphys_lang'), 'it');
});
