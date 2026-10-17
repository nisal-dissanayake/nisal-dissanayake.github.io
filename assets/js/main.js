// Clear Money Sheets: menu toggle, product filters, product gallery. No dependencies.
document.documentElement.classList.remove("no-js");

(function menu() {
  var btn = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (!btn || !nav) return;
  btn.addEventListener("click", function () {
    var open = btn.getAttribute("aria-expanded") === "true";
    btn.setAttribute("aria-expanded", String(!open));
    nav.classList.toggle("open", !open);
  });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && nav.classList.contains("open")) {
      btn.setAttribute("aria-expanded", "false");
      nav.classList.remove("open");
      btn.focus();
    }
  });
})();

(function filters() {
  var chips = document.querySelectorAll(".chip[data-filter]");
  var cards = document.querySelectorAll(".card[data-category]");
  var status = document.getElementById("filter-status");
  if (!chips.length) return;
  function apply(filter) {
    var shown = 0;
    chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c.dataset.filter === filter)); });
    cards.forEach(function (card) {
      var match = filter === "all" || card.dataset.category === filter;
      card.hidden = !match;
      if (match) shown++;
    });
    if (status) status.textContent = shown === 1 ? "Showing 1 spreadsheet" : "Showing " + shown + " spreadsheets";
  }
  chips.forEach(function (c) { c.addEventListener("click", function () { apply(c.dataset.filter); }); });
})();

(function gallery() {
  var main = document.getElementById("gallery-main");
  var thumbs = document.querySelectorAll(".thumbs [data-full]");
  if (!main || !thumbs.length) return;
  thumbs.forEach(function (t) {
    t.addEventListener("click", function (e) {
      e.preventDefault();
      var pic = main.querySelector("picture");
      pic.querySelector("source").srcset = t.dataset.fullWebp;
      var img = pic.querySelector("img");
      img.src = t.dataset.full;
      img.alt = t.dataset.alt;
      thumbs.forEach(function (o) { o.setAttribute("aria-current", String(o === t)); });
    });
  });
})();
