/* MagzGold — калькулятор стоимости номера по красоте.
   Цена у Безлимит зависит от КРАСОТЫ (категории), НЕ от региона. Берём реальные тарифы категории (API, клиент). */
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
    out.innerHTML = '<span class="calc-load">Считаю по реальным номерам…</span>';
    link.hidden = true;
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&mask_categories=" +
        encodeURIComponent(cat.code) + "&phone_pattern=9NNNNNNNNN")
      .then(function (d) {
        var pr = pricesOf(d);
        if (!pr.length) { out.innerHTML = '<span class="calc-note">Для этой категории сейчас нет активных номеров — выберите другую.</span>'; return; }
        var mn = Math.min.apply(null, pr), mx = Math.max.apply(null, pr);
        var range = mn === mx ? fmt(mn) : fmt(mn) + " – " + fmt(mx);
        out.innerHTML =
          '<div class="calc-range">' + range + ' <span>/мес</span></div>' +
          '<div class="calc-sub">' + cat.name + ' номера · ' + pr.length + ' в наличии</div>' +
          '<div class="calc-note">Стоимость определяется красотой номера (категорией) и равна абонплате тарифа; ' +
          'регион на цену не влияет. Точные условия — при бронировании у оператора.</div>';
        link.href = "/kategoriya/" + cat.slug + "/";
        link.hidden = false;
      })
      .catch(function (e) { out.innerHTML = '<span class="calc-note">Не удалось посчитать (' + e.message + '). Обновите страницу.</span>'; });
  }

  catSel.addEventListener("change", calc);
  calc();
})();
