/* numstore — клиентская витрина номеров Безлимит. Номера сгруппированы по категориям (секции).
   Каталог/поиск тянутся в браузере посетителя напрямую из API (CORS открыт) — ban-proof. */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var $ = function (id) { return document.getElementById(id); };
  var statusEl = $("status"), gridEl = $("grid"), countEl = $("count");
  var tariffEl = $("tariff"), sortEl = $("sort");
  var cubesEl = $("cubes"), findBtn = $("find"), resetBtn = $("reset");
  var refBar = $("refBar"), refLink = $("refLink"), copyBtn = $("copyLink"), openStore = $("openStore");

  var CUBES = 10;
  var GROUPS = [];       // [{name, phones:[...]}] — категории с номерами
  var BY_PHONE = {};     // digits -> объект номера (для брони по клику)
  var searchTimer = null;

  var CAT_LABELS = {
    brilliant: "Бриллиантовые", brilliant_super: "Супер-бриллиантовые",
    gold: "Золотые", silver: "Серебряные", bronze: "Бронзовые",
    standard: "Стандартные", vip: "VIP"
  };
  function labelCat(k) {
    return String(k).split(",").map(function (x) { x = x.trim(); return CAT_LABELS[x] || x; }).join(" · ");
  }

  /* ---------- утилиты ---------- */
  function fmtPhone(p) {
    var s = String(p).replace(/\D/g, "").slice(-10);
    if (s.length !== 10) return "+7 " + s;
    return "+7 " + s.slice(0, 3) + " " + s.slice(3, 6) + "-" + s.slice(6, 8) + "-" + s.slice(8, 10);
  }
  function digitsOf(p) { return String(p).replace(/\D/g, "").slice(-10); }
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
  function api(path, opts) {
    opts = opts || {};
    opts.headers = { Authorization: CFG.API_TOKEN };
    return fetch(CFG.API_BASE + path, opts).then(function (r) {
      if (!r.ok && !opts._softError) throw new Error("HTTP " + r.status);
      return r.json();
    });
  }

  /* Разбор ответа в группы. Коллекции: {items:[{name,phones}]}. Поиск: {cat:{items:[...]}}. */
  function toGroups(data) {
    var groups = [];
    if (data && Array.isArray(data.items)) {
      data.items.forEach(function (c) { groups.push({ name: c.name || "Номера", phones: c.phones || [] }); });
    } else if (data && typeof data === "object") {
      Object.keys(data).forEach(function (k) {
        var v = data[k];
        if (v && Array.isArray(v.items)) groups.push({ name: labelCat(k), phones: v.items });
      });
    }
    if (!groups.length) { var all = deepPhones(data); if (all.length) groups.push({ name: "Номера", phones: all }); }
    return groups.filter(function (g) { return g.phones && g.phones.length; });
  }
  function deepPhones(data) { // запасной глубокий разбор
    var out = [];
    (function walk(x) {
      if (!x || typeof x !== "object") return;
      if (Array.isArray(x)) { x.forEach(walk); return; }
      if (x.phone != null && (x.tariff || x.type != null)) out.push(x);
      Object.keys(x).forEach(function (k) { if (k !== "tariff" && k !== "region") walk(x[k]); });
    })(data);
    return out;
  }

  /* ---------- маска (cubes) ---------- */
  function buildCubes() {
    var cells = cubesEl.querySelectorAll("input"), mask = "";
    for (var i = 0; i < cells.length; i++) { var v = (cells[i].value || "").trim(); mask += v === "" ? "N" : v; }
    return mask;
  }
  function isEmptyMask(mask) { return /^N{10}$/i.test(mask); }
  function updateRefLink() {
    var mask = buildCubes();
    if (isEmptyMask(mask)) { refBar.hidden = true; return; }
    var url = CFG.REF_STORE_URL + "?type=p&cubes=" + encodeURIComponent(mask);
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
  function showStatus(msg) { statusEl.textContent = msg; statusEl.style.display = ""; gridEl.innerHTML = ""; }

  function loadDefault() {
    showStatus("Загружаю номера…");
    api("/super-link/phones/collection?expand=phones.tariff")
      .then(function (d) { setResult(toGroups(d)); })
      .catch(function (e) { showStatus("Не удалось загрузить номера (" + e.message + "). Обнови страницу."); });
  }
  function search() {
    var mask = buildCubes();
    if (isEmptyMask(mask)) { loadDefault(); return; }
    showStatus("Ищу номера по маске…");
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=60&phone_pattern=" + encodeURIComponent(mask))
      .then(function (d) {
        var g = toGroups(d);
        if (!g.length) showStatus("По маске ничего не нашлось. Измени позиции.");
        else setResult(g);
      })
      .catch(function (e) { showStatus("Ошибка поиска (" + e.message + ")."); });
  }

  function setResult(groups) {
    GROUPS = groups;
    BY_PHONE = {};
    var seenTariff = {};
    groups.forEach(function (g) {
      g.phones.forEach(function (p) {
        BY_PHONE[digitsOf(p.phone)] = p;
        var t = p.tariff && p.tariff.name; if (t) seenTariff[t] = true;
      });
    });
    buildTariffOptions(seenTariff);
    render();
  }

  function buildTariffOptions(seen) {
    var cur = tariffEl.value;
    tariffEl.innerHTML = '<option value="">Все тарифы</option>';
    Object.keys(seen).sort().forEach(function (name) {
      var o = document.createElement("option"); o.value = name; o.textContent = name;
      if (name === cur) o.selected = true;
      tariffEl.appendChild(o);
    });
  }

  function filterSort(phones) {
    var tf = tariffEl.value;
    var list = phones.filter(function (p) { return !tf || (p.tariff && p.tariff.name === tf); });
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
    var total = 0, html = "";
    GROUPS.forEach(function (g) {
      var list = filterSort(g.phones);
      if (!list.length) return;
      total += list.length;
      html += '<section class="cat">' +
                '<div class="cat-head"><h2 class="cat-title">' + esc(g.name) + "</h2>" +
                '<span class="cat-count">' + list.length + "</span></div>" +
                '<div class="grid">' + list.map(card).join("") + "</div>" +
              "</section>";
    });
    countEl.textContent = total ? (total + " " + plural(total, ["номер", "номера", "номеров"])) : "";
    if (html) { statusEl.style.display = "none"; gridEl.innerHTML = html; }
    else showStatus("Ничего не найдено.");
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
    tariffEl.value = ""; sortEl.value = "default"; refBar.hidden = true; loadDefault();
  });
  copyBtn.addEventListener("click", function () {
    refLink.select();
    try { navigator.clipboard.writeText(refLink.value); } catch (e) { document.execCommand("copy"); }
    copyBtn.textContent = "Скопировано"; setTimeout(function () { copyBtn.textContent = "Копировать"; }, 1500);
  });
  tariffEl.addEventListener("change", render);
  sortEl.addEventListener("change", render);
  gridEl.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest(".num-buy") : null;
    if (!b) return;
    var p = BY_PHONE[b.getAttribute("data-phone")];
    if (p) reserve(p);
  });

  renderCubes();
  loadDefault();
})();
