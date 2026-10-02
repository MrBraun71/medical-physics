/*!
 * MedPhys — sanitizzazione centralizzata dei contenuti.
 *
 * Questo file e' l'unico punto autorizzato per trasformare dati non fidati
 * (contenuti editoriali, link, immagini, embed) in markup sicuro.
 *
 * Regole applicate:
 *  - ogni valore interpolato in HTML viene codificato (escape);
 *  - ogni URL passa da un allow-list di schemi e viene ricostruito;
 *  - il markup ricco viene ricostruito tag per tag su un allow-list,
 *    quindi un attributo pericoloso non puo' "sopravvivere" al filtraggio;
 *  - gli accessi a dizionari usano hasOwnProperty (niente prototype chain).
 *
 * Nessuna dipendenza esterna: gira identico nel browser e sotto `node --test`.
 */
(function (root, factory) {
  'use strict';
  var api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.MedPhysSanitize = api;
  }
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  // -------------------------------------------------------------------------
  // 0. Primitive
  // -------------------------------------------------------------------------

  var ESCAPE_MAP = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  };

  function toStr(value) {
    if (value === null || value === undefined) {
      return '';
    }
    return String(value);
  }

  function escapeHtml(value) {
    return toStr(value).replace(/[&<>"']/g, function (ch) {
      return ESCAPE_MAP[ch];
    });
  }

  // Gli attributi sono sempre quotati con doppi apici: stesso set di escape.
  function escapeAttr(value) {
    return escapeHtml(value);
  }

  var NAMED_ENTITIES = {
    amp: '&',
    lt: '<',
    gt: '>',
    quot: '"',
    apos: "'",
    colon: ':',
    sol: '/',
    tab: '\t',
    newline: '\n',
    lpar: '(',
    rpar: ')',
    nbsp: '\u00a0',
    ndash: '\u2013',
    mdash: '\u2014',
    hellip: '\u2026',
    lsquo: '\u2018',
    rsquo: '\u2019',
    ldquo: '\u201c',
    rdquo: '\u201d',
    bull: '\u2022',
    deg: '\u00b0',
    eacute: '\u00e9',
    egrave: '\u00e8',
    agrave: '\u00e0',
    ccedil: '\u00e7'
  };

  /* Decodifica le entita' HTML prima di validare: cosi' `javascript&colon;x`
     diventa `javascript:x` e viene rifiutato, e `&quot;` dentro un attributo
     non puo' chiudere la virgoletta. L'output viene poi ri-codificato.

     ATTENZIONE: il valore restituito e' testo NON fidato e questa funzione
     non e' idempotente (`&amp;lt;` -> `&lt;` -> `<`). Se un chiamante lo
     reinserisce in innerHTML o in un attributo deve ri-codificarlo con
     escapeHtml/escapeAttr; lo fa gia' `serializeAttribute`. */
  function decodeEntities(value) {
    return toStr(value).replace(
      /&(#[xX][0-9a-fA-F]{1,6}|#[0-9]{1,7}|[a-zA-Z][a-zA-Z0-9]{1,31});?/g,
      function (match, entity) {
        if (entity.charAt(0) === '#') {
          var isHex = entity.charAt(1) === 'x' || entity.charAt(1) === 'X';
          var code = isHex
            ? parseInt(entity.slice(2), 16)
            : parseInt(entity.slice(1), 10);
          if (!isFinite(code) || code < 0 || code > 0x10ffff) {
            return '';
          }
          try {
            return String.fromCodePoint(code);
          } catch (err) {
            return '';
          }
        }
        var decoded = NAMED_ENTITIES[entity.toLowerCase()];
        return decoded === undefined ? match : decoded;
      }
    );
  }

  // -------------------------------------------------------------------------
  // 1. Allow-list degli URL
  // -------------------------------------------------------------------------

  var LINK_SCHEMES = { 'https:': 1, 'mailto:': 1, 'tel:': 1 };
  var MEDIA_SCHEMES = { 'https:': 1 };

  // Solo l'host "no-cookie" di YouTube e' accettato come embed.
  var EMBED_RE = /^https:\/\/www\.youtube-nocookie\.com\/embed\/[A-Za-z0-9_-]{6,24}(?:\?[A-Za-z0-9=&%._~+-]*)?$/;
  var YOUTUBE_LEGACY_RE = /^https:\/\/(?:www\.)?youtube(?:-nocookie)?\.com\/embed\//i;

  /* Migra l'host di YouTube a quello "no-cookie": nessun cookie di tracking
     finche' l'utente non avvia il video. */
  function toNoCookieEmbed(url) {
    var value = toStr(url);
    return YOUTUBE_LEGACY_RE.test(value)
      ? value.replace(
        /^https:\/\/(?:www\.)?youtube\.com\/embed\//i,
        'https://www.youtube-nocookie.com/embed/'
      )
      : value;
  }

  /* Spazi e caratteri di controllo sono rifiutati: `java\tscript:` e
     ` javascript:` non devono poter superare il controllo dello schema.
     Anche il backslash e' rifiutato, perche' il browser lo risolve come `/`:
     `/\evil.tld` e `https:\evil.tld` puntano a un altro origin pur senza
     mostrare alcuno schema. */
  var CONTROL_OR_SPACE_RE = /[\u0000-\u0020\u007f]/;
  var SCHEME_RE = /^([a-zA-Z][a-zA-Z0-9+.-]*):/;

  /* Le entita' vengono decodificate prima della validazione, perche' il
     browser le decodifica quando legge l attributo: `jav&#x09;ascript:` e
     `&Tab;javascript:` devono fallire come fallirebbe `java\tscript:`.
     Il valore restituito e' quello decodificato, cosi' chi lo ri-codifica con
     escapeAttr ottiene esattamente l'URL che l'utente vede (e non un doppio
     escaping). */
  function safeUrl(url, kind) {
    var value = decodeEntities(toStr(url));
    var mode = kind || 'link';

    if (!value) {
      return null;
    }
    if (CONTROL_OR_SPACE_RE.test(value)) {
      return null;
    }
    if (value.indexOf('\\') !== -1) {
      return null;
    }
    // URL protocol-relative: nessuno schema verificabile.
    if (value.slice(0, 2) === '//') {
      return null;
    }

    var schemeMatch = SCHEME_RE.exec(value);

    if (mode === 'embed') {
      if (!schemeMatch) {
        return null;
      }
      return EMBED_RE.test(value) ? value : null;
    }

    if (schemeMatch) {
      var scheme = schemeMatch[1].toLowerCase() + ':';
      // http in chiaro non e' mai accettato: si forza https (o si perde il link).
      if (scheme === 'http:') {
        return null;
      }
      var table = mode === 'media' ? MEDIA_SCHEMES : LINK_SCHEMES;
      return table[scheme] ? value : null;
    }

    // Senza schema: ancore, percorsi assoluti o relativi (gia' sicuri).
    return value;
  }

  function isExternalUrl(url) {
    return /^https?:\/\//i.test(toStr(url));
  }

  function relAttrs(url) {
    return isExternalUrl(url) ? 'noopener noreferrer' : '';
  }

  // -------------------------------------------------------------------------
  // 2. Slug: niente prototype chain
  // -------------------------------------------------------------------------

  // Lo slug viaggia solo come fragment (#/slug) e come chiave di dizionario:
  // non viene mai usato come percorso di filesystem o come selettore CSS,
  // quindi il trattino basso e' accettato per non rompere i link pubblicati
  // (es. "pattern_recognition"). Resta escluso qualsiasi carattere di percorso.
  var SLUG_RE = /^[a-z0-9]+(?:[-_][a-z0-9]+)*$/;
  // Tetto solo anti-input patologico, non un controllo di sicurezza: lo slug
  // piu' lungo pubblicato (titolo di progetto UE) e' di 140 caratteri, quindi
  // il limite deve restare sopra quella soglia o i link gia' online si rompono.
  var SLUG_MAX_LENGTH = 200;
  // Nomi presenti su Object.prototype: hanno una forma di slug valida, quindi
  // vanno esclusi esplicitamente oltre al controllo hasOwnProperty.
  // "__proto__" non e' elencato di proposito: in un oggetto letterale non puo'
  // diventare chiave propria, e inoltre e' gia' respinto da SLUG_RE perche'
  // comincia con un trattino basso.
  var RESERVED_SLUGS = {
    constructor: 1,
    prototype: 1,
    tostring: 1,
    valueof: 1,
    hasownproperty: 1,
    isprototypeof: 1,
    propertyisenumerable: 1,
    tolocalestring: 1
  };

  function isValidSlug(slug) {
    if (typeof slug !== 'string' || !slug || slug.length > SLUG_MAX_LENGTH) {
      return false;
    }
    if (has(RESERVED_SLUGS, slug.toLowerCase())) {
      return false;
    }
    return SLUG_RE.test(slug);
  }

  function hasSlug(dictionary, key) {
    return !!dictionary
      && typeof key === 'string'
      && Object.prototype.hasOwnProperty.call(dictionary, key);
  }

  // Le tabelle di allow-list sono oggetti letterali: senza questo controllo
  // `ALLOWED_TAGS['toString']` risulterebbe truthy per laherited property e un
  // tag <toString> farebbe scartare l'intero contenuto successivo. Con has() la
  // risposta dipende solo dalle chiavi dichiarate nella tabella.
  function has(dictionary, key) {
    return !!dictionary
      && typeof key === 'string'
      && Object.prototype.hasOwnProperty.call(dictionary, key);
  }

  // -------------------------------------------------------------------------
  // 3. Sanitizzatore del markup ricco
  // -------------------------------------------------------------------------

  var ALLOWED_TAGS = {
    a: 1, abbr: 1, b: 1, blockquote: 1, br: 1, caption: 1, div: 1, em: 1,
    figcaption: 1, figure: 1, h1: 1, h2: 1, h3: 1, h4: 1, hr: 1, i: 1, iframe: 1,
    img: 1, li: 1, ol: 1, p: 1, span: 1, strong: 1, sub: 1, sup: 1, table: 1,
    tbody: 1, td: 1, tfoot: 1, th: 1, thead: 1, tr: 1, ul: 1
  };

  /* Tag il cui contenuto viene eliminato per intero: script e affini. */
  var DROP_SUBTREE_TAGS = {
    script: 1, style: 1, object: 1, applet: 1, svg: 1, math: 1, template: 1,
    noscript: 1, form: 1, frameset: 1, frame: 1, base: 1, link: 1, meta: 1,
    title: 1, head: 1, canvas: 1, audio: 1, video: 1, source: 1, track: 1
  };

  /* Tag vuoti: non hanno contenuto, quindi non si "entra" nel loro subtree. */
  var VOID_TAGS = {
    area: 1, base: 1, br: 1, col: 1, embed: 1, hr: 1, img: 1, input: 1,
    link: 1, meta: 1, param: 1, source: 1, track: 1, wbr: 1
  };

  /* Classi ammesse dal CSS per il markup ricco. */
  var ALLOWED_CLASSES = { 'video-embed': 1, 'pub-entry': 1, 'video-card': 1, 'video-desc': 1 };

  /* Attributi ammessi per tag, con il tipo di validazione da applicare. */
  var TAG_ATTRS = {
    a: { href: 'link', title: 'text', target: 'target' },
    img: { src: 'media', alt: 'text', title: 'text', loading: 'loading' },
    iframe: { src: 'embed', title: 'text', loading: 'loading' },
    td: { colspan: 'number', rowspan: 'number' },
    th: { colspan: 'number', rowspan: 'number' },
    table: { summary: 'text' },
    div: { class: 'class' },
    p: { class: 'class' },
    span: { class: 'class' },
    figure: { class: 'class' },
    figcaption: { class: 'class' },
    blockquote: { class: 'class' }
  };

  var IFRAME_SANDBOX = 'allow-scripts allow-same-origin allow-presentation allow-popups';
  var IFRAME_REFERRER_POLICY = 'strict-origin-when-cross-origin';
  var IFRAME_ALLOW = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen';

  /* Riconosce un tag finendo a '>' anche se un attributo contiene '>' quotato. */
  var TAG_RE = /^<(\/?)([a-zA-Z][a-zA-Z0-9-]*)((?:[^>"']|"[^"]*"|'[^']*')*)>/;
  var ATTR_RE = /([a-zA-Z_:][-a-zA-Z0-9_:.]*)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+)))?/g;

  function parseAttributes(raw) {
    var attrs = [];
    var rest = toStr(raw);
    var consumed = 0;
    ATTR_RE.lastIndex = 0;
    var match = ATTR_RE.exec(rest);
    while (match) {
      // Tra un attributo e l'altro puo' esserci solo spazio: altro contenuto
      // significa markup ambiguo e va respinto.
      if (rest.slice(consumed, match.index).trim() !== '') {
        return null;
      }
      var value = match[2];
      if (value === undefined) {
        value = match[3];
      }
      if (value === undefined) {
        value = match[4];
      }
      attrs.push({
        name: match[1].toLowerCase(),
        hasValue: value !== undefined,
        value: value === undefined ? '' : decodeEntities(value)
      });
      consumed = match.index + match[0].length;
      match = ATTR_RE.exec(rest);
    }
    if (rest.slice(consumed).trim() !== '') {
      return null;
    }
    return attrs;
  }

  function filterClasses(rawValue) {
    var kept = [];
    var tokens = toStr(rawValue).split(/\s+/);
    for (var i = 0; i < tokens.length; i += 1) {
      if (has(ALLOWED_CLASSES, tokens[i]) && kept.indexOf(tokens[i]) === -1) {
        kept.push(tokens[i]);
      }
    }
    return kept;
  }

  function serializeAttribute(name, value) {
    return ' ' + name + '="' + escapeAttr(value) + '"';
  }

  function sanitizeTagAttributes(tagName, attrs) {
    var allowed = TAG_ATTRS[tagName] || {};
    var href = null;
    var src = null;
    var target = null;
    var title = null;
    var summary = null;
    var loading = null;
    var numbers = {};
    var classes = [];

    for (var i = 0; i < attrs.length; i += 1) {
      var name = attrs[i].name;
      var value = attrs[i].value;
      // Difesa esplicita contro i gestori evento, anche se non sono in tabella.
      if (name.indexOf('on') === 0 || name === 'style' || name === 'srcdoc' || name === 'formaction') {
        continue;
      }
      var kind = allowed[name];
      if (!kind) {
        continue;
      }
      if (!attrs[i].hasValue) {
        continue;
      }
      if (kind === 'link' || kind === 'media' || kind === 'embed') {
        var safe = safeUrl(kind === 'embed' ? toNoCookieEmbed(value) : value, kind);
        if (!safe) {
          continue;
        }
        if (name === 'href') {
          href = safe;
        } else if (name === 'src') {
          src = safe;
        }
        continue;
      }
      if (kind === 'target') {
        if (value === '_blank' || value === '_self') {
          target = value;
        }
        continue;
      }
      if (kind === 'class') {
        classes = filterClasses(value);
        continue;
      }
      if (kind === 'number') {
        if (/^[0-9]{1,3}$/.test(value)) {
          numbers[name] = value;
        }
        continue;
      }
      if (kind === 'loading') {
        if (value === 'lazy' || value === 'eager') {
          loading = value;
        }
        continue;
      }
      if (kind === 'text') {
        if (name === 'title') {
          title = value;
        } else if (name === 'summary') {
          summary = value;
        }
      }
    }

    /* Ordine fisso: il markup emesso non dipende dall'ordine di arrivo. */
    var out = '';
    if (href) {
      out += serializeAttribute('href', href);
    }
    if (src) {
      out += serializeAttribute('src', src);
    }
    if (numbers.colspan) {
      out += serializeAttribute('colspan', numbers.colspan);
    }
    if (numbers.rowspan) {
      out += serializeAttribute('rowspan', numbers.rowspan);
    }
    if (title) {
      out += serializeAttribute('title', title);
    }
    if (summary) {
      out += serializeAttribute('summary', summary);
    }
    if (loading) {
      out += serializeAttribute('loading', loading);
    }
    if (tagName === 'iframe') {
      if (!title) {
        out += serializeAttribute('title', 'Video');
      }
      if (!loading) {
        out += serializeAttribute('loading', 'lazy');
      }
      out += serializeAttribute('sandbox', IFRAME_SANDBOX);
      out += serializeAttribute('referrerpolicy', IFRAME_REFERRER_POLICY);
      // Sempre presente: rende l'output deterministico e idempotente.
      out += serializeAttribute('allow', IFRAME_ALLOW);
    }
    if (target) {
      out += serializeAttribute('target', target);
    }
    if (relAttrs(href || '')) {
      out += serializeAttribute('rel', relAttrs(href || ''));
    }
    if (classes.length) {
      out += serializeAttribute('class', classes.join(' '));
    }

    return out;
  }

  /*
   * Ricostruisce il markup da zero: un tag ammesso riceve solo attributi
   * ammessi e validati, un tag non ammesso perde i suoi attributi (unwrap) o
   * l'intero contenuto (drop). Non viene mai ri-emesso input grezzo.
   */
  function sanitizeRichHtml(html) {
    var input = toStr(html);
    if (!input) {
      return '';
    }

    var out = '';
    var index = 0;
    var length = input.length;
    var dropTag = null;
    var dropDepth = 0;

    while (index < length) {
      var ch = input.charAt(index);

      if (ch !== '<') {
        var next = input.indexOf('<', index);
        var chunk = next === -1 ? input.slice(index) : input.slice(index, next);
        if (!dropTag) {
          out += escapeHtml(decodeEntities(chunk));
        }
        index = next === -1 ? length : next;
        continue;
      }

      // Commenti: rimossi per intero (niente payload condizionali).
      if (input.slice(index, index + 4) === '<!--') {
        var commentEnd = input.indexOf('-->', index + 4);
        index = commentEnd === -1 ? length : commentEnd + 3;
        continue;
      }

      // Doctype, processing instruction, CDATA: rimossi.
      if (input.charAt(index + 1) === '!' || input.charAt(index + 1) === '?') {
        var declEnd = input.indexOf('>', index);
        index = declEnd === -1 ? length : declEnd + 1;
        continue;
      }

      var tagMatch = TAG_RE.exec(input.slice(index));
      if (!tagMatch) {
        // '<' che non introduce un tag: viene codificato come testo.
        if (!dropTag) {
          out += '&lt;';
        }
        index += 1;
        continue;
      }

      var isClosing = tagMatch[1] === '/';
      var tagName = tagMatch[2].toLowerCase();
      index += tagMatch[0].length;

      if (dropTag) {
        if (tagName === dropTag) {
          if (isClosing) {
            dropDepth -= 1;
            if (dropDepth <= 0) {
              dropTag = null;
            }
          } else if (!VOID_TAGS[tagName] && tagMatch[3].slice(-1) !== '/') {
            dropDepth += 1;
          }
        }
        continue;
      }

      if (isClosing) {
        // Solo le chiusure di tag ammessi vengono ri-emesse.
        if (has(ALLOWED_TAGS, tagName)) {
          out += '</' + tagName + '>';
        }
        continue;
      }

      if (has(VOID_TAGS, tagName)) {
        if (has(DROP_SUBTREE_TAGS, tagName) || !has(ALLOWED_TAGS, tagName)) {
          continue;
        }
        var voidAttrs = parseAttributes(tagMatch[3]);
        if (!voidAttrs) {
          continue;
        }
        out += '<' + tagName + sanitizeTagAttributes(tagName, voidAttrs) + '>';
        continue;
      }

      if (has(DROP_SUBTREE_TAGS, tagName)) {
        dropTag = tagName;
        dropDepth = 1;
        continue;
      }

      if (!has(ALLOWED_TAGS, tagName)) {
        // Tag ignoto: si scarta il tag, si conserva il testo interno.
        continue;
      }

      var attrs = parseAttributes(tagMatch[3]);
      if (!attrs) {
        continue;
      }

      if (tagName === 'iframe') {
        var iframeSrc = null;
        for (var i = 0; i < attrs.length; i += 1) {
          if (attrs[i].name === 'src' && attrs[i].hasValue) {
            iframeSrc = attrs[i].value;
            break;
          }
        }
        if (!safeUrl(toNoCookieEmbed(iframeSrc), 'embed')) {
          // Embed non ammesso: si elimina anche il contenuto.
          dropTag = 'iframe';
          dropDepth = 1;
          continue;
        }
      }

      out += '<' + tagName + sanitizeTagAttributes(tagName, attrs) + '>';
    }

    return out;
  }

  return {
    escapeHtml: escapeHtml,
    escapeAttr: escapeAttr,
    decodeEntities: decodeEntities,
    safeUrl: safeUrl,
    isExternalUrl: isExternalUrl,
    relAttrs: relAttrs,
    isValidSlug: isValidSlug,
    hasSlug: hasSlug,
    sanitizeRichHtml: sanitizeRichHtml
  };
}));
