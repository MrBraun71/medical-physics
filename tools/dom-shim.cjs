'use strict';
/* Shim DOM minimale, zero dipendenze, sufficiente a eseguire assets/js/app.js
 * fuori dal browser.
 *
 * Non e' un browser e non vuole esserlo: implementa solo il piccolo sottoinsieme
 * di DOM che app.js tocca davvero (template.innerHTML, replaceChildren,
 * querySelector su tag/.class/[attr], addEventListener, hashchange). Serve ai
 * test di rendering, cosi' l'hardening della sicurezza puo' essere provato
 * anche sul comportamento dell'interfaccia e non solo con controlli statici.
 *
 * File solo di test: non viene caricato dal sito.
 */

class ClassList {
  constructor(el) { this.el = el; }
  get set() { return new Set((this.el.attrs.class || '').split(/\s+/).filter(Boolean)); }
  contains(c) { return this.set.has(c); }
  add(c) { const s = this.set; s.add(c); this.el.attrs.class = [...s].join(' '); }
  remove(c) { const s = this.set; s.delete(c); this.el.attrs.class = [...s].join(' '); }
  toggle(c, force) { const has = this.contains(c); const want = force === undefined ? !has : !!force; want ? this.add(c) : this.remove(c); return want; }
}

class El {
  constructor(tag) {
    this.tagName = String(tag).toLowerCase();
    this.attrs = {};
    this.children = [];
    this.parent = null;
    this._text = '';
    this.listeners = {};
    this.classList = new ClassList(this);
  }
  get textContent() {
    if (this.children.length) return this.children.map((c) => c.textContent).join('');
    return this._text;
  }
  set textContent(v) { this._text = String(v); this.children = []; }
  get innerHTML() { return this._raw || ''; }
  set innerHTML(html) {
    this._raw = String(html);
    const parsed = parseHTML(String(html), this);
    this.children = parsed;
    // <template> non ha figli diretti: il parser li mette in .content.
    if (this.tagName === 'template') {
      const frag = new El('#fragment');
      frag.children = parsed;
      parsed.forEach((n) => { n.parent = frag; });
      this.children = [];
      this.content = frag;
    }
  }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return Object.prototype.hasOwnProperty.call(this.attrs, k) ? this.attrs[k] : null; }
  removeAttribute(k) { delete this.attrs[k]; }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  dispatch(type, ev = {}) { (this.listeners[type] || []).forEach((f) => f(ev)); }
  replaceChildren(...nodes) { this.children = nodes.filter(Boolean); nodes.forEach((n) => { if (n) n.parent = this; }); }
  querySelector(sel) { return this.querySelectorAll(sel)[0] || null; }
  querySelectorAll(sel) {
    // Supporta cio' che app.js usa davvero: tag, .class, [attr], e le loro
    // combinazioni (niente discendenti, niente pseudo-classi).
    const m = /^([a-zA-Z][\w-]*)?((?:\.[\w-]+)*)(?:\[([\w-]+)\])?$/.exec(sel);
    if (!m) throw new Error('shim: selettore non supportato: ' + sel);
    const [, tag, classesPart, attr] = m;
    const classes = (classesPart.match(/\.[\w-]+/g) || []).map((c) => c.slice(1));
    const out = [];
    (function walk(n) {
      for (const c of n.children) {
        if (c.tagName === '#fragment') { walk(c); continue; }
        if (!c.tagName || c.tagName === '#text') continue;
        let ok = !tag || c.tagName === tag.toLowerCase();
        if (ok && classes.length) {
          const own = new Set(String(c.attrs.class || '').split(/\s+/).filter(Boolean));
          ok = classes.every((k) => own.has(k));
        }
        if (ok && attr && !Object.prototype.hasOwnProperty.call(c.attrs, attr)) ok = false;
        if (ok) out.push(c);
        walk(c);
      }
    })(this);
    return out;
  }
  get outerHTML() { return serialize(this); }
  get innerHTMLSerialized() { return serializeChildren(this); }
}

const VOID = new Set(['area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr']);

function parseAttrs(s) {
  const attrs = {};
  const re = /([a-zA-Z_:][-\w:.]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'>]+)))?/g;
  let m;
  while ((m = re.exec(s))) {
    attrs[m[1].toLowerCase()] = m[2] !== undefined ? m[2] : m[3] !== undefined ? m[3] : m[4] !== undefined ? m[4] : '';
  }
  return attrs;
}

function parseHTML(html, parent) {
  const out = [];
  const stack = [];
  const push = (node) => {
    if (stack.length) { node.parent = stack[stack.length - 1]; stack[stack.length - 1].children.push(node); }
    else { node.parent = parent; out.push(node); }
  };
  const re = /<!--[\s\S]*?-->|<!\w[^>]*>|<\/([a-zA-Z][\w:-]*)\s*>|<([a-zA-Z][\w:-]*)((?:"[^"]*"|'[^']*'|[^>])*?)(\/?)>|([^<]+)/g;
  let m;
  while ((m = re.exec(html))) {
    if (m[0].startsWith('<!--') || m[0].startsWith('<!')) continue;
    if (m[1]) { // chiusura
      for (let i = stack.length - 1; i >= 0; i--) {
        if (stack[i].tagName === m[1].toLowerCase()) { stack.length = i; break; }
      }
      continue;
    }
    if (m[2]) { // apertura
      const el = new El(m[2]);
      el.attrs = parseAttrs(m[3] || '');
      push(el);
      const selfClose = m[4] === '/';
      if (!selfClose && !VOID.has(el.tagName)) stack.push(el);
      continue;
    }
    if (m[5] !== undefined) { // testo
      const txt = m[5];
      if (!txt.trim()) continue;
      const node = new El('#text');
      node._text = txt;
      push(node);
    }
  }
  return out;
}

const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;' };
const ATTR_ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' };

function serialize(node) {
  if (!node.tagName || node.tagName === '#text') return node._text;
  if (node.tagName === '#fragment') return serializeChildren(node);
  let attrs = '';
  for (const [k, v] of Object.entries(node.attrs)) {
    attrs += ` ${k}="${String(v).replace(/[&<>"]/g, (c) => ATTR_ESC[c])}"`;
  }
  if (VOID.has(node.tagName)) return `<${node.tagName}${attrs}>`;
  return `<${node.tagName}${attrs}>${serializeChildren(node)}</${node.tagName}>`;
}

function serializeChildren(node) {
  return (node.children || []).map(serialize).join('');
}

/* Esegue un file di script dentro l'ambiente finto. I file UMD usano
   `globalThis` come root, quindi il globalThis reale di Node viene ombreggiato
   con lo shim: e' il dettaglio che permette a sanitize.js di attaccarsi a
   window.MedPhysSanitize come nel browser. */
function runScript(win, file) {
  const src = require('node:fs').readFileSync(file, 'utf8');
  const fn = new Function(
    'window', 'self', 'globalThis', 'document', 'location', 'localStorage', 'console',
    src + '\n//# sourceURL=' + file
  );
  fn(win, win, win, win.document, win.location, win.localStorage, win.console);
}

/* Crea un `window` finto con tutto il necessario e carica i file indicati. */
function makeWindow(files, opts = {}) {
  const store = new Map();
  const win = {
    console: { log() {}, warn() {}, error() {} },
    scrollTo() {},
    addEventListener(type, fn) { (win._ev ||= {})[type] = fn; },
    localStorage: {
      getItem: (k) => (store.has(k) ? store.get(k) : null),
      setItem: (k, v) => store.set(k, String(v)),
      removeItem: (k) => store.delete(k),
    },
  };
  win.window = win;
  win.self = win;
  win.globalThis = win;

  const app = new El('div');
  app.attrs.id = 'app';
  const docEl = new El('html');
  docEl.lang = 'en';
  win.document = {
    title: '',
    documentElement: docEl,
    getElementById: (id) => (id === 'app' ? app : null),
    createElement: (tag) => new El(tag),
    addEventListener: win.addEventListener,
  };
  win.location = { hash: opts.hash || '#/home' };

  for (const f of files) runScript(win, f);
  win.run = (f) => runScript(win, f);
  return { window: win, app, El, serialize, runScript };
}

module.exports = { makeWindow, runScript, El, serialize, parseHTML };
