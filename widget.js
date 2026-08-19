/* MagzGold — встраиваемый виджет красивых номеров для сторонних сайтов.
   Использование на чужом сайте:
     <div class="magzgold-widget" data-cat="gold" data-count="6"></div>
     <script src="https://magzgold.ru/widget.js" async></script>
   Тянет номера напрямую из API Безлимита в браузере посетителя (ban-proof, много IP).
   Бронь ведёт на magzgold.ru/nomer/ (реф-атрибуция остаётся за нами). Стили самодостаточны (scoped). */
(function () {
  var SITE = "https://magzgold.ru";
  var API_BASE = "https://api.store.bezlimit.ru/v2";
  var API_TOKEN = "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw==";
  var CAT_CODE = { brilliant: "brilliant,brilliant_super", platinum: "platinum,platinum_lite",
    gold: "gold", silver: "silver,silver_special,silver_special_2", bronze: "bronze,bronze_vip,bronze AAA" };
  var CAT_LABEL = { brilliant: "Бриллиант", platinum: "Платина", gold: "Золото", silver: "Серебро", bronze: "Бронза" };

  function digits(p) { return String(p).replace(/\D/g, "").slice(-10); }
  function fmtPhone(p) { var s = digits(p); return s.length === 10 ? "+7 " + s.slice(0,3) + " " + s.slice(3,6) + "-" + s.slice(6,8) + "-" + s.slice(8,10) : "+7 " + s; }
  function money(n) { return n == null || isNaN(n) ? "" : String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}

  function injectCss() {
    if (document.getElementById("mgw-css")) return;
    var css = "" +
      ".mgw{max-width:720px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#eef0f4;" +
        "background:linear-gradient(180deg,#1c2030,#161923);border:1px solid rgba(201,165,88,.28);" +
        "border-radius:14px;padding:16px 16px 12px;box-sizing:border-box}" +
      ".mgw *{box-sizing:border-box}" +
      ".mgw-h{display:flex;align-items:baseline;justify-content:space-between;gap:8px;margin-bottom:12px}" +
      ".mgw-t{font-weight:700;font-size:16px;letter-spacing:.3px}" +
      ".mgw-t b{color:#c9a558}" +
      ".mgw-h a{color:#8b909c;font-size:12px;text-decoration:none}" +
      ".mgw-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}" +
      ".mgw-num{background:#0f121a;border:1px solid rgba(255,255,255,.07);border-radius:10px;padding:12px 14px}" +
      ".mgw-badge{font-size:10px;letter-spacing:.5px;text-transform:uppercase;color:#c9a558;border:1px solid rgba(201,165,88,.28);border-radius:20px;padding:1px 8px;display:inline-block;margin-bottom:8px}" +
      ".mgw-phone{font-size:19px;font-weight:600;letter-spacing:1px;font-variant-numeric:tabular-nums}" +
      ".mgw-price{color:#8b909c;font-size:13px;margin-top:4px}" +
      ".mgw-btn{display:block;text-align:center;margin-top:10px;padding:9px;border-radius:8px;text-decoration:none;" +
        "font-weight:700;font-size:14px;color:#1a1608;background:linear-gradient(180deg,#e6cd8c,#c9a558)}" +
      ".mgw-f{margin-top:12px;text-align:right;font-size:11px}" +
      ".mgw-f a{color:#8b909c;text-decoration:none}" +
      ".mgw-msg{color:#8b909c;font-size:14px;padding:14px 0;text-align:center}";
    var el = document.createElement("style"); el.id = "mgw-css"; el.textContent = css;
    document.head.appendChild(el);
  }

  function flatten(data) {
    var out = [];
    if (data && typeof data === "object") Object.keys(data).forEach(function (k) {
      var v = data[k]; if (v && v.items) v.items.forEach(function (p) { if (p && p.phone != null) { p._cat = k; out.push(p); } });
    });
    return out;
  }
  function badge(cat) { return CAT_LABEL[String(cat || "").split(",")[0].trim()] || ""; }

  function render(box, list, title) {
    var cards = list.map(function (p) {
      var t = p.tariff || {}, d = digits(p.phone), b = badge(p._cat);
      return '<div class="mgw-num">' +
        (b ? '<span class="mgw-badge">' + esc(b) + "</span>" : "") +
        '<div class="mgw-phone">' + esc(fmtPhone(p.phone)) + "</div>" +
        (t.price != null ? '<div class="mgw-price">' + esc(money(t.price)) + "/мес</div>" : "") +
        '<a class="mgw-btn" href="' + SITE + "/nomer/?p=" + d + '" target="_blank" rel="noopener">Забронировать</a>' +
        "</div>";
    }).join("");
    box.innerHTML =
      '<div class="mgw">' +
        '<div class="mgw-h"><span class="mgw-t">' + esc(title) + '</span>' +
          '<a href="' + SITE + '/" target="_blank" rel="noopener">Весь каталог →</a></div>' +
        (list.length ? '<div class="mgw-grid">' + cards + "</div>" : '<div class="mgw-msg">Номера временно недоступны</div>') +
        '<div class="mgw-f"><a href="' + SITE + '/" target="_blank" rel="noopener">Powered by MagzGold</a></div>' +
      "</div>";
  }

  function initBox(box) {
    if (box.getAttribute("data-mgw-done")) return;
    box.setAttribute("data-mgw-done", "1");
    var cat = (box.getAttribute("data-cat") || "").toLowerCase();
    var count = Math.max(1, Math.min(24, parseInt(box.getAttribute("data-count"), 10) || 6));
    var title = box.getAttribute("data-title") || ("Красивые номера" + (CAT_LABEL[cat] ? " · " + CAT_LABEL[cat] : ""));
    box.innerHTML = '<div class="mgw"><div class="mgw-msg">Загружаю красивые номера…</div></div>';
    var q = ["expand=tariff", "is_reserved=false", "per_page=" + (count + 4), "phone_pattern=9NNNNNNNNN"];
    if (CAT_CODE[cat]) q.push("mask_categories=" + encodeURIComponent(CAT_CODE[cat]));
    fetch(API_BASE + "/super-link/phones/mask-category?" + q.join("&"), { headers: { Authorization: API_TOKEN } })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (data) {
        var seen = {}, list = [];
        flatten(data || {}).forEach(function (p) { var d = digits(p.phone); if (!seen[d]) { seen[d] = 1; list.push(p); } });
        render(box, list.slice(0, count), title);
      })
      .catch(function () { render(box, [], title); });
  }

  function initAll() {
    injectCss();
    var boxes = document.querySelectorAll(".magzgold-widget, #magzgold-widget");
    for (var i = 0; i < boxes.length; i++) initBox(boxes[i]);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initAll);
  else initAll();
})();
