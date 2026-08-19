/* MagzGold — страница /tarify/: список тарифов рисуем из ЖИВОГО API (ban-proof, в браузере посетителя),
   чтобы кнопки всегда соответствовали текущим тарифам Безлимит. Статические карточки в HTML — фолбэк
   для поисковика и на случай сбоя сети. */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var grid = document.getElementById("tariffGrid");
  if (!grid || !CFG) return;
  var BAD = /Анадыр|Норильск/i; // региональные тарифы прячем (как в каталоге)
  function money(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽"; }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  fetch(CFG.API_BASE + "/super-link/phones/mask-category?expand=tariff&is_reserved=false&per_page=100&phone_pattern=9NNNNNNNNN",
        { headers: { Authorization: CFG.API_TOKEN } })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || typeof d !== "object") return;
      var m = {};
      Object.keys(d).forEach(function (k) {
        var v = d[k];
        if (v && Array.isArray(v.items)) v.items.forEach(function (p) {
          var t = p.tariff;
          if (t && t.price != null && t.name && !BAD.test(t.name) && !m[t.price]) m[t.price] = { name: t.name, price: t.price };
        });
      });
      var list = Object.keys(m).map(function (k) { return m[k]; }).sort(function (a, b) { return a.price - b.price; });
      if (!list.length) return; // сеть/данные пусты — оставляем статический фолбэк
      grid.innerHTML = list.map(function (t) {
        return '<a class="blog-card" href="/?tariff=' + t.price + '"><h2>' + esc(t.name) + "</h2>" +
          "<p>Абонплата " + money(t.price) + "/мес · безлимит на звонки Безлимит и Билайн · красивые номера на этом тарифе</p></a>";
      }).join("");
    })
    .catch(function () {});
})();
