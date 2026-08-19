/* numstore — витрина номеров Безлимит: маркетплейс с серверными фильтрами (категория/тариф → запрос к API).
   Каталог/поиск тянутся в браузере посетителя напрямую из API (CORS открыт) — ban-proof. */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var $ = function (id) { return document.getElementById(id); };
  var statusEl = $("status"), gridEl = $("grid"), countEl = $("count"), moreBtn = $("more");
  var sortEl = $("sort");
  var cubesEl = $("cubes"), findBtn = $("find"), resetBtn = $("reset");
  var refBar = $("refBar"), refLink = $("refLink"), copyBtn = $("copyLink"), openStore = $("openStore");
  var fCat = $("fCat"), fPrice = $("fPrice"), fTariff = $("fTariff");

  var CUBES = 10, PAGE = 60, DEFAULT_MASK = "9NNNNNNNNN";
  var ALL = [], BY_PHONE = {}, shown = PAGE, searchTimer = null;
  var CATS = [], TARIFFS = [];
  var flt = { cat: null, tariff: null, price: null }; // cat=код mask_categories, tariff=id mask_tariff, price=тир (клиент)

  // Избранное (localStorage): digits -> {phone, tariff}
  var FAV = {}, favMode = false;
  try { FAV = JSON.parse(localStorage.getItem("magz_fav") || "{}") || {}; } catch (e) { FAV = {}; }
  function saveFav() { try { localStorage.setItem("magz_fav", JSON.stringify(FAV)); } catch (e) {} }
  function favCountUpd() {
    var n = Object.keys(FAV).length, el = document.getElementById("favCount");
    if (el) el.textContent = n ? "(" + n + ")" : "";
  }
  function toggleFav(p) {
    var d = digitsOf(p.phone);
    if (FAV[d]) delete FAV[d]; else FAV[d] = { phone: p.phone, tariff: p.tariff };
    saveFav(); favCountUpd();
    if (favMode) render(); else {
      var btn = gridEl.querySelector('.fav[data-fav="' + d + '"]');
      if (btn) btn.classList.toggle("on", !!FAV[d]);
    }
  }
  var CAT_BADGE = { brilliant: "Бриллиант", brilliant_super: "Бриллиант", platinum: "Платина",
    platinum_lite: "Платина", gold: "Золото", silver: "Серебро", bronze: "Бронза" };
  function catBadge(cat) {
    if (!cat) return "";
    var key = String(cat).split(",")[0].trim();
    return CAT_BADGE[key] || "";
  }

  var PRICE_TIERS = [
    { key: "lo", label: "до 1 000 ₽", test: function (v) { return v < 1000; } },
    { key: "mid", label: "1 000 – 3 000 ₽", test: function (v) { return v >= 1000 && v <= 3000; } },
    { key: "hi", label: "свыше 3 000 ₽", test: function (v) { return v > 3000; } }
  ];

  /* ---------- утилиты ---------- */
  function fmtPhone(p) {
    var s = String(p).replace(/\D/g, "").slice(-10);
    if (s.length !== 10) return "+7 " + s;
    return "+7 " + s.slice(0, 3) + " " + s.slice(3, 6) + "-" + s.slice(6, 8) + "-" + s.slice(8, 10);
  }
  function digitsOf(p) { return String(p).replace(/\D/g, "").slice(-10); }
  function fmtMoney(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function plural(n, f) {
    var a = n % 10, b = n % 100;
    if (a === 1 && b !== 11) return f[0];
    if (a >= 2 && a <= 4 && (b < 10 || b >= 20)) return f[1];
    return f[2];
  }
  function api(path) {
    return fetch(CFG.API_BASE + path, { headers: { Authorization: CFG.API_TOKEN } })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
  }
  function flatten(data) {
    var out = [];
    function add(list, cat) { (list || []).forEach(function (p) { if (p && p.phone != null) { p._cat = cat; out.push(p); } }); }
    if (data && Array.isArray(data.items)) data.items.forEach(function (c) { add(c.phones, c.name || ""); });
    else if (data && typeof data === "object") Object.keys(data).forEach(function (k) { var v = data[k]; if (v && Array.isArray(v.items)) add(v.items, k); });
    var seen = {}, res = [];
    out.forEach(function (p) { var d = digitsOf(p.phone); if (!seen[d]) { seen[d] = 1; res.push(p); } });
    return res;
  }

  /* ---------- маска ---------- */
  function buildCubes() {
    var cells = cubesEl.querySelectorAll("input"), m = "";
    for (var i = 0; i < cells.length; i++) { var v = (cells[i].value || "").trim(); m += v === "" ? "N" : v; }
    return m;
  }
  function isEmptyMask(m) { return /^N{10}$/i.test(m); }
  function setCubes(mask) { // пресет маски для паттерн-страниц (window.PAGE.mask)
    var cells = cubesEl.querySelectorAll("input");
    for (var i = 0; i < cells.length; i++) {
      var ch = (mask && mask[i]) || "";
      cells[i].value = (ch === "N" || ch === "n" || ch === "") ? "" : ch;
    }
    updateRefLink();
  }
  function updateRefLink() {
    var m = buildCubes();
    if (isEmptyMask(m)) { refBar.hidden = true; return; }
    var url = CFG.REF_STORE_URL + "?type=p&cubes=" + encodeURIComponent(m);
    refLink.value = url; openStore.href = url; refBar.hidden = false;
  }
  function renderCubes() {
    for (var i = 0; i < CUBES; i++) {
      var inp = document.createElement("input");
      inp.className = "cube"; inp.maxLength = 1; inp.autocomplete = "off";
      inp.setAttribute("aria-label", "Позиция " + (i + 1));
      cubesEl.appendChild(inp);
    }
    cubesEl.addEventListener("input", function (e) {
      var t = e.target;
      if (t.value && t.nextElementSibling && t.nextElementSibling.tagName === "INPUT") t.nextElementSibling.focus();
      updateRefLink();
      clearTimeout(searchTimer); searchTimer = setTimeout(fetchNumbers, 500);
    });
    cubesEl.addEventListener("keydown", function (e) {
      if (e.key === "Backspace" && !e.target.value && e.target.previousElementSibling &&
          e.target.previousElementSibling.tagName === "INPUT") e.target.previousElementSibling.focus();
    });
  }

  /* ---------- сайдбар (официальные списки из /filters) ---------- */
  function loadFilters() {
    api("/super-link/phones/filters")
      .then(function (d) { CATS = d.mask_category || []; TARIFFS = d.mask_tariff || []; buildSidebar(); })
      .catch(function () { buildSidebar(); }); // без списков — только цена/дефолт
  }
  function buildSidebar() {
    fillList(fCat, [{ v: null, t: "Все категории" }].concat(CATS.map(function (c) { return { v: c.filter, t: c.name }; })), "cat", true);
    fillList(fPrice, [{ v: null, t: "Любая" }].concat(PRICE_TIERS.map(function (t) { return { v: t.key, t: t.label }; })), "price", false);
  }
  // Тарифы — ТОЛЬКО те, по которым есть номера в загруженном пуле (в /filters есть мёртвые). Сортировка по цене.
  function buildTariffFilter() {
    var m = {};
    ALL.forEach(function (p) { var t = p.tariff; if (t && t.id != null && !m[t.id]) m[t.id] = { id: t.id, name: t.name, price: t.price || 0 }; });
    var list = Object.keys(m).map(function (k) { return m[k]; }).sort(function (a, b) { return a.price - b.price; });
    if (flt.tariff && !m[flt.tariff]) flt.tariff = null; // выбранный тариф исчез из выдачи
    fillList(fTariff, [{ v: null, t: "Все тарифы" }].concat(list.map(function (t) { return { v: t.id, t: t.name }; })), "tariff", false);
  }
  function fillList(ul, items, key, refetch) {
    ul.innerHTML = "";
    items.forEach(function (it) {
      var li = document.createElement("li");
      li.className = "filter-item" + (flt[key] === it.v ? " active" : "");
      li.textContent = it.t;
      li.addEventListener("click", function () {
        flt[key] = it.v; shown = PAGE;
        ul.querySelectorAll(".filter-item").forEach(function (x) { x.classList.remove("active"); });
        li.classList.add("active");
        if (refetch) fetchNumbers(); else render();
      });
      ul.appendChild(li);
    });
  }

  /* ---------- загрузка номеров (категория/тариф/маска → серверный запрос) ---------- */
  function showStatus(m) { statusEl.textContent = m; statusEl.style.display = ""; gridEl.innerHTML = ""; moreBtn.hidden = true; }

  function fetchNumbers() {
    showStatus("Загружаю номера…");
    var mask = buildCubes();
    var q = ["expand=tariff", "is_reserved=false", "per_page=100"];
    q.push("phone_pattern=" + encodeURIComponent(isEmptyMask(mask) ? DEFAULT_MASK : mask));
    if (flt.cat) q.push("mask_categories=" + encodeURIComponent(flt.cat));
    // тариф API на mask-category не фильтрует (проверено) → фильтруем на клиенте в matchesClient
    api("/super-link/phones/mask-category?" + q.join("&"))
      .then(function (d) {
        var f = flatten(d);
        ALL = f; BY_PHONE = {};
        f.forEach(function (p) { BY_PHONE[digitsOf(p.phone)] = p; });
        buildTariffFilter(); // список тарифов из фактических номеров
        render();
      })
      .catch(function (e) { showStatus("Ошибка загрузки (" + e.message + ")."); });
  }

  function matchesClient(p) {
    if (flt.tariff && !(p.tariff && p.tariff.id === flt.tariff)) return false; // тариф — клиентский фильтр
    if (flt.price) {
      var tr = PRICE_TIERS.filter(function (t) { return t.key === flt.price; })[0];
      var pr = p.tariff && p.tariff.price;
      if (!(tr && pr != null && tr.test(pr))) return false;
    }
    return true;
  }
  function sorted(list) {
    var s = sortEl.value;
    if (s === "price-asc" || s === "price-desc") {
      return list.slice().sort(function (a, b) {
        var pa = (a.tariff && a.tariff.price) || 0, pb = (b.tariff && b.tariff.price) || 0;
        return s === "price-asc" ? pa - pb : pb - pa;
      });
    }
    return list;
  }
  function render() {
    var base = favMode ? Object.keys(FAV).map(function (k) { return FAV[k]; }) : ALL;
    var list = sorted(base.filter(matchesClient));
    countEl.textContent = list.length + " " + plural(list.length, ["номер", "номера", "номеров"]);
    if (!list.length) { showStatus(favMode ? "В избранном пусто. Добавьте номера ♥." : "Ничего не найдено. Смягчи фильтры."); return; }
    statusEl.style.display = "none";
    gridEl.innerHTML = list.slice(0, shown).map(card).join("");
    moreBtn.hidden = list.length <= shown;
  }

  function card(p) {
    var t = p.tariff || {}, d = digitsOf(p.phone), badge = catBadge(p._cat);
    var specs = [];
    if (t.minutes != null) specs.push(t.minutes + " мин");
    if (t.sms != null) specs.push(t.sms + " смс");
    if (t.internet != null) specs.push(t.internet + " ГБ");
    return (
      '<article class="num">' +
        '<button class="fav' + (FAV[d] ? " on" : "") + '" data-fav="' + esc(d) + '" aria-label="В избранное" type="button">♥</button>' +
        (badge ? '<span class="num-badge">' + esc(badge) + "</span>" : "") +
        '<div class="num-phone">' + esc(fmtPhone(p.phone)) + "</div>" +
        (t.name ? '<div class="num-tariff">' + esc(t.name) + "</div>" : "") +
        (specs.length ? '<div class="num-specs">' + esc(specs.join(" · ")) + "</div>" : "") +
        (t.price != null ? '<div class="num-price">' + esc(fmtMoney(t.price)) + "<span>/мес</span></div>" : "") +
        '<button class="num-buy" data-phone="' + esc(digitsOf(p.phone)) + '">Забронировать</button>' +
      "</article>"
    );
  }

  /* ---------- бронь ---------- */
  function deepUuid(o) {
    if (!o || typeof o !== "object") return null;
    if (o.super_link_uuid && o.super_link_uuid.uuid) return o.super_link_uuid.uuid;
    for (var k in o) {
      var v = o[k];
      if (typeof v === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-/i.test(v)) return v;
      if (v && typeof v === "object") { var r = deepUuid(v); if (r) return r; }
    }
    return null;
  }
  function reserve(p) {
    var tariffId = p.tariff && p.tariff.id, digits = digitsOf(p.phone);
    if (!tariffId) { alert("У номера не указан тариф — бронь недоступна."); return; }
    if (!confirm("Забронировать номер " + fmtPhone(p.phone) + "?\nБронь держится ~1 час.")) return;
    var w = window.open("", "_blank");
    var fd = new FormData();
    fd.append("phone", digits); fd.append("tariff_id", tariffId);
    fd.append("type", "store"); fd.append("user_id", CFG.REF_ID); fd.append("filter", "professional");
    fetch(CFG.API_BASE + "/super-link/reservations?expand=super_link_uuid",
          { method: "POST", headers: { Authorization: CFG.API_TOKEN }, body: fd })
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var uuid = deepUuid(d);
        if (!uuid) { if (w) w.close(); alert("Не удалось забронировать: " + ((d && d.message) || "нет сессии") + "."); return; }
        var url = CFG.REF_STORE_URL + "?type=p&cubes=" + digits + "&uuid=" + encodeURIComponent(uuid);
        if (w) w.location = url; else window.open(url, "_blank", "noopener");
      })
      .catch(function (e) { if (w) w.close(); alert("Ошибка брони: " + e.message); });
  }

  /* ---------- события ---------- */
  findBtn.addEventListener("click", fetchNumbers);
  resetBtn.addEventListener("click", function () {
    cubesEl.querySelectorAll("input").forEach(function (c) { c.value = ""; });
    sortEl.value = "default"; refBar.hidden = true;
    flt = { cat: null, tariff: null, price: null };
    buildSidebar(); fetchNumbers();
  });
  copyBtn.addEventListener("click", function () {
    refLink.select();
    try { navigator.clipboard.writeText(refLink.value); } catch (e) { document.execCommand("copy"); }
    copyBtn.textContent = "Скопировано"; setTimeout(function () { copyBtn.textContent = "Копировать"; }, 1500);
  });
  sortEl.addEventListener("change", function () { shown = PAGE; render(); });
  moreBtn.addEventListener("click", function () { shown += PAGE; render(); });
  gridEl.addEventListener("click", function (e) {
    if (!e.target.closest) return;
    var fav = e.target.closest(".fav");
    if (fav) { var d = fav.getAttribute("data-fav"); var pf = BY_PHONE[d] || FAV[d]; if (pf) toggleFav(pf); return; }
    var b = e.target.closest(".num-buy");
    if (b) { var d2 = b.getAttribute("data-phone"), pb = BY_PHONE[d2] || FAV[d2]; if (pb) reserve(pb); }
  });
  var favBtn = document.getElementById("favToggle");
  if (favBtn) favBtn.addEventListener("click", function () {
    favMode = !favMode; favBtn.classList.toggle("on", favMode); shown = PAGE; render();
  });
  favCountUpd();

  // Пресет страницы (категорийные SEO-страницы задают window.PAGE = {cat:"<код>"}).
  var PAGE = window.PAGE || {};
  if (PAGE.cat) flt.cat = PAGE.cat;
  if (PAGE.tariff) flt.tariff = PAGE.tariff; // тарифные страницы задают тариф (клиентский фильтр)

  renderCubes();
  if (PAGE.mask) setCubes(PAGE.mask); // паттерн-страницы задают маску
  loadFilters();
  fetchNumbers();
})();
