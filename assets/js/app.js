(function () {
  "use strict";

  /* MedPhys — rendering dell'applicazione.
   *
   * Regola di sicurezza applicata in questo file: nessun valore proveniente
   * dai dati viene mai concatenato "cosi' com'e'" nel markup.
   *   - `e()` per il testo, `a()` per gli attributi;
   *   - `media()` / `link()` validano lo schema dell'URL;
   *   - `rich()` ricostruisce il markup editoriale su allow-list;
   *   - `mount()` e' l'unico punto in cui il DOM viene scritto.
   */

  var S = window.MedPhysSanitize;
  var app = document.getElementById("app");

  /* Senza il modulo di sanificazione il sito non viene renderizzato: meglio
     una pagina vuota che una pagina potenzialmente vulnerabile. */
  if (!S) {
    if (app) app.textContent = "Errore di configurazione del sito.";
    return;
  }

  var SITE = window.MEDPHYS_SITE || {};
  var EN = window.MEDPHYS_EN || {};
  var META = window.MEDPHYS_META || {};
  var IT = window.MEDPHYS_IT || {};
  var ENX = window.MEDPHYS_EN_X || {};
  var T = { en: "Home", it: "Home" };

  var lang = "en";
  try {
    var stored = localStorage.getItem("medphys_lang");
    // Solo le due lingue previste: evita di usare localStorage come vettore.
    lang = stored === "it" ? "it" : "en";
  } catch (e) { /* modalita' privata: si resta su "en" */ }

  /* ---------------- Helper di output sicuro ---------------- */

  function e(value) { return S.escapeHtml(value); }
  function a(value) { return S.escapeAttr(value); }
  function rich(value) { return S.sanitizeRichHtml(value); }
  function media(value) { return a(S.safeUrl(value, "media") || ""); }
  function link(value) { var u = S.safeUrl(value, "link"); return u === null ? "" : a(u); }

  /* Dizionari e array: niente prototype chain, niente dati mancanti. */
  function t(o) {
    if (!o || typeof o !== "object") return "";
    if (S.hasSlug(o, lang) && typeof o[lang] === "string") return o[lang];
    if (S.hasSlug(o, "en") && typeof o.en === "string") return o.en;
    return "";
  }

  function pageOf(dict, slug) { return S.hasSlug(dict, slug) ? dict[slug] : ""; }
  function metaOf(slug) {
    var entry = S.hasSlug(META, slug) ? META[slug] : null;
    return entry && typeof entry.title === "string" ? entry.title : "";
  }
  function section(key) {
    var sections = SITE.sections && typeof SITE.sections === "object" ? SITE.sections : {};
    return S.hasSlug(sections, key) ? t(sections[key]) : "";
  }
  function listOf(name) {
    var value = SITE[name];
    return Array.isArray(value) ? value : [];
  }

  function img(src, alt, cls) {
    return "<img" + (cls ? ' class="' + a(cls) + '"' : "") +
      ' src="' + media(src) + '" alt="' + a(alt) + '">';
  }

  /* ---------------- Modello ---------------- */

  function allPeople() { return listOf("people").concat(listOf("collaborators")); }
  function allProjects() {
    var projects = SITE.projects && typeof SITE.projects === "object" ? SITE.projects : {};
    var ongoing = Array.isArray(projects.ongoing) ? projects.ongoing : [];
    var past = Array.isArray(projects.past) ? projects.past : [];
    return ongoing.concat(past);
  }
  function bySlug(list, slug) {
    for (var i = 0; i < list.length; i += 1) {
      if (list[i] && list[i].slug === slug) return list[i];
    }
    return null;
  }
  function findPerson(slug) { return bySlug(allPeople(), slug); }
  function findProject(slug) { return bySlug(allProjects(), slug); }
  function findChallenge(slug) { return bySlug(listOf("challenges"), slug); }
  function findResearch(slug) { return bySlug(listOf("research"), slug); }
  function findPublication(slug) { return bySlug(listOf("publications"), slug); }

  function basePage(slug) {
    if (lang === "it" && pageOf(IT, slug)) return pageOf(IT, slug);
    if (lang === "en" && pageOf(ENX, slug)) return pageOf(ENX, slug);
    return pageOf(EN, slug);
  }

  function external(url) {
    var safe = S.safeUrl(url, "link");
    if (!safe || !S.isExternalUrl(safe)) return e(url);
    return '<a href="' + a(safe) + '" target="_blank" rel="noopener noreferrer">' + e(safe) + "</a>";
  }

  function nameOf(slug) {
    return String(slug == null ? "" : slug).split("-").map(function (w) {
      return w.charAt(0).toUpperCase() + w.slice(1);
    }).join(" ");
  }

  /* ---------------- Header ---------------- */
  function langButtons(short) {
    return '<button data-setlang="en" class="' + (lang === "en" ? "on" : "") + '">' + short.en + "</button>" +
      '<button data-setlang="it" class="' + (lang === "it" ? "on" : "") + '">' + short.it + "</button>";
  }

  function header(route) {
    var toggle = '<button class="menu-toggle" aria-label="Menu" aria-expanded="false">☰</button>';
    var langBox = '<div class="lang" role="group" aria-label="Language">' + langButtons({ en: "EN", it: "IT" }) + "</div>";
    var items = listOf("nav").map(function (n) {
      var children = Array.isArray(n.children) ? n.children : [];
      var active = n.route === route || children.some(function (c) { return c.route === route; });
      var cls = active ? ' class="active"' : "";
      if (children.length) {
        var sub = children.map(function (c) {
          return '<a href="#/' + a(c.route) + '">' + e(t(c)) + "</a>";
        }).join("");
        return '<div class="nav-drop"><a href="#/' + a(n.route) + '"' + cls + ">" + e(t(n)) +
          '</a><div class="dropdown">' + sub + "</div></div>";
      }
      return '<a href="#/' + a(n.route) + '"' + cls + ">" + e(t(n)) + "</a>";
    }).join("");
    return '<a class="skip" href="#main">Skip to content</a>' +
      '<header class="site-header"><div class="container header-inner">' +
      '<a class="brand" href="#/home">' +
      '<span class="bt"><strong>' + e(t(SITE.short)) + "</strong><span>" + e(t(SITE.brand)) + "</span></span></a>" +
      toggle + '<nav class="main-nav" id="mainnav" aria-label="Main">' + items + langBox + "</nav>" +
      "</div></header>";
  }

  /* ---------------- Footer ---------------- */
  function footer() {
    var navLinks = listOf("nav").map(function (n) {
      return '<li><a href="#/' + a(n.route) + '">' + e(t(n)) + "</a></li>";
    }).join("");
    var mails = listOf("emails").map(function (m) {
      var mail = S.safeUrl("mailto:" + m, "link");
      if (!mail) return "";
      return '<div>✉ <a href="' + a(mail) + '">' + e(m) + "</a></div>";
    }).join("");
    var resources = [
      ["#/join-us", { en: "Master theses", it: "Tesi di laurea" }],
      ["#/multimedia", { en: "Multimedia", it: "Multimedia" }],
      ["#/privary-cookie-policy", { en: "Cookie policy", it: "Cookie policy" }]
    ].map(function (item) {
      return '<li><a href="' + a(item[0]) + '">' + e(t(item[1])) + "</a></li>";
    }).join("") +
      '<li><a href="https://www.uniba.it" target="_blank" rel="noopener noreferrer">University of Bari</a></li>' +
      '<li><a href="https://www.ba.infn.it" target="_blank" rel="noopener noreferrer">INFN Bari</a></li>';

    return '<footer class="site-footer"><div class="container">' +
      '<div class="footer-grid">' +
      '<div class="footer-brand">' + img(SITE.logo, "Medical Physics") +
      "<p>" + e(t(SITE.brand)) + "<br>" + e(t(SITE.org)) + "</p>" +
      '<div class="footer-contact"><div>⌂ <span>' + e(SITE.address) + "</span></div>" + mails + "</div></div>" +
      '<div><h3>' + e(t({ en: "Navigate", it: "Naviga" })) + "</h3><ul>" + navLinks + "</ul></div>" +
      '<div><h3>' + e(t({ en: "Resources", it: "Risorse" })) + "</h3><ul>" + resources + "</ul></div>" +
      "</div>" +
      '<div class="copyright"><span>© ' + new Date().getFullYear() + " " + e(t(SITE.brand)) +
      " • " + e(t({ en: "Realized by Lorenzo de Trizio", it: "Realizzato da Lorenzo de Trizio" })) +
      " • " + e(t({ en: "University of Bari Aldo Moro", it: "Università degli Studi di Bari Aldo Moro" })) +
      '</span><span class="footer-lang">' + langButtons({ en: "English", it: "Italiano" }) +
      "</span></div></div></footer>";
  }

  /* ---------------- Home ---------------- */
  function sectionWrap(id, title, inner, cls) {
    return '<section class="section ' + a(cls || "") + '" id="' + a(id) + '"><div class="container">' +
      '<div class="section-head"><div class="eyebrow">' + e(t(SITE.short)) + "</div><h2>" + e(title) + "</h2></div>" +
      inner + "</div></section>";
  }

  function renderHome() {
    var h = SITE.home && typeof SITE.home === "object" ? SITE.home : {};
    var hero = '<section class="hero">' + img(h.hero_img, "", "hero-bg") +
      '<div class="container hero-inner">' +
      '<span class="kicker">' + e(t(h.kicker)) + "</span>" +
      "<h1>" + e(t(h.title)) + "</h1>" +
      "<p>" + e(t(h.lead)) + "</p><p>" + e(t(h.para2)) + "</p>" +
      '<div class="cta"><a class="btn btn-primary" href="#/research">' +
      e(t({ en: "Explore research", it: "Esplora la ricerca" })) + "</a>" +
      '<a class="btn btn-ghost" href="#/people">' + e(t({ en: "Meet the people", it: "Conosci il gruppo" })) +
      "</a></div></div></section>";

    var research = sectionWrap("research", section("research"), listOf("research").map(function (r) {
      return '<a class="card" href="#/' + a(r.slug) + '"><div class="thumb">' + img(r.img, "") + "</div>" +
        '<div class="body"><h3>' + e(t(r.title)) + "</h3><p>" + e(t(r.summary)) + "</p>" +
        '<span class="more">' + e(t({ en: "Read more →", it: "Leggi di più →" })) + "</span></div></a>";
    }).join(""), "");

    var people = sectionWrap("people", section("people"), staffGrid(listOf("people")), "alt");

    var pubs = sectionWrap("publications-preview", section("publications"),
      '<p class="notice">' + e(t(SITE.pub_notice)) + "</p>" +
      '<div class="grid cols-3">' + listOf("publications").map(function (p) {
        return '<a class="card" href="#/' + a(p.slug) + '"><div class="body"><h3>' + e(t(p)) + "</h3><p>" + e(t(p.desc)) + "</p>" +
          '<span class="more">' + e(t({ en: "Browse →", it: "Sfoglia →" })) + "</span></div></a>";
      }).join("") + "</div>", "");

    var challenges = sectionWrap("challenges-preview", section("challenges"),
      '<div class="grid cols-3">' + listOf("challenges").map(function (c) {
        return '<a class="card" href="#/' + a(c.slug) + '"><div class="thumb contain">' + img(c.img, "") + "</div>" +
          '<div class="body"><h3>' + e(t(c.title)) + "</h3><p>" + e(t(c.desc)) + "</p></div></a>";
      }).join("") + "</div>", "alt");

    var newsroom = sectionWrap("newsroom", section("newsroom"),
      '<div class="news-grid">' + listOf("newsroom").map(function (n) {
        var url = S.safeUrl(n.url, "link");
        var attrs = url
          ? ' href="' + a(url) + '" target="_blank" rel="noopener noreferrer"'
          : "";
        return '<a class="news-item"' + attrs + ' title="' + a(n.name) + '">' + img(n.img, n.name) + "</a>";
      }).join("") + "</div>", "dark");

    var projects = sectionWrap("projects-preview", section("projects"),
      '<p class="projects-lead">' +
      e(t({ en: "Our group takes part in national and European research projects, from medical imaging and AI to remote sensing and industry.",
        it: "Il nostro gruppo partecipa a progetti di ricerca nazionali ed europei, dall\u2019imaging medico e dall\u2019IA al telerilevamento e all\u2019industria." })) +
      '</p><a class="btn btn-primary" href="#/projects">' +
      e(t({ en: "See all our projects", it: "Vedi tutti i progetti" })) + "</a>", "");

    return hero + research + people + pubs + challenges + projects + newsroom;
  }

  function staffGrid(list) {
    return '<div class="grid cols-4">' + list.map(function (p) {
      return '<a class="person" href="#/' + a(p.slug) + '"><div class="ph">' + img(p.img, p.slug) + "</div>" +
        '<div class="pb"><h3>' + e(nameOf(p.slug)) + "</h3><span>" + e(t(p.keywords)) + "</span></div></a>";
    }).join("") + "</div>";
  }

  /* ---------------- Pagine di indice e dettaglio ---------------- */
  function pageHero(title, sub, crumb) {
    return '<section class="page-hero"><div class="container">' +
      (crumb ? '<div class="crumbs"><a href="#/home">' + e(t(T)) + "</a> / " + crumb + "</div>" : "") +
      "<h1>" + e(title) + "</h1>" + (sub ? '<p class="sub">' + e(sub) + "</p>" : "") + "</div></section>";
  }

  function crumbFor(route, label) {
    return '<a href="#/' + a(route) + '">' + e(label) + "</a>";
  }

  function renderResearchIndex() {
    return pageHero(section("research"),
      t({ en: "Four research lines at the intersection of physics, engineering and medicine.",
        it: "Quattro linee di ricerca all\u2019intersezione tra fisica, ingegneria e medicina." })) +
      '<section class="section"><div class="container"><div class="grid cols-2">' +
      listOf("research").map(function (r) {
        return '<a class="card" href="#/' + a(r.slug) + '"><div class="thumb">' + img(r.img, "") + "</div>" +
          '<div class="body"><h3>' + e(t(r.title)) + "</h3><p>" + e(t(r.summary)) + "</p></div></a>";
      }).join("") + "</div></div></section>";
  }

  function renderResearch(slug) {
    var r = findResearch(slug);
    var body = rich(t(r.body) || basePage(slug));
    var siblings = listOf("research").map(function (x) {
      return '<p class="aside-link"><a href="#/' + a(x.slug) + '">' + e(t(x.title)) + "</a></p>";
    }).join("");
    return pageHero(t(r.title), t(r.summary), crumbFor("research", section("research"))) +
      '<section class="section"><div class="container"><div class="detail-layout"><div class="prose">' + body + "</div>" +
      '<aside class="aside-card"><h3>' + e(t({ en: "Research lines", it: "Linee di ricerca" })) + "</h3>" +
      siblings + "</aside></div></div></section>";
  }

  function renderPeople() {
    return pageHero(section("people"),
      t({ en: "Researchers and technologists of the Medical Physics group.",
        it: "Ricercatori e tecnologi del gruppo di Fisica Medica." })) +
      '<section class="section"><div class="container"><div class="section-head"><h2>' +
      e(section("people")) + "</h2></div>" + staffGrid(listOf("people")) + "</div></section>";
  }

  function renderPerson(slug) {
    var p = findPerson(slug);
    var tags = t(p.keywords).split(",").map(function (k) {
      return '<span class="tag">' + e(k.trim()) + "</span>";
    }).join("");
    var mail = "";
    if (p.email) {
      var mailto = S.safeUrl("mailto:" + p.email, "link");
      if (mailto) mail = '<p class="contact-mail">✉ <a href="' + a(mailto) + '">' + e(p.email) + "</a></p>";
    }
    return pageHero(nameOf(slug), "", crumbFor("people", section("people"))) +
      '<section class="section"><div class="container">' +
      '<div class="person-hero">' + img(p.img, slug) +
      '<div class="ph-txt"><h2 class="person-name">' + e(nameOf(slug)) + "</h2>" +
      '<p class="person-keywords">' + e(t(p.keywords)) + "</p>" +
      '<div class="tags">' + tags + "</div></div></div>" +
      '<div class="prose person-bio"><p>' + e(t(p.bio)) + "</p>" + mail + "</div></div></section>";
  }

  function projectCard(p) {
    var summary = t(p.abstract).slice(0, 150);
    return '<a class="card" href="#/' + a(p.slug) + '"><div class="thumb contain">' + img(p.img, "") + "</div>" +
      '<div class="body"><h3>' + e(t(p.title)) + "</h3><p>" + e(summary) + "…</p>" +
      '<span class="more">' + e(p.duration) + "</span></div></a>";
  }

  function renderProjects() {
    var projects = SITE.projects && typeof SITE.projects === "object" ? SITE.projects : {};
    var ongoing = Array.isArray(projects.ongoing) ? projects.ongoing : [];
    var past = Array.isArray(projects.past) ? projects.past : [];
    return pageHero(section("projects")) +
      '<section class="section"><div class="container"><div class="section-head"><h2>' +
      e(t({ en: "Ongoing projects", it: "Progetti in corso" })) + "</h2></div>" +
      '<div class="grid cols-3">' + ongoing.map(projectCard).join("") + "</div></div></section>" +
      '<section class="section alt"><div class="container"><div class="section-head"><h2>' +
      e(t({ en: "Past projects", it: "Progetti conclusi" })) + "</h2></div>" +
      '<div class="grid cols-3">' + past.map(projectCard).join("") + "</div></div></section>";
  }

  function renderProject(slug) {
    var p = findProject(slug);
    var projects = SITE.projects && typeof SITE.projects === "object" ? SITE.projects : {};
    var past = Array.isArray(projects.past) ? projects.past : [];
    return pageHero(t(p.title), "", crumbFor("projects", section("projects"))) +
      '<section class="section"><div class="container"><div class="detail-layout"><div>' +
      '<div class="figure-inline">' + img(p.img, "", "figure-inline-media") + "</div>" +
      '<div class="prose"><p>' + e(t(p.abstract)) + "</p></div></div>" +
      '<aside class="aside-card"><h3>' + e(t({ en: "Project details", it: "Dettagli del progetto" })) + "</h3><dl>" +
      "<dt>" + e(t({ en: "Duration", it: "Durata" })) + "</dt><dd>" + e(p.duration) + "</dd>" +
      "<dt>" + e(t({ en: "Status", it: "Stato" })) + "</dt><dd>" +
      e(past.indexOf(p) >= 0 ? t({ en: "Completed", it: "Concluso" }) : t({ en: "Ongoing", it: "In corso" })) +
      "</dd></dl></aside></div></div></section>";
  }

  function renderChallenges() {
    return pageHero(section("challenges"),
      t({ en: "International machine learning and image analysis challenges our group took part in.",
        it: "Sfide internazionali di machine learning e analisi di immagini a cui il nostro gruppo ha partecipato." })) +
      '<section class="section"><div class="container"><div class="grid cols-3">' +
      listOf("challenges").map(function (c) {
        return '<a class="card" href="#/' + a(c.slug) + '"><div class="thumb contain">' + img(c.img, "") + "</div>" +
          '<div class="body"><h3>' + e(t(c.title)) + "</h3><p>" + e(t(c.desc)) + "</p>" +
          '<span class="more">' + e(t({ en: "Details →", it: "Dettagli →" })) + "</span></div></a>";
      }).join("") + "</div></div></section>";
  }

  function renderChallenge(slug) {
    var c = findChallenge(slug);
    var url = S.safeUrl(c.url, "link");
    var button = url
      ? '<p><a class="btn btn-primary" href="' + a(url) + '" target="_blank" rel="noopener noreferrer">' +
        e(t({ en: "Open challenge →", it: "Apri la sfida →" })) + "</a></p>"
      : "";
    return pageHero(t(c.title), "", crumbFor("challenges", section("challenges"))) +
      '<section class="section"><div class="container"><div class="detail-layout"><div>' +
      '<div class="figure-inline">' + img(c.img, "", "figure-inline-media is-compact") + "</div>" +
      '<div class="prose"><p>' + e(t(c.desc)) + "</p></div></div>" +
      '<aside class="aside-card"><h3>' + e(t({ en: "External link", it: "Link esterno" })) + "</h3>" +
      button + "</aside></div></div></section>";
  }

  function renderPublications() {
    return pageHero(section("publications"),
      t({ en: "Scientific production of the Medical Physics group.",
        it: "Produzione scientifica del gruppo di Fisica Medica." })) +
      '<section class="section"><div class="container"><div class="grid cols-3">' +
      listOf("publications").map(function (p) {
        return '<a class="card" href="#/' + a(p.slug) + '"><div class="body"><h3>' + e(t(p)) + "</h3><p>" + e(t(p.desc)) + "</p>" +
          '<span class="more">' + e(t({ en: "Browse →", it: "Sfoglia →" })) + "</span></div></a>";
      }).join("") + "</div></div></section>";
  }

  function renderPublication(slug) {
    var p = findPublication(slug);
    return pageHero(t(p), t(p.desc), crumbFor("publications", section("publications"))) +
      '<section class="section"><div class="container"><p class="notice">' + e(t(SITE.pub_notice)) + "</p>" +
      '<div class="prose pub-list">' + rich(basePage(slug)) + "</div></div></section>";
  }

  function renderJoin() {
    var j = SITE.join_us && typeof SITE.join_us === "object" ? SITE.join_us : {};
    var theses = Array.isArray(j.theses) ? j.theses : [];
    var rows = theses.map(function (x) {
      return "<tr><td>" + e(t(x.t)) + "</td><td>" + e(x.s) + "</td></tr>";
    }).join("");
    return pageHero(t({ en: "Join Us", it: "Unisciti a noi" }), t(j.intro)) +
      '<section class="section"><div class="container prose"><table><thead><tr><th>' + e(t(j.col_title)) +
      "</th><th>" + e(t(j.col_sup)) + "</th></tr></thead><tbody>" + rows + "</tbody></table></div></section>";
  }

  function renderCourses() {
    var courses = SITE.courses && typeof SITE.courses === "object" ? SITE.courses : {};
    var items = (Array.isArray(courses.items) ? courses.items : []).map(function (c) {
      return "<li>" + e(t(c)) + "</li>";
    }).join("");
    return pageHero(t({ en: "Courses", it: "Corsi" })) +
      '<section class="section"><div class="container prose"><ul>' + items + "</ul></div></section>";
  }

  function renderProtected(slug) {
    var protectedPages = SITE.protected && typeof SITE.protected === "object" ? SITE.protected : {};
    var entry = S.hasSlug(protectedPages, slug) ? protectedPages[slug] : null;
    var title = t(entry && entry.title);
    /* Nota di sicurezza: questa schermata e' solo informativa. La protezione
       reale dei contenuti deve vivere lato server (HTTP Basic Auth o simili):
       nessuna password inserita qui puo' custodire un segreto nel browser. */
    return pageHero(title) +
      '<section class="section"><div class="container"><div class="lock"><h3>' + e(title) + "</h3>" +
      "<p>" + e(t(SITE.protected_msg)) + "</p>" +
      '<form data-lock><label>' + e(t({ en: "Password", it: "Password" })) + '</label>' +
      '<input type="password" autocomplete="off" aria-label="' + e(t({ en: "Password", it: "Password" })) + '">' +
      '<button class="btn btn-primary" type="submit">' + e(t({ en: "Enter", it: "Accedi" })) + "</button>" +
      "</form></div></div></section>";
  }

  function renderBase(slug) {
    var title = metaOf(slug) || nameOf(slug);
    var body = rich(basePage(slug));
    if (!body) body = "<p>" + e(t({ en: "Content not available.", it: "Contenuto non disponibile." })) + "</p>";
    var extra = "";
    if (lang === "en" && (slug === "privary-cookie-policy" || slug === "disattivazione-dei-cookies-sui-browser")) {
      extra = '<div class="notice">' + e(t({ en: "Official notice provided in Italian.", it: "" })) + "</div>";
    }
    return pageHero(title) +
      '<section class="section"><div class="container"><div class="prose">' + extra + body + "</div></div></section>";
  }

  function notFound() {
    return pageHero("404") + '<section class="section"><div class="container"><p>' +
      e(t({ en: "Page not found.", it: "Pagina non trovata." })) +
      ' <a href="#/home">' + e(t({ en: "Back home", it: "Torna alla home" })) + "</a></p></div></section>";
  }

  function renderError() {
    return pageHero("500") + '<section class="section"><div class="container"><p>' +
      e(t({ en: "This page could not be rendered.", it: "Questa pagina non e' stato possibile renderizzarla." })) +
      ' <a href="#/home">' + e(t({ en: "Back home", it: "Torna alla home" })) + "</a></p></div></section>";
  }

  /* ---------------- Router ---------------- */
  function routeSlug() {
    var raw = location.hash.replace(/^#\/?/, "").split("?")[0].toLowerCase();
    if (!raw) return "home";
    return S.isValidSlug(raw) ? raw : "";
  }

  /* Unico punto in cui il DOM viene scritto: il markup arriva qui gia'
     ricostruito dal sanitizer o composto da valori codificati. */
  function mount(html) {
    var template = document.createElement("template");
    template.innerHTML = html;
    app.replaceChildren(template.content);
  }

  function render() {
    if (!app) return;
    var slug = routeSlug();
    var body = "";
    var title = t(SITE.short) || "MedPhys";

    try {
      if (slug === "home") body = renderHome();
      else if (slug === "research") body = renderResearchIndex();
      else if (findResearch(slug)) {
        body = renderResearch(slug);
        title = t(findResearch(slug).title);
      } else if (slug === "people") body = renderPeople();
      else if (findPerson(slug)) {
        body = renderPerson(slug);
        title = nameOf(slug);
      } else if (slug === "projects" || slug === "ongoing-projects" || slug === "past-projects") body = renderProjects();
      else if (findProject(slug)) {
        body = renderProject(slug);
        title = t(findProject(slug).title);
      } else if (slug === "challenges") body = renderChallenges();
      else if (findChallenge(slug)) {
        body = renderChallenge(slug);
        title = t(findChallenge(slug).title);
      } else if (slug === "publications" || slug === "pubblication") body = renderPublications();
      else if (findPublication(slug)) {
        body = renderPublication(slug);
        title = t(findPublication(slug));
      } else if (slug === "join-us") body = renderJoin();
      else if (slug === "courses") body = renderCourses();
      else if (isProtected(slug)) {
        body = renderProtected(slug);
        title = t(pageOf(SITE.protected, slug).title);
      } else if (slug && (pageOf(EN, slug) || pageOf(IT, slug) || pageOf(ENX, slug))) {
        body = renderBase(slug);
        title = metaOf(slug) || title;
      } else body = notFound();
    } catch (error) {
      // Un dato malformato non deve lasciare la pagina a meta' o spezzata.
      body = renderError();
      if (window.console && console.error) console.error("[medphys] render fallito", error);
    }

    try {
      mount(header(slug) + '<main id="main">' + body + "</main>" + footer());
      document.title = title + " — " + t(SITE.brand);
      bindShell();
      if (window.scrollTo) window.scrollTo(0, 0);
    } catch (error) {
      if (window.console && console.error) console.error("[medphys] mount fallito", error);
      app.textContent = t({ en: "This page could not be rendered.", it: "Questa pagina non e' stato possibile renderizzarla." });
    }
  }

  function isProtected(slug) {
    var protectedPages = SITE.protected && typeof SITE.protected === "object" ? SITE.protected : {};
    return !!slug && S.hasSlug(protectedPages, slug);
  }

  function bindShell() {
    var btn = app.querySelector(".menu-toggle");
    var nav = app.querySelector(".main-nav");
    if (btn && nav) btn.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", open ? "true" : "false");
    });
    Array.prototype.forEach.call(app.querySelectorAll("[data-setlang]"), function (b) {
      b.addEventListener("click", function () { setLang(b.getAttribute("data-setlang")); });
    });
    if (nav) Array.prototype.forEach.call(nav.querySelectorAll("a"), function (link) {
      link.addEventListener("click", function () { nav.classList.remove("open"); });
    });
    // La schermata protetta non autentica: si evita solo l'invio del form.
    var lockForm = app.querySelector("form[data-lock]");
    if (lockForm) lockForm.addEventListener("submit", function (event) { event.preventDefault(); });
  }

  function setLang(next) {
    lang = next === "it" ? "it" : "en";
    try { localStorage.setItem("medphys_lang", lang); } catch (e) { /* modalita' privata */ }
    document.documentElement.lang = lang;
    render();
  }

  window.addEventListener("hashchange", render);
  if (!location.hash) location.hash = "#/home";
  render();
})();
