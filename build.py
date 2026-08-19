#!/usr/bin/env python3
# MagzGold — генератор статических SEO-страниц (главная + категории + sitemap/robots).
# Витрина (номера) остаётся клиентской (ban-proof); вокруг — уникальный текст под запросы.
import os, shutil, html
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")

SITE = {
    "name": "MagzGold",
    "base": "https://magzgold.ru",
}

# Категории: slug, код для API (mask_categories), витринное имя, SEO-тексты.
CATEGORIES = [
    {"slug": "brilliant", "pmin": 400000, "pmax": 4000000, "code": "brilliant,brilliant_super", "name": "Бриллиантовые",
     "h1": "Бриллиантовые номера",
     "desc": "Бриллиантовые номера телефонов — самая красивая категория: подбор по маске, тарифы, бронирование онлайн на MagzGold.",
     "intro": "Бриллиантовые номера — вершина категорий красоты: максимально «чистые» комбинации, "
              "повторяющиеся и зеркальные цифры, лёгкие для запоминания. Такой номер подчёркивает статус "
              "и почти не встречается в свободной продаже. Ниже — доступные бриллиантовые номера с тарифами; "
              "уточните комбинацию маской и забронируйте онлайн."},
    {"slug": "platinum", "pmin": 25000, "pmax": 600000, "code": "platinum,platinum_lite", "name": "Платиновые",
     "h1": "Платиновые номера",
     "desc": "Платиновые номера телефонов на MagzGold: красивые комбинации, разные тарифы, подбор по маске и онлайн-бронь.",
     "intro": "Платиновые номера — премиальная категория чуть доступнее бриллиантовых: эффектные сочетания "
              "цифр, которые приятно диктовать и легко запомнить. Подходят тем, кто хочет заметный номер без "
              "переплаты за топ-категорию. Выберите подходящий по маске и тарифу."},
    {"slug": "gold", "pmin": 50000, "pmax": 200000, "code": "gold", "name": "Золотые",
     "h1": "Золотые номера",
     "desc": "Золотые номера телефонов: баланс красоты и цены. Подбор по маске, тарифы, бронирование онлайн — MagzGold.",
     "intro": "Золотые номера — оптимальный баланс красоты и стоимости: узнаваемые комбинации, повторы и "
              "приятные окончания за разумные деньги. Самая популярная категория для личного и рабочего номера. "
              "Отфильтруйте по тарифу и подберите свой."},
    {"slug": "silver", "pmin": 12000, "pmax": 100000, "code": "silver,silver_special,silver_special_2", "name": "Серебряные",
     "h1": "Серебряные номера",
     "desc": "Серебряные номера телефонов на MagzGold: доступные красивые комбинации, тарифы, онлайн-бронь.",
     "intro": "Серебряные номера — доступная красота: аккуратные комбинации, которые проще запомнить, чем "
              "случайный набор, но без премиальной наценки. Хороший выбор, если нужен приятный номер недорого."},
    {"slug": "bronze", "pmin": 3000, "pmax": 12000, "code": "bronze,bronze_vip,bronze AAA", "name": "Бронзовые",
     "h1": "Бронзовые номера",
     "desc": "Бронзовые номера телефонов: самый доступный вход в красивые номера. Подбор по маске и тарифу — MagzGold.",
     "intro": "Бронзовые номера — начальная категория красоты и самый доступный вход: лёгкие для запоминания "
              "сочетания по минимальной цене. Отличный вариант для второго номера или подарка."},
]

# Паттерны красоты: slug (top-level URL), маска phone_pattern (N=любая, буквы=повтор), имя, SEO-тексты.
PATTERNS = [
    {"slug": "zerkalnye", "mask": "NNNNabccba", "name": "Зеркальные", "h1": "Зеркальные номера",
     "desc": "Зеркальные номера телефонов — цифры симметричны (…abc-cba). Подбор и бронирование на MagzGold.",
     "intro": "Зеркальные номера — красивая симметрия: концовка читается одинаково в обе стороны (…abc-cba). "
              "Легко запоминаются и приятно диктуются. Ниже — доступные зеркальные номера; уточните комбинацию маской."},
    {"slug": "povtory", "mask": "NNNNNNNaaa", "name": "С повторами", "h1": "Номера с повторами",
     "desc": "Номера с повторяющимися цифрами (три одинаковые в конце, …-XXX) — купить и забронировать на MagzGold.",
     "intro": "Номера с повторами — одинаковые цифры подряд (…-XXX). Чем длиннее повтор, тем «чище» и дороже номер. "
              "Запоминающийся выбор для личного или рабочего номера."},
    {"slug": "pary", "mask": "NNNNNNabab", "name": "Пары", "h1": "Номера-пары (ABAB)",
     "desc": "Номера-пары — ритмичное чередование двух цифр (…ABAB). Красивые и запоминающиеся. MagzGold.",
     "intro": "Номера-пары — чередование двух цифр (…ABAB). Ритмичные, легко диктуются и хорошо смотрятся."},
    {"slug": "kruglye", "mask": "NNNNNNN000", "name": "Круглые", "h1": "Круглые номера",
     "desc": "Круглые номера — оканчиваются на нули (…000). Солидно и легко запомнить. Подбор на MagzGold.",
     "intro": "Круглые номера оканчиваются на нули (…000) — выглядят солидно и запоминаются с первого раза."},
    {"slug": "na-777", "mask": "NNNNNNN777", "name": "На 777", "h1": "Номера на 777",
     "desc": "Номера, оканчивающиеся на 777 (три семёрки) — счастливая комбинация. Подбор и бронь на MagzGold.",
     "intro": "Номера на 777 — три семёрки в конце, «счастливое» окончание, которое легко запоминается."},
    {"slug": "na-999", "mask": "NNNNNNN999", "name": "На 999", "h1": "Номера на 999",
     "desc": "Номера, оканчивающиеся на 999 (три девятки). Красиво и запоминается. Подбор на MagzGold.",
     "intro": "Номера на 999 — три девятки в конце, эффектное и запоминающееся окончание."},
    {"slug": "na-888", "mask": "NNNNNNN888", "name": "На 888", "h1": "Номера на 888",
     "desc": "Номера, оканчивающиеся на 888 (три восьмёрки). Подбор и бронирование на MagzGold.",
     "intro": "Номера на 888 — три восьмёрки в конце; восьмёрка символизирует достаток и гармонию."},
]

# Префиксы (первые 3 цифры мобильного, +7 9XX). Страница /kod/<pfx>/ = маска <pfx>NNNNNNN.
PREFIXES = ["900", "903", "905", "906", "909", "916", "925", "929",
            "950", "960", "965", "966", "967", "968", "969", "999"]

# FAQ: вопрос → ответ (HTML в ответе допустим). Идёт в FAQPage schema.
FAQ = [
    ("Что такое красивый номер?",
     "Красивый номер — телефонный номер с запоминающейся комбинацией цифр: повторами, зеркальностью, "
     "круглыми окончаниями. Чем «чище» комбинация, тем выше категория (от бронзы до бриллианта)."),
    ("Как забронировать номер?",
     "Выберите номер в каталоге (по маске, категории или тарифу) и нажмите «Забронировать». Бронь удержит "
     "номер за вами ограниченное время; оформление и оплата — у оператора."),
    ("Сколько стоит красивый номер?",
     "Стоимость зависит от красоты: бронза — от 3 000 ₽, бриллиант — от 400 000 ₽. Оцените диапазон на "
     '<a href="/skolko-stoit-nomer/">калькуляторе стоимости</a>. Абонплата тарифа оплачивается отдельно.'),
    ("Регион влияет на цену номера?",
     "Нет. У оператора цена номера определяется его красотой (категорией), а не кодом или регионом."),
    ("Кто оказывает услуги связи?",
     "Оператор связи ООО «Безлимит». MagzGold — информационная витрина, которая помогает подобрать и "
     "забронировать номер; оформление и оплата проходят на стороне оператора."),
    ("Можно ли выбрать номер с моей датой рождения?",
     "Да. В каталоге задайте маску — зафиксируйте нужные цифры на позициях, а остальные оставьте любыми."),
    ("Как я получу номер — нужно ехать в офис?",
     "Нет. Оператор бесплатно доставляет SIM-карту по всей России. Если смартфон поддерживает eSIM, номер "
     "можно оформить вообще без пластиковой карты и ожидания — прямо на устройстве."),
]

# Гайды/блог: slug, title, desc, h1, body (HTML).
BLOG = [
    {"slug": "kak-vybrat-krasivyy-nomer", "h1": "Как выбрать красивый номер",
     "title": "Как выбрать красивый номер телефона — гайд | MagzGold",
     "desc": "Как выбрать красивый номер: категории красоты, паттерны (зеркальные, повторы, круглые), на что смотреть и как не переплатить. Пошаговый гайд MagzGold.",
     "body": (
        "<p>Красивый номер — это не просто набор цифр, а комбинация, которую легко запомнить и приятно "
        "диктовать. Разберём, из чего складывается «красота» и как выбрать номер под задачу и бюджет.</p>"
        "<h2>1. Определите категорию красоты</h2>"
        "<p>Все красивые номера делятся на категории — от доступных до премиальных: "
        '<a href="/kategoriya/bronze/">бронзовые</a>, <a href="/kategoriya/silver/">серебряные</a>, '
        '<a href="/kategoriya/gold/">золотые</a>, <a href="/kategoriya/platinum/">платиновые</a> и '
        '<a href="/kategoriya/brilliant/">бриллиантовые</a>. Чем «чище» комбинация, тем выше категория и цена.</p>'
        "<h2>2. Выберите тип комбинации (паттерн)</h2>"
        "<p>Подумайте, какой рисунок вам ближе: "
        '<a href="/zerkalnye/">зеркальные</a> (симметрия), <a href="/povtory/">с повторами</a> (одинаковые цифры), '
        '<a href="/pary/">пары</a> (ABAB) или <a href="/kruglye/">круглые</a> (окончание на нули). '
        "Паттерн влияет и на запоминаемость, и на стоимость.</p>"
        "<h2>3. Прикиньте бюджет</h2>"
        '<p>Стоимость сильно зависит от красоты. Оцените диапазон на <a href="/skolko-stoit-nomer/">калькуляторе '
        "стоимости</a>: он покажет цену номера по категории и текущую абонплату тарифа.</p>"
        "<h2>4. Подберите точную комбинацию маской</h2>"
        "<p>В каталоге можно задать маску: зафиксировать нужные цифры на позициях, оставить остальные любыми "
        "или отметить повторы буквами. Так вы найдёте номер с личными датами или любимыми цифрами.</p>"
        "<h2>5. Забронируйте онлайн</h2>"
        '<p>Понравившийся номер бронируется в пару кликов — подробнее в гайде '
        '<a href="/blog/kak-zabronirovat-nomer/">как забронировать номер</a>.</p>'),
     },
    {"slug": "kategorii-krasivyh-nomerov", "h1": "Категории красивых номеров",
     "title": "Категории красивых номеров: бронза, серебро, золото, платина, бриллиант | MagzGold",
     "desc": "Категории красивых номеров и их отличия: бронза, серебро, золото, платина, бриллиант — что означают и сколько стоят. Гайд MagzGold.",
     "body": (
        "<p>Красивые номера ранжируют по категориям — они отражают редкость комбинации и определяют цену. "
        "Разберём каждую от доступной к премиальной.</p>"
        '<h2><a href="/kategoriya/bronze/">Бронзовые</a> — от 3 000 ₽</h2>'
        "<p>Начальная категория: лёгкие для запоминания сочетания, пары и небольшие повторы. Доступный вход "
        "в красивые номера, хороший вариант для второго номера.</p>"
        '<h2><a href="/kategoriya/silver/">Серебряные</a> — от 12 000 ₽</h2>'
        "<p>Аккуратные комбинации заметно приятнее случайного набора, но без премиальной наценки.</p>"
        '<h2><a href="/kategoriya/gold/">Золотые</a> — от 50 000 ₽</h2>'
        "<p>Оптимальный баланс красоты и статуса: узнаваемые повторы и ровные окончания. Популярный выбор.</p>"
        '<h2><a href="/kategoriya/platinum/">Платиновые</a> — от 25 000 ₽</h2>'
        "<p>Премиальные комбинации с выраженной симметрией и длинными повторами.</p>"
        '<h2><a href="/kategoriya/brilliant/">Бриллиантовые</a> — от 400 000 ₽</h2>'
        "<p>Вершина: максимально «чистые» номера (например, семь одинаковых цифр). Встречаются редко и "
        "подчёркивают статус.</p>"
        '<p>Точную цену конкретного номера удобно прикинуть на <a href="/skolko-stoit-nomer/">калькуляторе</a>.</p>'),
     },
    {"slug": "kak-zabronirovat-nomer", "h1": "Как забронировать и купить красивый номер",
     "title": "Как забронировать и купить красивый номер — инструкция | MagzGold",
     "desc": "Как забронировать красивый номер онлайн: поиск по маске, выбор, бронь и оформление у оператора. Простая инструкция MagzGold.",
     "body": (
        "<p>Забронировать красивый номер можно за несколько минут, не выходя из дома. Разберём по шагам.</p>"
        "<h2>Шаг 1. Найдите номер</h2>"
        '<p>Откройте <a href="/">каталог</a>, выберите категорию слева или задайте маску: зафиксируйте нужные '
        "цифры, остальное оставьте любыми. Отфильтруйте по тарифу и цене.</p>"
        "<h2>Шаг 2. Забронируйте</h2>"
        "<p>Нажмите «Забронировать» на карточке номера. Бронь удерживает номер за вами ограниченное время "
        "(обычно около часа), чтобы его не занял другой покупатель.</p>"
        "<h2>Шаг 3. Оформите у оператора</h2>"
        "<p>Дальше оформление и оплата проходят на стороне оператора связи по его условиям. Абонентская плата "
        "тарифа списывается ежемесячно, стоимость самого номера — единоразово.</p>"
        '<p>Не уверены в бюджете? Сначала загляните на <a href="/skolko-stoit-nomer/">калькулятор стоимости</a> '
        'или почитайте, <a href="/blog/kak-vybrat-krasivyy-nomer/">как выбрать красивый номер</a>.</p>'),
     },
]


# Тарифы (из /filters mask_tariff): slug, id, цена (= число в названии). Специфику не выдумываем.
TARIFFS = [
    {"slug": "ultra-399", "id": 16194, "price": 399},
    {"slug": "ultra-550", "id": 16184, "price": 550},
    {"slug": "ultra-750", "id": 16185, "price": 750},
    {"slug": "ultra-950", "id": 16186, "price": 950},
    {"slug": "ultra-1300", "id": 16187, "price": 1300},
    {"slug": "ultra-1600", "id": 16188, "price": 1600},
    {"slug": "ultra-2000", "id": 16189, "price": 2000},
    {"slug": "ultra-3000", "id": 16190, "price": 3000},
    {"slug": "ultra-4000", "id": 16191, "price": 4000},
    {"slug": "ultra-5000", "id": 16192, "price": 5000},
]
for _t in TARIFFS:
    _t["name"] = "Безлимит ULTRA %d" % _t["price"]


def _dlinks(items):
    return "".join('<a href="%s">%s</a>' % (h, html.escape(t)) for h, t in items)


def _build_drawer():
    other = [("/", "Все номера"), ("/tarify/", "Тарифы"), ("/kody/", "Номера по кодам"), ("/blog/", "Блог"), ("/faq/", "Вопросы и ответы"), ("/skolko-stoit-nomer/", "Сколько стоит номер"), ("/o-servise/", "О сервисе")]
    legal = [("/politika/", "Политика конфиденциальности"), ("/polzovatelskoe-soglashenie/", "Пользовательское соглашение")]
    return (
        '<div class="drawer-backdrop" id="drawerBg"></div>'
        '<aside class="drawer" id="drawer" aria-label="Меню сайта">'
        '<button class="drawer-close" aria-label="Закрыть">\u00d7</button>'
        '<a class="drawer-brand" href="/">Magz<span class="brand-gold">Gold</span></a>'
        '<div class="drawer-group"><h4>Разделы</h4>%s</div>'
        '<div class="drawer-group"><h4>Документы</h4>%s</div>'
        '</aside>'
    ) % (_dlinks(other), _dlinks(legal))


_DRAWER = _build_drawer()


def esc(s):
    return html.escape(str(s), quote=True)


def nav_links(active_slug=None):
    items = ['<a href="/"%s>Все номера</a>' % (' class="active"' if active_slug is None else "")]
    for c in CATEGORIES:
        cls = ' class="active"' if c["slug"] == active_slug else ""
        items.append('<a href="/kategoriya/%s/"%s>%s</a>' % (c["slug"], cls, esc(c["name"])))
    return '<nav class="catnav">' + "".join(items) + "</nav>"


def patnav(active_slug=None):
    items = []
    for p in PATTERNS:
        cls = ' class="active"' if p["slug"] == active_slug else ""
        items.append('<a href="/%s/"%s>%s</a>' % (p["slug"], cls, esc(p["name"])))
    return '<div class="patnav-wrap"><span class="patnav-label">Паттерны:</span><nav class="catnav">' + "".join(items) + "</nav></div>"


def crumbs(active=None):
    parts = ['<a href="/">Главная</a>']
    if active:
        parts.append("<span>" + esc(active) + "</span>")
    return '<nav class="crumbs">' + " / ".join(parts) + "</nav>"


# Разметка витрины (общая для всех страниц) — маска-поиск + сайдбар-фильтры + сетка.
VITRINA = """    <section class="search-box">
      <div class="cubes" id="cubes" aria-label="Маска номера из 10 цифр"><span class="cube-prefix">+7</span></div>
      <div class="cube-actions">
        <button id="find" class="btn-primary">Найти по маске</button>
        <button id="reset" class="btn-ghost">Сбросить</button>
      </div>
      <p class="cube-hint">Цифра — точная позиция · пусто — любая · буква (a, b, …) — повторяющаяся цифра</p>
      <div class="ref-bar" id="refBar" hidden>
        <input id="refLink" class="ref-link" readonly>
        <button id="copyLink" class="btn-ghost">Копировать</button>
        <a id="openStore" class="btn-primary" target="_blank" rel="noopener">Открыть в магазине</a>
      </div>
    </section>
    <div class="layout">
      <aside class="sidebar">
        <div class="filter-group"><h3 class="filter-title">Категория</h3><ul class="filter-list" id="fCat"></ul></div>
        <div class="filter-group"><h3 class="filter-title">Цена тарифа</h3><ul class="filter-list" id="fPrice"></ul></div>
        <div class="filter-group"><h3 class="filter-title">Тариф</h3><ul class="filter-list" id="fTariff"></ul></div>
      </aside>
      <div class="content">
        <div class="controls">
          <select id="sort">
            <option value="default">По умолчанию</option>
            <option value="price-asc">Цена тарифа ↑</option>
            <option value="price-desc">Цена тарифа ↓</option>
          </select>
          <button id="favToggle" class="btn-ghost btn-sm" type="button">★ Избранное <span id="favCount"></span></button>
          <span id="count" class="count"></span>
        </div>
        <div id="status" class="status">Загружаю номера…</div>
        <div id="grid"></div>
        <div class="more-wrap"><button id="more" class="btn-ghost" hidden>Показать ещё</button></div>
      </div>
    </div>"""

PAGE_TMPL = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="https://magzgold.ru/og.png">
<meta property="og:site_name" content="MagzGold">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/styles.css">
{metrika}
{page_js}
{schema}
</head>
<body>
<header class="top">
  <div class="wrap">
    <button class="burger" id="burger" aria-label="Открыть меню">≡</button>
{header_block}
    {nav}
  </div>
</header>
<main class="wrap">
{main_top}
{vitrina}
</main>
<footer class="foot">
  <div class="wrap">
    {footnav}
    <nav class="catnav footlinks"><a href="/blog/">Блог</a><a href="/skolko-stoit-nomer/">Сколько стоит номер</a><a href="/tarify/">Тарифы</a><a href="/kody/">Коды</a><a href="/faq/">FAQ</a><a href="/o-servise/">О сервисе</a><a href="/politika/">Политика</a><a href="/polzovatelskoe-soglashenie/">Соглашение</a></nav>
    <p>MagzGold — официальный партнёр оператора «Безлимит». Информационная витрина красивых номеров; подключение и оплата на стороне оператора.</p>
  </div>
</footer>
{drawer}
<script src="/nav.js"></script>
{scripts}
</body>
</html>
"""
SCRIPTS = '<script src="/config.js"></script>\n<script src="/app.js"></script>'
METRIKA = '<!-- Yandex.Metrika counter -->\n<script type="text/javascript">\n    (function(m,e,t,r,i,k,a){\n        m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};\n        m[i].l=1*new Date();\n        for (var j = 0; j < document.scripts.length; j++) {if (document.scripts[j].src === r) { return; }}\n        k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.insertBefore(k,a)\n    })(window, document,\'script\',\'https://mc.yandex.ru/metrika/tag.js?id=111737982\', \'ym\');\n\n    ym(111737982, \'init\', {ssr:true, webvisor:true, clickmap:true, ecommerce:"dataLayer", referrer: document.referrer, url: location.href, accurateTrackBounce:true, trackLinks:true});\n</script>\n<noscript><div><img src="https://mc.yandex.ru/watch/111737982" style="position:absolute; left:-9999px;" alt="" /></div></noscript>\n<!-- /Yandex.Metrika counter -->'
GTAG = '<!-- Google tag (gtag.js) -->\n<script async src="https://www.googletagmanager.com/gtag/js?id=G-R1CLPNLWLD"></script>\n<script>\n  window.dataLayer = window.dataLayer || [];\n  function gtag(){dataLayer.push(arguments);}\n  gtag(\'js\', new Date());\n  gtag(\'config\', \'G-R1CLPNLWLD\');\n</script>\n<!-- /Google tag -->'
METRIKA = METRIKA + "\n" + GTAG


def schema_breadcrumb(active=None):
    items = [{"pos": 1, "name": "Главная", "url": SITE["base"] + "/"}]
    if active:
        url = SITE["base"] + ("/%s/" % active["slug"] if active.get("toplevel") else "/kategoriya/%s/" % active["slug"])
        items.append({"pos": 2, "name": active["name"], "url": url})
    li = ",".join(
        '{"@type":"ListItem","position":%d,"name":"%s","item":"%s"}' % (i["pos"], esc(i["name"]), i["url"])
        for i in items
    )
    return ('<script type="application/ld+json">{"@context":"https://schema.org",'
            '"@type":"BreadcrumbList","itemListElement":[%s]}</script>' % li)


def write(path, content):
    full = os.path.join(DIST, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def home_schema():
    org = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization",'
           '"name":"MagzGold","url":"%s/","logo":"%s/og.png"}</script>') % (SITE["base"], SITE["base"])
    web = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite",'
           '"name":"MagzGold","url":"%s/"}</script>') % SITE["base"]
    return org + web + schema_breadcrumb()


def make_og():
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (13, 15, 19))
    d = ImageDraw.Draw(img)
    FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f1 = ImageFont.truetype(FB, 110); f2 = ImageFont.truetype(FB, 46)
    gold = (201, 165, 88); white = (238, 240, 244); muted = (150, 155, 168)
    m, g = "Magz", "Gold"
    wm = d.textlength(m, font=f1); wg = d.textlength(g, font=f1)
    x = (W - (wm + wg)) / 2; y = 210
    d.text((x, y), m, font=f1, fill=white)
    d.text((x + wm, y), g, font=f1, fill=gold)
    d.rectangle([(W/2 - 60, y + 132), (W/2 + 60, y + 137)], fill=gold)
    sub = "Красивые номера"
    ws = d.textlength(sub, font=f2)
    d.text(((W - ws) / 2, y + 160), sub, font=f2, fill=muted)
    img.save(os.path.join(DIST, "og.png"))


def render_home():
    header_block = ('    <h1 class="hero">Magz<span class="brand-gold">Gold</span>'
                    ' <span class="hero-tag">— премиальные номера</span></h1>')
    intro = ("MagzGold — витрина красивых номеров телефонов. Соберите нужную комбинацию маской или выберите "
             "категорию: бриллиантовые, платиновые, золотые, серебряные, бронзовые. Каждый номер — с тарифом "
             "и мгновенной бронью онлайн. Бесплатная доставка SIM по всей России и eSIM — без визита в офис.")
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="MagzGold — красивые номера: купить и забронировать онлайн",
        desc="MagzGold — красивые и премиальные номера телефонов: подбор по маске и категориям, тарифы, "
             "бронирование онлайн. Бриллиантовые, платиновые, золотые, серебряные и бронзовые номера.",
        canonical=SITE["base"] + "/",
        page_js="",
        schema=home_schema(),
        nav=nav_links(None),
        header_block=header_block,
        main_top='  <p class="page-intro">%s</p>' % intro,
        vitrina=VITRINA,
        footnav=nav_links(None) + patnav(),
        scripts=SCRIPTS,
    )
    write("index.html", html_out)


def render_category(c):
    page_js = '<script>window.PAGE={cat:"%s"};</script>' % c["code"]
    header_block = '    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>'
    main_top = "%s\n  <h1 class=\"page-h1\">%s</h1>\n  <p class=\"page-intro\">%s</p>" % (
        crumbs(c["name"]), esc(c["h1"]), c["intro"])
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="%s номера — купить и забронировать | MagzGold" % c["name"],
        desc=c["desc"],
        canonical=SITE["base"] + "/kategoriya/%s/" % c["slug"],
        page_js=page_js,
        schema=schema_breadcrumb(c),
        nav=nav_links(c["slug"]),
        header_block=header_block,
        main_top=main_top,
        vitrina=VITRINA,
        footnav=nav_links(c["slug"]) + patnav(),
        scripts=SCRIPTS,
    )
    write("kategoriya/%s/index.html" % c["slug"], html_out)


def render_pattern(p):
    page_js = '<script>window.PAGE={mask:"%s"};</script>' % p["mask"]
    header_block = '    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>'
    main_top = "%s\n  <h1 class=\"page-h1\">%s</h1>\n  <p class=\"page-intro\">%s</p>" % (
        crumbs(p["h1"]), esc(p["h1"]), p["intro"])
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="%s — купить и забронировать | MagzGold" % p["h1"],
        desc=p["desc"],
        canonical=SITE["base"] + "/%s/" % p["slug"],
        page_js=page_js,
        schema=schema_breadcrumb({"name": p["h1"], "slug": p["slug"], "toplevel": True}),
        nav=nav_links(None),
        header_block=header_block,
        main_top=main_top,
        vitrina=VITRINA,
        footnav=nav_links(None) + patnav(p["slug"]),
        scripts=SCRIPTS,
    )
    write("%s/index.html" % p["slug"], html_out)


def render_calc():
    cats_js = "[" + ",".join(
        '{"slug":"%s","code":"%s","name":"%s","pmin":%d,"pmax":%d}' % (c["slug"], c["code"], c["name"], c["pmin"], c["pmax"]) for c in CATEGORIES) + "]"
    page_js = "<script>window.CALC_CATS=%s;</script>" % cats_js
    cat_opts = "".join('<option value="%s">%s</option>' % (c["slug"], esc(c["name"])) for c in CATEGORIES)
    body = (
        '<div class="calc">'
        '<div class="calc-form">'
        '<label>Красота номера<select id="calcCat">' + cat_opts + '</select></label>'
        '</div>'
        '<div class="calc-out" id="calcOut"></div>'
        '<a id="calcLink" class="btn-primary" hidden>Показать такие номера</a>'
        '</div>'
        '<section class="seo-text">'
        '<h2>От чего зависит цена красивого номера</h2>'
        '<p><b>Категория красоты.</b> Чем «чище» комбинация — повторы, зеркальность, круглые окончания — тем '
        'выше категория (бронза → серебро → золото → платина → бриллиант) и стоимость. Бриллиантовые номера '
        'встречаются редко и стоят заметно дороже бронзовых.</p>'
        '<p><b>Редкость комбинации.</b> Три и более одинаковых цифры подряд, «зеркала», ровные окончания на нули '
        'и легко запоминаемые сочетания ценятся выше случайного набора.</p>'
        '<p><b>Тариф.</b> Стоимость номера — это абонентская плата тарифа, и она привязана к красоте: чем выше '
        'категория, тем ёмче тариф и дороже номер. Точные условия и итоговую сумму вы видите при бронировании '
        'у оператора.</p>'
        '<p><b>Регион на цену не влияет.</b> У оператора стоимость номера определяется его красотой (категорией), '
        'а не кодом или регионом — одинаковый по красоте номер стоит одинаково.</p>'
        '<p class="calc-disc">Калькулятор показывает официальную стоимость номера по категории (единоразово) '
        'и текущую абонплату тарифа (ежемесячно). Точная цена конкретного номера зависит от его маски внутри '
        'категории — полный прайс в документах оператора: '
        '<a href="https://bezlimit.ru/legal" target="_blank" rel="noopener">bezlimit.ru/legal</a>. '
        'Это не оферта; итоговая сумма — у оператора при оформлении.</p>'
        '</section>'
    )
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="Сколько стоит красивый номер — калькулятор стоимости | MagzGold",
        desc="Сколько стоит красивый номер телефона: онлайн-калькулятор ориентировочной стоимости по категории "
             "красоты и региону. Реальные тарифы и факторы цены — MagzGold.",
        canonical=SITE["base"] + "/skolko-stoit-nomer/",
        page_js=page_js,
        schema=schema_breadcrumb({"name": "Сколько стоит номер", "slug": "skolko-stoit-nomer", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Сколько стоит красивый номер</h1>\n'
                 '  <p class="page-intro">Оцените ориентировочную стоимость красивого номера по категории красоты '
                 'и региону — расчёт на основе реальных тарифов. Ниже — из чего складывается цена.</p>'
                 % crumbs("Сколько стоит номер"),
        vitrina=body,
        footnav=nav_links(None) + patnav(),
        scripts='<script src="/config.js"></script>\n<script src="/calc.js"></script>',
    )
    write("skolko-stoit-nomer/index.html", html_out)


def render_blog_index():
    cards = "".join(
        '<a class="blog-card" href="/blog/%s/"><h2>%s</h2><p>%s</p></a>' % (a["slug"], esc(a["h1"]), esc(a["desc"]))
        for a in BLOG)
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="Блог о красивых номерах — гайды и советы | MagzGold",
        desc="Блог MagzGold: как выбрать красивый номер, категории красоты, как забронировать и сколько стоит номер.",
        canonical=SITE["base"] + "/blog/",
        page_js="",
        schema=schema_breadcrumb({"name": "Блог", "slug": "blog", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Блог о красивых номерах</h1>\n'
                 '  <p class="page-intro">Гайды: как выбрать номер, что означают категории красоты и как оформить бронь.</p>'
                 % crumbs("Блог"),
        vitrina='<div class="blog-list">%s</div>' % cards,
        footnav=nav_links(None) + patnav(),
        scripts="",
    )
    write("blog/index.html", html_out)


def render_article(a):
    art_ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Article",'
              '"headline":"%s","publisher":{"@type":"Organization","name":"MagzGold"},'
              '"mainEntityOfPage":"%s/blog/%s/"}</script>' % (esc(a["h1"]), SITE["base"], a["slug"]))
    bc = ('<nav class="crumbs"><a href="/">Главная</a> / <a href="/blog/">Блог</a> / <span>%s</span></nav>'
          % esc(a["h1"]))
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title=a["title"],
        desc=a["desc"],
        canonical=SITE["base"] + "/blog/%s/" % a["slug"],
        page_js="",
        schema=art_ld,
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">%s</h1>' % (bc, esc(a["h1"])),
        vitrina='<article class="article">%s</article>' % a["body"],
        footnav=nav_links(None) + patnav(),
        scripts="",
    )
    write("blog/%s/index.html" % a["slug"], html_out)


def render_tariff(t):
    page_js = "<script>window.PAGE={tariff:%d};</script>" % t["id"]
    intro = ("Номера с тарифом %s — абонентская плата %d ₽/мес с ёмким пакетом минут, SMS и интернета. "
             "Ниже — красивые номера, доступные на этом тарифе; уточните комбинацию маской и забронируйте онлайн."
             % (t["name"], t["price"]))
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="Номера с тарифом %s (%d ₽/мес) | MagzGold" % (t["name"], t["price"]),
        desc="Красивые номера с тарифом %s — абонплата %d ₽/мес. Подбор по маске, категории, бронирование онлайн — MagzGold."
             % (t["name"], t["price"]),
        canonical=SITE["base"] + "/tarif/%s/" % t["slug"],
        page_js=page_js,
        schema=schema_breadcrumb({"name": t["name"], "slug": "tarif/%s" % t["slug"], "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Номера с тарифом %s</h1>\n  <p class="page-intro">%s</p>'
                 % (crumbs(t["name"]), esc(t["name"]), esc(intro)),
        vitrina=VITRINA,
        footnav=nav_links(None) + patnav(),
        scripts=SCRIPTS,
    )
    write("tarif/%s/index.html" % t["slug"], html_out)


def render_tariffs_index():
    rows = "".join(
        '<a class="blog-card" href="/tarif/%s/"><h2>%s</h2><p>Абонплата %d ₽/мес · красивые номера на этом тарифе</p></a>'
        % (t["slug"], esc(t["name"]), t["price"]) for t in TARIFFS)
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="Тарифы Безлимит ULTRA — номера по тарифам | MagzGold",
        desc="Тарифы Безлимит ULTRA (от 399 до 5000 ₽/мес) и красивые номера на каждом из них. Подбор и бронирование — MagzGold.",
        canonical=SITE["base"] + "/tarify/",
        page_js="",
        schema=schema_breadcrumb({"name": "Тарифы", "slug": "tarify", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Тарифы Безлимит ULTRA</h1>\n'
                 '  <p class="page-intro">Линейка тарифов Безлимит ULTRA — от 399 до 5000 ₽/мес. Выберите тариф, '
                 'чтобы посмотреть красивые номера на нём.</p>' % crumbs("Тарифы"),
        vitrina='<div class="blog-list">%s</div>' % rows,
        footnav=nav_links(None) + patnav(),
        scripts="",
    )
    write("tarify/index.html", html_out)


def render_about():
    body = (
        '<article class="article">'
        "<p>MagzGold — <b>официальный партнёр оператора связи «Безлимит»</b> и информационная витрина красивых "
        "номеров телефонов. Мы помогаем подобрать номер по маске или категории красоты и оформить бронь онлайн. "
        "MagzGold не является оператором связи и не оказывает услуги связи самостоятельно — их предоставляет "
        "оператор.</p>"
        "<h2>Как это работает</h2>"
        '<p>Вы выбираете номер в <a href="/">каталоге</a> (по маске, категории, тарифу или цене), бронируете его '
        "в пару кликов, а регистрация и оплата проходят на стороне оператора связи по его условиям. Оператор "
        "бесплатно доставляет SIM по всей России или оформляет eSIM — без визита в офис.</p>"
        "<h2>Оператор связи</h2>"
        "<p>Услуги связи и продажу номеров осуществляет оператор <b>ООО «Безлимит»</b> "
        "(ИНН 9725007063, ОГРН 1197746244750, г. Москва). Актуальные тарифы, оферты и стоимость номеров "
        "определяются оператором; итоговые условия вы видите при оформлении. Официальные документы — на сайте "
        'оператора: <a href="https://bezlimit.ru/legal" target="_blank" rel="noopener">bezlimit.ru/legal</a>.</p>'
        "<h2>Владелец сайта</h2>"
        "<p>Сайт MagzGold ведёт самозанятый (плательщик налога на профессиональный доход) "
        "<b>Семенцул Максим Геннадиевич</b>, ИНН 381616884622. "
        'Контакт для связи: <a href="mailto:sementsul.maksim@yandex.ru">sementsul.maksim@yandex.ru</a>.</p>'
        "<h2>Дисклеймер</h2>"
        "<p>Информация на сайте носит справочный характер и не является публичной офертой. Стоимость номеров, "
        "тарифы и условия обслуживания определяются оператором и могут меняться; итоговые условия вы видите при "
        "оформлении. Наличие номеров ограничено.</p>"
        "</article>"
    )
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="О сервисе MagzGold — витрина красивых номеров",
        desc="О сервисе MagzGold: информационная витрина красивых номеров, как работает подбор и бронь, оператор связи и официальные документы.",
        canonical=SITE["base"] + "/o-servise/",
        page_js="",
        schema=schema_breadcrumb({"name": "О сервисе", "slug": "o-servise", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">О сервисе</h1>' % crumbs("О сервисе"),
        vitrina=body,
        footnav=nav_links(None) + patnav(),
        scripts="",
    )
    write("o-servise/index.html", html_out)


def _legal_page(slug, h1, title, desc, body):
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title=title, desc=desc, canonical=SITE["base"] + "/%s/" % slug,
        page_js="", schema=schema_breadcrumb({"name": h1, "slug": slug, "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">%s</h1>' % (crumbs(h1), esc(h1)),
        vitrina='<article class="article">%s</article>' % body,
        footnav=nav_links(None) + patnav(), scripts="",
    )
    write("%s/index.html" % slug, html_out)


def render_privacy():
    body = (
        "<p>Настоящая политика описывает обработку данных на сайте MagzGold (magzgold.ru) — информационной "
        "витрине красивых номеров.</p>"
        "<h2>Оператор данных сайта</h2>"
        "<p>Обработку данных, связанных с работой сайта, осуществляет самозанятый (плательщик НПД) "
        "Семенцул Максим Геннадиевич, ИНН 381616884622, "
        '<a href="mailto:sementsul.maksim@yandex.ru">sementsul.maksim@yandex.ru</a>.</p>'
        "<h2>Какие данные обрабатываются</h2>"
        "<p>Сайт статический и не требует регистрации. Для улучшения работы сайта мы используем сервисы "
        "веб-аналитики <b>Яндекс.Метрика</b> (включая технологию Вебвизор — запись обезличенных действий на "
        "страницах: клики, прокрутка, движение курсора) и <b>Google Analytics</b>. Они собирают обезличенные "
        "cookie и технические данные (тип устройства, просмотренные страницы, источник перехода). Персональные "
        "данные для покупки и оформления номера собираются и обрабатываются оператором связи на его стороне и "
        "по его политике.</p>"
        "<h2>Цели и правовые основания</h2>"
        "<p>Технические и аналитические данные обрабатываются для функционирования и улучшения сайта на "
        "основании законного интереса и согласия, выражаемого использованием сайта (152-ФЗ).</p>"
        "<h2>Передача третьим лицам</h2>"
        "<p>Мы не продаём персональные данные. Оформление и услуги связи выполняет оператор "
        "<b>ООО «Безлимит»</b> согласно его документам: "
        '<a href="https://bezlimit.ru/legal" target="_blank" rel="noopener">bezlimit.ru/legal</a>.</p>'
        "<h2>Ваши права</h2>"
        "<p>Вы можете запросить сведения об обработке ваших данных сайтом или их удаление, написав на "
        '<a href="mailto:sementsul.maksim@yandex.ru">sementsul.maksim@yandex.ru</a>. Отключить cookie можно '
        "в настройках браузера.</p>"
    )
    _legal_page("politika", "Политика конфиденциальности",
                "Политика конфиденциальности | MagzGold",
                "Политика конфиденциальности сайта MagzGold: какие данные обрабатываются, оператор данных, права пользователя.", body)


def render_terms():
    body = (
        "<p>Настоящее соглашение регулирует использование сайта MagzGold (magzgold.ru).</p>"
        "<h2>О сервисе</h2>"
        "<p>MagzGold — информационная витрина: помогает подобрать красивый номер по маске, категории или тарифу "
        "и оформить бронь. MagzGold не является оператором связи и не оказывает услуги связи самостоятельно.</p>"
        "<h2>Оформление и оплата</h2>"
        "<p>Бронирование удерживает номер ограниченное время. Регистрация, оплата и оказание услуг связи "
        "выполняются оператором <b>ООО «Безлимит»</b> по его условиям и документам "
        '(<a href="https://bezlimit.ru/legal" target="_blank" rel="noopener">bezlimit.ru/legal</a>). '
        "Стоимость номеров и тарифы определяются оператором.</p>"
        "<h2>Ограничение ответственности</h2>"
        "<p>Информация на сайте носит справочный характер и не является публичной офертой. Наличие номеров, "
        "цены и условия могут меняться; актуальные условия вы видите при оформлении у оператора. "
        "Сайт не несёт ответственности за услуги, оказываемые оператором.</p>"
        "<h2>Контакты</h2>"
        "<p>Владелец сайта: самозанятый Семенцул Максим Геннадиевич, ИНН 381616884622, "
        '<a href="mailto:sementsul.maksim@yandex.ru">sementsul.maksim@yandex.ru</a>.</p>'
    )
    _legal_page("polzovatelskoe-soglashenie", "Пользовательское соглашение",
                "Пользовательское соглашение | MagzGold",
                "Пользовательское соглашение MagzGold: условия использования сайта, оформление, ограничение ответственности.", body)


def render_prefix(pfx):
    page_js = '<script>window.PAGE={mask:"%sNNNNNNN"};</script>' % pfx
    intro = ("Красивые номера с кодом +7 %s: подбор по маске, категории и тарифу, бронирование онлайн. "
             "Ниже — доступные номера на %s; уточните нужные цифры маской." % (pfx, pfx))
    html_out = PAGE_TMPL.format(metrika=METRIKA, 
        drawer=_DRAWER,
        title="Красивые номера на %s (+7 %s) | MagzGold" % (pfx, pfx),
        desc="Красивые номера с кодом +7 %s — подбор по маске, категории, тарифу и бронирование онлайн на MagzGold." % pfx,
        canonical=SITE["base"] + "/kod/%s/" % pfx,
        page_js=page_js,
        schema=schema_breadcrumb({"name": "Код %s" % pfx, "slug": "kod/%s" % pfx, "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Номера на %s</h1>\n  <p class="page-intro">%s</p>'
                 % (crumbs("Код %s" % pfx), pfx, esc(intro)),
        vitrina=VITRINA, footnav=nav_links(None) + patnav(), scripts=SCRIPTS,
    )
    write("kod/%s/index.html" % pfx, html_out)


def render_prefixes_hub():
    rows = "".join(
        '<a class="blog-card" href="/kod/%s/"><h2>+7 %s</h2><p>Красивые номера на %s</p></a>' % (p, p, p)
        for p in PREFIXES)
    html_out = PAGE_TMPL.format(metrika=METRIKA, 
        drawer=_DRAWER,
        title="Номера по кодам (+7 9XX) — выбор кода | MagzGold",
        desc="Красивые номера по кодам мобильного оператора (+7 900, 916, 999 и другие). Выберите код и подберите номер — MagzGold.",
        canonical=SITE["base"] + "/kody/", page_js="",
        schema=schema_breadcrumb({"name": "Коды", "slug": "kody", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Номера по кодам</h1>\n'
                 '  <p class="page-intro">Выберите код мобильного (+7 9XX) — покажем красивые номера на нём.</p>'
                 % crumbs("Коды"),
        vitrina='<div class="blog-list">%s</div>' % rows,
        footnav=nav_links(None) + patnav(), scripts="",
    )
    write("kody/index.html", html_out)


def render_faq():
    items = "".join(
        '<div class="faq-item"><h2>%s</h2><div>%s</div></div>' % (esc(q), a) for q, a in FAQ)
    faq_ld = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"FAQPage",'
              '"mainEntity":[%s]}</script>' % ",".join(
                  '{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}'
                  % (esc(q), esc(__import__("re").sub("<[^>]+>", "", a))) for q, a in FAQ))
    html_out = PAGE_TMPL.format(metrika=METRIKA, 
        drawer=_DRAWER,
        title="Частые вопросы о красивых номерах — FAQ | MagzGold",
        desc="Ответы на частые вопросы о красивых номерах: что это, как забронировать, сколько стоит, кто оператор — FAQ MagzGold.",
        canonical=SITE["base"] + "/faq/", page_js="", schema=faq_ld,
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Частые вопросы</h1>' % crumbs("FAQ"),
        vitrina='<div class="faq">%s</div>' % items,
        footnav=nav_links(None) + patnav(), scripts="",
    )
    write("faq/index.html", html_out)


def render_404():
    err = ('<div class="err"><div class="err-code">404</div>'
           '<h1>Страница не найдена</h1>'
           '<p>Похоже, такой страницы нет или она переехала.</p>'
           '<a class="btn-primary" href="/">На главную</a></div>')
    html_out = PAGE_TMPL.format(metrika=METRIKA, drawer=_DRAWER, 
        title="Страница не найдена — MagzGold",
        desc="Страница не найдена.",
        canonical=SITE["base"] + "/404.html",
        page_js="",
        schema='<meta name="robots" content="noindex">',
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top="",
        vitrina=err,
        footnav=nav_links(None),
        scripts="",
    )
    write("404.html", html_out)


def render_sitemap():
    urls = ([SITE["base"] + "/"] + [SITE["base"] + "/kategoriya/%s/" % c["slug"] for c in CATEGORIES]
            + [SITE["base"] + "/%s/" % p["slug"] for p in PATTERNS]
            + [SITE["base"] + "/skolko-stoit-nomer/", SITE["base"] + "/blog/"]
            + [SITE["base"] + "/blog/%s/" % a["slug"] for a in BLOG]
            + [SITE["base"] + "/o-servise/", SITE["base"] + "/tarify/", SITE["base"] + "/politika/", SITE["base"] + "/polzovatelskoe-soglashenie/"]
            + [SITE["base"] + "/tarif/%s/" % t["slug"] for t in TARIFFS]
            + [SITE["base"] + "/kody/", SITE["base"] + "/faq/"]
            + [SITE["base"] + "/kod/%s/" % pfx for pfx in PREFIXES])
    today = date.today().isoformat()
    body = "".join("<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>daily</changefreq></url>" % (u, today) for u in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % body)
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE["base"])


def copy_assets():
    for f in ("app.js", "styles.css", "config.js", "calc.js", "nav.js", "favicon.svg"):
        shutil.copy(os.path.join(ROOT, f), os.path.join(DIST, f))
    make_og()
    write("CNAME", "magzgold.ru\n")
    open(os.path.join(DIST, ".nojekyll"), "w").close()


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    render_home()
    for c in CATEGORIES:
        render_category(c)
    for p in PATTERNS:
        render_pattern(p)
    render_calc()
    render_blog_index()
    for a in BLOG:
        render_article(a)
    render_about()
    render_tariffs_index()
    for t in TARIFFS:
        render_tariff(t)
    render_privacy()
    render_terms()
    render_prefixes_hub()
    for pfx in PREFIXES:
        render_prefix(pfx)
    render_faq()
    render_404()
    render_sitemap()
    copy_assets()
    print("✅ dist/: %d кат + %d паттернов + %d тарифов + %d кодов + FAQ + калькулятор + %d статей + юр + 404" % (len(CATEGORIES), len(PATTERNS), len(TARIFFS), len(PREFIXES), len(BLOG)))


if __name__ == "__main__":
    main()
