/* numstore — витрина номеров Безлимит: маркетплейс (сайдбар-фильтры + густая сетка).
   Каталог/поиск тянутся в браузере посетителя напрямую из API (CORS открыт) — ban-proof. */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var $ = function (id) { return document.getElementById(id); };
  var statusEl = $("status"), gridEl = $("grid"), countEl = $("count"), moreBtn = $("more");
  var sortEl = $("sort");
  var cubesEl = $("cubes"), findBtn = $("find"), resetBtn = $("reset");
  var refBar = $("refBar"), refLink = $("refLink"), copyBtn = $("copyLink"), openStore = $("openStore");
  var fCat = $("fCat"), fPrice = $("fPrice"), fTariff = $("fTariff");

  var CUBES = 10, PAGE = 60;
  var ALL = [];          // плоский список номеров (у каждого ._cat)
  var BY_PHONE = {};     // digits -> объект номера
  var shown = PAGE;      // сколько карточек показано
  var searchTimer = null;
  var flt = { cat: null, price: null, tariff: null };

  var CAT_LABELS = {
    brilliant: "Бриллиантовые", brilliant_super: "Супер-бриллиантовые",
    gold: "Золотые", silver: "Серебряные", bronze: "Бронзовые", standard: "Стандартные", vip: "VIP"
  };
  function labelCat(k) {
    return String(k).split(",").map(function (x) { x = x.trim(); return CAT_LABELS[x] || x; }).join(" · ");
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

  /* Разбор ответа → плоский список, каждому номеру проставляем ._cat (категория/коллекция). */
  function flatten(data) {
    var out = [];
    function add(list, cat) { (list || []).forEach(function (p) { if (p && p.phone != null) { p._cat = cat; out.push(p); } }); }
    if (data && Array.isArray(data.items)) {
      data.items.forEach(function (c) { add(c.phones, c.name || "Номера"); });
    } else if (data && typeof data === "object") {
      Object.keys(data).forEach(function (k) { var v = data[k]; if (v && Array.isArray(v.items)) add(v.items, labelCat(k)); });
    }
    // дедуп по номеру
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
      clearTimeout(searchTimer); searchTimer = setTimeout(search, 500);
    });
    cubesEl.addEventListener("keydown", function (e) {
      if (e.key === "Backspace" && !e.target.value && e.target.previousElementSibling &&
          e.target.previousElementSibling.tagName === "INPUT") e.target.previousElementSibling.focus();
    });
  }

  /* ---------- загрузка ---------- */
  function showStatus(m) { statusEl.textContent = m; statusEl.style.display = ""; gridEl.innerHTML = ""; moreBtn.hidden = true; }

  function loadDefault() {
    showStatus("Загружаю номера…");
    // широкий пул: все мобильные (маска 9 + любые) — густой каталог, а не мелкие коллекции
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=9NNNNNNNNN")
      .then(function (d) { setData(flatten(d)); })
      .catch(function (e) { showStatus("Не удалось загрузить номера (" + e.message + "). Обнови страницу."); });
  }
  function search() {
    var m = buildCubes();
    if (isEmptyMask(m)) { loadDefault(); return; }
    showStatus("Ищу номера по маске…");
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=" + encodeURIComponent(m))
      .then(function (d) { var f = flatten(d); if (!f.length) showStatus("По маске ничего не нашлось. Измени позиции."); else setData(f); })
      .catch(function (e) { showStatus("Ошибка поиска (" + e.message + ")."); });
  }

  function setData(list) {
    ALL = list; BY_PHONE = {};
    list.forEach(function (p) { BY_PHONE[digitsOf(p.phone)] = p; });
    flt = { cat: null, price: null, tariff: null };
    buildFilters();
    shown = PAGE;
    render();
  }

  /* ---------- фильтры (сайдбар) ---------- */
  function uniq(arr) { var s = {}, r = []; arr.forEach(function (x) { if (x && !s[x]) { s[x] = 1; r.push(x); } }); return r; }

  function buildFilters() {
    // Категория
    var cats = uniq(ALL.map(function (p) { return p._cat; })).sort();
    fillList(fCat, [{ v: null, t: "Все категории" }].concat(cats.map(function (c) { return { v: c, t: c }; })), "cat");
    // Цена (только тиры, где есть номера)
    var tiers = PRICE_TIERS.filter(function (tr) {
      return ALL.some(function (p) { var pr = p.tariff && p.tariff.price; return pr != null && tr.test(pr); });
    });
    fillList(fPrice, [{ v: null, t: "Любая" }].concat(tiers.map(function (tr) { return { v: tr.key, t: tr.label }; })), "price");
    // Тариф
    var tars = uniq(ALL.map(function (p) { return p.tariff && p.tariff.name; })).sort();
    fillList(fTariff, [{ v: null, t: "Все тарифы" }].concat(tars.map(function (n) { return { v: n, t: n }; })), "tariff");
  }
  function fillList(ul, items, key) {
    ul.innerHTML = "";
    items.forEach(function (it) {
      var li = document.createElement("li");
      li.className = "filter-item" + (flt[key] === it.v ? " active" : "");
      li.textContent = it.t;
      li.addEventListener("click", function () {
        flt[key] = it.v; shown = PAGE;
        // подсветка
        ul.querySelectorAll(".filter-item").forEach(function (x) { x.classList.remove("active"); });
        li.classList.add("active");
        render();
      });
      ul.appendChild(li);
    });
  }

  function matches(p) {
    if (flt.cat && p._cat !== flt.cat) return false;
    if (flt.tariff && !(p.tariff && p.tariff.name === flt.tariff)) return false;
    if (flt.price) {
      var tr = PRICE_TIERS.filter(function (t) { return t.key === flt.price; })[0];
      var pr = p.tariff && p.tariff.price;
      if (!tr || pr == null || !tr.test(pr)) return false;
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
    var list = sorted(ALL.filter(matches));
    countEl.textContent = list.length + " " + plural(list.length, ["номер", "номера", "номеров"]);
    if (!list.length) { showStatus("Ничего не найдено. Смягчи фильтры."); return; }
    statusEl.style.display = "none";
    var page = list.slice(0, shown);
    gridEl.innerHTML = page.map(card).join("");
    moreBtn.hidden = list.length <= shown;
  }

  function card(p) {
    var t = p.tariff || {};
    var specs = [];
    if (t.minutes != null) specs.push(t.minutes + " мин");
    if (t.sms != null) specs.push(t.sms + " смс");
    if (t.internet != null) specs.push(t.internet + " ГБ");
    return (
      '<article class="num">' +
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
  findBtn.addEventListener("click", search);
  resetBtn.addEventListener("click", function () {
    cubesEl.querySelectorAll("input").forEach(function (c) { c.value = ""; });
    sortEl.value = "default"; refBar.hidden = true; loadDefault();
  });
  copyBtn.addEventListener("click", function () {
    refLink.select();
    try { navigator.clipboard.writeText(refLink.value); } catch (e) { document.execCommand("copy"); }
    copyBtn.textContent = "Скопировано"; setTimeout(function () { copyBtn.textContent = "Копировать"; }, 1500);
  });
  sortEl.addEventListener("change", function () { shown = PAGE; render(); });
  moreBtn.addEventListener("click", function () { shown += PAGE; render(); });
  gridEl.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest(".num-buy") : null;
    if (!b) return;
    var p = BY_PHONE[b.getAttribute("data-phone")];
    if (p) reserve(p);
  });

  renderCubes();
  loadDefault();
})();
