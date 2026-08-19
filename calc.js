/* MagzGold — калькулятор стоимости номера по красоте.
   Стоимость номера (единоразово) — из ОФИЦИАЛЬНОГО прайса Безлимит (pmin/pmax по категории).
   Абонплата тарифа (ежемесячно) — из реальных номеров API (клиент, ban-proof). */
(function () {
  var CFG = window.NUMSTORE_CONFIG, CATS = window.CALC_CATS || [];
  var $ = function (id) { return document.getElementById(id); };
  var catSel = $("calcCat"), out = $("calcOut"), link = $("calcLink");

  function fmt(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function api(path) {
    return fetch(CFG.API_BASE + path, { headers: { Authorization: CFG.API_TOKEN } })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
  }
  function pricesOf(data) {
    var res = [];
    (function walk(x) {
      if (!x || typeof x !== "object") return;
      if (Array.isArray(x)) { x.forEach(walk); return; }
      if (x.phone != null && x.tariff && x.tariff.price != null) res.push(x.tariff.price);
      Object.keys(x).forEach(function (k) { if (k !== "tariff") walk(x[k]); });
    })(data);
    return res;
  }

  function calc() {
    var cat = CATS.filter(function (c) { return c.slug === catSel.value; })[0];
    if (!cat) return;
    var price = cat.pmin === cat.pmax ? fmt(cat.pmin) : fmt(cat.pmin) + " – " + fmt(cat.pmax);
    out.innerHTML =
      '<div class="calc-range">' + price + '</div>' +
      '<div class="calc-sub">' + cat.name + ' номера · стоимость номера (единоразово, по прайсу оператора)</div>' +
      '<div class="calc-live" id="calcLive">Абонплата тарифа: считаю по наличию…</div>' +
      '<div class="calc-note">Итоговая цена конкретного номера зависит от его маски внутри категории ' +
      '(см. официальный прайс). Абонплата тарифа оплачивается отдельно, ежемесячно.</div>';
    link.href = "/kategoriya/" + cat.slug + "/";
    link.hidden = false;

    var live = $("calcLive");
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&mask_categories=" +
        encodeURIComponent(cat.code) + "&phone_pattern=9NNNNNNNNN")
      .then(function (d) {
        var pr = pricesOf(d);
        if (!pr.length) { live.textContent = "Сейчас нет активных номеров этой категории."; return; }
        var mn = Math.min.apply(null, pr), mx = Math.max.apply(null, pr);
        live.innerHTML = "Абонплата тарифа: <b>" + (mn === mx ? fmt(mn) : fmt(mn) + " – " + fmt(mx)) +
                         "/мес</b> · в наличии: " + pr.length;
      })
      .catch(function () { live.textContent = "Абонплату не удалось загрузить."; });
  }

  catSel.addEventListener("change", calc);
  calc();
})();
