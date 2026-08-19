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
    <nav class="catnav footlinks"><a href="/skolko-stoit-nomer/">Сколько стоит номер</a></nav>
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
            + [SITE["base"] + "/skolko-stoit-nomer/"])
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
    render_404()
    render_sitemap()
    copy_assets()
    print("✅ dist/: главная + %d категорий + %d паттернов + калькулятор + 404 + sitemap/robots" % (len(CATEGORIES), len(PATTERNS)))


if __name__ == "__main__":
    main()
