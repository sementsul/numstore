/* MagzGold — «Узнать оператора и регион по номеру».
   Лукап по компактной базе Россвязи (dist/data/operators.json): код (3 цифры) + диапазон → оператор/регион.
   Всё в браузере, номер никуда не отправляется. Плюс подтягиваем похожие красивые номера из каталога. */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var input = document.getElementById("opInput");
  var btn = document.getElementById("opBtn");
  var out = document.getElementById("opOut");
  var sim = document.getElementById("opSimilar");
  if (!input || !btn || !out) return;

  var DB = null, dbP = null;
  function digitsOf(s) { return String(s).replace(/\D/g, "").replace(/^7|^8/, "").slice(-10); }
  function fmtPhone(d) { return d.length === 10 ? "+7 " + d.slice(0, 3) + " " + d.slice(3, 6) + "-" + d.slice(6, 8) + "-" + d.slice(8, 10) : "+7 " + d; }
  function money(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function cleanOp(op) { return op.replace(/^(АО|ООО|ПАО|ЗАО|ОАО)\s+/i, "").replace(/[«»"]/g, "").trim(); } // «АО "МТТ"» → МТТ

  function loadDB() {
    if (DB) return Promise.resolve(DB);
    if (dbP) return dbP;
    dbP = fetch("/data/operators.json").then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (j) { DB = j; return j; });
    return dbP;
  }
  function lookup(d) {
    var ranges = DB.codes[d.slice(0, 3)];
    if (!ranges) return null;
    var n = parseInt(d.slice(3), 10);
    for (var i = 0; i < ranges.length; i++) { if (ranges[i][0] <= n && n <= ranges[i][1]) return { op: DB.ops[ranges[i][2]], reg: DB.regs[ranges[i][3]] }; }
    return null;
  }

  function render(d) {
    out.innerHTML = '<p class="chk-loading">Определяю…</p>';
    loadDB().then(function () {
      var r = lookup(d);
      out.innerHTML =
        '<div class="chk-card">' +
          '<div class="chk-phone">' + esc(fmtPhone(d)) + "</div>" +
          (r
            ? '<div class="op-row"><span>Оператор</span><b>' + esc(cleanOp(r.op)) + "</b></div>" +
              '<div class="op-row"><span>Регион</span><b>' + esc(r.reg) + "</b></div>"
            : '<p class="op-none">Не удалось определить — проверьте, что номер введён верно (10 цифр после +7).</p>') +
          '<p class="op-note">По плану нумерации Россвязи — это <b>место выдачи</b> номера. При переносе (MNP) ' +
          "фактический оператор мог смениться.</p>" +
        "</div>";
    }).catch(function () { out.innerHTML = '<p class="chk-err">Не удалось загрузить базу операторов. Обновите страницу.</p>'; });
    loadSimilar(d);
  }

  function loadSimilar(d) {
    if (!sim || !CFG) return;
    sim.hidden = true; sim.innerHTML = "";
    var mask = "NNNNNN" + d.slice(6); // фиксируем окончание (последние 4 цифры), остальное любое
    fetch(CFG.API_BASE + "/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=" + mask,
          { headers: { Authorization: CFG.API_TOKEN } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        if (!data || typeof data !== "object") return;
        var items = [];
        Object.keys(data).forEach(function (k) {
          var v = data[k];
          if (v && Array.isArray(v.items)) v.items.forEach(function (p) { var dd = digitsOf(p.phone); if (dd.length === 10 && dd !== d) items.push(p); });
        });
        items = items.slice(0, 8);
        if (!items.length) return;
        sim.innerHTML = "<h3>Похожие красивые номера в каталоге</h3>" + items.map(function (p) {
          var dd = digitsOf(p.phone), t = p.tariff || {};
          return '<a class="sim-item" href="/nomer/?p=' + dd + '"><span class="sim-phone">' + esc(fmtPhone(dd)) + "</span>" +
            (t.price != null ? '<span class="sim-price">тариф ' + esc(money(t.price)) + "</span>" : "") + "</a>";
        }).join("");
        sim.hidden = false;
      })
      .catch(function () {});
  }

  function run() {
    var d = digitsOf(input.value);
    if (d.length !== 10) { out.innerHTML = '<p class="chk-err">Введите номер из 10 цифр (после +7).</p>'; return; }
    render(d);
  }
  btn.addEventListener("click", run);
  input.addEventListener("keydown", function (e) { if (e.key === "Enter") run(); });

  // автозапуск из ?p=<цифры>
  var pm = /[?&]p=(\d+)/.exec(location.search);
  if (pm) {
    var pd = digitsOf(pm[1]);
    if (pd.length === 10) { input.value = pd.slice(0, 3) + " " + pd.slice(3, 6) + "-" + pd.slice(6, 8) + "-" + pd.slice(8, 10); render(pd); }
  }
})();
