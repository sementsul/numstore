/* MagzGold — встраиваемый виджет красивых номеров с фильтрами (категория/цена/окончание).
   На чужом сайте:
     <div class="magzgold-widget" data-count="6"></div>
     <script src="https://magzgold.ru/widget.js" async></script>
   Атрибуты: data-cat (стартовая категория), data-count (на странице), data-title, data-controls="off" (скрыть фильтры).
   Тянет номера из API Безлимита в браузере посетителя (ban-proof). Бронь → magzgold.ru/nomer/ (реф за нами). */
(function () {
  var SITE = "https://magzgold.ru";
  var API_BASE = "https://api.store.bezlimit.ru/v2";
  var API_TOKEN = "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw==";
  var CATS = [["", "Все"], ["brilliant", "Бриллиант"], ["platinum", "Платина"], ["gold", "Золото"], ["silver", "Серебро"], ["bronze", "Бронза"]];
  var CAT_LABEL = { brilliant: "Бриллиант", brilliant_super: "Бриллиант", platinum: "Платина", platinum_lite: "Платина",
    gold: "Золото", silver: "Серебро", bronze: "Бронза" };
  var PRICES = [["", "Любая цена"], ["lo", "до 1000 ₽"], ["mid", "1000–3000 ₽"], ["hi", "свыше 3000 ₽"]];

  function digits(p) { return String(p).replace(/\D/g, "").slice(-10); }
  function fmtPhone(p) { var s = digits(p); return s.length === 10 ? "+7 " + s.slice(0,3) + " " + s.slice(3,6) + "-" + s.slice(6,8) + "-" + s.slice(8,10) : "+7 " + s; }
  function money(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
  function badge(c) { return CAT_LABEL[String(c || "").split(",")[0].trim()] || ""; }
  function priceOk(key, v) { if (!key || v == null) return !key; return key === "lo" ? v < 1000 : key === "mid" ? (v >= 1000 && v <= 3000) : v > 3000; }

  function injectCss() {
    if (document.getElementById("mgw-css")) return;
    var css =
      ".mgw{max-width:760px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#eef0f4;background:linear-gradient(180deg,#1c2030,#161923);border:1px solid rgba(201,165,88,.28);border-radius:14px;padding:16px 16px 12px;box-sizing:border-box}" +
      ".mgw *{box-sizing:border-box}" +
      ".mgw-h{display:flex;align-items:baseline;justify-content:space-between;gap:8px;margin-bottom:12px}" +
      ".mgw-t{font-weight:700;font-size:16px}.mgw-t b{color:#c9a558}.mgw-h a{color:#8b909c;font-size:12px;text-decoration:none}" +
      ".mgw-ctl{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px;align-items:center}" +
      ".mgw-cat{padding:5px 11px;border-radius:20px;font-size:13px;cursor:pointer;color:#8b909c;background:transparent;border:1px solid rgba(255,255,255,.08)}" +
      ".mgw-cat.on{color:#1a1608;background:linear-gradient(180deg,#e6cd8c,#c9a558);border-color:transparent;font-weight:600}" +
      ".mgw-sel,.mgw-inp{padding:7px 10px;border-radius:8px;font-size:13px;background:#0f121a;border:1px solid rgba(255,255,255,.08);color:#eef0f4}" +
      ".mgw-inp{width:130px}" +
      ".mgw-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}" +
      ".mgw-num{background:#0f121a;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:12px 14px}" +
      ".mgw-badge{font-size:10px;letter-spacing:.5px;text-transform:uppercase;color:#c9a558;border:1px solid rgba(201,165,88,.28);border-radius:20px;padding:1px 8px;display:inline-block;margin-bottom:8px}" +
      ".mgw-phone{font-size:19px;font-weight:600;letter-spacing:1px;font-variant-numeric:tabular-nums}" +
      ".mgw-price{color:#8b909c;font-size:13px;margin-top:4px}" +
      ".mgw-btn{display:block;text-align:center;margin-top:10px;padding:9px;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;color:#1a1608;background:linear-gradient(180deg,#e6cd8c,#c9a558)}" +
      ".mgw-more{display:block;margin:12px auto 4px;padding:9px 20px;border-radius:8px;cursor:pointer;background:transparent;color:#c9a558;border:1px solid rgba(201,165,88,.28);font-size:14px}" +
      ".mgw-msg{color:#8b909c;font-size:14px;padding:14px 0;text-align:center}" +
      ".mgw-f{margin-top:12px;text-align:right;font-size:11px}.mgw-f a{color:#8b909c;text-decoration:none}";
    var el = document.createElement("style"); el.id = "mgw-css"; el.textContent = css; document.head.appendChild(el);
  }

  function flatten(data) {
    var out = [], seen = {};
    if (data && typeof data === "object") Object.keys(data).forEach(function (k) {
      var v = data[k]; if (v && v.items) v.items.forEach(function (p) {
        if (p && p.phone != null) { var d = digits(p.phone); if (!seen[d]) { seen[d] = 1; p._cat = k; out.push(p); } }
      });
    });
    return out;
  }

  function initBox(box) {
    if (box.getAttribute("data-mgw-done")) return;
    box.setAttribute("data-mgw-done", "1");
    var pageSize = Math.max(1, Math.min(48, parseInt(box.getAttribute("data-count"), 10) || 6));
    var showCtl = (box.getAttribute("data-controls") || "").toLowerCase() !== "off";
    var title = box.getAttribute("data-title") || "Красивые номера MagzGold";
    var state = { cat: (box.getAttribute("data-cat") || "").toLowerCase(), price: "", search: "", shown: pageSize, pool: null };

    box.innerHTML = '<div class="mgw"><div class="mgw-msg">Загружаю красивые номера…</div></div>';

    function matches(p) {
      if (state.cat && badge(p._cat) !== (CAT_LABEL[state.cat] || "")) return false;
      if (state.price && !priceOk(state.price, p.tariff && p.tariff.price)) return false;
      if (state.search && digits(p.phone).indexOf(state.search) === -1) return false;
      return true;
    }
    function draw() {
      var wrap = box.querySelector(".mgw"); if (!wrap) return;
      var list = state.pool.filter(matches);
      var grid = wrap.querySelector(".mgw-grid"), more = wrap.querySelector(".mgw-more-wrap");
      var cards = list.slice(0, state.shown).map(function (p) {
        var t = p.tariff || {}, d = digits(p.phone), b = badge(p._cat);
        return '<div class="mgw-num">' + (b ? '<span class="mgw-badge">' + esc(b) + "</span>" : "") +
          '<div class="mgw-phone">' + esc(fmtPhone(p.phone)) + "</div>" +
          (t.price != null ? '<div class="mgw-price">' + esc(money(t.price)) + "/мес</div>" : "") +
          '<a class="mgw-btn" href="' + SITE + "/nomer/?p=" + d + '" target="_blank" rel="noopener">Забронировать</a></div>';
      }).join("");
      grid.innerHTML = cards || '<div class="mgw-msg">Под фильтры ничего не нашлось</div>';
      more.innerHTML = list.length > state.shown ? '<button class="mgw-more">Показать ещё</button>' : "";
    }
    function build() {
      var ctl = "";
      if (showCtl) {
        var cats = CATS.map(function (c) { return '<button class="mgw-cat' + (state.cat === c[0] ? " on" : "") + '" data-cat="' + c[0] + '">' + c[1] + "</button>"; }).join("");
        var prices = PRICES.map(function (p) { return '<option value="' + p[0] + '">' + p[1] + "</option>"; }).join("");
        ctl = '<div class="mgw-ctl">' + cats +
          '<select class="mgw-sel" data-role="price">' + prices + "</select>" +
          '<input class="mgw-inp" data-role="search" inputmode="numeric" placeholder="цифры / окончание"></div>';
      }
      box.innerHTML = '<div class="mgw">' +
        '<div class="mgw-h"><span class="mgw-t">' + esc(title) + '</span><a href="' + SITE + '/" target="_blank" rel="noopener">Весь каталог →</a></div>' +
        ctl + '<div class="mgw-grid"></div><div class="mgw-more-wrap"></div>' +
        '<div class="mgw-f"><a href="' + SITE + '/" target="_blank" rel="noopener">Powered by MagzGold</a></div></div>';
      box.addEventListener("click", function (e) {
        var c = e.target.closest && e.target.closest(".mgw-cat");
        if (c) { state.cat = c.getAttribute("data-cat"); state.shown = pageSize;
          box.querySelectorAll(".mgw-cat").forEach(function (b) { b.classList.toggle("on", b === c); }); draw(); return; }
        if (e.target.classList && e.target.classList.contains("mgw-more")) { state.shown += pageSize; draw(); }
      });
      var sel = box.querySelector('[data-role="price"]'); if (sel) sel.addEventListener("change", function () { state.price = sel.value; state.shown = pageSize; draw(); });
      var inp = box.querySelector('[data-role="search"]'); if (inp) inp.addEventListener("input", function () { state.search = inp.value.replace(/\D/g, ""); state.shown = pageSize; draw(); });
      draw();
    }

    fetch(API_BASE + "/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=9NNNNNNNNN", { headers: { Authorization: API_TOKEN } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) { state.pool = flatten(data || {}); if (!state.pool.length) { box.innerHTML = '<div class="mgw"><div class="mgw-msg">Номера временно недоступны</div></div>'; return; } build(); })
      .catch(function () { box.innerHTML = '<div class="mgw"><div class="mgw-msg">Номера временно недоступны</div></div>'; });
  }

  function initAll() {
    injectCss();
    var boxes = document.querySelectorAll(".magzgold-widget, #magzgold-widget");
    for (var i = 0; i < boxes.length; i++) initBox(boxes[i]);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initAll);
  else initAll();
})();
