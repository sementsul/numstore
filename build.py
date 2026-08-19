#!/usr/bin/env python3
# MagzGold — генератор статических SEO-страниц (главная + категории + sitemap/robots).
# Витрина (номера) остаётся клиентской (ban-proof); вокруг — уникальный текст под запросы.
import os, shutil, html

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
<link rel="stylesheet" href="/styles.css">
{page_js}
{schema}
</head>
<body>
<header class="top">
  <div class="wrap">
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
    <nav class="catnav footlinks"><a href="/blog/">Блог</a><a href="/skolko-stoit-nomer/">Сколько стоит номер</a><a href="/o-servise/">О сервисе</a></nav>
    <p>MagzGold — информационная витрина красивых номеров. Подбор и бронирование; подключение и оплата на стороне оператора.</p>
  </div>
</footer>
{scripts}
</body>
</html>
"""
SCRIPTS = '<script src="/config.js"></script>\n<script src="/app.js"></script>'


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


def render_home():
    header_block = ('    <h1 class="hero">Magz<span class="brand-gold">Gold</span>'
                    ' <span class="hero-tag">— премиальные номера</span></h1>')
    intro = ("MagzGold — витрина красивых номеров телефонов. Соберите нужную комбинацию маской или выберите "
             "категорию: бриллиантовые, платиновые, золотые, серебряные, бронзовые. Каждый номер — с тарифом "
             "и мгновенной бронью онлайн.")
    html_out = PAGE_TMPL.format(
        title="MagzGold — красивые номера: купить и забронировать онлайн",
        desc="MagzGold — красивые и премиальные номера телефонов: подбор по маске и категориям, тарифы, "
             "бронирование онлайн. Бриллиантовые, платиновые, золотые, серебряные и бронзовые номера.",
        canonical=SITE["base"] + "/",
        page_js="",
        schema=schema_breadcrumb(),
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
    html_out = PAGE_TMPL.format(
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
    html_out = PAGE_TMPL.format(
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
        'и текущую абонплату тарифа (ежемесячно). Точная цена номера зависит от его маски внутри категории — '
        'полный прайс: '
        '<a href="https://bezlimit.ru/files/%D0%A1%D1%82%D0%BE%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D1%8C%20%D0%BD%D0%BE%D0%BC%D0%B5%D1%80%D0%BE%D0%B2.pdf" '
        'target="_blank" rel="noopener">Стоимость номеров (PDF)</a>. Это не оферта; итоговая сумма — у оператора.</p>'
        '</section>'
    )
    html_out = PAGE_TMPL.format(
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
    html_out = PAGE_TMPL.format(
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
    html_out = PAGE_TMPL.format(
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


def render_about():
    body = (
        '<article class="article">'
        "<p>MagzGold — информационная витрина красивых номеров телефонов. Мы помогаем подобрать номер по маске "
        "или категории красоты и оформить бронь онлайн. MagzGold не является оператором связи и не оказывает "
        "услуги связи самостоятельно.</p>"
        "<h2>Как это работает</h2>"
        '<p>Вы выбираете номер в <a href="/">каталоге</a> (по маске, категории, тарифу или цене), бронируете его '
        "в пару кликов, а регистрация и оплата проходят на стороне оператора связи по его условиям.</p>"
        "<h2>Оператор</h2>"
        "<p>Услуги связи и продажу номеров осуществляет оператор <b>ООО «Безлимит»</b> "
        "(ИНН 9725007063, ОГРН 1197746244750, г. Москва). Актуальные условия, тарифы, оферты и правила — "
        'в официальных документах оператора: <a href="https://bezlimit.ru/files/" target="_blank" rel="noopener">'
        "bezlimit.ru/files</a>, стоимость номеров — в "
        '<a href="https://bezlimit.ru/files/%D0%A1%D1%82%D0%BE%D0%B8%D0%BC%D0%BE%D1%81%D1%82%D1%8C%20%D0%BD%D0%BE%D0%BC%D0%B5%D1%80%D0%BE%D0%B2.pdf" '
        'target="_blank" rel="noopener">официальном прайсе</a>.</p>'
        "<h2>Дисклеймер</h2>"
        "<p>Информация на сайте носит справочный характер и не является публичной офертой. Стоимость номеров, "
        "тарифы и условия обслуживания определяются оператором и могут меняться; итоговые условия вы видите при "
        "оформлении. Наличие номеров ограничено.</p>"
        "</article>"
    )
    html_out = PAGE_TMPL.format(
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


def render_404():
    err = ('<div class="err"><div class="err-code">404</div>'
           '<h1>Страница не найдена</h1>'
           '<p>Похоже, такой страницы нет или она переехала.</p>'
           '<a class="btn-primary" href="/">На главную</a></div>')
    html_out = PAGE_TMPL.format(
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
            + [SITE["base"] + "/o-servise/"])
    body = "".join("<url><loc>%s</loc><changefreq>daily</changefreq></url>" % u for u in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % body)
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE["base"])


def copy_assets():
    for f in ("app.js", "styles.css", "config.js", "calc.js"):
        shutil.copy(os.path.join(ROOT, f), os.path.join(DIST, f))
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
    render_404()
    render_sitemap()
    copy_assets()
    print("✅ dist/: главная + %d кат + %d паттернов + калькулятор + %d статей + 404 + sitemap" % (len(CATEGORIES), len(PATTERNS), len(BLOG)))


if __name__ == "__main__":
    main()
