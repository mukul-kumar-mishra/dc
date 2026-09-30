/* DestroCorp — same interaction pattern as buildopsy.com:
   dark default + light opt-in toggle, mobile nav, consent manager.
   First-party only. Inline SVG icons (no icon CDN). */
(function () {
  "use strict";

  /* ---- Theme (dark default, light opt-in) ---- */
  var THEME_KEY = "dc-theme";
  var root = document.documentElement;
  function syncThemeIcons() {
    var dark = root.classList.contains("dark");
    document.querySelectorAll(".ic-sun").forEach(function (el) { el.style.display = dark ? "none" : ""; });
    document.querySelectorAll(".ic-moon").forEach(function (el) { el.style.display = dark ? "" : "none"; });
    var meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.setAttribute("content", dark ? "#12130f" : "#f2eee4");
  }

  /* ---- Consent manager (unchanged behaviour) ---- */
  var KEY = "destrocorp-consent-v1";
  function read() {
    try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; }
  }
  function write(v) {
    try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) { /* private mode */ }
  }
  var dnt = (navigator.doNotTrack === "1" || window.doNotTrack === "1" ||
             navigator.globalPrivacyControl === true);
  function current() {
    var c = read();
    if (!c) return { necessary: true, preferences: false, analytics: false, marketing: false, decided: false, dnt: dnt };
    c.decided = true; c.dnt = dnt;
    if (dnt) { c.analytics = false; c.marketing = false; }
    return c;
  }
  function applyBanner() {
    var box = document.getElementById("consent");
    if (!box) return;
    var c = current();
    box.classList.toggle("show", !c.decided);
    var p = document.getElementById("c-pref"), a = document.getElementById("c-an"), m = document.getElementById("c-mkt");
    if (p) p.checked = !!c.preferences;
    if (a) a.checked = !!c.analytics && !dnt;
    if (m) m.checked = !!c.marketing && !dnt;
    if (dnt) {
      var note = document.getElementById("c-dnt");
      if (note) note.hidden = false;
    }
  }
  function decide(prefs, analytics, marketing) {
    if (dnt) { analytics = false; marketing = false; }
    write({ necessary: true, preferences: !!prefs, analytics: !!analytics,
            marketing: !!marketing, decided: true, ts: new Date().toISOString() });
    applyBanner();
  }

  document.addEventListener("DOMContentLoaded", function () {
    /* theme */
    syncThemeIcons();
    var themeBtn = document.getElementById("themeToggle");
    if (themeBtn) themeBtn.addEventListener("click", function () {
      root.classList.toggle("dark");
      try { localStorage.setItem(THEME_KEY, root.classList.contains("dark") ? "dark" : "light"); } catch (e) {}
      syncThemeIcons();
    });

    /* mobile nav — supports both buildopsy (.topnav) and legacy (#primary-nav) markup */
    function wireNav(toggleSel, navSel) {
      var toggle = document.querySelector(toggleSel), nav = document.querySelector(navSel);
      if (!toggle || !nav) return;
      toggle.addEventListener("click", function () {
        var open = nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      nav.addEventListener("click", function (e) {
        if (e.target.closest("a")) { nav.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && nav.classList.contains("open")) { nav.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); toggle.focus(); }
      });
      window.addEventListener("resize", function () {
        if (window.innerWidth > 760 && nav.classList.contains("open")) { nav.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
      });
    }
    wireNav("#navToggle", "#topnav");
    wireNav(".nav-toggle", "#primary-nav");

    /* consent */
    applyBanner();
    var bAll = document.getElementById("c-accept");
    var bNec = document.getElementById("c-reject");
    var bSave = document.getElementById("c-save");
    if (bAll) bAll.addEventListener("click", function () { decide(true, true, false); });
    if (bNec) bNec.addEventListener("click", function () { decide(false, false, false); });
    if (bSave) bSave.addEventListener("click", function () {
      var p = document.getElementById("c-pref"), a = document.getElementById("c-an"), m = document.getElementById("c-mkt");
      decide(p && p.checked, a && a.checked, m && m.checked);
    });
    document.querySelectorAll("[data-open-consent]").forEach(function (el) {
      el.addEventListener("click", function (ev) {
        ev.preventDefault();
        var box = document.getElementById("consent");
        if (box) { box.classList.add("show"); box.scrollIntoView({ block: "nearest" }); }
      });
    });
    document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });

    /* reduced-motion flag shared by glow + counters */
    var hbReduce = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);

    /* hero pointer glow (fine pointers only, no reduced motion) */
    var heroXl = document.querySelector(".hero-xl");
    var canGlow = !hbReduce && window.matchMedia && window.matchMedia("(hover: hover)").matches;
    if (heroXl && canGlow) {
      var glowTick = false;
      heroXl.addEventListener("pointermove", function (e) {
        if (glowTick) return; glowTick = true;
        requestAnimationFrame(function () {
          var r = heroXl.getBoundingClientRect();
          heroXl.style.setProperty("--mx", ((e.clientX - r.left) / r.width * 100).toFixed(2) + "%");
          heroXl.style.setProperty("--my", ((e.clientY - r.top) / r.height * 100).toFixed(2) + "%");
          heroXl.classList.add("glow");
          glowTick = false;
        });
      });
      heroXl.addEventListener("pointerleave", function () { heroXl.classList.remove("glow"); });
    }

    /* count-up stats */
    function countUp(el) {
      var target = parseInt(el.getAttribute("data-count"), 10);
      var suffix = el.getAttribute("data-suffix") || "";
      if (isNaN(target)) return;
      if (hbReduce) { el.textContent = target + suffix; return; }
      var t0 = null, dur = 1200;
      function step(t) {
        if (!t0) t0 = t;
        var p = Math.min((t - t0) / dur, 1), e = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(target * e) + (p === 1 ? suffix : "");
        if (p < 1) requestAnimationFrame(step);
      }
      requestAnimationFrame(step);
    }
    var counters = document.querySelectorAll("[data-count]");
    if ("IntersectionObserver" in window && counters.length) {
      var cio = new IntersectionObserver(function (es) {
        es.forEach(function (en) { if (en.isIntersecting) { countUp(en.target); cio.unobserve(en.target); } });
      }, { threshold: 0.5 });
      counters.forEach(function (el) { cio.observe(el); });
    }

    /* subtle reveal */
    var els = document.querySelectorAll(".reveal");
    if ("IntersectionObserver" in window && els.length) {
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
        });
      }, { threshold: 0.1 });
      els.forEach(function (el) { io.observe(el); });
    } else {
      els.forEach(function (el) { el.classList.add("in"); });
    }

    /* contact form -> mailto composer (no backend, nothing stored) */
    var f = document.getElementById("dsr-form");
    if (f) f.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var fd = new FormData(f);
      var subject = encodeURIComponent("DSR request [" + (fd.get("right") || "general") + "] — destrocorp.com");
      var body = encodeURIComponent(
        "Hello DestroCorp,\n\nI am exercising my data right.\n\nRight: " + (fd.get("right") || "") +
        "\nName: " + (fd.get("name") || "") + "\nEmail: " + (fd.get("email") || "") +
        "\nJurisdiction: " + (fd.get("region") || "") + "\nDetails:\n" + (fd.get("details") || "") +
        "\n\n— sent from destrocorp.com (opens in my email app; nothing was stored on the site)");
      window.location.href = "mailto:grievance@destrocorp.com?subject=" + subject + "&body=" + body;
    });
  });
  window.DestroConsent = { current: current, decide: decide };
})();
