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
    {"slug": "brilliant", "code": "brilliant,brilliant_super", "name": "Бриллиантовые",
     "h1": "Бриллиантовые номера",
     "desc": "Бриллиантовые номера телефонов — самая красивая категория: подбор по маске, тарифы, бронирование онлайн на MagzGold.",
     "intro": "Бриллиантовые номера — вершина категорий красоты: максимально «чистые» комбинации, "
              "повторяющиеся и зеркальные цифры, лёгкие для запоминания. Такой номер подчёркивает статус "
              "и почти не встречается в свободной продаже. Ниже — доступные бриллиантовые номера с тарифами; "
              "уточните комбинацию маской и забронируйте онлайн."},
    {"slug": "platinum", "code": "platinum,platinum_lite", "name": "Платиновые",
     "h1": "Платиновые номера",
     "desc": "Платиновые номера телефонов на MagzGold: красивые комбинации, разные тарифы, подбор по маске и онлайн-бронь.",
     "intro": "Платиновые номера — премиальная категория чуть доступнее бриллиантовых: эффектные сочетания "
              "цифр, которые приятно диктовать и легко запомнить. Подходят тем, кто хочет заметный номер без "
              "переплаты за топ-категорию. Выберите подходящий по маске и тарифу."},
    {"slug": "gold", "code": "gold", "name": "Золотые",
     "h1": "Золотые номера",
     "desc": "Золотые номера телефонов: баланс красоты и цены. Подбор по маске, тарифы, бронирование онлайн — MagzGold.",
     "intro": "Золотые номера — оптимальный баланс красоты и стоимости: узнаваемые комбинации, повторы и "
              "приятные окончания за разумные деньги. Самая популярная категория для личного и рабочего номера. "
              "Отфильтруйте по тарифу и подберите свой."},
    {"slug": "silver", "code": "silver,silver_special,silver_special_2", "name": "Серебряные",
     "h1": "Серебряные номера",
     "desc": "Серебряные номера телефонов на MagzGold: доступные красивые комбинации, тарифы, онлайн-бронь.",
     "intro": "Серебряные номера — доступная красота: аккуратные комбинации, которые проще запомнить, чем "
              "случайный набор, но без премиальной наценки. Хороший выбор, если нужен приятный номер недорого."},
    {"slug": "bronze", "code": "bronze,bronze_vip,bronze AAA", "name": "Бронзовые",
     "h1": "Бронзовые номера",
     "desc": "Бронзовые номера телефонов: самый доступный вход в красивые номера. Подбор по маске и тарифу — MagzGold.",
     "intro": "Бронзовые номера — начальная категория красоты и самый доступный вход: лёгкие для запоминания "
              "сочетания по минимальной цене. Отличный вариант для второго номера или подарка."},
]


def esc(s):
    return html.escape(str(s), quote=True)


def nav_links(active_slug=None):
    items = ['<a href="/"%s>Все номера</a>' % (' class="active"' if active_slug is None else "")]
    for c in CATEGORIES:
        cls = ' class="active"' if c["slug"] == active_slug else ""
        items.append('<a href="/kategoriya/%s/"%s>%s</a>' % (c["slug"], cls, esc(c["name"])))
    return '<nav class="catnav">' + "".join(items) + "</nav>"


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
    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>
    {nav}
  </div>
</header>
<main class="wrap">
  {crumbs}
  <h1 class="page-h1">{h1}</h1>
  <p class="page-intro">{intro}</p>
{vitrina}
</main>
<footer class="foot">
  <div class="wrap">
    {footnav}
    <p>MagzGold — информационная витрина красивых номеров. Подбор и бронирование; подключение и оплата на стороне оператора.</p>
  </div>
</footer>
<script src="/config.js"></script>
<script src="/app.js"></script>
</body>
</html>
"""


def schema_breadcrumb(active=None):
    items = [{"pos": 1, "name": "Главная", "url": SITE["base"] + "/"}]
    if active:
        items.append({"pos": 2, "name": active["name"], "url": SITE["base"] + "/kategoriya/%s/" % active["slug"]})
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
    html_out = PAGE_TMPL.format(
        title="MagzGold — красивые номера: купить и забронировать онлайн",
        desc="MagzGold — красивые и премиальные номера телефонов: подбор по маске и категориям, тарифы, "
             "бронирование онлайн. Бриллиантовые, платиновые, золотые, серебряные и бронзовые номера.",
        canonical=SITE["base"] + "/",
        page_js="",
        schema=schema_breadcrumb(),
        nav=nav_links(None),
        crumbs="",
        h1="Красивые номера",
        intro="MagzGold — витрина красивых номеров телефонов. Соберите нужную комбинацию маской или выберите "
              "категорию слева: бриллиантовые, платиновые, золотые, серебряные, бронзовые. Каждый номер — с "
              "тарифом и мгновенной бронью онлайн.",
        vitrina=VITRINA,
        footnav=nav_links(None),
    )
    write("index.html", html_out)


def render_category(c):
    page_js = '<script>window.PAGE={cat:"%s"};</script>' % c["code"]
    html_out = PAGE_TMPL.format(
        title="%s номера — купить и забронировать | MagzGold" % c["name"],
        desc=c["desc"],
        canonical=SITE["base"] + "/kategoriya/%s/" % c["slug"],
        page_js=page_js,
        schema=schema_breadcrumb(c),
        nav=nav_links(c["slug"]),
        crumbs=crumbs(c["name"]),
        h1=c["h1"],
        intro=c["intro"],
        vitrina=VITRINA,
        footnav=nav_links(c["slug"]),
    )
    write("kategoriya/%s/index.html" % c["slug"], html_out)


def render_sitemap():
    urls = [SITE["base"] + "/"] + [SITE["base"] + "/kategoriya/%s/" % c["slug"] for c in CATEGORIES]
    body = "".join("<url><loc>%s</loc><changefreq>daily</changefreq></url>" % u for u in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % body)
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE["base"])


def copy_assets():
    for f in ("app.js", "styles.css", "config.js"):
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
    render_sitemap()
    copy_assets()
    print("✅ dist/: главная + %d категорий + sitemap/robots" % len(CATEGORIES))


if __name__ == "__main__":
    main()
