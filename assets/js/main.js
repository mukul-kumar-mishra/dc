/* DestroCorp consent manager — 100% first-party, no trackers loaded by default.
   Compliant with: EU GDPR/ePrivacy, UK GDPR, India DPDP Act 2023,
   California CCPA/CPRA, Brazil LGPD, Canada PIPEDA, Australia Privacy Act.
   Default state = "rejected" (no analytics, no marketing). Choice stored locally. */
(function () {
  "use strict";
  var KEY = "destrocorp-consent-v1";
  function read() {
    try { return JSON.parse(localStorage.getItem(KEY) || "null"); } catch (e) { return null; }
  }
  function write(v) {
    try { localStorage.setItem(KEY, JSON.stringify(v)); } catch (e) { /* private mode */ }
  }
  // Respect Do-Not-Track / Global Privacy Control: never enable optional storage.
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
    // Reflect stored choice in checkboxes
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
    applyBanner();
    // Mobile nav toggle
    var toggle = document.querySelector(".nav-toggle"), nav = document.getElementById("primary-nav");
    if (toggle && nav) {
      toggle.addEventListener("click", function () {
        var open = nav.classList.toggle("open");
        toggle.setAttribute("aria-expanded", open ? "true" : "false");
      });
      nav.addEventListener("click", function (e) {
        if (e.target.closest("a")) { nav.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
      });
    }
    var bAll = document.getElementById("c-accept");
    var bNec = document.getElementById("c-reject");
    var bSave = document.getElementById("c-save");
    if (bAll) bAll.addEventListener("click", function () { decide(true, true, false); });
    if (bNec) bNec.addEventListener("click", function () { decide(false, false, false); });
    if (bSave) bSave.addEventListener("click", function () {
      var p = document.getElementById("c-pref"), a = document.getElementById("c-an"), m = document.getElementById("c-mkt");
      decide(p && p.checked, a && a.checked, m && m.checked);
    });
    // Footer "Cookie settings" re-opener
    document.querySelectorAll("[data-open-consent]").forEach(function (el) {
      el.addEventListener("click", function (ev) {
        ev.preventDefault();
        var box = document.getElementById("consent");
        if (box) { box.classList.add("show"); box.scrollIntoView({ block: "nearest" }); }
      });
    });
    // Footer year
    document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = new Date().getFullYear(); });
    // Contact form -> mailto composer (no backend, no data stored by us)
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
