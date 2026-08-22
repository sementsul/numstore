/* MagzGold — подбор номеров по «красоте» с ползунком.
   Оценка 0..100 тем же анализатором, что и /proverit-nomer/ (checker.js analyze).
   Данные — локальный /data/catalog.json (без обращений к API): считаем красоту всех номеров один раз,
   сортируем по убыванию; ползунок задаёт МИНИМАЛЬНЫЙ порог красоты. */
(function () {
  var grid = document.getElementById("bGrid");
  if (!grid) return;
  var slider = document.getElementById("bMin"), valEl = document.getElementById("bVal"),
      countEl = document.getElementById("bCount"), statusEl = document.getElementById("bStatus"),
      moreBtn = document.getElementById("bMore");
  var STEP = 60, shown = STEP, ALL = [];
  var CAT_LABEL = { brilliant: "Бриллиант", platinum: "Платина", gold: "Золото", silver: "Серебро", bronze: "Бронза" };

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function fmtPhone(d) { d = String(d); return d.length === 10 ? "+7 " + d.slice(0, 3) + " " + d.slice(3, 6) + "-" + d.slice(6, 8) + "-" + d.slice(8, 10) : "+7 " + d; }
  function fmtMoney(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function plural(n, a, b, c) { n = Math.abs(n) % 100; var d = n % 10; if (n > 10 && n < 20) return c; if (d > 1 && d < 5) return b; if (d === 1) return a; return c; }

  // оценка красоты 0..100 — портирована из checker.js analyze() (те же веса, чтобы совпадало с «Проверить красоту»)
  function score(d) {
    d = String(d);
    var counts = {}; for (var i = 0; i < 10; i++) counts[d[i]] = (counts[d[i]] || 0) + 1;
    var distinct = Object.keys(counts).length, maxFreq = 0; for (var k in counts) maxFreq = Math.max(maxFreq, counts[k]);
    var run = 1, maxRun = 1; for (var j = 1; j < 10; j++) { if (d[j] === d[j - 1]) { run++; maxRun = Math.max(maxRun, run); } else run = 1; }
    function seqRun(st) { var r = 1, m = 1; for (var i2 = 1; i2 < 10; i2++) { if ((+d[i2] - +d[i2 - 1]) === st) { r++; m = Math.max(m, r); } else r = 1; } return m; }
    var maxSeq = Math.max(seqRun(1), seqRun(-1));
    var alt = 1, ar = 1; for (var a = 2; a < 10; a++) { if (d[a] === d[a - 2] && d[a] !== d[a - 1]) { ar = (ar < 2 ? 3 : ar + 1); alt = Math.max(alt, ar); } else ar = 1; }
    var trail = 1; for (var b = 8; b >= 0; b--) { if (d[b] === d[9]) trail++; else break; }
    var tz = (d.match(/0+$/) || [""])[0].length;
    var palin = d === d.split("").reverse().join("");
    var rep = (10 - distinct) / 9, runC = Math.min(1, (maxRun - 1) / 7), freqC = (maxFreq - 1) / 9,
        seqC = (maxSeq - 1) / 9, altC = Math.min(1, (alt - 2) / 6), tailC = Math.min(1, (trail - 1) / 5), round = Math.min(1, tz / 4);
    var repBeauty = 0.45 * rep + 0.35 * runC + 0.20 * freqC;
    var pat = Math.max(repBeauty, seqC * 0.8, altC * 0.72, palin ? 0.7 : 0);
    return Math.round(Math.min(100, (pat + tailC * 0.15 + round * 0.06) * 100));
  }
  function scoreCls(s) { return s >= 75 ? "v-top" : s >= 50 ? "v-nice" : s >= 25 ? "v-ok" : "v-plain"; }

  function card(x) {
    var d = String(x.n), badge = CAT_LABEL[x.cat] || "";
    return '<article class="num">'
      + (badge ? '<span class="num-badge">' + esc(badge) + "</span>" : "")
      + '<span class="num-score ' + scoreCls(x.s) + '" title="Оценка красоты, 0–100">★ ' + x.s + "</span>"
      + '<div class="num-phone">' + esc(fmtPhone(d)) + "</div>"
      + (x.t ? '<div class="num-tariff">' + esc(x.t) + "</div>" : "")
      + (x.p != null ? '<div class="num-price">' + esc(fmtMoney(x.p)) + "<span>/мес</span></div>" : "")
      + '<a class="num-buy" href="/nomer/?p=' + esc(d) + '">Забронировать →</a>'
      + "</article>";
  }

  function render() {
    var min = +slider.value;
    var list = ALL.filter(function (x) { return x.s >= min; });
    countEl.textContent = list.length + " " + plural(list.length, "номер", "номера", "номеров") + " с красотой от " + min;
    if (!list.length) { grid.innerHTML = ""; statusEl.textContent = "Нет номеров с такой красотой — сдвиньте ползунок левее."; statusEl.style.display = ""; moreBtn.hidden = true; return; }
    statusEl.style.display = "none";
    grid.innerHTML = list.slice(0, shown).map(card).join("");
    moreBtn.hidden = list.length <= shown;
  }

  slider.addEventListener("input", function () { valEl.textContent = slider.value; shown = STEP; render(); });
  moreBtn.addEventListener("click", function () { shown += STEP; render(); });

  fetch("/data/catalog.json").then(function (r) { return r.json(); }).then(function (j) {
    var cats = j.cats || {};
    Object.keys(cats).forEach(function (slug) {
      (cats[slug] || []).forEach(function (it) {
        var d = String(it.n); if (d.length !== 10) return;
        ALL.push({ n: d, t: it.t, p: it.p, cat: slug, s: score(d) });
      });
    });
    ALL.sort(function (a, b) { return b.s - a.s || (a.p || 0) - (b.p || 0); });
    valEl.textContent = slider.value;
    render();
  }).catch(function () { statusEl.textContent = "Не удалось загрузить номера. Обновите страницу."; });
})();
