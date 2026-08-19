/* MagzGold — проверка «красоты» номера. Свой анализатор паттернов (для любого номера) +
   проверка наличия в каталоге Безлимита (через API в браузере). */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var input = document.getElementById("chkInput");
  var btn = document.getElementById("chkBtn");
  var out = document.getElementById("chkOut");
  if (!input || !btn || !out) return;

  function digitsOf(s) { return String(s).replace(/\D/g, "").replace(/^7|^8/, "").slice(-10); }
  function fmtPhone(d) {
    return d.length === 10 ? "+7 " + d.slice(0, 3) + " " + d.slice(3, 6) + "-" + d.slice(6, 8) + "-" + d.slice(8, 10) : "+7 " + d;
  }
  function fmtMoney(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}

  /* ---- анализатор паттернов (10 цифр) ---- */
  function analyze(d) {
    var counts = {}; for (var i = 0; i < 10; i++) counts[d[i]] = (counts[d[i]] || 0) + 1;
    var distinct = Object.keys(counts).length, maxFreq = 0;
    for (var k in counts) maxFreq = Math.max(maxFreq, counts[k]);
    var run = 1, maxRun = 1;
    for (var j = 1; j < 10; j++) { if (d[j] === d[j - 1]) { run++; maxRun = Math.max(maxRun, run); } else run = 1; }
    function seqRun(st) { var r = 1, m = 1; for (var i = 1; i < 10; i++) { if ((+d[i] - +d[i - 1]) === st) { r++; m = Math.max(m, r); } else r = 1; } return m; }
    var maxSeq = Math.max(seqRun(1), seqRun(-1));
    // чередование пар ABAB (напр. 505050)
    var alt = 1, ar = 1;
    for (var a = 2; a < 10; a++) { if (d[a] === d[a - 2] && d[a] !== d[a - 1]) { ar = (ar < 2 ? 3 : ar + 1); alt = Math.max(alt, ar); } else ar = 1; }
    // длина серии одинаковых цифр В КОНЦЕ (красивое окончание)
    var trail = 1; for (var b = 8; b >= 0; b--) { if (d[b] === d[9]) trail++; else break; }
    var tz = (d.match(/0+$/) || [""])[0].length;
    var palin = d === d.split("").reverse().join("");
    var rep = (10 - distinct) / 9, runC = Math.min(1, (maxRun - 1) / 7), freqC = (maxFreq - 1) / 9,
        seqC = (maxSeq - 1) / 9, altC = Math.min(1, (alt - 2) / 6), tailC = Math.min(1, (trail - 1) / 5), round = Math.min(1, tz / 4);
    var repBeauty = 0.45 * rep + 0.35 * runC + 0.20 * freqC;             // сила повторов, 0..1
    var pat = Math.max(repBeauty, seqC * 0.8, altC * 0.72, palin ? 0.7 : 0); // лучший паттерн, без двойного счёта
    var score = Math.round(Math.min(100, (pat + tailC * 0.15 + round * 0.06) * 100));  // + бонус за красивое окончание
    var verdict, cls;
    if (score >= 75) { verdict = "Премиальный · редкий"; cls = "v-top"; }
    else if (score >= 50) { verdict = "Красивый"; cls = "v-nice"; }
    else if (score >= 25) { verdict = "Приятный"; cls = "v-ok"; }
    else { verdict = "Обычный номер"; cls = "v-plain"; }
    var feats = [];
    if (distinct === 1) feats.push("Все цифры одинаковые");
    else {
      if (maxRun >= 4) feats.push(maxRun + " одинаковых подряд");
      else if (maxRun === 3) feats.push("Тройка одинаковых");
      if (trail >= 3) feats.push("Красивое окончание: " + trail + " одинаковых в конце");
      if (alt >= 4) feats.push("Чередование пар (ABAB)");
      if (maxSeq >= 5) feats.push("Последовательность из " + maxSeq + " цифр");
      if (palin) feats.push("Зеркальный (палиндром)");
      if (tz >= 4) feats.push("Круглый: " + tz + " нулей в конце");
      else if (tz >= 2 && trail < 3) feats.push("Ровное окончание на нули");
      if (distinct <= 2) feats.push("Всего " + distinct + " разные цифры");
      else if (distinct === 3) feats.push("Три разные цифры");
      if (maxFreq >= 4 && maxRun < 4) feats.push("Цифра повторяется " + maxFreq + " раз");
    }
    if (!feats.length) feats.push("Особых закономерностей нет");
    return { verdict: verdict, cls: cls, feats: feats.slice(0, 5), score: score };
  }

  function api(path) {
    return fetch(CFG.API_BASE + path, { headers: { Authorization: CFG.API_TOKEN } }).then(function (r) { return r.ok ? r.json() : null; });
  }
  function flatten(data) {
    var out = [];
    if (data && typeof data === "object") Object.keys(data).forEach(function (k) {
      var v = data[k]; if (v && Array.isArray(v.items)) v.items.forEach(function (p) { if (p && p.phone != null) { p._cat = k; out.push(p); } });
    });
    return out;
  }
  var CAT_BADGE = { brilliant: "Бриллиант", brilliant_super: "Бриллиант", platinum: "Платина", platinum_lite: "Платина", gold: "Золото", silver: "Серебро", bronze: "Бронза" };
  function catBadge(c) { return c ? (CAT_BADGE[String(c).split(",")[0].trim()] || "") : ""; }

  function render(d) {
    var a = analyze(d);
    var chips = a.feats.map(function (f) { return '<span class="chk-chip">' + esc(f) + "</span>"; }).join("");
    out.innerHTML =
      '<div class="chk-card">' +
        '<div class="chk-phone">' + esc(fmtPhone(d)) + "</div>" +
        '<div class="chk-verdict ' + a.cls + '">' + esc(a.verdict) + '<span class="chk-score">оценка ' + a.score + "</span></div>" +
        '<div class="chk-chips">' + chips + "</div>" +
        '<div class="chk-avail" id="chkAvail">Проверяю наличие в каталоге…</div>' +
      "</div>";
    // наличие в каталоге красивых номеров
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=" + d)
      .then(function (data) {
        var list = flatten(data || {}), m = null;
        list.forEach(function (p) { if (digitsOf(p.phone) === d) m = p; });
        var el = document.getElementById("chkAvail");
        if (!el) return;
        if (m) {
          var t = m.tariff || {}, b = catBadge(m._cat);
          el.innerHTML = '✅ Есть в каталоге MagzGold' + (b ? " · <b>" + esc(b) + "</b>" : "") +
            (t.price != null ? " · тариф " + esc(fmtMoney(t.price)) + "/мес" : "") +
            ' — <a href="/nomer/?p=' + d + '">открыть и забронировать →</a>';
        } else {
          el.innerHTML = 'В каталоге красивых номеров MagzGold не найден (возможно, обычный номер или уже занят). ' +
            '<a href="/">Подобрать похожий →</a>';
        }
      })
      .catch(function () { var el = document.getElementById("chkAvail"); if (el) el.textContent = ""; });
  }

  function run() {
    var d = digitsOf(input.value);
    if (d.length !== 10) { out.innerHTML = '<p class="chk-err">Введите номер из 10 цифр (после +7).</p>'; return; }
    render(d);
  }
  btn.addEventListener("click", run);
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") run(); });
})();
