/* numstore — клиентская витрина номеров Безлимит.
   Каталог тянется в браузере посетителя напрямую из API (CORS открыт) — ban-proof. */
(function () {
  var CFG = window.NUMSTORE_CONFIG;
  var $ = function (id) { return document.getElementById(id); };
  var statusEl = $("status"), gridEl = $("grid"), countEl = $("count");
  var searchEl = $("search"), tariffEl = $("tariff"), sortEl = $("sort");

  var ALL = []; // плоский список номеров

  // 9584949494 -> +7 958 494-94-94
  function fmtPhone(p) {
    var s = String(p).replace(/\D/g, "").slice(-10);
    if (s.length !== 10) return "+7 " + s;
    return "+7 " + s.slice(0, 3) + " " + s.slice(3, 6) + "-" + s.slice(6, 8) + "-" + s.slice(8, 10);
  }
  function fmtMoney(n) {
    if (n == null || isNaN(n)) return "";
    return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " ") + " ₽";
  }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  function api(path) {
    return fetch(CFG.API_BASE + path, { headers: { Authorization: CFG.API_TOKEN } })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      });
  }

  function load() {
    api("/super-link/phones/collection?expand=phones.tariff")
      .then(function (data) {
        var items = (data && data.items) || [];
        ALL = [];
        items.forEach(function (col) {
          (col.phones || []).forEach(function (ph) {
            ph._collection = col.name || "";
            ALL.push(ph);
          });
        });
        if (!ALL.length) {
          statusEl.textContent = "Номера не найдены.";
          return;
        }
        statusEl.style.display = "none";
        buildTariffOptions();
        render();
      })
      .catch(function (e) {
        statusEl.textContent = "Не удалось загрузить номера (" + e.message + "). Обнови страницу.";
      });
  }

  function buildTariffOptions() {
    var seen = {};
    ALL.forEach(function (p) {
      var t = p.tariff && p.tariff.name;
      if (t && !seen[t]) seen[t] = true;
    });
    Object.keys(seen).sort().forEach(function (name) {
      var o = document.createElement("option");
      o.value = name; o.textContent = name;
      tariffEl.appendChild(o);
    });
  }

  function currentList() {
    var q = (searchEl.value || "").replace(/\D/g, "");
    var tf = tariffEl.value;
    var list = ALL.filter(function (p) {
      if (q && String(p.phone).indexOf(q) === -1) return false;
      if (tf && !(p.tariff && p.tariff.name === tf)) return false;
      return true;
    });
    var s = sortEl.value;
    if (s === "price-asc" || s === "price-desc") {
      list = list.slice().sort(function (a, b) {
        var pa = (a.tariff && a.tariff.price) || 0, pb = (b.tariff && b.tariff.price) || 0;
        return s === "price-asc" ? pa - pb : pb - pa;
      });
    }
    return list;
  }

  function render() {
    var list = currentList();
    countEl.textContent = list.length + " " + plural(list.length, ["номер", "номера", "номеров"]);
    gridEl.innerHTML = list.map(card).join("");
  }

  function card(p) {
    var t = p.tariff || {};
    var specs = [];
    if (t.minutes != null) specs.push(t.minutes + " мин");
    if (t.sms != null) specs.push(t.sms + " смс");
    if (t.internet != null) specs.push(t.internet + " ГБ");
    return (
      '<article class="num">' +
        '<div class="num-phone">' + esc(fmtPhone(p.phone)) + "</div>" +
        (t.name ? '<div class="num-tariff">' + esc(t.name) + "</div>" : "") +
        (specs.length ? '<div class="num-specs">' + esc(specs.join(" · ")) + "</div>" : "") +
        (t.price != null ? '<div class="num-price">' + esc(fmtMoney(t.price)) + "<span>/мес</span></div>" : "") +
        '<a class="num-buy" href="' + esc(CFG.REF_STORE_URL) + '" target="_blank" rel="noopener">Купить</a>' +
      "</article>"
    );
  }

  function plural(n, forms) {
    var n10 = n % 10, n100 = n % 100;
    if (n10 === 1 && n100 !== 11) return forms[0];
    if (n10 >= 2 && n10 <= 4 && (n100 < 10 || n100 >= 20)) return forms[1];
    return forms[2];
  }

  searchEl.addEventListener("input", render);
  tariffEl.addEventListener("change", render);
  sortEl.addEventListener("change", render);
  load();
})();
