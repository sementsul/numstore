/* MagzGold — калькулятор стоимости владения номером.
   Через реферал НОМЕР БЕСПЛАТНЫЙ — платишь только за тариф (абонплата × срок).
   Цена номера (по категории, офиц. прайс) актуальна лишь при переносе к другому оператору. */
(function () {
  var CATS = window.CALC_CATS || [], TARIFFS = window.CALC_TARIFFS || [];
  var $ = function (id) { return document.getElementById(id); };
  var catSel = $("calcCat"), tarSel = $("calcTariff"), months = $("calcMonths"), monthsVal = $("calcMonthsVal"), out = $("calcOut");
  if (!catSel || !out) return;

  function fmt(n) { return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function plural(n, f) { var a = n % 10, b = n % 100; return (a === 1 && b !== 11) ? f[0] : (a >= 2 && a <= 4 && (b < 10 || b >= 20)) ? f[1] : f[2]; }
  function currentCat() { return CATS.filter(function (c) { return c.slug === catSel.value; })[0]; }

  function calc() {
    var c = currentCat(); if (!c) return;
    var tar = TARIFFS.filter(function (t) { return String(t.price) === tarSel.value; })[0] || TARIFFS[0] || { price: 0 };
    var monthly = +tar.price, m = +months.value, abon = monthly * m;
    var mtxt = m + " " + plural(m, ["месяц", "месяца", "месяцев"]);
    monthsVal.textContent = mtxt;
    out.innerHTML =
      '<div class="calc-row"><span>Сам номер (через MagzGold)</span><b class="calc-free">бесплатно</b></div>' +
      '<div class="calc-row"><span>Абонплата ' + fmt(monthly) + "/мес × " + m + "</span><b>" + fmt(abon) + "</b></div>" +
      '<div class="calc-total"><span>Итого за ' + mtxt + "</span><b>" + fmt(abon) + "</b></div>" +
      '<div class="calc-note">Номер достаётся <b>бесплатно</b> — платите только абонплату тарифа. ' +
      'Номер становится платным только при <b>переносе к другому оператору</b> — цену в этом случае уточняйте ' +
      'у оператора.</div>' +
      '<a class="btn-primary calc-cta" href="/kategoriya/' + c.slug + '/">Смотреть ' + c.name.toLowerCase() + " номера</a>";
  }

  catSel.addEventListener("change", calc);
  [tarSel, months].forEach(function (el) { if (el) el.addEventListener("input", calc); });
  calc();
})();
