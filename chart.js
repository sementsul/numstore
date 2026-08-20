/* MagzGold — график динамики средней абонплаты тарифа по категориям номеров.
   Данные: /data/price_history.json (копится кроном). Рисуем на canvas сами (self-contained, без библиотек).
   Кнопки диапазонов (неделя…10 лет) показываются только когда истории хватает — «появляются по мере накопления». */
(function () {
  var cv = document.getElementById("priceChart");
  var rangesEl = document.getElementById("chartRanges");
  var legendEl = document.getElementById("chartLegend");
  var noteEl = document.getElementById("chartNote");
  if (!cv) return;
  var COLORS = { "Бронза": "#c98a4b", "Серебро": "#9aa4b2", "Золото": "#e0b64a", "Платина": "#6fb0dd", "Бриллиант": "#b98ce6" };
  var RANGES = [{ k: 7, l: "Неделя" }, { k: 30, l: "Месяц" }, { k: 90, l: "3 месяца" }, { k: 180, l: "6 месяцев" },
                { k: 365, l: "Год" }, { k: 1095, l: "3 года" }, { k: 1825, l: "5 лет" }, { k: 3650, l: "10 лет" }];
  var DATA = null, cats = [], sel = 0;

  function dayNum(s) { var p = s.split("-"); return Date.UTC(+p[0], +p[1] - 1, +p[2]) / 86400000; }
  function fmtDate(s) { var p = s.split("-"); return p[2] + "." + p[1] + "." + p[0].slice(2); }
  function rub(n) { return Math.round(n).toLocaleString("ru-RU") + " ₽"; }

  fetch("/data/price_history.json").then(function (r) { return r.json(); }).then(function (j) {
    DATA = j; cats = j.categories || [];
    buildRanges(); draw();
    window.addEventListener("resize", draw);
  }).catch(function () { if (noteEl) noteEl.textContent = "Не удалось загрузить историю цен."; });

  function spanDays() { var p = DATA.points; return p.length < 2 ? 0 : dayNum(p[p.length - 1].date) - dayNum(p[0].date); }
  function buildRanges() {
    var span = spanDays();
    var avail = RANGES.filter(function (r) { return span >= r.k; });
    var btns = avail.concat([{ k: 0, l: "Всё" }]);
    sel = avail.length ? avail[avail.length - 1].k : 0;
    rangesEl.innerHTML = btns.map(function (r) { return '<button class="chart-btn" data-k="' + r.k + '">' + r.l + "</button>"; }).join("");
    Array.prototype.forEach.call(rangesEl.querySelectorAll(".chart-btn"), function (b) {
      b.addEventListener("click", function () { sel = +b.getAttribute("data-k"); mark(); draw(); });
    });
    mark();
  }
  function mark() {
    Array.prototype.forEach.call(rangesEl.querySelectorAll(".chart-btn"), function (b) {
      b.classList.toggle("on", +b.getAttribute("data-k") === sel);
    });
  }
  function visiblePoints() {
    var p = DATA.points || [];
    if (!sel || p.length < 2) return p;
    var from = dayNum(p[p.length - 1].date) - sel;
    return p.filter(function (x) { return dayNum(x.date) >= from; });
  }

  function draw() {
    if (!DATA) return;
    var pts = visiblePoints();
    var W = cv.clientWidth || (cv.parentNode && cv.parentNode.clientWidth) || 700, H = 360, dpr = window.devicePixelRatio || 1;
    cv.width = W * dpr; cv.height = H * dpr; cv.style.height = H + "px";
    var ctx = cv.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0); ctx.clearRect(0, 0, W, H);
    var padL = 58, padR = 16, padT = 16, padB = 34, w = W - padL - padR, h = H - padT - padB;

    var vals = [];
    pts.forEach(function (pt) { cats.forEach(function (c) { var v = pt.avg[c]; if (v != null) vals.push(v); }); });
    if (!vals.length) { if (noteEl) noteEl.textContent = "Нет данных."; return; }
    var mn = Math.floor(Math.min.apply(null, vals) / 500) * 500;
    var mx = Math.ceil(Math.max.apply(null, vals) / 500) * 500; if (mx === mn) mx += 500;
    var x0 = dayNum(pts[0].date), x1 = dayNum(pts[pts.length - 1].date), xspan = (x1 - x0) || 1;
    function X(d) { return padL + (pts.length === 1 ? w / 2 : (dayNum(d) - x0) / xspan * w); }
    function Y(v) { return padT + h - (v - mn) / (mx - mn) * h; }

    ctx.font = "12px -apple-system,sans-serif"; ctx.textBaseline = "middle";
    for (var i = 0; i <= 5; i++) {
      var v = mn + (mx - mn) * i / 5, y = Y(v);
      ctx.strokeStyle = "rgba(255,255,255,.07)"; ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(W - padR, y); ctx.stroke();
      ctx.fillStyle = "#969ba8"; ctx.textAlign = "right"; ctx.fillText(rub(v), padL - 8, y);
    }
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    (pts.length <= 1 ? [0] : [0, Math.floor((pts.length - 1) / 2), pts.length - 1]).forEach(function (ix) {
      ctx.fillStyle = "#969ba8"; ctx.fillText(fmtDate(pts[ix].date), X(pts[ix].date), H - padB + 8);
    });

    cats.forEach(function (c) {
      var col = COLORS[c] || "#888";
      ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = 2;
      ctx.beginPath(); var started = false;
      pts.forEach(function (pt) { var v = pt.avg[c]; if (v == null) return; var xx = X(pt.date), yy = Y(v); if (!started) { ctx.moveTo(xx, yy); started = true; } else ctx.lineTo(xx, yy); });
      ctx.stroke();
      pts.forEach(function (pt) { var v = pt.avg[c]; if (v == null) return; ctx.beginPath(); ctx.arc(X(pt.date), Y(v), pts.length === 1 ? 4 : 2.5, 0, 7); ctx.fill(); });
    });

    if (legendEl) legendEl.innerHTML = cats.map(function (c) {
      var last = pts[pts.length - 1].avg[c];
      return '<span class="lg"><i style="background:' + (COLORS[c] || "#888") + '"></i>' + c + " <b>" + (last != null ? rub(last) : "—") + "</b></span>";
    }).join("");
    if (noteEl) noteEl.textContent = pts.length === 1
      ? "История копится с " + fmtDate(DATA.points[0].date) + ". Кнопки диапазонов (неделя, месяц, год…) появятся по мере накопления данных."
      : "Средняя абонплата тарифа по категориям, ₽/мес. Данные обновляются автоматически.";
  }
})();
