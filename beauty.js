/* MagzGold — подбор номеров по «красоте» с ползунком.
   Оценка 0..100 тем же анализатором, что и /proverit-nomer/ (checker.js analyze).
   Данные — локальный /data/catalog.json (без обращений к API): считаем красоту всех номеров один раз,
   сортируем по убыванию; ползунок задаёт МИНИМАЛЬНЫЙ порог красоты. */
(function () {
  var grid = document.getElementById("bGrid");
  if (!grid) return;
  var sliderMin = document.getElementById("bMin"), valMin = document.getElementById("bVal"),
      sliderMax = document.getElementById("bMax"), valMax = document.getElementById("bMaxVal"),
      countEl = document.getElementById("bCount"), statusEl = document.getElementById("bStatus"),
      moreBtn = document.getElementById("bMore");
  var STEP = 60, shown = STEP, ALL = [];
  var CAT_LABEL = { brilliant: "Бриллиант", platinum: "Платина", gold: "Золото", silver: "Серебро", bronze: "Бронза" };

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function fmtPhone(d) { d = String(d); return d.length === 10 ? "+7 " + d.slice(0, 3) + " " + d.slice(3, 6) + "-" + d.slice(6, 8) + "-" + d.slice(8, 10) : "+7 " + d; }
  function fmtMoney(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function plural(n, a, b, c) { n = Math.abs(n) % 100; var d = n % 10; if (n > 10 && n < 20) return c; if (d > 1 && d < 5) return b; if (d === 1) return a; return c; }

  // сила паттернов произвольной длины 0..1 (повторы/серии/последовательности/ABAB/палиндром)
  function patStrength(s) {
    var n = s.length; if (n < 2) return 0;
    var counts = {}, i; for (i = 0; i < n; i++) counts[s[i]] = (counts[s[i]] || 0) + 1;
    var distinct = Object.keys(counts).length, maxFreq = 0, k; for (k in counts) maxFreq = Math.max(maxFreq, counts[k]);
    var run = 1, maxRun = 1, j; for (j = 1; j < n; j++) { if (s[j] === s[j - 1]) { run++; maxRun = Math.max(maxRun, run); } else run = 1; }
    function seqRun(st) { var r = 1, m = 1, i2; for (i2 = 1; i2 < n; i2++) { if ((+s[i2] - +s[i2 - 1]) === st) { r++; m = Math.max(m, r); } else r = 1; } return m; }
    var maxSeq = Math.max(seqRun(1), seqRun(-1));
    var alt = 1, ar = 1, a; for (a = 2; a < n; a++) { if (s[a] === s[a - 2] && s[a] !== s[a - 1]) { ar = (ar < 2 ? 3 : ar + 1); alt = Math.max(alt, ar); } else ar = 1; }
    var palin = s === s.split("").reverse().join("");
    var rep = (n - distinct) / (n - 1), runC = Math.min(1, (maxRun - 1) / Math.max(1, n - 3)), freqC = (maxFreq - 1) / (n - 1),
        seqC = (maxSeq - 1) / (n - 1), altC = Math.min(1, (alt - 2) / Math.max(1, n - 4));
    // частота цифры весома (шесть одинаковых важнее четырёх подряд); палиндром — ДОБАВКА, а не потолок,
    // иначе симметричные бриллиантовые (5558555) проигрывали сплошным повторам и тонули в сортировке.
    var repBeauty = 0.40 * rep + 0.30 * runC + 0.30 * freqC;
    var base = Math.max(repBeauty, seqC * 0.8, altC * 0.72);
    return Math.min(1, base + (palin ? 0.16 : 0));
  }
  // оценка красоты 0..100. Красоту меряем по ТЕЛУ (7 цифр после кода) и хвосту-6, а не только по всем 10 —
  // иначе случайный код (напр. 984) разбавляет красивое тело. Синхронно с checker.js.
  function score(d) {
    d = String(d);
    var trail = 1; for (var b = 8; b >= 0; b--) { if (d[b] === d[9]) trail++; else break; }
    var tz = (d.match(/0+$/) || [""])[0].length;
    var pat = Math.max(patStrength(d), patStrength(d.slice(3)) * 0.97, patStrength(d.slice(4)) * 0.93);
    var tailC = Math.min(1, (trail - 1) / 5), round = Math.min(1, tz / 4);
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
    var min = +sliderMin.value, max = +sliderMax.value;
    var list = ALL.filter(function (x) { return x.s >= min && x.s <= max; });
    countEl.textContent = list.length + " " + plural(list.length, "номер", "номера", "номеров") + " с красотой " + min + "–" + max;
    if (!list.length) { grid.innerHTML = ""; statusEl.textContent = "Нет номеров в этом диапазоне красоты — расширьте вилку ползунками."; statusEl.style.display = ""; moreBtn.hidden = true; return; }
    statusEl.style.display = "none";
    grid.innerHTML = list.slice(0, shown).map(card).join("");
    moreBtn.hidden = list.length <= shown;
  }

  // не даём ползункам пересечься: минимум не заходит выше максимума и наоборот
  sliderMin.addEventListener("input", function () {
    if (+sliderMin.value > +sliderMax.value) { sliderMax.value = sliderMin.value; valMax.textContent = sliderMax.value; }
    valMin.textContent = sliderMin.value; shown = STEP; render();
  });
  sliderMax.addEventListener("input", function () {
    if (+sliderMax.value < +sliderMin.value) { sliderMin.value = sliderMax.value; valMin.textContent = sliderMin.value; }
    valMax.textContent = sliderMax.value; shown = STEP; render();
  });
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
    valMin.textContent = sliderMin.value; valMax.textContent = sliderMax.value;
    render();
  }).catch(function () { statusEl.textContent = "Не удалось загрузить номера. Обновите страницу."; });
})();
