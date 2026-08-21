/* numstore — витрина номеров Безлимит: маркетплейс с серверными фильтрами (категория/тариф → запрос к API).
   Каталог/поиск тянутся в браузере посетителя напрямую из API (CORS открыт) — ban-proof. */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var $ = function (id) { return document.getElementById(id); };
  var statusEl = $("status"), gridEl = $("grid"), countEl = $("count"), moreBtn = $("more");
  var sortEl = $("sort");
  var cubesEl = $("cubes"), findBtn = $("find"), resetBtn = $("reset");
  var fCat = $("fCat"), fPrice = $("fPrice"), fTariff = $("fTariff"), fCode = $("fCode");

  var CUBES = 10, PAGE = 60, DEFAULT_MASK = "9NNNNNNNNN";
  var ALL = [], BY_PHONE = {}, shown = PAGE, searchTimer = null;
  // Региональные тарифы (Анадырь/Норильск) выглядят стрёмно и не для широкой продажи — прячем такие номера.
  var BAD_TARIFF = /Анадыр|Норильск/i;
  function okTariff(p) { return !(p && p.tariff && p.tariff.name && BAD_TARIFF.test(p.tariff.name)); }
  var CATS = [], TARIFFS = [], TREND = {}; // TREND[метка категории] = {pct, arrow} — из истории цен (≥2 точек)
  function loadTrend() {
    fetch("/data/price_history.json").then(function (r) { return r.ok ? r.json() : null; }).then(function (j) {
      if (!j || !j.points || j.points.length < 2) return; // тренд показываем только при ≥2 точках истории
      var f = j.points[0].avg, l = j.points[j.points.length - 1].avg;
      (j.categories || []).forEach(function (c) {
        var a = f[c], b = l[c];
        if (a == null || b == null || !a) return;
        var pct = Math.round((b - a) / a * 100);
        TREND[c] = { pct: pct, arrow: pct > 0 ? "▲" + pct + "%" : pct < 0 ? "▼" + Math.abs(pct) + "%" : "→0%" };
      });
      if (gridEl && gridEl.children.length) render(); // перерисуем карточки с трендом
    }).catch(function () {});
  }
  var flt = { cat: null, tariff: null, price: null, code: null, tariffPrice: null }; // tariffPrice — пресет тарифной страницы (по цене)

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
      clearTimeout(searchTimer); searchTimer = setTimeout(render, 500);
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
    // Категории выбираются в шапке (верхнее меню), в сайдбаре их не дублируем.
    fillList(fPrice, [{ v: null, t: "Любая" }].concat(PRICE_TIERS.map(function (t) { return { v: t.key, t: t.label }; })), "price", false);
  }
  // Тарифы — ТОЛЬКО те, по которым есть номера в загруженном пуле (в /filters есть мёртвые). Сортировка по цене.
  function buildTariffFilter() {
    var m = {};
    ALL.forEach(function (p) { var t = p.tariff; if (t && t.id != null && !m[t.id] && !(PRESET.tmin && (t.price || 0) <= PRESET.tmin)) m[t.id] = { id: t.id, name: t.name, price: t.price || 0 }; });
    var list = Object.keys(m).map(function (k) { return m[k]; }).sort(function (a, b) { return a.price - b.price; });
    if (flt.tariff && !m[flt.tariff]) flt.tariff = null; // выбранный тариф исчез из выдачи
    fillList(fTariff, [{ v: null, t: "Все тарифы" }].concat(list.map(function (t) { return { v: t.id, t: t.name }; })), "tariff", false);
  }
  // Коды (первые 3 цифры) — из фактических номеров, только те, где есть номера. С счётчиком.
  function buildCodeFilter() {
    if (!fCode) return;
    var m = {};
    ALL.forEach(function (p) { var d = digitsOf(p.phone); if (d.length === 10) { var c = d.slice(0, 3); m[c] = (m[c] || 0) + 1; } });
    var codes = Object.keys(m).sort();
    if (flt.code && !m[flt.code]) flt.code = null; // выбранный код исчез из выдачи
    fCode.innerHTML = '<option value="">Все коды</option>' + codes.map(function (c) {
      return '<option value="' + c + '"' + (c === flt.code ? " selected" : "") + ">" + c + " (" + m[c] + ")</option>";
    }).join("");
    fCode.value = flt.code || "";
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

  // какие категории каталога брать для текущей страницы (по flt.cat; slug — подстрока кода)
  function catSlugsForPage(cats) {
    var all = Object.keys(cats);
    if (!flt.cat) return all;                                   // /start/ и паттерны — все категории
    var sel = all.filter(function (sl) { return flt.cat.indexOf(sl) >= 0; });
    return sel.length ? sel : all;
  }
  // маска на клиенте (локальная база не отфильтрована по маске): цифра=точно, N/пусто=любая, буква=повтор
  function maskMatch(digits, mask) {
    if (!mask || isEmptyMask(mask)) return true;
    var rep = {};
    for (var i = 0; i < 10; i++) {
      var c = mask.charAt(i), d = digits.charAt(i);
      if (c === "N" || c === "n" || c === "") continue;
      if (c >= "0" && c <= "9") { if (d !== c) return false; }
      else { var lc = c.toLowerCase(); if (rep[lc] == null) rep[lc] = d; else if (rep[lc] !== d) return false; }
    }
    return true;
  }
  // ГЛАВНОЕ: грузим из ЛОКАЛЬНОЙ базы catalog.json (прогрев кроном), а НЕ из медленного API Безлимита.
  function fetchNumbers() {
    showStatus("Загружаю номера…");
    fetch("/data/catalog.json", { cache: "no-store" })
      .then(function (r) { if (!r.ok) { throw 0; } return r.json(); })
      .then(function (j) {
        var cats = j.cats || {}, out = [];
        catSlugsForPage(cats).forEach(function (sl) {
          (cats[sl] || []).forEach(function (x) {
            out.push({ phone: x.n, _cat: sl, tariff: { id: x.i, name: x.t, price: x.p } });
          });
        });
        if (!out.length) { fetchNumbersLive(); return; }        // база пуста → живой API
        ALL = out.filter(okTariff); BY_PHONE = {};
        ALL.forEach(function (p) { BY_PHONE[digitsOf(p.phone)] = p; });
        buildTariffFilter(); buildCodeFilter(); render();
      })
      .catch(function () { fetchNumbersLive(); });                // нет базы → живой API (фолбэк)
  }
  // Фолбэк: живой API Безлимит (если catalog.json недоступен).
  function fetchNumbersLive() {
    showStatus("Загружаю номера…");
    var mask = buildCubes();
    var q = ["expand=tariff", "is_reserved=false", "per_page=100"];
    q.push("phone_pattern=" + encodeURIComponent(isEmptyMask(mask) ? DEFAULT_MASK : mask));
    if (flt.cat) q.push("mask_categories=" + encodeURIComponent(flt.cat));
    api("/super-link/phones/mask-category?" + q.join("&"))
      .then(function (d) {
        var f = flatten(d).filter(okTariff);
        ALL = f; BY_PHONE = {};
        f.forEach(function (p) { BY_PHONE[digitsOf(p.phone)] = p; });
        buildTariffFilter(); buildCodeFilter(); render();
      })
      .catch(function (e) { showStatus("Ошибка загрузки (" + e.message + ")."); });
  }

  function matchesClient(p) {
    if (PRESET.tmin && !(p.tariff && (p.tariff.price || 0) > PRESET.tmin)) return false; // порог тарифа (vip/бизнес)
    if (flt.code && digitsOf(p.phone).slice(0, 3) !== flt.code) return false; // код — первые 3 цифры
    if (flt.tariff && !(p.tariff && p.tariff.id === flt.tariff)) return false; // тариф — клиентский фильтр
    if (flt.tariffPrice && !(p.tariff && p.tariff.price === flt.tariffPrice)) return false; // тарифная страница — по цене
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
    var mask = buildCubes();
    var base = favMode ? Object.keys(FAV).map(function (k) { return FAV[k]; }) : ALL;
    var list = sorted(base.filter(function (p) { return matchesClient(p) && maskMatch(digitsOf(p.phone), mask); }));
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
        '<button class="share-ic" data-share="' + esc(d) + '" title="Поделиться номером" aria-label="Поделиться номером" type="button">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.6" y1="13.5" x2="15.4" y2="17.5"></line><line x1="15.4" y1="6.5" x2="8.6" y2="10.5"></line></svg>' +
        "</button>" +
        '<a class="rate-ic" href="/proverit-nomer/?p=' + esc(d) + '" title="Оценить красоту номера" aria-label="Оценить красоту номера" target="_blank" rel="noopener">' +
          '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"></circle><line x1="21" y1="21" x2="16.5" y2="16.5"></line></svg>' +
        "</a>" +
        (badge ? '<span class="num-badge">' + esc(badge) + "</span>" : "") +
        '<div class="num-phone">' + esc(fmtPhone(p.phone)) + "</div>" +
        (t.name ? '<div class="num-tariff">' + esc(t.name) + "</div>" : "") +
        (specs.length ? '<div class="num-specs">' + esc(specs.join(" · ")) + "</div>" : "") +
        (t.price != null ? '<div class="num-price">' + esc(fmtMoney(t.price)) + "<span>/мес</span></div>" : "") +
        (badge && TREND[badge] ? '<div class="num-trend" title="Тренд средней абонплаты категории «' + esc(badge) + '»">' + esc(badge) + " " + TREND[badge].arrow + "</div>" : "") +
        '<button class="num-buy" data-phone="' + esc(digitsOf(p.phone)) + '">Забронировать</button>' +
      "</article>"
    );
  }
  function shareNumber(d, btn) {
    var url = location.origin + "/nomer/?p=" + d;
    if (navigator.share) { navigator.share({ title: "Красивый номер " + fmtPhone(d), url: url }).catch(function () {}); return; }
    try { navigator.clipboard.writeText(url); } catch (e) {}
    if (btn) { var o = btn.innerHTML; btn.innerHTML = "✓"; btn.classList.add("copied"); setTimeout(function () { btn.innerHTML = o; btn.classList.remove("copied"); }, 1500); }
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
  /* Памятка перед бронью (то, что Безлимит показывает ДО загрузки паспорта):
     4 шага оформления + важное ограничение «только граждане РФ». */
  function bookingInfo(p) {
    var tariffId = p.tariff && p.tariff.id;
    if (!tariffId) { alert("У номера не указан тариф — бронь недоступна."); return; }
    var back = document.getElementById("bookModal");
    if (!back) {
      back = document.createElement("div");
      back.id = "bookModal";
      back.className = "book-modal";
      back.innerHTML =
        '<div class="book-card" role="dialog" aria-modal="true" aria-labelledby="bookTitle">' +
          '<button class="book-x" aria-label="Закрыть">×</button>' +
          '<h3 id="bookTitle">Давайте оформим всё по правилам</h3>' +
          '<p class="book-sub">Это займёт пару минут. Оформление и оплата — на защищённой странице оператора Безлимит.</p>' +
          '<p class="book-num" id="bookNum"></p>' +
          '<ol class="book-steps">' +
            '<li><b>Шаг 1.</b> Загрузить фото паспорта РФ</li>' +
            '<li><b>Шаг 2.</b> Подписать документы</li>' +
            '<li><b>Шаг 3.</b> Оплатить тарифный план</li>' +
            '<li><b>Шаг 4.</b> Получить SIM-карту</li>' +
          '</ol>' +
          '<p class="book-warn">🔴 <b>Важно:</b> подключение доступно только гражданам РФ. Паспорт другого государства не подходит.</p>' +
          '<div class="book-actions">' +
            '<button class="btn-ghost book-cancel">Отмена</button>' +
            '<button class="btn-primary book-go">Забронировать и продолжить</button>' +
          '</div>' +
        '</div>';
      document.body.appendChild(back);
      back.addEventListener("click", function (e) {
        if (e.target === back || e.target.closest(".book-x") || e.target.closest(".book-cancel")) closeBook();
      });
      document.addEventListener("keydown", function (e) {
        if (e.key === "Escape" && back.classList.contains("open")) closeBook();
      });
    }
    document.getElementById("bookNum").textContent = fmtPhone(p.phone) + " · бронь держится ~1 час";
    var go = back.querySelector(".book-go");
    go.onclick = function () { closeBook(); doReserve(p); };
    back.classList.add("open");
    document.body.style.overflow = "hidden";
  }
  function closeBook() {
    var b = document.getElementById("bookModal");
    if (b) b.classList.remove("open");
    document.body.style.overflow = "";
  }
  // Модалка «номер уже купили» (как на лендинге) — переиспользует стили .book-modal/.book-card.
  function showTaken() {
    var m = document.getElementById("takenModal");
    if (!m) {
      m = document.createElement("div");
      m.id = "takenModal"; m.className = "book-modal";
      m.innerHTML =
        '<div class="book-card" role="dialog" aria-modal="true" style="text-align:center">' +
          '<button class="book-x" aria-label="Закрыть">×</button>' +
          '<div style="font-size:40px;line-height:1;margin-bottom:8px">😔</div>' +
          '<h3>Ой, кажется, номер уже купили</h3>' +
          '<p class="book-sub">Похоже, этот номер кто-то забрал буквально только что. Но не расстраивайтесь — у нас есть другие, не менее эффектные.</p>' +
          '<div class="book-actions" style="justify-content:center">' +
            '<button class="btn-ghost taken-close" type="button">Выбрать другой</button>' +
            '<a class="btn-primary" href="/start/">Весь каталог →</a>' +
          '</div>' +
        '</div>';
      document.body.appendChild(m);
      m.addEventListener("click", function (e) {
        if (e.target === m || e.target.closest(".book-x") || e.target.closest(".taken-close")) {
          m.classList.remove("open"); document.body.style.overflow = "";
        }
      });
    }
    m.classList.add("open"); document.body.style.overflow = "hidden";
  }

  function removeSold(digits) {   // номер заняли между загрузкой и кликом — убираем из выдачи
    delete BY_PHONE[digits];
    ALL = ALL.filter(function (x) { return digitsOf(x.phone) !== digits; });
    var btn = gridEl.querySelector('.num-buy[data-phone="' + digits + '"]');
    if (btn && btn.closest) { var art = btn.closest(".num"); if (art) art.remove(); }
  }

  function doReserve(p) {
    var tariffId = p.tariff && p.tariff.id, digits = digitsOf(p.phone);
    if (!tariffId) { alert("У номера не указан тариф — бронь недоступна."); return; }
    var tg = window.Telegram && window.Telegram.WebApp;   // внутри Telegram Mini App
    var w = tg ? null : window.open("", "_blank");         // в браузере — окно заранее (антипопап)
    // 1) ЖИВАЯ пере-проверка: номер ещё свободен прямо сейчас? (защита от оформления проданного номера)
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=" + digits)
      .then(function (data) {
        var free = false;
        flatten(data).forEach(function (x) { if (digitsOf(x.phone) === digits) free = true; });
        if (!free) { if (w) w.close(); showTaken(); removeSold(digits); throw "sold"; }
        // 2) свободен → создаём бронь
        var fd = new FormData();
        fd.append("phone", digits); fd.append("tariff_id", tariffId);
        fd.append("type", "store"); fd.append("user_id", CFG.REF_ID); fd.append("filter", "professional");
        return fetch(CFG.API_BASE + "/super-link/reservations?expand=super_link_uuid",
              { method: "POST", headers: { Authorization: CFG.API_TOKEN }, body: fd }).then(function (r) { return r.json(); });
      })
      .then(function (d) {
        var uuid = deepUuid(d);
        if (!uuid) { if (w) w.close(); showTaken(); removeSold(digits); return; }
        var url = CFG.REF_STORE_URL + "?type=p&cubes=" + digits + "&uuid=" + encodeURIComponent(uuid);
        if (tg) tg.openLink(url); else if (w) w.location = url; else window.open(url, "_blank", "noopener");
      })
      .catch(function (e) { if (e === "sold") return; if (w) w.close(); alert("Ошибка брони: " + (e && e.message ? e.message : e)); });
  }

  /* ---------- события ---------- */
  findBtn.addEventListener("click", function () { shown = PAGE; render(); });
  // «🔔 Следить» — подписка на маску через Telegram-бота (уведомит, когда появится такой номер)
  var watchBtn = $("watch");
  if (watchBtn) watchBtn.addEventListener("click", function () {
    var m = buildCubes();
    if (isEmptyMask(m)) { alert("Укажите хотя бы одну цифру в маске — тогда пришлём уведомление, когда появится такой номер."); return; }
    window.open("https://t.me/magzgoldbot?start=watch_" + encodeURIComponent(m), "_blank", "noopener");
  });
  resetBtn.addEventListener("click", function () {
    cubesEl.querySelectorAll("input").forEach(function (c) { c.value = ""; });
    sortEl.value = "default";
    flt = { cat: null, tariff: null, price: null };
    buildSidebar(); shown = PAGE; render();
  });
  sortEl.addEventListener("change", function () { shown = PAGE; render(); });
  if (fCode) fCode.addEventListener("change", function () { flt.code = fCode.value || null; shown = PAGE; render(); });
  moreBtn.addEventListener("click", function () { shown += PAGE; render(); });
  gridEl.addEventListener("click", function (e) {
    if (!e.target.closest) return;
    var fav = e.target.closest(".fav");
    if (fav) { var d = fav.getAttribute("data-fav"); var pf = BY_PHONE[d] || FAV[d]; if (pf) toggleFav(pf); return; }
    var b = e.target.closest(".num-buy");
    if (b) { var d2 = b.getAttribute("data-phone"), pb = BY_PHONE[d2] || FAV[d2]; if (pb) bookingInfo(pb); return; }
    var sh = e.target.closest(".share-ic");
    if (sh) { shareNumber(sh.getAttribute("data-share"), sh); }
  });
  var favBtn = document.getElementById("favToggle");
  if (favBtn) favBtn.addEventListener("click", function () {
    favMode = !favMode; favBtn.classList.toggle("on", favMode); shown = PAGE; render();
  });
  favCountUpd();

  // Пресет страницы (категорийные SEO-страницы задают window.PAGE = {cat:"<код>"}).
  // ВНИМАНИЕ: не называть переменную PAGE — она уже занята размером страницы (60), иначе shown=PAGE ломается.
  var PRESET = window.PAGE || {};
  if (PRESET.cat) flt.cat = PRESET.cat;
  if (PRESET.tariff) flt.tariff = PRESET.tariff; // тарифные страницы задают тариф (клиентский фильтр)
  if (PRESET.tariffPrice) flt.tariffPrice = PRESET.tariffPrice; // тарифная страница по цене
  var _qt = /[?&]tariff=(\d+)/.exec(location.search); // живой фильтр по цене тарифа из URL (?tariff=550) — кнопки /tarify/
  if (_qt) flt.tariffPrice = parseInt(_qt[1], 10) || null;
  if (PRESET.hidePrice && fPrice) { var _pg = fPrice.closest && fPrice.closest(".filter-group"); if (_pg) _pg.style.display = "none"; } // vip/бизнес: раздел «Цена тарифа» не нужен

  renderCubes();
  if (PRESET.mask) setCubes(PRESET.mask); // паттерн-страницы задают маску
  buildSidebar();   // было loadFilters() — тянул /filters с Безлимита; данные не использовались, строим локально
  loadTrend();
  fetchNumbers();
})();
