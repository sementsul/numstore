/* numstore — клиентская витрина номеров Безлимит.
   Каталог/поиск тянутся в браузере посетителя напрямую из API (CORS открыт) — ban-proof. */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var $ = function (id) { return document.getElementById(id); };
  var statusEl = $("status"), gridEl = $("grid"), countEl = $("count");
  var tariffEl = $("tariff"), sortEl = $("sort");
  var cubesEl = $("cubes"), findBtn = $("find"), resetBtn = $("reset");
  var refBar = $("refBar"), refLink = $("refLink"), copyBtn = $("copyLink"), openStore = $("openStore");

  var CUBES = 10;
  var SHOWN = [];     // текущий показываемый список номеров
  var searchTimer = null;

  /* ---------- утилиты ---------- */
  function fmtPhone(p) {
    var s = String(p).replace(/\D/g, "").slice(-10);
    if (s.length !== 10) return "+7 " + s;
    return "+7 " + s.slice(0, 3) + " " + s.slice(3, 6) + "-" + s.slice(6, 8) + "-" + s.slice(8, 10);
  }
  function fmtMoney(n) {
    if (n == null || isNaN(n)) return "";
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽";
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  function plural(n, forms) {
    var n10 = n % 10, n100 = n % 100;
    if (n10 === 1 && n100 !== 11) return forms[0];
    if (n10 >= 2 && n10 <= 4 && (n100 < 10 || n100 >= 20)) return forms[1];
    return forms[2];
  }

  function api(path) {
    return fetch(CFG.API_BASE + path, { headers: { Authorization: CFG.API_TOKEN } })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
  }

  /* Гибкий разбор ответа: находит объекты-номера в ЛЮБОЙ структуре (плоский/сгруппированный). */
  function extractPhones(data) {
    var out = [];
    (function walk(x) {
      if (!x || typeof x !== "object") return;
      if (Array.isArray(x)) { x.forEach(walk); return; }
      if (x.phone != null && (x.tariff || x.type != null || x.type_category)) out.push(x);
      Object.keys(x).forEach(function (k) {
        if (k === "tariff" || k === "region") return; // не спускаемся в под-объекты номера
        var v = x[k];
        if (v && typeof v === "object") walk(v);
      });
    })(data);
    var seen = {};
    return out.filter(function (p) { if (seen[p.phone]) return false; seen[p.phone] = true; return true; });
  }

  /* ---------- маска (cubes) ---------- */
  function buildCubes() {
    var cells = cubesEl.querySelectorAll("input");
    var mask = "";
    for (var i = 0; i < cells.length; i++) {
      var v = (cells[i].value || "").trim();
      mask += v === "" ? "N" : v;
    }
    return mask;
  }
  function isEmptyMask(mask) { return /^N{10}$/i.test(mask); }

  function updateRefLink() {
    var mask = buildCubes();
    if (isEmptyMask(mask)) { refBar.hidden = true; return; }
    var url = CFG.REF_STORE_URL + "?type=p&cubes=" + encodeURIComponent(mask);
    refLink.value = url;
    openStore.href = url;
    refBar.hidden = false;
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
      if (t.value && t.nextElementSibling && t.nextElementSibling.tagName === "INPUT") {
        t.nextElementSibling.focus();
      }
      updateRefLink();
    });
    cubesEl.addEventListener("keydown", function (e) {
      if (e.key === "Backspace" && !e.target.value && e.target.previousElementSibling &&
          e.target.previousElementSibling.tagName === "INPUT") {
        e.target.previousElementSibling.focus();
      }
    });
  }

  /* ---------- загрузка ---------- */
  function showLoading(msg) { statusEl.textContent = msg; statusEl.style.display = ""; }

  function loadDefault() {
    showLoading("Загружаю номера…");
    api("/super-link/phones/collection?expand=phones.tariff")
      .then(function (data) { setResult(extractPhones(data)); })
      .catch(function (e) { showLoading("Не удалось загрузить номера (" + e.message + "). Обнови страницу."); });
  }

  function search() {
    var mask = buildCubes();
    if (isEmptyMask(mask)) { loadDefault(); return; }
    showLoading("Ищу номера по маске…");
    var p = "/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=60&cubes=" + encodeURIComponent(mask);
    api(p)
      .then(function (data) {
        var list = extractPhones(data);
        if (!list.length) showLoading("По маске ничего не нашлось. Измени позиции.");
        else setResult(list);
      })
      .catch(function (e) { showLoading("Ошибка поиска (" + e.message + ")."); });
  }

  function setResult(list) {
    SHOWN = list;
    if (!list.length) { showLoading("Номера не найдены."); gridEl.innerHTML = ""; return; }
    statusEl.style.display = "none";
    buildTariffOptions(list);
    render();
  }

  function buildTariffOptions(list) {
    var cur = tariffEl.value, seen = {};
    list.forEach(function (p) { var t = p.tariff && p.tariff.name; if (t) seen[t] = true; });
    tariffEl.innerHTML = '<option value="">Все тарифы</option>';
    Object.keys(seen).sort().forEach(function (name) {
      var o = document.createElement("option"); o.value = name; o.textContent = name;
      if (name === cur) o.selected = true;
      tariffEl.appendChild(o);
    });
  }

  function viewList() {
    var tf = tariffEl.value;
    var list = SHOWN.filter(function (p) { return !tf || (p.tariff && p.tariff.name === tf); });
    var s = sortEl.value;
    if (s === "price-asc" || s === "price-desc") {
      list = list.slice().sort(function (a, b) {
        var pa = (a.tariff && a.tariff.price) || 0, pb = (b.tariff && b.tariff.price) || 0;
        return s === "price-asc" ? pa - pb : pb - pa;
      });
    }
    return list;
  }

  function render() {
    var list = viewList();
    countEl.textContent = list.length + " " + plural(list.length, ["номер", "номера", "номеров"]);
    gridEl.innerHTML = list.map(card).join("");
  }

  // uuid листинга в объекте номера (ищем строку в формате GUID среди полей).
  function findUuid(p) {
    if (p.uuid) return p.uuid;
    for (var k in p) {
      if (typeof p[k] === "string" && /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-/i.test(p[k])) return p[k];
    }
    return null;
  }
  // Ссылка на КОНКРЕТНЫЙ номер: cubes=<весь номер> (+uuid, если есть). Реф 800848 несёт REF_STORE_URL.
  function numberUrl(p) {
    var d = String(p.phone).replace(/\D/g, "").slice(-10);
    var u = CFG.REF_STORE_URL + "?type=p&cubes=" + d;
    var uuid = findUuid(p);
    if (uuid) u += "&uuid=" + encodeURIComponent(uuid);
    return u;
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
        '<a class="num-buy" href="' + esc(numberUrl(p)) + '" target="_blank" rel="noopener">Купить</a>' +
      "</article>"
    );
  }

  /* ---------- события ---------- */
  findBtn.addEventListener("click", search);
  resetBtn.addEventListener("click", function () {
    cubesEl.querySelectorAll("input").forEach(function (c) { c.value = ""; });
    tariffEl.value = ""; sortEl.value = "default";
    refBar.hidden = true;
    loadDefault();
  });
  cubesEl.addEventListener("input", function () {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(search, 500); // живой поиск с дебаунсом
  });
  copyBtn.addEventListener("click", function () {
    refLink.select();
    try { navigator.clipboard.writeText(refLink.value); } catch (e) { document.execCommand("copy"); }
    copyBtn.textContent = "Скопировано";
    setTimeout(function () { copyBtn.textContent = "Копировать"; }, 1500);
  });
  tariffEl.addEventListener("change", render);
  sortEl.addEventListener("change", render);

  renderCubes();
  loadDefault();
})();
