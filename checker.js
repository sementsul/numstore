/* MagzGold — проверка «красоты» номера. Свой анализатор паттернов (для любого номера) +
   проверка наличия в каталоге Безлимита (через API в браузере). */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var input = document.getElementById("chkInput");
  var btn = document.getElementById("chkBtn");
  var out = document.getElementById("chkOut");
  if (!input || !btn || !out) return;

  // Снимаем 7/8 ТОЛЬКО у 11-значного (код страны/межгород) → тело 10 цифр. Иначе отдаём как есть,
  // чтобы неверную длину поймал run() и предупредил, а не молча резал последние 10 (напр. 11-значный с 9).
  function digitsOf(s) {
    var r = String(s).replace(/\D/g, "");
    if (r.length === 11 && (r.charAt(0) === "7" || r.charAt(0) === "8")) r = r.slice(1);
    return r;
  }
  function fmtPhone(d) {
    return d.length === 10 ? "+7 " + d.slice(0, 3) + " " + d.slice(3, 6) + "-" + d.slice(6, 8) + "-" + d.slice(8, 10) : "+7 " + d;
  }
  function fmtMoney(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}

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
    // частота цифры весома; палиндром — ДОБАВКА, а не потолок (симметричные бриллиантовые не должны тонуть). Синхронно с beauty.js.
    var repBeauty = 0.40 * rep + 0.30 * runC + 0.30 * freqC;
    var base = Math.max(repBeauty, seqC * 0.8, altC * 0.72);
    return Math.min(1, base + (palin ? 0.16 : 0));
  }

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
    var tailC = Math.min(1, (trail - 1) / 5), round = Math.min(1, tz / 4);
    // красоту меряем по ТЕЛУ (7 цифр после кода) и хвосту-6, а не только по всем 10 — иначе случайный код
    // (напр. 984) разбавляет красивое тело; палиндром тела тоже ловится этими окнами. Синхронно с beauty.js.
    var pat = Math.max(patStrength(d), patStrength(d.slice(3)) * 0.97, patStrength(d.slice(4)) * 0.93);
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
      else if (d.slice(3) === d.slice(3).split("").reverse().join("") || d.slice(4) === d.slice(4).split("").reverse().join("")) feats.push("Зеркальное тело номера");
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
    if (d.length !== 10) {
      out.innerHTML = '<p class="chk-err">Номер должен быть из 10 цифр (можно с 7 или 8 в начале). Вы ввели ' + d.length + ' — проверьте ввод.</p>';
      return;
    }
    render(d);
  }
  btn.addEventListener("click", run);
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") run(); });

  // автозапуск из ?p=<цифры> (кнопка «оценить» на карточке номера)
  var pm = /[?&]p=(\d+)/.exec(location.search);
  if (pm) {
    var pd = digitsOf(pm[1]);
    if (pd.length === 10) {
      input.value = pd.slice(0, 3) + " " + pd.slice(3, 6) + "-" + pd.slice(6, 8) + "-" + pd.slice(8, 10);
      render(pd);
    }
  }
})();
