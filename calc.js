/* MagzGold — калькулятор стоимости владения номером.
   Разовая цена номера (по категории, офиц. прайс) + абонплата тарифа × срок = итог. */
(function () {
  var CATS = window.CALC_CATS || [], TARIFFS = window.CALC_TARIFFS || [];
  var $ = function (id) { return document.getElementById(id); };
  var catSel = $("calcCat"), price = $("calcPrice"), priceVal = $("calcPriceVal"),
      tarSel = $("calcTariff"), months = $("calcMonths"), monthsVal = $("calcMonthsVal"), out = $("calcOut");
  if (!catSel || !out) return;

  function fmt(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function plural(n, f) { var a = n % 10, b = n % 100; return (a === 1 && b !== 11) ? f[0] : (a >= 2 && a <= 4 && (b < 10 || b >= 20)) ? f[1] : f[2]; }
  function currentCat() { return CATS.filter(function (c) { return c.slug === catSel.value; })[0]; }

  function setCatRange() {
    var c = currentCat(); if (!c) return;
    price.min = c.pmin; price.max = c.pmax;
    price.step = Math.max(500, Math.round((c.pmax - c.pmin) / 200));
    price.value = Math.round((c.pmin + c.pmax) / 2);
  }

  function calc() {
    var c = currentCat(); if (!c) return;
    var onetime = +price.value;
    var tar = TARIFFS.filter(function (t) { return String(t.price) === tarSel.value; })[0] || TARIFFS[0] || { price: 0 };
    var monthly = +tar.price, m = +months.value;
    var abon = monthly * m, total = onetime + abon;
    priceVal.textContent = fmt(onetime);
    monthsVal.textContent = m + " " + plural(m, ["месяц", "месяца", "месяцев"]);
    out.innerHTML =
      '<div class="calc-row"><span>Разовая цена номера</span><b>' + fmt(onetime) + "</b></div>" +
      '<div class="calc-row"><span>Абонплата ' + fmt(monthly) + "/мес × " + m + "</span><b>" + fmt(abon) + "</b></div>" +
      '<div class="calc-total"><span>Итого за ' + m + " " + plural(m, ["месяц", "месяца", "месяцев"]) + "</span><b>" + fmt(total) + "</b></div>" +
      '<a class="btn-primary calc-cta" href="/kategoriya/' + c.slug + '/">Смотреть ' + c.name.toLowerCase() + " номера</a>";
  }

  catSel.addEventListener("change", function () { setCatRange(); calc(); });
  [price, tarSel, months].forEach(function (el) { if (el) el.addEventListener("input", calc); });
  setCatRange(); calc();
})();
