/* MagzGold — калькулятор ориентировочной стоимости номера.
   Абонплата берётся из РЕАЛЬНЫХ тарифов выбранной категории (API Безлимит, клиент — ban-proof).
   Регион — рыночный фактор (оценочно). */
(function () {
  var CFG = window.NUMSTORE_CONFIG, CATS = window.CALC_CATS || [];
  var $ = function (id) { return document.getElementById(id); };
  var catSel = $("calcCat"), regSel = $("calcReg"), out = $("calcOut"), link = $("calcLink");

  // Рыночный коэффициент по региону/коду (оценочно: спрос, а не тариф).
  var REGIONS = {
    "msk": { name: "Москва (495 / 499)", k: 1.3, note: "столичные коды ценятся выше — выше спрос и статус." },
    "spb": { name: "Санкт-Петербург (812)", k: 1.15, note: "популярный код, стабильный спрос." },
    "mob": { name: "Мобильный (9XX)", k: 1.0, note: "федеральный мобильный — базовый ориентир." },
    "reg": { name: "Регионы", k: 0.9, note: "региональные коды обычно доступнее." }
  };

  function fmt(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }

  function api(path) {
    return fetch(CFG.API_BASE + path, { headers: { Authorization: CFG.API_TOKEN } })
      .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
  }
  function pricesOf(data) {
    var out = [];
    (function walk(x) {
      if (!x || typeof x !== "object") return;
      if (Array.isArray(x)) { x.forEach(walk); return; }
      if (x.phone != null && x.tariff && x.tariff.price != null) out.push(x.tariff.price);
      Object.keys(x).forEach(function (k) { if (k !== "tariff") walk(x[k]); });
    })(data);
    return out;
  }

  function calc() {
    var cat = CATS.filter(function (c) { return c.slug === catSel.value; })[0];
    var reg = REGIONS[regSel.value];
    if (!cat || !reg) return;
    out.innerHTML = '<span class="calc-load">Считаю по реальным номерам…</span>';
    link.hidden = true;
    api("/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&mask_categories=" +
        encodeURIComponent(cat.code) + "&phone_pattern=9NNNNNNNNN")
      .then(function (d) {
        var pr = pricesOf(d);
        if (!pr.length) { out.innerHTML = '<span class="calc-note">Для этой категории сейчас нет активных номеров — попробуйте другую.</span>'; return; }
        var mn = Math.min.apply(null, pr), mx = Math.max.apply(null, pr);
        var lo = mn * reg.k, hi = mx * reg.k;
        out.innerHTML =
          '<div class="calc-range">' + fmt(lo) + ' – ' + fmt(hi) + ' <span>/мес</span></div>' +
          '<div class="calc-sub">' + cat.name + ' номера · ' + reg.name + ' · ' + pr.length + ' в наличии</div>' +
          '<div class="calc-note">Абонплата — из реальных тарифов категории. Региональный коэффициент (×' + reg.k +
          ') оценочный: ' + reg.note + ' Итоговую стоимость и условия смотрите при бронировании у оператора.</div>';
        link.href = "/kategoriya/" + cat.slug + "/";
        link.hidden = false;
      })
      .catch(function (e) { out.innerHTML = '<span class="calc-note">Не удалось посчитать (' + e.message + '). Обновите страницу.</span>'; });
  }

  catSel.addEventListener("change", calc);
  regSel.addEventListener("change", calc);
  calc();
})();
