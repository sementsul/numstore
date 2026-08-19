/* MagzGold — гео-баннер: по IP определяем город (ipwho.is, способ A) и, если он среди наших
   гео-страниц и юзер не на ней, мягко предлагаем открыть. Дропдаун — сменить город. × — больше не звать.
   Сбой/чужой город/Telegram — молча ничего. Никаких данных не храним, только localStorage-отказ. */
(function () {
  var CITIES = [
    { slug: "moskva",     name: "Москве",             nom: "Москва",           match: ["moscow", "москва"] },
    { slug: "spb",        name: "Санкт-Петербурге",   nom: "Санкт-Петербург",  match: ["peterburg", "petersburg", "piter", "санкт-петер", "ленинград", "leningrad"] },
    { slug: "krasnodar",  name: "Краснодаре",         nom: "Краснодар",        match: ["krasnodar", "краснодар"] },
    { slug: "sochi",      name: "Сочи",               nom: "Сочи",             match: ["sochi", "сочи", "adler", "адлер"] },
    { slug: "rostov",     name: "Ростове-на-Дону",    nom: "Ростов-на-Дону",   match: ["rostov", "ростов"] },
    { slug: "grozny",     name: "Грозном",            nom: "Грозный",          match: ["grozny", "грозный", "chechn", "чечн"] },
    { slug: "mahachkala", name: "Махачкале",          nom: "Махачкала",        match: ["makhachkala", "mahachkala", "махачкала", "dagestan", "дагестан", "kaspiysk", "каспийск"] }
  ];
  var KEY = "mg_geo_banner_off";

  // Тест-режим: ?geo=<slug> принудительно показывает баннер (в обход IP и отказа) — для проверки.
  var forced = (/[?&]geo=([a-z]+)/.exec(location.search) || [])[1];
  if (forced) {
    for (var f = 0; f < CITIES.length; f++) { if (CITIES[f].slug === forced) { showBanner(CITIES[f]); return; } }
  }

  try { if (localStorage.getItem(KEY)) return; } catch (e) {}
  // в Telegram Mini App не мешаем
  if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) return;

  fetch("https://ipwho.is/")
    .then(function (r) { return r.json(); })
    .then(function (d) {
      if (!d || d.success === false) return;
      var hay = ((d.city || "") + " " + (d.region || "")).toLowerCase();
      var city = null;
      for (var i = 0; i < CITIES.length; i++) {
        var m = CITIES[i].match;
        for (var j = 0; j < m.length; j++) { if (hay.indexOf(m[j]) >= 0) { city = CITIES[i]; break; } }
        if (city) break;
      }
      if (!city) return;
      if (location.pathname.indexOf("/krasivye-nomera/" + city.slug + "/") === 0) return; // уже здесь
      showBanner(city);
    })
    .catch(function () {});

  function showBanner(city) {
    var b = document.createElement("div");
    b.className = "geo-banner";
    var opts = CITIES.map(function (c) {
      return '<option value="' + c.slug + '"' + (c.slug === city.slug ? " selected" : "") + ">" + c.nom + "</option>";
    }).join("");
    b.innerHTML =
      '<span class="geo-txt">Вы, похоже, из города <b>' + city.nom + "</b>. Открыть красивые номера в " + city.name + "?</span>" +
      '<a class="geo-go" href="/krasivye-nomera/' + city.slug + '/">Открыть →</a>' +
      '<select class="geo-sel" aria-label="Другой город">' + opts + "</select>" +
      '<button class="geo-x" type="button" aria-label="Закрыть">×</button>';
    document.body.appendChild(b);
    requestAnimationFrame(function () { b.classList.add("show"); });
    b.querySelector(".geo-sel").addEventListener("change", function () {
      location.href = "/krasivye-nomera/" + this.value + "/";
    });
    b.querySelector(".geo-x").addEventListener("click", function () {
      b.classList.remove("show");
      try { localStorage.setItem(KEY, "1"); } catch (e) {}
      setTimeout(function () { if (b.parentNode) b.remove(); }, 250);
    });
  }
})();
