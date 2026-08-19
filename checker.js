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
    var feats = [], score = 0;
    function add(label, w) { feats.push(label); score += w; }

    if (/^(\d)\1{9}$/.test(d)) add("Все цифры одинаковые", 12);

    // максимальная серия одинаковых подряд
    var run = 1, maxRun = 1;
    for (var i = 1; i < d.length; i++) { if (d[i] === d[i - 1]) { run++; maxRun = Math.max(maxRun, run); } else run = 1; }
    if (maxRun >= 6) add(maxRun + " одинаковых подряд", 9);
    else if (maxRun === 5) add("Пять одинаковых подряд", 7);
    else if (maxRun === 4) add("Четыре одинаковых подряд", 5);
    else if (maxRun === 3) add("Тройка одинаковых", 3);

    // палиндром (зеркальный)
    if (d === d.split("").reverse().join("")) add("Зеркальный (палиндром)", 8);

    // нули на конце
    var z = d.match(/0+$/);
    if (z) { var n = z[0].length; if (n >= 4) add("Круглый: " + n + " нулей в конце", 7); else if (n >= 2) add("Ровное окончание на " + n + " нуля", 3); }

    // повторяющиеся пары в хвосте: ..ABAB или пары XX-XX-XX
    if (/(\d)\1(\d)\2(\d)\3$/.test(d)) add("Три пары в конце", 6);
    else if (/(\d\d)\1$/.test(d)) add("Повтор пары в конце", 4);
    if (/^(\d\d)(\d\d)(\d\d)(\d\d)(\d\d)$/.test(d) && d[0]===d[2]&&d[2]===d[4]&&d[1]===d[3]&&d[3]===d[5]) add("Ритм пар ABAB", 5);

    // последовательность (возр/убыв) длиной >=4
    function seqRun(step) { var r=1,m=1; for(var i=1;i<d.length;i++){ if((+d[i]-+d[i-1])===step){r++;m=Math.max(m,r);}else r=1;} return m; }
    var up = seqRun(1), dn = seqRun(-1);
    if (up >= 4) add("Возрастающая последовательность", 4);
    if (dn >= 4) add("Убывающая последовательность", 4);

    // две тройки (AAA BBB)
    if (/(\d)\1\1.*(\d)\2\2/.test(d)) add("Несколько троек", 4);

    // мало разных цифр
    var uniq = {}; for (var k = 0; k < d.length; k++) uniq[d[k]] = 1;
    var nu = Object.keys(uniq).length;
    if (nu <= 2) add("Всего " + nu + " разные цифры", 5);
    else if (nu === 3) add("Три разные цифры", 2);

    var verdict, cls;
    if (score >= 13) { verdict = "Премиальный · редкий"; cls = "v-top"; }
    else if (score >= 8) { verdict = "Красивый"; cls = "v-nice"; }
    else if (score >= 4) { verdict = "Приятный"; cls = "v-ok"; }
    else { verdict = "Обычный номер"; cls = "v-plain"; }
    if (!feats.length) feats.push("Особых закономерностей не найдено");
    return { verdict: verdict, cls: cls, feats: feats, score: score };
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
