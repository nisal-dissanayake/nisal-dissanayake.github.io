// Clear Money Sheets free calculators. Everything runs in the browser; nothing is sent anywhere.
(function () {
  "use strict";

  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  function money(n) { return Math.round(n).toLocaleString("en-US"); }
  function num(el) { var v = parseFloat(String(el.value).replace(/,/g, "")); return isFinite(v) ? v : NaN; }
  function monthLabel(y, m) { // m is 0-based and may overflow
    var d = new Date(y, m, 1);
    return MONTHS[d.getMonth()] + " " + d.getFullYear();
  }
  function el(tag, attrs, text) {
    var e = document.createElement(tag);
    if (attrs) for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (text != null) e.textContent = text;
    return e;
  }
  function dl(pairs) {
    var d = el("dl");
    pairs.forEach(function (p) { d.appendChild(el("dt", null, p[0])); d.appendChild(el("dd", null, p[1])); });
    return d;
  }

  // ------------------------------------------------------------------
  // Debt snowball vs avalanche. Same rules as the Debt Payoff Calculator spreadsheet:
  // each month every debt gets interest (APR/12) and its minimum payment; the extra pool
  // (your extra payment + the minimums of debts already paid off) goes to debts in priority order.
  // ------------------------------------------------------------------
  function simulateDebts(debts, extra, order, maxMonths) {
    var n = debts.length;
    var bal = debts.map(function (d) { return d.balance; });
    var endPrev = bal.map(function () { return 1; }); // balance at end of previous month (non-zero placeholder)
    var totalInterest = 0, totalPaid = 0, paidOffMonth = new Array(n).fill(null);
    for (var m = 1; m <= maxMonths; m++) {
      var pool = extra;
      if (m > 1) for (var i = 0; i < n; i++) if (endPrev[i] <= 0) pool += debts[i].min;
      var used = 0, total = 0, endNow = new Array(n);
      for (var p = 0; p < n; p++) {
        var k = order[p], E = bal[k];
        var F = E * debts[k].apr / 100 / 12;
        var G = E <= 0 ? 0 : Math.min(debts[k].min, E + F);
        var H = Math.max(0, E + F - G);
        var K = E <= 0 ? 0 : Math.max(0, Math.min(pool - used, H));
        used += K;
        var M = G + K;
        var N = Math.max(0, E + F - M);
        totalInterest += F; totalPaid += M;
        endNow[k] = N; total += N;
        if (N <= 0 && E > 0 && paidOffMonth[k] === null) paidOffMonth[k] = m;
      }
      bal = endNow; endPrev = endNow;
      if (total === 0) return { months: m, interest: totalInterest, paid: totalPaid, paidOffMonth: paidOffMonth };
    }
    return { months: null, interest: totalInterest, paid: totalPaid, paidOffMonth: paidOffMonth };
  }
  function snowballOrder(debts) { // smallest balance first, ties by list order
    return debts.map(function (d, i) { return i; }).sort(function (a, b) { return (debts[a].balance - debts[b].balance) || (a - b); });
  }
  function avalancheOrder(debts) { // highest APR first, ties by list order
    return debts.map(function (d, i) { return i; }).sort(function (a, b) { return (debts[b].apr - debts[a].apr) || (a - b); });
  }
  // Exposed for testing (node) and reuse.
  var api = { simulateDebts: simulateDebts, snowballOrder: snowballOrder, avalancheOrder: avalancheOrder };
  if (typeof module !== "undefined" && module.exports) { module.exports = api; return; }

  function debtTool() {
    var form = document.getElementById("debt-form");
    if (!form) return;
    var rows = document.getElementById("debt-rows");
    var tpl = document.getElementById("debt-row-template");
    var out = document.getElementById("debt-results");
    var count = 0;

    function addRow(d) {
      count++;
      var frag = tpl.content.cloneNode(true);
      var row = frag.querySelector(".debt-row");
      row.querySelectorAll("[data-f]").forEach(function (input) {
        var id = "debt-" + count + "-" + input.dataset.f;
        input.id = id;
        input.parentNode.querySelector("label").setAttribute("for", id);
        if (d && d[input.dataset.f] != null) input.value = d[input.dataset.f];
      });
      row.querySelector(".remove").addEventListener("click", function () {
        if (rows.children.length > 1) { row.remove(); rows.querySelector("input").focus(); }
      });
      rows.appendChild(frag);
    }
    [
      { name: "Credit card A", balance: 4800, apr: 24.99, min: 120 },
      { name: "Store card", balance: 650, apr: 27.99, min: 35 },
      { name: "Car loan", balance: 9500, apr: 6.5, min: 230 },
      { name: "Personal loan", balance: 3000, apr: 11.5, min: 140 },
      { name: "Credit card B", balance: 2200, apr: 19.99, min: 70 }
    ].forEach(addRow);
    document.getElementById("add-debt").addEventListener("click", function () {
      if (rows.children.length >= 12) return;
      addRow(); rows.lastElementChild.querySelector("input").focus();
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      out.innerHTML = "";
      var extra = num(document.getElementById("debt-extra"));
      if (!isFinite(extra) || extra < 0) extra = 0;
      var debts = [], problem = null;
      rows.querySelectorAll(".debt-row").forEach(function (r, i) {
        var name = r.querySelector('[data-f="name"]').value.trim() || ("Debt " + (i + 1));
        var balance = num(r.querySelector('[data-f="balance"]'));
        var apr = num(r.querySelector('[data-f="apr"]'));
        var min = num(r.querySelector('[data-f="min"]'));
        if (!isFinite(balance) || balance <= 0) return; // empty row: skip
        if (!isFinite(apr) || apr < 0) apr = 0;
        if (!isFinite(min) || min < 0) min = 0;
        debts.push({ name: name, balance: balance, apr: apr, min: min });
      });
      out.hidden = false;
      if (!debts.length) { out.appendChild(el("p", { "class": "error" }, "Add at least one debt with a balance.")); return; }

      var MAX = 600;
      var sb = simulateDebts(debts, extra, snowballOrder(debts), MAX);
      var av = simulateDebts(debts, extra, avalancheOrder(debts), MAX);
      var now = new Date(), y = now.getFullYear(), m0 = now.getMonth() + 1; // payoff starts next month

      function card(title, r, order) {
        var c = el("div", { "class": "result-card" });
        c.appendChild(el("h3", null, title));
        if (r.months === null) {
          c.appendChild(el("p", { "class": "error" }, "Not paid off within 50 years. The payments don't cover the interest. Try a larger extra payment."));
          return c;
        }
        c.appendChild(dl([
          ["Debt-free", monthLabel(y, m0 + r.months - 1)],
          ["Months", String(r.months) + " (" + (r.months / 12).toFixed(1) + " years)"],
          ["Total interest", money(r.interest)],
          ["Total paid", money(r.paid)]
        ]));
        var ol = el("ol", { "class": "small", style: "margin:10px 0 0;padding-left:1.2em" });
        order.forEach(function (k) {
          var pm = r.paidOffMonth[k];
          ol.appendChild(el("li", null, debts[k].name + (pm ? ", paid off " + monthLabel(y, m0 + pm - 1) : "")));
        });
        c.appendChild(el("p", { "class": "small", style: "margin:12px 0 0;font-weight:600" }, "Order extra payments go to"));
        c.appendChild(ol);
        return c;
      }
      var cards = el("div", { "class": "result-cards" });
      cards.appendChild(card("Snowball (smallest balance first)", sb, snowballOrder(debts)));
      cards.appendChild(card("Avalanche (highest rate first)", av, avalancheOrder(debts)));
      out.appendChild(el("h3", null, "Your results"));
      out.appendChild(cards);
      if (sb.months !== null && av.months !== null) {
        var diff = sb.interest - av.interest;
        var msg = Math.abs(diff) < 1
          ? "Both methods cost about the same in interest with these numbers. Pick the one you'll stick with."
          : (diff > 0 ? "Avalanche saves about " + money(diff) + " in interest compared with Snowball."
                      : "Snowball saves about " + money(-diff) + " in interest compared with Avalanche.");
        out.appendChild(el("p", { "class": "big-number", style: "font-size:1.15rem" }, msg));
      }
      out.appendChild(el("p", { "class": "small muted" }, "Assumes payments start next month, rates stay the same, you pay the same extra amount every month and add no new debt. Amounts are in whatever currency you entered."));
      out.querySelector("h3").setAttribute("tabindex", "-1");
      out.querySelector("h3").focus();
    });
  }

  // ------------------------------------------------------------------
  // 50/30/20 budget split
  // ------------------------------------------------------------------
  function splitTool() {
    var form = document.getElementById("split-form");
    if (!form) return;
    var out = document.getElementById("split-results");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      out.innerHTML = ""; out.hidden = false;
      var income = num(document.getElementById("split-income"));
      var pN = num(document.getElementById("split-needs-pct")), pW = num(document.getElementById("split-wants-pct")), pS = num(document.getElementById("split-savings-pct"));
      if (!isFinite(income) || income <= 0) { out.appendChild(el("p", { "class": "error" }, "Enter your monthly take-home pay.")); return; }
      if (![pN, pW, pS].every(isFinite) || Math.abs(pN + pW + pS - 100) > 0.001) {
        out.appendChild(el("p", { "class": "error" }, "Your three percentages add up to " + ((pN || 0) + (pW || 0) + (pS || 0)) + "%. They need to add up to 100%."));
        return;
      }
      var parts = [
        { label: "Needs", pct: pN, color: "#1F5F6B", actual: num(document.getElementById("split-needs-now")), note: "rent, utilities, groceries, insurance, minimum debt payments" },
        { label: "Wants", pct: pW, color: "#E0A458", actual: num(document.getElementById("split-wants-now")), note: "eating out, subscriptions, hobbies, travel" },
        { label: "Savings & extra debt payments", pct: pS, color: "#7FA9B1", actual: num(document.getElementById("split-savings-now")), note: "emergency fund, goals, investing, paying debt faster" }
      ];
      out.appendChild(el("h3", { tabindex: "-1" }, "Your " + pN + "/" + pW + "/" + pS + " split of " + money(income) + " a month"));
      var bar = el("div", { "class": "bar", role: "img", "aria-label": parts.map(function (p) { return p.label + " " + p.pct + "%"; }).join(", ") });
      parts.forEach(function (p) { var s = el("span"); s.style.width = p.pct + "%"; s.style.background = p.color; bar.appendChild(s); });
      out.appendChild(bar);
      var cards = el("div", { "class": "result-cards" });
      parts.forEach(function (p) {
        var target = income * p.pct / 100;
        var c = el("div", { "class": "result-card" });
        var h = el("h3"); var sw = el("i"); sw.style.background = p.color; sw.style.display = "inline-block"; sw.style.width = "12px"; sw.style.height = "12px"; sw.style.borderRadius = "3px"; sw.style.marginRight = "8px";
        h.appendChild(sw); h.appendChild(document.createTextNode(p.label + " (" + p.pct + "%)")); c.appendChild(h);
        var pairs = [["Target", money(target)]];
        if (isFinite(p.actual) && p.actual >= 0) {
          var d = p.actual - target;
          pairs.push(["You now", money(p.actual)]);
          pairs.push([d > 0 ? "Over target" : "Under target", money(Math.abs(d))]);
        }
        c.appendChild(dl(pairs));
        c.appendChild(el("p", { "class": "small muted", style: "margin:8px 0 0" }, p.note));
        cards.appendChild(c);
      });
      out.appendChild(cards);
      out.appendChild(el("p", { "class": "small muted" }, "50/30/20 is a rule of thumb, not a rule. If rent alone is half your pay, a 60/20/20 or 70/20/10 split may be more realistic. Adjust the percentages above."));
      out.querySelector("h3").focus();
    });
  }

  // ------------------------------------------------------------------
  // Savings goal timeline (no interest assumed, same as the Savings Goals Tracker)
  // ------------------------------------------------------------------
  function savingsTool() {
    var form = document.getElementById("savings-form");
    if (!form) return;
    var out = document.getElementById("savings-results");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      out.innerHTML = ""; out.hidden = false;
      var target = num(document.getElementById("sav-target"));
      var saved = num(document.getElementById("sav-saved")); if (!isFinite(saved) || saved < 0) saved = 0;
      var monthly = num(document.getElementById("sav-monthly")); if (!isFinite(monthly) || monthly < 0) monthly = 0;
      var dateVal = document.getElementById("sav-date").value.trim();
      if (!isFinite(target) || target <= 0) { out.appendChild(el("p", { "class": "error" }, "Enter the amount you want to save.")); return; }
      var now = new Date(), y = now.getFullYear(), m = now.getMonth();
      var left = Math.max(0, target - saved);
      out.appendChild(el("h3", { tabindex: "-1" }, "Your savings timeline"));
      var pairs = [["Goal", money(target)], ["Saved so far", money(saved) + " (" + Math.min(100, saved / target * 100).toFixed(0) + "%)"], ["Still to save", money(left)]];
      var verdict = null;
      if (left === 0) {
        verdict = "You've already reached this goal.";
      } else if (monthly > 0) {
        var months = Math.ceil(left / monthly);
        pairs.push(["Months to go at " + money(monthly) + "/month", String(months)]);
        pairs.push(["Fully funded", monthLabel(y, m + months)]);
      } else {
        verdict = "Add a monthly amount to see when you'll reach this goal.";
      }
      if (dateVal && left > 0) {
        var mt = /^(\d{4})-(\d{1,2})$/.exec(dateVal);
        if (!mt) { verdict = "Enter the target date as year and month, for example 2027-12."; }
        else {
          var monthsLeft = (parseInt(mt[1], 10) - y) * 12 + (parseInt(mt[2], 10) - 1 - m);
          if (monthsLeft <= 0) {
            verdict = "That target date is this month or already past, so the full " + money(left) + " is needed now.";
          } else {
            var needed = left / monthsLeft;
            pairs.push(["Needed per month to hit " + monthLabel(parseInt(mt[1], 10), parseInt(mt[2], 10) - 1), money(Math.ceil(needed))]);
            verdict = monthly >= needed - 0.005 ? "On track: your monthly amount is enough to reach the goal by your target date."
                                                : "Behind: you'd need about " + money(Math.ceil(needed - monthly)) + " more a month to make your target date.";
          }
        }
      }
      var c = el("div", { "class": "result-card" }); c.appendChild(dl(pairs)); out.appendChild(c);
      if (verdict) out.appendChild(el("p", { "class": "big-number", style: "font-size:1.15rem;margin-top:14px" }, verdict));
      out.appendChild(el("p", { "class": "small muted" }, "Counts from this month and assumes no interest, so it's a conservative estimate."));
      out.querySelector("h3").focus();
    });
  }

  debtTool(); splitTool(); savingsTool();
})();
