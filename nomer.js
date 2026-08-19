/* numstore — страница одного номера /nomer/?p=<10 цифр>.
   Тянет номер напрямую из API (как каталог, ban-proof). Если номер уже занят/куплен —
   его нет в выдаче is_reserved=false → показываем «недоступен для бронирования». */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var view = document.getElementById("numView");
  var simEl = document.getElementById("numSimilar");
  if (!view) return;

  function digitsOf(p) { return String(p).replace(/\D/g, "").slice(-10); }
  function fmtPhone(p) {
    var s = String(p).replace(/\D/g, "").slice(-10);
    if (s.length !== 10) return "+7 " + s;
    return "+7 " + s.slice(0, 3) + " " + s.slice(3, 6) + "-" + s.slice(6, 8) + "-" + s.slice(8, 10);
  }
  function fmtMoney(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }
  var CAT_BADGE = { brilliant: "Бриллиант", brilliant_super: "Бриллиант", platinum: "Платина",
    platinum_lite: "Платина", gold: "Золото", silver: "Серебро", bronze: "Бронза" };
  function catBadge(cat) {
    if (!cat) return "";
    var key = String(cat).split(",")[0].trim();
    return CAT_BADGE[key] || "";
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
    return out;
  }

  /* ---------- бронь (памятка + POST), как в каталоге ---------- */
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
    back.querySelector(".book-go").onclick = function () { closeBook(); doReserve(p); };
    back.classList.add("open");
    document.body.style.overflow = "hidden";
  }
  function closeBook() {
    var b = document.getElementById("bookModal");
    if (b) b.classList.remove("open");
    document.body.style.overflow = "";
  }
  function doReserve(p) {
    var tariffId = p.tariff && p.tariff.id, digits = digitsOf(p.phone);
    if (!tariffId) { alert("У номера не указан тариф — бронь недоступна."); return; }
    var tg = window.Telegram && window.Telegram.WebApp;
    var w = tg ? null : window.open("", "_blank");
    // 1) живая пере-проверка: номер ещё свободен? (защита от оформления проданного)
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=" + digits)
      .then(function (data) {
        var free = false;
        flatten(data).forEach(function (x) { if (digitsOf(x.phone) === digits) free = true; });
        if (!free) { if (w) w.close(); alert("Этот номер уже заняли. Обновите страницу или выберите другой в каталоге."); throw "sold"; }
        var fd = new FormData();
        fd.append("phone", digits); fd.append("tariff_id", tariffId);
        fd.append("type", "store"); fd.append("user_id", CFG.REF_ID); fd.append("filter", "professional");
        return fetch(CFG.API_BASE + "/super-link/reservations?expand=super_link_uuid",
              { method: "POST", headers: { Authorization: CFG.API_TOKEN }, body: fd }).then(function (r) { return r.json(); });
      })
      .then(function (d) {
        var uuid = deepUuid(d);
        if (!uuid) { if (w) w.close(); alert("Похоже, этот номер только что заняли. Обновите страницу или выберите другой."); return; }
        var url = CFG.REF_STORE_URL + "?type=p&cubes=" + digits + "&uuid=" + encodeURIComponent(uuid);
        if (tg) tg.openLink(url); else if (w) w.location = url; else window.open(url, "_blank", "noopener");
      })
      .catch(function (e) { if (e === "sold") return; if (w) w.close(); alert("Ошибка брони: " + (e && e.message ? e.message : e)); });
  }

  function shareNumber(d, btn) {
    var url = location.origin + "/nomer/?p=" + d;
    if (navigator.share) { navigator.share({ title: "Красивый номер " + fmtPhone(d), url: url }).catch(function () {}); return; }
    try { navigator.clipboard.writeText(url); } catch (e) {}
    if (btn) { var o = btn.textContent; btn.textContent = "Ссылка скопирована ✓"; setTimeout(function () { btn.textContent = o; }, 1600); }
  }

  /* ---------- рендер ---------- */
  function renderCard(p, d) {
    var t = p.tariff || {}, badge = catBadge(p._cat);
    var specs = [];
    if (t.minutes != null) specs.push(t.minutes + " мин");
    if (t.sms != null) specs.push(t.sms + " смс");
    if (t.internet != null) specs.push(t.internet + " ГБ");
    document.title = "Номер " + fmtPhone(p.phone) + " — купить | MagzGold";
    view.innerHTML =
      '<article class="num num-solo">' +
        (badge ? '<span class="num-badge">' + esc(badge) + "</span>" : "") +
        '<div class="num-phone">' + esc(fmtPhone(p.phone)) + "</div>" +
        (t.name ? '<div class="num-tariff">' + esc(t.name) + "</div>" : "") +
        (specs.length ? '<div class="num-specs">' + esc(specs.join(" · ")) + "</div>" : "") +
        (t.price != null ? '<div class="num-price">' + esc(fmtMoney(t.price)) + "<span>/мес абонплата</span></div>" : "") +
        '<p class="num-solo-desc">Красивый номер' + (badge ? " категории «" + esc(badge) + "»" : "") +
          ". Доставка SIM по РФ бесплатно или eSIM. Оформление — у оператора «Безлимит»." +
          " Бронь удерживает номер за вами около часа.</p>" +
        '<button class="num-buy num-buy-solo" type="button">Забронировать</button>' +
        '<button class="num-share" type="button">Поделиться номером</button>' +
      "</article>" +
      '<p class="num-solo-back"><a href="/">← Смотреть другие номера</a></p>';
    view.querySelector(".num-buy-solo").onclick = function () { bookingInfo(p); };
    view.querySelector(".num-share").onclick = function (e) { shareNumber(d, e.target); };
  }
  function renderUnavailable(d) {
    document.title = "Номер " + fmtPhone(d) + " недоступен | MagzGold";
    view.innerHTML =
      '<article class="num num-solo num-solo-gone">' +
        '<div class="num-phone">' + esc(fmtPhone(d)) + "</div>" +
        '<p class="num-solo-desc"><b>Этот номер уже недоступен для бронирования</b> — его забронировали или купили. ' +
        "Не расстраивайтесь: в каталоге много других красивых номеров.</p>" +
        '<a class="btn-primary num-buy-solo" href="/">Подобрать другой номер</a>' +
      "</article>";
  }
  function renderError() {
    view.innerHTML = '<p class="status">Не удалось загрузить номер. Обновите страницу или откройте <a href="/">каталог</a>.</p>';
  }
  function renderSimilar(list, d) {
    if (!simEl) return;
    var items = list.filter(function (p) { return digitsOf(p.phone) !== d; }).slice(0, 8);
    if (!items.length) return;
    simEl.innerHTML = "<h3>Похожие номера</h3>" + items.map(function (p) {
      var t = p.tariff || {}, dd = digitsOf(p.phone);
      return '<a class="sim-item" href="/nomer/?p=' + dd + '">' +
        '<span class="sim-phone">' + esc(fmtPhone(p.phone)) + "</span>" +
        (t.price != null ? '<span class="sim-price">' + esc(fmtMoney(t.price)) + "</span>" : "") +
        "</a>";
    }).join("");
    simEl.hidden = false;
  }

  function param(name) {
    var m = new RegExp("[?&]" + name + "=([^&]+)").exec(location.search);
    return m ? decodeURIComponent(m[1]) : "";
  }

  var BASE = "/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=";

  var d = digitsOf(param("p"));
  if (d.length !== 10) { renderUnavailable(param("p") || "—"); return; }
  view.innerHTML = '<p class="status">Загружаю номер…</p>';

  // точный номер: доступен → карточка, иначе «недоступен»
  api(BASE + d)
    .then(function (data) {
      var list = flatten(data), match = null;
      list.forEach(function (p) { if (digitsOf(p.phone) === d) match = p; });
      if (match) renderCard(match, d); else renderUnavailable(d);
    })
    .catch(renderError);

  // похожие: «снимаем маску» — фиксируем окончание (последние 4 цифры), остальное любое
  var simMask = "NNNNNN" + d.slice(6);
  api(BASE + simMask)
    .then(function (data) { renderSimilar(flatten(data), d); })
    .catch(function () {});
})();
