(function () {
  "use strict";
  var SITE = window.MEDPHYS_SITE || {};
  var EN = window.MEDPHYS_EN || {};
  var META = window.MEDPHYS_META || {};
  var IT = window.MEDPHYS_IT || {};
  var ENX = window.MEDPHYS_EN_X || {};
  var app = document.getElementById("app");
  var lang = "en";
  try { lang = localStorage.getItem("medphys_lang") || "en"; } catch (e) {}

  function t(o) { return o ? (o[lang] || o.en || "") : ""; }
  function esc(s) { return String(s == null ? "" : s); }
  function allPeople() { return (SITE.people || []).concat(SITE.collaborators || []); }
  function allProjects() {
    var p = SITE.projects || {};
    return (p.ongoing || []).concat(p.past || []);
  }
  function findPerson(s) { return allPeople().filter(function (x) { return x.slug === s; })[0]; }
  function findProject(s) { return allProjects().filter(function (x) { return x.slug === s; })[0]; }
  function findChallenge(s) { return (SITE.challenges || []).filter(function (x) { return x.slug === s; })[0]; }
  function findResearch(s) { return (SITE.research || []).filter(function (x) { return x.slug === s; })[0]; }
  function findPublication(s) { return (SITE.publications || []).filter(function (x) { return x.slug === s; })[0]; }

  function basePage(slug) {
    if (lang === "it" && IT[slug]) return IT[slug];
    if (lang === "en" && ENX[slug]) return ENX[slug];
    return EN[slug] || "";
  }

  function external(url) {
    return '<a href="' + url + '" target="_blank" rel="noopener">' + url + "</a>";
  }

  /* ---------------- Header ---------------- */
  function header(route) {
    var toggle = '<button class="menu-toggle" aria-label="Menu" aria-expanded="false">\u2630</button>';
    var langBox = '<div class="lang" role="group" aria-label="Language">' +
      '<button data-setlang="en" class="' + (lang === "en" ? "on" : "") + '">EN</button>' +
      '<button data-setlang="it" class="' + (lang === "it" ? "on" : "") + '">IT</button></div>';
    var items = (SITE.nav || []).map(function (n) {
      var active = n.route === route || (n.children || []).some(function (c) { return c.route === route; });
      var cls = active ? ' class="active"' : "";
      if (n.children && n.children.length) {
        var sub = n.children.map(function (c) {
          return '<a href="#/' + c.route + '">' + esc(t(c)) + "</a>";
        }).join("");
        return '<div class="nav-drop"><a href="#/' + n.route + '"' + cls + ">" + esc(t(n)) + '</a><div class="dropdown">' + sub + "</div></div>";
      }
      return '<a href="#/' + n.route + '"' + cls + ">" + esc(t(n)) + "</a>";
    }).join("");
    return '<a class="skip" href="#main">Skip to content</a>' +
      '<header class="site-header"><div class="container header-inner">' +
      '<a class="brand" href="#/home">' +
      '<span class="bt"><strong>' + t(SITE.short) + "</strong><span>" + t(SITE.brand) + "</span></span></a>" +
      toggle + '<nav class="main-nav" id="mainnav" aria-label="Main">' + items + langBox + "</nav>" +
      "</div></header>";
  }

  /* ---------------- Footer ---------------- */
  function footer() {
    var navLinks = (SITE.nav || []).map(function (n) {
      return '<li><a href="#/' + n.route + '">' + esc(t(n)) + "</a></li>";
    }).join("");
    var mails = (SITE.emails || []).map(function (m) {
      return '<div>\u2709 <a href="mailto:' + m + '">' + m + "</a></div>";
    }).join("");
    return '<footer class="site-footer"><div class="container">' +
      '<div class="footer-grid">' +
      '<div class="footer-brand"><img src="' + SITE.logo + '" alt="Medical Physics">' +
      "<p>" + t(SITE.brand) + "<br>" + t(SITE.org) + "</p>" +
      '<div class="footer-contact"><div>\u2302 <span>' + SITE.address + "</span></div>" + mails + "</div></div>" +
      '<div><h3>' + t({ en: "Navigate", it: "Naviga" }) + "</h3><ul>" + navLinks + "</ul></div>" +
      '<div><h3>' + t({ en: "Resources", it: "Risorse" }) + "</h3><ul>" +
      '<li><a href="#/join-us">' + t({ en: "Master theses", it: "Tesi di laurea" }) + "</a></li>" +
      '<li><a href="#/multimedia">' + t({ en: "Multimedia", it: "Multimedia" }) + "</a></li>" +
      '<li><a href="#/privary-cookie-policy">' + t({ en: "Cookie policy", it: "Cookie policy" }) + "</a></li>" +
      '<li><a href="https://www.uniba.it" target="_blank" rel="noopener">University of Bari</a></li>' +
      '<li><a href="https://www.ba.infn.it" target="_blank" rel="noopener">INFN Bari</a></li>' +
      "</ul></div></div>" +
      '<div class="copyright"><span>\u00a9 ' + new Date().getFullYear() + " " + t(SITE.brand) +
      " \u2022 " + t({ en: "Realized by Lorenzo de Trizio", it: "Realizzato da Lorenzo de Trizio" }) +
      " \u2022 " + t({ en: "University of Bari Aldo Moro", it: "Universit\u00e0 degli Studi di Bari Aldo Moro" }) +
      '</span><span class="footer-lang">' +
      '<button data-setlang="en" class="' + (lang === "en" ? "on" : "") + '">English</button>' +
      '<button data-setlang="it" class="' + (lang === "it" ? "on" : "") + '">Italiano</button>' +
      "</span></div></div></footer>";
  }

  /* ---------------- Home ---------------- */
  function renderHome() {
    var h = SITE.home;
    var hero = '<section class="hero"><img class="hero-bg" src="' + h.hero_img + '" alt="">' +
      '<div class="container hero-inner">' +
      '<span class="kicker">' + t(h.kicker) + "</span>" +
      "<h1>" + t(h.title) + "</h1>" +
      "<p>" + t(h.lead) + "</p><p>" + t(h.para2) + "</p>" +
      '<div class="cta"><a class="btn btn-primary" href="#/research">' +
      t({ en: "Explore research", it: "Esplora la ricerca" }) + "</a>" +
      '<a class="btn btn-ghost" href="#/people">' + t({ en: "Meet the people", it: "Conosci il gruppo" }) + "</a></div>" +
      "</div></section>";

    var research = sectionWrap("research", "research", (SITE.research || []).map(function (r) {
      return '<a class="card" href="#/' + r.slug + '"><div class="thumb"><img src="' + r.img + '" alt=""></div>' +
        '<div class="body"><h3>' + t(r.title) + "</h3><p>" + t(r.summary) + "</p>" +
        '<span class="more">' + t({ en: "Read more \u2192", it: "Leggi di pi\u00f9 \u2192" }) + "</span></div></a>";
    }).join(""), "");

    var people = sectionWrap("people", "people", staffGrid(SITE.people || []), "alt");

    var pubs = sectionWrap("publications-preview", "publications",
      '<p class="notice">' + t(SITE.pub_notice) + "</p>" +
      '<div class="grid cols-3">' + (SITE.publications || []).map(function (p) {
        return '<a class="card" href="#/' + p.slug + '"><div class="body"><h3>' + t(p) + "</h3><p>" + t(p.desc) + "</p>" +
          '<span class="more">' + t({ en: "Browse \u2192", it: "Sfoglia \u2192" }) + "</span></div></a>";
      }).join("") + "</div>", "");

    var challenges = sectionWrap("challenges-preview", "challenges",
      '<div class="grid cols-3">' + (SITE.challenges || []).map(function (c) {
        return '<a class="card" href="#/' + c.slug + '"><div class="thumb contain"><img src="' + c.img + '" alt=""></div>' +
          '<div class="body"><h3>' + t(c.title) + "</h3><p>" + t(c.desc) + "</p></div></a>";
      }).join("") + "</div>", "alt");

    var news = sectionWrap("newsroom", "newsroom",
      '<div class="news-grid">' + (SITE.newsroom || []).map(function (n) {
        return '<a class="news-item" href="' + n.url + '" target="_blank" rel="noopener" title="' + n.name + '"><img src="' + n.img + '" alt="' + n.name + '"></a>';
      }).join("") + "</div>", "dark");

    var projects = sectionWrap("projects-preview", "projects",
      '<p style="max-width:70ch;color:var(--ink-soft)">' +
      t({ en: "Our group takes part in national and European research projects, from medical imaging and AI to remote sensing and industry.", it: "Il nostro gruppo partecipa a progetti di ricerca nazionali ed europei, dall\u2019imaging medico e dall\u2019IA al telerilevamento e all\u2019industria." }) +
      '</p><a class="btn btn-primary" href="#/projects">' + t({ en: "See all our projects", it: "Vedi tutti i progetti" }) + "</a>", "");

    return hero + research + people + pubs + challenges + projects + news;
  }

  function sectionWrap(id, titleKey, inner, cls) {
    var title = t((SITE.sections || {})[titleKey] || { en: titleKey, it: titleKey });
    return '<section class="section ' + (cls || "") + '" id="' + id + '"><div class="container">' +
      '<div class="section-head"><div class="eyebrow">' + t(SITE.short) + "</div><h2>" + title + "</h2></div>" +
      inner + "</div></section>";
  }

  function staffGrid(list) {
    return '<div class="grid cols-4">' + list.map(function (p) {
      return '<a class="person" href="#/' + p.slug + '"><div class="ph"><img src="' + p.img + '" alt="' + p.slug + '"></div>' +
        '<div class="pb"><h3>' + nameOf(p.slug) + "</h3><span>" + t(p.keywords) + "</span></div></a>";
    }).join("") + "</div>";
  }
  function nameOf(slug) {
    return slug.split("-").map(function (w) { return w.charAt(0).toUpperCase() + w.slice(1); }).join(" ");
  }

  /* ---------------- Index pages ---------------- */
  function pageHero(title, sub, crumb) {
    return '<section class="page-hero"><div class="container">' +
      (crumb ? '<div class="crumbs"><a href="#/home">' + t({ en: "Home", it: "Home" }) + "</a> / " + crumb + "</div>" : "") +
      "<h1>" + title + "</h1>" + (sub ? '<p class="sub">' + sub + "</p>" : "") + "</div></section>";
  }

  function renderResearchIndex() {
    return pageHero(t(SITE.sections.research), t({ en: "Four research lines at the intersection of physics, engineering and medicine.", it: "Quattro linee di ricerca all\u2019intersezione tra fisica, ingegneria e medicina." })) +
      '<section class="section"><div class="container"><div class="grid cols-2">' +
      (SITE.research || []).map(function (r) {
        return '<a class="card" href="#/' + r.slug + '"><div class="thumb"><img src="' + r.img + '" alt=""></div>' +
          '<div class="body"><h3>' + t(r.title) + "</h3><p>" + t(r.summary) + "</p></div></a>";
      }).join("") + "</div></div></section>";
  }

  function renderResearch(slug) {
    var r = findResearch(slug);
    var body = r.body ? t(r.body) : basePage(slug);
    return pageHero(t(r.title), t(r.summary), '<a href="#/research">' + t(SITE.sections.research) + "</a>") +
      '<section class="section"><div class="container"><div class="detail-layout"><div class="prose">' + body + "</div>" +
      '<aside class="aside-card"><h3>' + t({ en: "Research lines", it: "Linee di ricerca" }) + "</h3>" +
      (SITE.research || []).map(function (x) {
        return '<p style="margin:.3rem 0"><a href="#/' + x.slug + '">' + t(x.title) + "</a></p>";
      }).join("") + "</aside></div></div></section>";
  }

  function renderPeople() {
    var html = pageHero(t(SITE.sections.people), t({ en: "Researchers and technologists of the Medical Physics group.", it: "Ricercatori e tecnologi del gruppo di Fisica Medica." }));
    html += '<section class="section"><div class="container"><div class="section-head"><h2>' + t(SITE.sections.people) + "</h2></div>" + staffGrid(SITE.people || []) + "</div></section>";
    return html;
  }

  function renderPerson(slug) {
    var p = findPerson(slug);
    var tags = t(p.keywords).split(",").map(function (k) { return '<span class="tag">' + k.trim() + "</span>"; }).join("");
    var mail = p.email ? '<p style="margin-top:1rem">\u2709 <a href="mailto:' + p.email + '">' + p.email + "</a></p>" : "";
    return pageHero(nameOf(slug), "", '<a href="#/people">' + t(SITE.sections.people) + "</a>") +
      '<section class="section"><div class="container">' +
      '<div class="person-hero"><img src="' + p.img + '" alt="' + slug + '">' +
      '<div class="ph-txt"><h2 style="margin-bottom:.4rem">' + nameOf(slug) + "</h2>" +
      '<p style="font-weight:600;color:var(--brand-2)">' + t(p.keywords) + "</p>" +
      '<div class="tags">' + tags + "</div></div></div>" +
      '<div class="prose" style="margin-top:2rem"><p>' + t(p.bio) + "</p>" + mail + "</div></div></section>";
  }

  function projectCard(p) {
    return '<a class="card" href="#/' + p.slug + '"><div class="thumb contain"><img src="' + p.img + '" alt=""></div>' +
      '<div class="body"><h3>' + t(p.title) + "</h3><p>" + t(p.abstract).slice(0, 150) + "\u2026</p>" +
      '<span class="more">' + p.duration + "</span></div></a>";
  }

  function renderProjects() {
    var pr = SITE.projects || { ongoing: [], past: [] };
    return pageHero(t(SITE.sections.projects)) +
      '<section class="section"><div class="container"><div class="section-head"><h2>' + t({ en: "Ongoing projects", it: "Progetti in corso" }) + "</h2></div>" +
      '<div class="grid cols-3">' + (pr.ongoing || []).map(projectCard).join("") + "</div></div></section>" +
      '<section class="section alt"><div class="container"><div class="section-head"><h2>' + t({ en: "Past projects", it: "Progetti conclusi" }) + "</h2></div>" +
      '<div class="grid cols-3">' + (pr.past || []).map(projectCard).join("") + "</div></div></section>";
  }

  function renderProject(slug) {
    var p = findProject(slug);
    return pageHero(t(p.title), "", '<a href="#/projects">' + t(SITE.sections.projects) + "</a>") +
      '<section class="section"><div class="container"><div class="detail-layout"><div>' +
      '<div class="figure-inline"><img src="' + p.img + '" alt="" style="max-height:320px;object-fit:contain;width:100%;padding:1rem"></div>' +
      '<div class="prose"><p>' + t(p.abstract) + "</p></div></div>" +
      '<aside class="aside-card"><h3>' + t({ en: "Project details", it: "Dettagli del progetto" }) + "</h3><dl>" +
      "<dt>" + t({ en: "Duration", it: "Durata" }) + "</dt><dd>" + p.duration + "</dd>" +
      "<dt>" + t({ en: "Status", it: "Stato" }) + "</dt><dd>" + ((SITE.projects.past || []).indexOf(p) >= 0 ? t({ en: "Completed", it: "Concluso" }) : t({ en: "Ongoing", it: "In corso" })) + "</dd>" +
      "</dl></aside></div></div></section>";
  }

  function renderChallenges() {
    return pageHero(t(SITE.sections.challenges), t({ en: "International machine learning and image analysis challenges our group took part in.", it: "Sfide internazionali di machine learning e analisi di immagini a cui il nostro gruppo ha partecipato." })) +
      '<section class="section"><div class="container"><div class="grid cols-3">' +
      (SITE.challenges || []).map(function (c) {
        return '<a class="card" href="#/' + c.slug + '"><div class="thumb contain"><img src="' + c.img + '" alt=""></div>' +
          '<div class="body"><h3>' + t(c.title) + "</h3><p>" + t(c.desc) + "</p>" +
          '<span class="more">' + t({ en: "Details \u2192", it: "Dettagli \u2192" }) + "</span></div></a>";
      }).join("") + "</div></div></section>";
  }

  function renderChallenge(slug) {
    var c = findChallenge(slug);
    return pageHero(t(c.title), "", '<a href="#/challenges">' + t(SITE.sections.challenges) + "</a>") +
      '<section class="section"><div class="container"><div class="detail-layout"><div>' +
      '<div class="figure-inline"><img src="' + c.img + '" alt="" style="max-height:280px;object-fit:contain;margin:auto;padding:1rem"></div>' +
      '<div class="prose"><p>' + t(c.desc) + "</p></div></div>" +
      '<aside class="aside-card"><h3>' + t({ en: "External link", it: "Link esterno" }) + "</h3>" +
      '<p><a class="btn btn-primary" href="' + c.url + '" target="_blank" rel="noopener">' + t({ en: "Open challenge \u2192", it: "Apri la sfida \u2192" }) + "</a></p></aside></div></div></section>";
  }

  function renderPublications() {
    return pageHero(t(SITE.sections.publications), t({ en: "Scientific production of the Medical Physics group.", it: "Produzione scientifica del gruppo di Fisica Medica." })) +
      '<section class="section"><div class="container"><div class="grid cols-3">' +
      (SITE.publications || []).map(function (p) {
        return '<a class="card" href="#/' + p.slug + '"><div class="body"><h3>' + t(p) + "</h3><p>" + t(p.desc) + "</p>" +
          '<span class="more">' + t({ en: "Browse \u2192", it: "Sfoglia \u2192" }) + "</span></div></a>";
      }).join("") + "</div></div></section>";
  }

  function renderPublication(slug) {
    var p = findPublication(slug);
    return pageHero(t(p), t(p.desc), '<a href="#/publications">' + t(SITE.sections.publications) + "</a>") +
      '<section class="section"><div class="container"><p class="notice">' + t(SITE.pub_notice) + "</p>" +
      '<div class="prose pub-list">' + basePage(slug) + "</div></div></section>";
  }

  function renderJoin() {
    var j = SITE.join_us;
    var rows = (j.theses || []).map(function (x) {
      return "<tr><td>" + t(x.t) + "</td><td>" + x.s + "</td></tr>";
    }).join("");
    return pageHero(t({ en: "Join Us", it: "Unisciti a noi" }), t(j.intro)) +
      '<section class="section"><div class="container prose"><table><thead><tr><th>' + t(j.col_title) + "</th><th>" + t(j.col_sup) + "</th></tr></thead><tbody>" + rows + "</tbody></table></div></section>";
  }

  function renderCourses() {
    var items = (SITE.courses.items || []).map(function (c) { return "<li>" + t(c) + "</li>"; }).join("");
    return pageHero(t({ en: "Courses", it: "Corsi" })) +
      '<section class="section"><div class="container prose"><ul>' + items + "</ul></div></section>";
  }

  function renderProtected(slug) {
    var p = SITE.protected[slug];
    var title = t(p.title);
    return pageHero(title) +
      '<section class="section"><div class="container"><div class="lock"><h3>' + title + "</h3>" +
      "<p>" + t(SITE.protected_msg) + "</p>" +
      '<form onsubmit="return false"><label>' + t({ en: "Password", it: "Password" }) + '</label>' +
      '<input type="password" autocomplete="off"><button class="btn btn-primary" type="submit">' +
      t({ en: "Enter", it: "Accedi" }) + "</button></form></div></div></section>";
  }

  function renderBase(slug) {
    var title = (META[slug] && META[slug].title) || nameOf(slug);
    var body = basePage(slug);
    if (!body) body = '<p>' + t({ en: "Content not available.", it: "Contenuto non disponibile." }) + "</p>";
    var extra = "";
    if (lang === "en" && (slug === "privary-cookie-policy" || slug === "disattivazione-dei-cookies-sui-browser")) {
      extra = '<div class="notice">' + t({ en: "Official notice provided in Italian.", it: "" }) + "</div>";
    }
    return pageHero(title) + '<section class="section"><div class="container"><div class="prose">' + extra + body + "</div></div></section>";
  }

  function notFound() {
    return pageHero("404") + '<section class="section"><div class="container"><p>' +
      t({ en: "Page not found.", it: "Pagina non trovata." }) + ' <a href="#/home">' + t({ en: "Back home", it: "Torna alla home" }) + "</a></p></div></section>";
  }

  /* ---------------- Router ---------------- */
  function routeSlug() {
    var h = location.hash.replace(/^#\/?/, "").split("?")[0];
    return h || "home";
  }

  function render() {
    var r = routeSlug();
    var html, title = t(SITE.short);

    if (r === "home" || r === "") html = renderHome();
    else if (r === "research") html = renderResearchIndex();
    else if (findResearch(r)) { html = renderResearch(r); title = t(findResearch(r).title); }
    else if (r === "people") html = renderPeople();
    else if (findPerson(r)) { html = renderPerson(r); title = nameOf(r); }
    else if (r === "projects" || r === "ongoing-projects" || r === "past-projects") html = renderProjects();
    else if (findProject(r)) { html = renderProject(r); title = t(findProject(r).title); }
    else if (r === "challenges") html = renderChallenges();
    else if (findChallenge(r)) { html = renderChallenge(r); title = t(findChallenge(r).title); }
    else if (r === "publications" || r === "pubblication") html = renderPublications();
    else if (findPublication(r)) { html = renderPublication(r); title = t(findPublication(r)); }
    else if (r === "join-us") html = renderJoin();
    else if (r === "courses") html = renderCourses();
    else if (SITE.protected && SITE.protected[r]) { html = renderProtected(r); title = t(SITE.protected[r].title); }
    else if (EN[r] || IT[r] || ENX[r]) { html = renderBase(r); title = (META[r] && META[r].title) || title; }
    else html = notFound();

    app.innerHTML = header(r) + '<main id="main">' + html + "</main>" + footer();
    document.title = title + " \u2014 " + t(SITE.brand);
    window.scrollTo(0, 0);
    bindShell();
  }

  function bindShell() {
    var btn = app.querySelector(".menu-toggle");
    var nav = app.querySelector(".main-nav");
    if (btn && nav) btn.addEventListener("click", function () {
      nav.classList.toggle("open");
      btn.setAttribute("aria-expanded", nav.classList.contains("open") ? "true" : "false");
    });
    Array.prototype.forEach.call(app.querySelectorAll("[data-setlang]"), function (b) {
      b.addEventListener("click", function () { setLang(b.getAttribute("data-setlang")); });
    });
    if (nav) Array.prototype.forEach.call(nav.querySelectorAll("a"), function (a) {
      a.addEventListener("click", function () { nav.classList.remove("open"); });
    });
  }

  function setLang(l) {
    lang = l;
    try { localStorage.setItem("medphys_lang", l); } catch (e) {}
    document.documentElement.lang = l;
    render();
  }

  window.addEventListener("hashchange", render);
  if (!location.hash) location.hash = "#/home";
  render();
})();
