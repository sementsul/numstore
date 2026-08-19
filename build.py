#!/usr/bin/env python3
# MagzGold — генератор статических SEO-страниц (главная + категории + sitemap/robots).
# Витрина (номера) остаётся клиентской (ban-proof); вокруг — уникальный текст под запросы.
import os, shutil, html, hashlib, json
from datetime import date

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST = os.path.join(ROOT, "dist")


def _ver(fname):
    """?v=<md5[:8]> по содержимому файла — кэш-бастинг: браузер тянет свежий ассет только при изменении."""
    try:
        h = hashlib.md5(open(os.path.join(ROOT, fname), "rb").read()).hexdigest()[:8]
        return "?v=" + h
    except OSError:
        return ""

SITE = {
    "name": "MagzGold",
    "base": "https://magzgold.ru",
    "tg_channel": "https://t.me/magzgoldmg",
    "tg_bot": "https://t.me/magzgoldbot",
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

# Углублённый уникальный текст по категориям (ниже витрины) — для глубины контента (SEO).
CAT_TEXT = {
    "brilliant": (
        "<h2>Чем особенны бриллиантовые номера</h2>"
        "<p>Бриллиантовая категория — это верх линейки красивых номеров. Сюда попадают самые «чистые» и редкие "
        "комбинации: семь одинаковых цифр подряд, идеальные зеркала, номера, где повторяется код и окончание. "
        "Такие сочетания встречаются в свободной продаже крайне редко, поэтому и ценятся выше всего — от 400 000 ₽ "
        "и до нескольких миллионов за эксклюзивные варианты.</p>"
        "<p>Бриллиантовый номер — это статусный аксессуар и одновременно инвестиция: действительно красивые "
        "комбинации со временем только растут в цене. Его выбирают под личный бренд, для первых лиц компаний и "
        "как коллекционную ценность. Подобрать конкретную комбинацию удобно маской, а прикинуть бюджет — на "
        '<a href="/skolko-stoit-nomer/">калькуляторе стоимости</a>.</p>'),
    "platinum": (
        "<h2>Платиновые номера: премиум без максимальной наценки</h2>"
        "<p>Платина — премиальная категория чуть доступнее бриллиантовой. Здесь выраженная симметрия, длинные "
        "повторы и эффектные окончания, но цена мягче — от 25 000 ₽. Отличный выбор, когда хочется солидный "
        "запоминающийся номер без перехода в топ-сегмент.</p>"
        "<p>Платиновые номера хорошо работают и для личного пользования, и как рабочий номер, который клиенты "
        "запоминают с первого раза. Уточните нужные цифры маской и подберите вариант под свой тариф.</p>"),
    "gold": (
        "<h2>Золотые номера — золотая середина</h2>"
        "<p>Золото — самая популярная категория: оптимальный баланс красоты и стоимости (от 50 000 ₽). "
        "Узнаваемые повторы, приятные окончания и лёгкие для диктовки комбинации, которые не стоят как "
        "бриллиантовые, но заметно выделяются на фоне обычного набора цифр.</p>"
        "<p>Такой номер одинаково уместен для личного телефона и для бизнеса. Отфильтруйте по тарифу и цене, "
        "добавьте понравившиеся в избранное и забронируйте онлайн.</p>"),
    "silver": (
        "<h2>Серебряные номера: доступная красота</h2>"
        "<p>Серебро — аккуратные, приятные комбинации по доступной цене (от 12 000 ₽). Они заметно удобнее "
        "случайного набора: легче запоминаются и диктуются, но без премиальной наценки.</p>"
        "<p>Хороший вариант для второго номера, для работы или в подарок. Подберите комбинацию маской и "
        "сравните тарифы.</p>"),
    "bronze": (
        "<h2>Бронзовые номера: доступный вход</h2>"
        "<p>Бронза — начальная категория красивых номеров (от 3 000 ₽). Лёгкие сочетания, небольшие повторы и "
        "пары цифр — минимальная цена за то, чтобы номер было проще запомнить.</p>"
        "<p>Отличный выбор для второго номера, для бизнеса или в подарок без больших вложений.</p>"),
}
for _c in CATEGORIES:
    _c["text"] = CAT_TEXT.get(_c["slug"], "")

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

# Лонгтейл-лендинги: витрина + уникальный текст под интент-запрос.
LANDINGS = [
    {"slug": "dlya-biznesa", "h1": "Красивые номера для бизнеса",
     "title": "Красивые номера для бизнеса — купить корпоративный номер | MagzGold",
     "desc": "Красивые номера для бизнеса: запоминающийся номер для рекламы, визиток и клиентов. Подбор по маске и категории, бронирование онлайн — MagzGold.",
     "text": ("<p>Красивый номер для бизнеса — это рабочий инструмент: его проще запомнить с рекламы, вывески или "
              "визитки, он повышает доверие и упрощает входящие обращения. Хороший корпоративный номер окупается "
              "ростом звонков от клиентов.</p>"
              "<p>Для компании обычно берут <a href=\"/kategoriya/gold/\">золотые</a> или "
              "<a href=\"/kategoriya/platinum/\">платиновые</a> номера с ровным окончанием или повтором. Подберите "
              "комбинацию маской — например, зафиксируйте окончание на <a href=\"/kruglye/\">нули</a> или "
              "<a href=\"/na-777/\">777</a>.</p>")},
    {"slug": "v-podarok", "h1": "Номер в подарок",
     "title": "Красивый номер в подарок — оригинальный подарок | MagzGold",
     "desc": "Красивый номер телефона в подарок — оригинально и статусно. Выберите номер по маске или дате, забронируйте онлайн — MagzGold.",
     "text": ("<p>Красивый номер — необычный и запоминающийся подарок: близкому человеку, партнёру или руководителю. "
              "Можно подобрать номер с личными цифрами — датой рождения, годом или счастливой комбинацией.</p>"
              "<p>Выберите категорию по бюджету — от доступной <a href=\"/kategoriya/bronze/\">бронзы</a> до "
              "<a href=\"/kategoriya/brilliant/\">бриллиантовой</a>, — и задайте нужные цифры маской.</p>")},
    {"slug": "legko-zapomnit", "h1": "Номера, которые легко запомнить",
     "title": "Легко запоминающиеся номера телефонов — купить | MagzGold",
     "desc": "Номера, которые легко запомнить: повторы, пары, круглые окончания. Подбор по маске и категории, бронирование онлайн — MagzGold.",
     "text": ("<p>Легко запоминающийся номер экономит время и вам, и тем, кто вам звонит. Проще всего запоминаются "
              "номера с <a href=\"/povtory/\">повторами</a>, <a href=\"/pary/\">парами</a> цифр и "
              "<a href=\"/kruglye/\">круглыми</a> окончаниями.</p>"
              "<p>Соберите комбинацию маской из привычных цифр — и номер будет отскакивать от зубов.</p>")},
    {"slug": "na-datu-rozhdeniya", "h1": "Номер с датой рождения",
     "title": "Номер телефона с датой рождения — подобрать | MagzGold",
     "desc": "Подберите красивый номер с вашей датой рождения или годом. Гибкая маска по позициям, бронирование онлайн — MagzGold.",
     "text": ("<p>Номер с датой рождения — личный и его невозможно забыть. В каталоге задайте маску: впишите день, "
              "месяц или год на нужные позиции, а остальные цифры оставьте любыми — система покажет подходящие "
              "варианты.</p>"
              "<p>Так же можно искать номер с годом (например, 2000) или другими значимыми цифрами. "
              "Понравившийся вариант добавьте в избранное и забронируйте.</p>")},
    {"slug": "vip-nomera", "h1": "VIP-номера телефонов",
     "title": "VIP-номера телефонов — купить эксклюзивный номер | MagzGold",
     "desc": "VIP-номера телефонов: эксклюзивные комбинации премиум-класса. Платиновые и бриллиантовые номера, подбор по маске, бронирование онлайн — MagzGold.",
     "text": ("<p>VIP-номер — это статус в одной строке: эксклюзивная комбинация, которую замечают и запоминают. "
              "Такой номер подчёркивает уровень владельца и одинаково уместен и в бизнесе, и в личном общении.</p>"
              "<p>В премиум-сегменте — <a href=\"/kategoriya/platinum/\">платиновые</a> и "
              "<a href=\"/kategoriya/brilliant/\">бриллиантовые</a> номера: выраженная симметрия, длинные повторы, "
              "максимально «чистые» комбинации. Хотите конкретный рисунок — задайте его маской, например "
              "<a href=\"/povtory/\">повторы</a> или окончание на <a href=\"/kruglye/\">нули</a>. "
              "Оценить бюджет поможет <a href=\"/skolko-stoit-nomer/\">калькулятор стоимости</a>.</p>")},
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
    {"slug": "kak-uznat-operatora-po-nomeru", "h1": "Как узнать оператора по номеру телефона",
     "title": "Как узнать оператора по номеру телефона — по коду | MagzGold",
     "desc": "Как определить мобильного оператора и регион по номеру телефона: что такое DEF-код (900, 903, 999…) и как его прочитать. Гайд MagzGold.",
     "body": (
        "<p>Оператора и регион можно определить по первым цифрам мобильного номера — так называемому "
        "DEF-коду. Разберём, как это работает.</p>"
        "<h2>Что такое код номера</h2>"
        "<p>Российский мобильный номер записывается как <b>+7 (XXX) XXX-XX-XX</b>, где <b>XXX</b> после «+7» — "
        "трёхзначный код (9XX). Именно он исторически закреплялся за оператором при выделении номерной ёмкости. "
        "Посмотреть номера по конкретному коду можно в разделе "
        '<a href="/kody/">номера по кодам</a> — например, <a href="/kod/999/">999</a> или '
        '<a href="/kod/903/">903</a>.</p>'
        "<h2>Почему код не всегда точен</h2>"
        "<p>Из-за <b>переноса номера</b> (MNP) абонент может сохранить номер при смене оператора — тогда код "
        "остаётся «старым», а обслуживает уже другой оператор. Поэтому код показывает исходную принадлежность, "
        "а не обязательно текущего оператора.</p>"
        "<h2>Как определить точно</h2>"
        "<p>Точную принадлежность на текущий момент дают официальные базы MNP и запрос самому оператору. Код "
        "же удобен для быстрой ориентировки и для подбора «красивого» кода под себя.</p>"
        '<p>Хотите номер с определённым кодом? Выберите его в <a href="/kody/">каталоге по кодам</a> или '
        'соберите нужную комбинацию маской в <a href="/">каталоге номеров</a>.</p>'),
     },
    {"slug": "nomer-telefona-v-podarok", "h1": "Можно ли подарить номер телефона",
     "title": "Можно ли подарить номер телефона и как это сделать | MagzGold",
     "desc": "Красивый номер в подарок: можно ли подарить номер телефона, как оформить и что учесть. Разбираемся в гайде MagzGold.",
     "body": (
        "<p>Красивый номер — необычный и запоминающийся подарок. Разберём, можно ли его подарить и как это "
        "оформить корректно.</p>"
        "<h2>Как это работает</h2>"
        "<p>Сам номер оформляется договором на оператора связи. Подарить можно двумя способами: оформить "
        "SIM сразу на будущего владельца (тогда паспорт и согласие нужны его) или подарить как сертификат/жест, "
        "а договор владелец заключит сам при активации.</p>"
        "<h2>Что учесть</h2>"
        "<p>Подключение доступно только гражданам РФ по паспорту РФ — это условие оператора. Заранее уточните, "
        "на чьё имя будет оформлен номер, чтобы не было сюрпризов при активации.</p>"
        "<h2>Как выбрать</h2>"
        '<p>Под подарок хорошо подходят номера с личными цифрами — датой рождения или счастливой комбинацией. '
        'Посмотрите подборку <a href="/v-podarok/">номеров в подарок</a> или задайте нужные цифры маской в '
        '<a href="/">каталоге</a>. Прикинуть бюджет поможет <a href="/skolko-stoit-nomer/">калькулятор</a>.</p>'),
     },
    {"slug": "zolotoy-ili-platinovyy-nomer", "h1": "Золотой или платиновый номер — чем отличаются",
     "title": "Золотой или платиновый номер: чем отличаются и что выбрать | MagzGold",
     "desc": "Чем золотой номер отличается от платинового: комбинации, редкость, цена — и какой выбрать под свою задачу. Сравнение MagzGold.",
     "body": (
        "<p>Золотые и платиновые номера — соседние премиальные категории, и выбрать между ними бывает непросто. "
        "Сравним по комбинации, редкости и цене.</p>"
        "<h2>Золотые номера</h2>"
        '<p><a href="/kategoriya/gold/">Золотые</a> — узнаваемые повторы и ровные окончания, оптимальный баланс '
        "красоты и статуса. Популярный выбор для личного и рабочего номера, который легко диктовать.</p>"
        "<h2>Платиновые номера</h2>"
        '<p><a href="/kategoriya/platinum/">Платиновые</a> — более выраженная симметрия и длинные повторы, '
        "комбинации встречаются реже. Смотрятся статуснее и, как правило, ценятся выше при равной «чистоте».</p>"
        "<h2>Что выбрать</h2>"
        "<p>Если нужен красивый, но не запредельный по цене номер на каждый день — берите золотой. Если важен "
        "максимальный статус и редкость комбинации — платиновый. Точную цену конкретного номера покажет "
        '<a href="/skolko-stoit-nomer/">калькулятор</a>, а разницу всех категорий — гайд '
        '<a href="/blog/kategorii-krasivyh-nomerov/">категории красивых номеров</a>.</p>'),
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
    other = [("/", "Все номера"), ("/kak-eto-rabotaet/", "Как это работает"), ("/tarify/", "Тарифы"), ("/kody/", "Номера по кодам"), ("/blog/", "Блог"), ("/faq/", "Вопросы и ответы"), ("/skolko-stoit-nomer/", "Сколько стоит номер"), ("/proverit-nomer/", "Проверить красоту номера"), ("/api-i-vidzhety/", "API и виджеты"), ("/o-servise/", "О сервисе")]
    picks = [("/%s/" % l["slug"], l["h1"]) for l in LANDINGS]
    legal = [("/dokumenty/", "Документы и партнёрство"), ("/politika/", "Политика конфиденциальности"), ("/polzovatelskoe-soglashenie/", "Пользовательское соглашение")]
    tg = ('<a href="https://t.me/magzgoldmg" target="_blank" rel="noopener">📢 Канал с номерами</a>'
          '<a href="https://t.me/magzgoldbot" target="_blank" rel="noopener">🤖 Бот подбора и брони</a>')
    return (
        '<div class="drawer-backdrop" id="drawerBg"></div>'
        '<aside class="drawer" id="drawer" aria-label="Меню сайта">'
        '<button class="drawer-close" aria-label="Закрыть">\u00d7</button>'
        '<a class="drawer-brand" href="/">Magz<span class="brand-gold">Gold</span></a>'
        '<div class="drawer-group"><h4>Разделы</h4>%s</div>'
        '<div class="drawer-group"><h4>Подборки</h4>%s</div>'
        '<div class="drawer-group"><h4>Telegram</h4>%s</div>'
        '<div class="drawer-group"><h4>Документы</h4>%s</div>'
        '</aside>'
    ) % (_dlinks(other), _dlinks(picks), tg, _dlinks(legal))


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
      <div class="search-main">
        <div class="cubes" id="cubes" aria-label="Маска номера из 10 цифр"><span class="cube-prefix">+7</span></div>
        <div class="cube-actions">
          <button id="find" class="btn-primary">Найти по маске</button>
          <button id="reset" class="btn-ghost">Сбросить</button>
        </div>
        <p class="cube-hint">Цифра — точная позиция · пусто — любая · буква (a, b, …) — повторяющаяся цифра</p>
      </div>
      <aside class="search-aside">
        <h3>Как искать</h3>
        <p class="hint-ex">Впишите только нужные цифры, остальные позиции оставьте пустыми.</p>
        <div class="ex">
          <div class="ex-mask"><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell on">7</span><span class="ex-cell on">7</span><span class="ex-cell on">7</span><span class="ex-cell on">7</span></div>
          <div class="ex-res">→ номера, что оканчиваются на 77-77</div>
        </div>
        <div class="ex">
          <div class="ex-mask"><span class="ex-cell on">9</span><span class="ex-cell on">9</span><span class="ex-cell on">9</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span><span class="ex-cell off">·</span></div>
          <div class="ex-res">→ все номера с кодом 999</div>
        </div>
      </aside>
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
<meta name="yandex-verification" content="e8b5b765f77b401c" />
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_image}">
<meta property="og:site_name" content="MagzGold">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{og_image}">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://api.store.bezlimit.ru">
<link rel="preconnect" href="https://mc.yandex.ru">
<link rel="dns-prefetch" href="https://www.googletagmanager.com">
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
    <div class="tg-links"><a href="https://t.me/magzgoldmg" target="_blank" rel="noopener">📢 Telegram-канал с номерами</a><a href="https://t.me/magzgoldbot" target="_blank" rel="noopener">🤖 Бот подбора и брони</a></div>
    <p>MagzGold — официальный партнёр оператора «Безлимит». Информационная витрина красивых номеров; подключение и оплата на стороне оператора.</p>
  </div>
</footer>
{drawer}
<script src="/nav.js"></script>
{scripts}
</body>
</html>
"""
# Кэш-бастинг: версии по хешу содержимого ассетов (после деплоя браузер тянет свежие CSS/JS).
PAGE_TMPL = (PAGE_TMPL
             .replace('/styles.css"', '/styles.css%s"' % _ver("styles.css"))
             .replace('/nav.js"', '/nav.js%s"' % _ver("nav.js")))
SCRIPTS = '<script src="/config.js%s"></script>\n<script src="/app.js%s"></script>' % (_ver("config.js"), _ver("app.js"))
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


def cat_schema(c):
    prod = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Product",'
            '"name":"%s","category":"Красивые номера телефонов",'
            '"offers":{"@type":"AggregateOffer","priceCurrency":"RUB","lowPrice":%d,"highPrice":%d,'
            '"availability":"https://schema.org/InStock"}}</script>') % (esc(c["h1"]), c["pmin"], c["pmax"])
    return prod + schema_breadcrumb(c)


def related_block(exclude_cat=None, exclude_pat=None):
    cats = [c for c in CATEGORIES if c["slug"] != exclude_cat][:4]
    pats = [p for p in PATTERNS if p["slug"] != exclude_pat][:5]
    links = "".join('<a href="/kategoriya/%s/">%s номера</a>' % (c["slug"], esc(c["name"])) for c in cats)
    links += "".join('<a href="/%s/">%s</a>' % (p["slug"], esc(p["h1"])) for p in pats)
    links += '<a href="/kody/">Номера по кодам</a><a href="/skolko-stoit-nomer/">Сколько стоит номер</a>'
    return '<section class="related"><h2>Смотрите также</h2><nav class="rel-links">%s</nav></section>' % links


def write(path, content):
    full = os.path.join(DIST, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)


def home_schema():
    org = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"Organization",'
           '"name":"MagzGold","url":"%s/","logo":"%s/og.png",'
           '"description":"Витрина красивых номеров телефонов, официальный партнёр оператора Безлимит",'
           '"contactPoint":{"@type":"ContactPoint","email":"sementsul.maksim@yandex.ru","contactType":"customer support"}}'
           "</script>") % (SITE["base"], SITE["base"])
    web = ('<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebSite",'
           '"name":"MagzGold","url":"%s/"}</script>') % SITE["base"]
    return org + web + schema_breadcrumb()


# Подписи OG под каждый тип страницы (файл og/<kind>.png). "home" дублируется в /og.png (дефолт + логотип).
OG_KINDS = {
    "home": "Красивые номера",
    "category": "Категории красивых номеров",
    "pattern": "Красивые комбинации цифр",
    "landing": "Подборки красивых номеров",
    "blog": "Блог о красивых номерах",
    "tariff": "Тарифы Безлимит",
    "code": "Номера по кодам операторов",
}


def _draw_og(sub):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), (13, 15, 19))
    d = ImageDraw.Draw(img)
    d.rectangle([(0, 0), (W - 1, H - 1)], outline=(201, 165, 88), width=4)
    FB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    f1 = ImageFont.truetype(FB, 110); f2 = ImageFont.truetype(FB, 44)
    gold = (201, 165, 88); white = (238, 240, 244); muted = (150, 155, 168)
    m, g = "Magz", "Gold"
    wm = d.textlength(m, font=f1); wg = d.textlength(g, font=f1)
    x = (W - (wm + wg)) / 2; y = 205
    d.text((x, y), m, font=f1, fill=white)
    d.text((x + wm, y), g, font=f1, fill=gold)
    d.rectangle([(W/2 - 60, y + 132), (W/2 + 60, y + 137)], fill=gold)
    # длинную подпись при необходимости ужимаем шрифтом, чтобы влезла в поле
    while d.textlength(sub, font=f2) > W - 120 and f2.size > 26:
        f2 = ImageFont.truetype(FB, f2.size - 2)
    ws = d.textlength(sub, font=f2)
    d.text(((W - ws) / 2, y + 158), sub, font=f2, fill=muted)
    return img


def make_og():
    os.makedirs(os.path.join(DIST, "og"), exist_ok=True)
    for kind, sub in OG_KINDS.items():
        img = _draw_og(sub)
        img.save(os.path.join(DIST, "og", "%s.png" % kind))
        if kind == "home":
            img.save(os.path.join(DIST, "og.png"))  # дефолт для инфо-страниц + логотип Organization


DEFAULT_OG = SITE["base"] + "/og.png"


def OG(kind):
    return SITE["base"] + "/og/%s.png" % kind


def render_page(**kw):
    """Обёртка над PAGE_TMPL.format с дефолтной OG-картинкой (переопределяется og_image=...)."""
    kw.setdefault("og_image", DEFAULT_OG)
    return PAGE_TMPL.format(**kw)


def render_home():
    header_block = ('    <h1 class="hero">Magz<span class="brand-gold">Gold</span>'
                    ' <span class="hero-tag">— премиальные номера</span></h1>')
    intro = ("MagzGold — витрина красивых номеров телефонов. Соберите нужную комбинацию маской или выберите "
             "категорию: бриллиантовые, платиновые, золотые, серебряные, бронзовые. Каждый номер — с тарифом "
             "и мгновенной бронью онлайн. Бесплатная доставка SIM по всей России и eSIM — без визита в офис.")
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
        title="MagzGold — красивые номера: купить и забронировать онлайн",
        desc="MagzGold — красивые и премиальные номера телефонов: подбор по маске и категориям, тарифы, "
             "бронирование онлайн. Бриллиантовые, платиновые, золотые, серебряные и бронзовые номера.",
        canonical=SITE["base"] + "/",
        og_image=OG("home"),
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
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
        title="%s номера — купить и забронировать | MagzGold" % c["name"],
        desc=c["desc"],
        canonical=SITE["base"] + "/kategoriya/%s/" % c["slug"],
        og_image=OG("category"),
        page_js=page_js,
        schema=cat_schema(c),
        nav=nav_links(c["slug"]),
        header_block=header_block,
        main_top=main_top,
        vitrina=VITRINA + '<section class="seo-text">' + c["text"] + "</section>" + related_block(exclude_cat=c["slug"]),
        footnav=nav_links(c["slug"]) + patnav(),
        scripts=SCRIPTS,
    )
    write("kategoriya/%s/index.html" % c["slug"], html_out)


def render_pattern(p):
    page_js = '<script>window.PAGE={mask:"%s"};</script>' % p["mask"]
    header_block = '    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>'
    main_top = "%s\n  <h1 class=\"page-h1\">%s</h1>\n  <p class=\"page-intro\">%s</p>" % (
        crumbs(p["h1"]), esc(p["h1"]), p["intro"])
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
        title="%s — купить и забронировать | MagzGold" % p["h1"],
        desc=p["desc"],
        canonical=SITE["base"] + "/%s/" % p["slug"],
        og_image=OG("pattern"),
        page_js=page_js,
        schema=schema_breadcrumb({"name": p["h1"], "slug": p["slug"], "toplevel": True}),
        nav=nav_links(None),
        header_block=header_block,
        main_top=main_top,
        vitrina=VITRINA + related_block(exclude_pat=p["slug"]),
        footnav=nav_links(None) + patnav(p["slug"]),
        scripts=SCRIPTS,
    )
    write("%s/index.html" % p["slug"], html_out)


def render_landing(l):
    header_block = '    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>'
    main_top = "%s\n  <h1 class=\"page-h1\">%s</h1>" % (crumbs(l["h1"]), esc(l["h1"]))
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title=l["title"],
        desc=l["desc"],
        canonical=SITE["base"] + "/%s/" % l["slug"],
        og_image=OG("landing"),
        page_js="",
        schema=schema_breadcrumb({"name": l["h1"], "slug": l["slug"], "toplevel": True}),
        nav=nav_links(None),
        header_block=header_block,
        main_top=main_top,
        vitrina=VITRINA + '<section class="seo-text">' + l["text"] + "</section>" + related_block(),
        footnav=nav_links(None) + patnav(),
        scripts=SCRIPTS,
    )
    write("%s/index.html" % l["slug"], html_out)


def render_promo():
    """Промо-лендинг: инфо-блоки о сервисе + кнопки «Смотреть номера» в каталог (без витрины)."""
    cat_cards = "".join(
        '<a class="blog-card" href="/kategoriya/%s/"><h2>%s</h2><p>от %s ₽ · %s</p></a>'
        % (c["slug"], esc(c["name"]), format(c["pmin"], ",d").replace(",", " "), esc(c["desc"]))
        for c in CATEGORIES)
    features = [
        ("🤝", "Официальный партнёр Безлимит", "Работаем напрямую с оператором. Номера и цены — настоящие, из его базы."),
        ("🔢", "Точный подбор по маске", "Зафиксируйте нужные цифры — дату, код, повтор — остальное подберём под вас."),
        ("⚡", "Бронь онлайн за минуту", "Понравился номер — бронируете в пару кликов, оформление у оператора."),
        ("📦", "Бесплатная доставка + eSIM", "SIM привезут по всей России бесплатно или подключат eSIM без визита в офис."),
    ]
    feat_html = "".join(
        '<div class="feature"><span class="feature-ico">%s</span><h3>%s</h3><p>%s</p></div>' % f
        for f in features)
    steps = [
        ("1", "Выберите номер", "В каталоге — по категории красоты, маске, тарифу или цене."),
        ("2", "Забронируйте", "Бронь удержит номер за вами, пока оформляете (около часа)."),
        ("3", "Оформите у оператора", "Паспорт РФ, договор и оплата — на защищённой странице Безлимит."),
        ("4", "Получите SIM", "Бесплатная доставка по РФ или eSIM — и номер ваш."),
    ]
    step_html = "".join(
        '<div class="p-step"><span class="p-step-n">%s</span><div><h3>%s</h3><p>%s</p></div></div>' % s
        for s in steps)
    body = (
        '<section class="promo-hero">'
        '<h1>Красивые номера телефонов</h1>'
        '<p class="promo-sub">Эксклюзивные комбинации от официального партнёра оператора «Безлимит». '
        'Подбор по маске и категории, честные цены, бронирование онлайн.</p>'
        '<div class="promo-actions">'
        '<a class="btn-primary" href="/">Смотреть номера</a>'
        '<a class="btn-ghost" href="/skolko-stoit-nomer/">Рассчитать стоимость</a>'
        '</div></section>'
        '<section class="features">' + feat_html + '</section>'
        '<section class="promo-block"><h2>Как это работает</h2>'
        '<div class="p-steps">' + step_html + '</div></section>'
        '<section class="promo-block"><h2>Категории красивых номеров</h2>'
        '<div class="blog-list">' + cat_cards + '</div></section>'
        '<section class="seo-text">'
        '<h2>Частые вопросы</h2>'
        '<p><b>Откуда номера?</b> Из официальной базы оператора «Безлимит», партнёром которого мы являемся. '
        'Ничего не выдумываем — цены и наличие настоящие.</p>'
        '<p><b>Кто может подключить?</b> Подключение доступно только гражданам РФ по паспорту РФ — это условие оператора.</p>'
        '<p><b>Сколько стоит?</b> Цена зависит от красоты номера. Прикиньте на '
        '<a href="/skolko-stoit-nomer/">калькуляторе</a> или посмотрите '
        '<a href="/blog/kategorii-krasivyh-nomerov/">категории</a>.</p>'
        '</section>'
        '<section class="promo-cta"><h2>Готовы выбрать номер?</h2>'
        '<a class="btn-primary" href="/">Смотреть номера</a></section>')
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title="MagzGold — красивые номера телефонов от партнёра Безлимит",
        desc="Красивые номера телефонов от официального партнёра «Безлимит»: подбор по маске и категории, честные цены, бронирование онлайн, бесплатная доставка SIM и eSIM.",
        canonical=SITE["base"] + "/kak-eto-rabotaet/",
        og_image=OG("home"),
        page_js="",
        schema=schema_breadcrumb({"name": "Как это работает", "slug": "kak-eto-rabotaet", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top=crumbs("Как это работает"),
        vitrina=body,
        footnav=nav_links(None) + patnav(),
        scripts="",
    )
    write("kak-eto-rabotaet/index.html", html_out)


def render_app():
    """Telegram Mini App — каталог номеров внутри Телеграма (кнопка меню бота ведёт сюда)."""
    tg_scripts = (
        '<script src="https://telegram.org/js/telegram-web-app.js"></script>\n'
        '<script>var _tg=window.Telegram&&window.Telegram.WebApp;'
        'if(_tg){_tg.ready();_tg.expand();document.documentElement.classList.add("in-tg");'
        'if(_tg.setHeaderColor)_tg.setHeaderColor("#0d0f13");'
        'if(_tg.setBackgroundColor)_tg.setBackgroundColor("#0d0f13");}</script>\n'
    ) + SCRIPTS
    main_top = ('<div class="tma-head"><span class="brand">Magz<span class="brand-gold">Gold</span></span>'
                '<span class="tma-sub">красивые номера · бронь онлайн</span></div>')
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title="MagzGold — красивые номера (Telegram Mini App)",
        desc="Каталог красивых номеров MagzGold внутри Telegram: подбор по маске и категориям, бронирование онлайн.",
        canonical=SITE["base"] + "/app/",
        og_image=OG("home"),
        page_js='<meta name="robots" content="noindex">',
        schema="",
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top=main_top,
        vitrina=VITRINA,
        footnav=nav_links(None) + patnav(),
        scripts=tg_scripts,
    )
    write("app/index.html", html_out)


def render_tools_hub():
    """Хаб «API и виджеты» — с него ссылки на виджет и API."""
    cards = (
        '<a class="blog-card" href="/vidzhet/"><h2>🧩 Виджет для сайта</h2>'
        '<p>Одна строка кода — и блок красивых номеров у вас на сайте. Оформление ведёт на MagzGold. '
        'Проще всего для не-разработчиков.</p></a>'
        '<a class="blog-card" href="/api/"><h2>⚙️ API для компаний</h2>'
        '<p>Программный доступ к каталогу с фильтрами (категория, цена, маска, тариф) — чтобы запускать '
        'оформление номеров из своих систем. Бронь — через ссылки на MagzGold.</p></a>')
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title="API и виджеты MagzGold — интеграция красивых номеров",
        desc="Инструменты MagzGold для сайтов и разработчиков: встраиваемый виджет красивых номеров и JSON-API. Бесплатно.",
        canonical=SITE["base"] + "/api-i-vidzhety/",
        og_image=OG("home"),
        page_js="",
        schema=schema_breadcrumb({"name": "API и виджеты", "slug": "api-i-vidzhety", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">API и виджеты</h1>\n'
                 '  <p class="page-intro">Встройте красивые номера MagzGold к себе: готовый виджет, JSON-API '
                 'или инструмент проверки. Всё бесплатно, оформление — на стороне оператора.</p>' % crumbs("API и виджеты"),
        vitrina='<div class="blog-list">%s</div>' % cards,
        footnav=nav_links(None) + patnav(),
        scripts="",
    )
    write("api-i-vidzhety/index.html", html_out)


def render_api_docs():
    """Страница API: JSON-фид номеров + как встроить (referral-safe)."""
    ex = ('fetch("https://magzgold.ru/api/numbers.json")\n'
          '  .then(r => r.json())\n'
          '  .then(d => {\n'
          '    d.numbers.forEach(n => {\n'
          '      // n.phone, n.category, n.price, n.url\n'
          '      console.log(n.phone, n.category, n.url);\n'
          '    });\n'
          '  });')
    sample = ('{\n  "site": "https://magzgold.ru",\n  "generated": "2026-08-19",\n  "count": 100,\n'
              '  "numbers": [\n    {\n      "digits": "9998887766",\n      "phone": "+7 999 888-77-66",\n'
              '      "category": "Золото",\n      "tariff": "Безлимит ULTRA 1600",\n      "price": 1600,\n'
              '      "url": "https://magzgold.ru/nomer/?p=9998887766"\n    }\n  ]\n}')
    body = (
        '<section class="seo-text">'
        '<p>Простой JSON-API актуальных красивых номеров MagzGold — для сайтов, ботов и своих витрин. '
        'Отдаётся по HTTPS, без ключей и регистрации. Бронь ведите на поле <code>url</code> каждого номера — '
        'так оформление проходит через MagzGold у оператора.</p>'
        '<h2>Эндпоинт</h2>'
        '<pre class="code">GET https://magzgold.ru/api/numbers.json</pre>'
        '<p>Возвращает снимок каталога (обновляется при каждом обновлении сайта). Поля номера: '
        '<code>digits</code>, <code>phone</code>, <code>category</code>, <code>tariff</code>, '
        '<code>price</code> (₽/мес), <code>url</code> (ссылка на бронь).</p>'
        '<h2>Пример ответа</h2>'
        '<pre class="code">' + esc(sample) + '</pre>'
        '<h2>Пример использования (JS)</h2>'
        '<pre class="code">' + esc(ex) + '</pre>'
        '<h2>Не хотите кодить?</h2>'
        '<p>Возьмите готовый <a href="/vidzhet/">виджет для сайта</a> — вставляется одной строкой и рендерит '
        'номера сам.</p>'
        '<p class="calc-disc">Данные и наличие номеров определяет оператор и могут меняться; поле '
        '<code>url</code> всегда показывает актуальный статус номера и условия оформления.</p>'
        '</section>')
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title="API красивых номеров (JSON) — для разработчиков | MagzGold",
        desc="Бесплатный JSON-API красивых номеров MagzGold по HTTPS: список номеров с категорией, тарифом, ценой и ссылкой на бронь. Без ключей.",
        canonical=SITE["base"] + "/api/",
        og_image=OG("home"),
        page_js="",
        schema=schema_breadcrumb({"name": "API", "slug": "api", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">API красивых номеров</h1>' % crumbs("API"),
        vitrina=body,
        footnav=nav_links(None) + patnav(),
        scripts="",
    )
    write("api/index.html", html_out)


def render_widget_docs():
    """Страница виджета: как встроить + настройки + ЖИВОЙ пример (сам виджет на странице)."""
    snippet = ('<div class="magzgold-widget" data-cat="gold" data-count="6"></div>\n'
               '<script src="https://magzgold.ru/widget.js" async></script>')
    body = (
        '<section class="seo-text">'
        '<p>Бесплатный виджет красивых номеров для вашего сайта. Показывает актуальные номера прямо у вас, '
        'а оформление ведёт на MagzGold. Тянет данные в браузере посетителя — не нагружает ваш сервер.</p>'
        '<h2>Как встроить</h2>'
        '<p>Вставьте этот код в HTML страницы, где нужен блок с номерами:</p>'
        '<pre class="code">' + esc(snippet) + '</pre>'
        '<h2>Настройки (атрибуты <code>data-*</code>)</h2>'
        '<ul>'
        '<li><b>data-cat</b> — категория: <code>brilliant</code>, <code>platinum</code>, <code>gold</code>, '
        '<code>silver</code>, <code>bronze</code> или пусто (все категории).</li>'
        '<li><b>data-count</b> — сколько номеров показать (1–24, по умолчанию 6).</li>'
        '<li><b>data-title</b> — свой заголовок над блоком (необязательно).</li>'
        '</ul>'
        '<p>Можно поставить несколько блоков с разными категориями на одной странице.</p>'
        '<h2>Живой пример</h2>'
        '</section>'
        '<div class="magzgold-widget" data-cat="gold" data-count="6"></div>'
        '<section class="seo-text">'
        '<p>Клик по «Забронировать» открывает страницу номера на MagzGold, где посетитель завершает бронь у '
        'оператора. Стили виджета самодостаточны и не конфликтуют с вашим сайтом.</p>'
        '</section>')
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title="Виджет красивых номеров для сайта — бесплатно | MagzGold",
        desc="Бесплатный встраиваемый виджет красивых номеров для вашего сайта: одна строка кода, номера из каталога MagzGold, оформление у оператора.",
        canonical=SITE["base"] + "/vidzhet/",
        og_image=OG("home"),
        page_js="",
        schema=schema_breadcrumb({"name": "Виджет", "slug": "vidzhet", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Виджет для сайта</h1>' % crumbs("Виджет"),
        vitrina=body,
        footnav=nav_links(None) + patnav(),
        scripts='<script src="/widget.js" async></script>',
    )
    write("vidzhet/index.html", html_out)


def render_checker():
    """Инструмент проверки «красоты» номера: свой анализатор паттернов + наличие в каталоге."""
    body = (
        '<div class="chk">'
        '<div class="chk-form">'
        '<span class="chk-prefix">+7</span>'
        '<input id="chkInput" class="chk-input" inputmode="numeric" maxlength="14" placeholder="999 888-77-66" autocomplete="off">'
        '<button id="chkBtn" class="btn-primary">Проверить</button>'
        '</div>'
        '<div id="chkOut" class="chk-out"></div>'
        '</div>'
        '<section class="seo-text">'
        '<h2>Как мы оцениваем красоту номера</h2>'
        '<p>Инструмент разбирает номер по закономерностям, которые ценятся на рынке: одинаковые цифры подряд, '
        'зеркальность (палиндром), круглые окончания на нули, повторяющиеся пары, последовательности и малое '
        'число разных цифр. Чем больше «чистых» комбинаций — тем выше оценка: <b>обычный → приятный → красивый → '
        'премиальный</b>.</p>'
        '<p>Оценка ориентировочная — это наш анализатор, а не официальная категория оператора. Если номер есть в '
        'каталоге MagzGold, ниже покажем его реальную категорию, тариф и цену, а также ссылку на бронирование. '
        'Не нашли нужный — <a href="/">подберите похожий в каталоге</a> или прикиньте бюджет на '
        '<a href="/skolko-stoit-nomer/">калькуляторе</a>.</p>'
        '</section>')
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title="Проверить красивый ли номер — оценка онлайн | MagzGold",
        desc="Проверьте, красивый ли номер телефона: онлайн-анализ паттернов (повторы, зеркальность, круглые, пары) + наличие в каталоге MagzGold.",
        canonical=SITE["base"] + "/proverit-nomer/",
        og_image=OG("home"),
        page_js="",
        schema=schema_breadcrumb({"name": "Проверить номер", "slug": "proverit-nomer", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Проверить красоту номера</h1>\n'
                 '  <p class="page-intro">Введите любой номер — покажем, насколько он «красивый» по закономерностям, '
                 'и есть ли он в каталоге MagzGold.</p>' % crumbs("Проверить номер"),
        vitrina=body,
        footnav=nav_links(None) + patnav(),
        scripts='<script src="/config.js%s"></script>\n<script src="/checker.js%s"></script>' % (_ver("config.js"), _ver("checker.js")),
    )
    write("proverit-nomer/index.html", html_out)


def render_number_page():
    """Страница одного номера /nomer/?p=<цифры> — данные тянет nomer.js из API в браузере."""
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title="Красивый номер — купить и забронировать | MagzGold",
        desc="Красивый номер телефона: описание, тариф и бронирование онлайн. Официальный партнёр оператора «Безлимит».",
        canonical=SITE["base"] + "/nomer/",
        og_image=OG("home"),
        page_js="",
        schema=schema_breadcrumb({"name": "Номер", "slug": "nomer", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Красивый номер</h1>' % crumbs("Номер"),
        vitrina=('<div class="num-page">'
                 '<div id="numView" class="num-view"><p class="status">Загружаю номер…</p></div>'
                 '<aside id="numSimilar" class="num-similar" hidden></aside>'
                 '</div>'),
        footnav=nav_links(None) + patnav(),
        scripts='<script src="/config.js%s"></script>\n<script src="/nomer.js%s"></script>' % (_ver("config.js"), _ver("nomer.js")),
    )
    write("nomer/index.html", html_out)


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
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
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
        scripts='<script src="/config.js%s"></script>\n<script src="/calc.js%s"></script>' % (_ver("config.js"), _ver("calc.js")),
    )
    write("skolko-stoit-nomer/index.html", html_out)


def render_blog_index():
    cards = "".join(
        '<a class="blog-card" href="/blog/%s/"><h2>%s</h2><p>%s</p></a>' % (a["slug"], esc(a["h1"]), esc(a["desc"]))
        for a in BLOG)
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
        title="Блог о красивых номерах — гайды и советы | MagzGold",
        desc="Блог MagzGold: как выбрать красивый номер, категории красоты, как забронировать и сколько стоит номер.",
        canonical=SITE["base"] + "/blog/",
        og_image=OG("blog"),
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
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
        title=a["title"],
        desc=a["desc"],
        canonical=SITE["base"] + "/blog/%s/" % a["slug"],
        og_image=OG("blog"),
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
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
        title="Номера с тарифом %s (%d ₽/мес) | MagzGold" % (t["name"], t["price"]),
        desc="Красивые номера с тарифом %s — абонплата %d ₽/мес. Подбор по маске, категории, бронирование онлайн — MagzGold."
             % (t["name"], t["price"]),
        canonical=SITE["base"] + "/tarif/%s/" % t["slug"],
        og_image=OG("tariff"),
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
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
        title="Тарифы Безлимит ULTRA — номера по тарифам | MagzGold",
        desc="Тарифы Безлимит ULTRA (от 399 до 5000 ₽/мес) и красивые номера на каждом из них. Подбор и бронирование — MagzGold.",
        canonical=SITE["base"] + "/tarify/",
        og_image=OG("tariff"),
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
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
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


def render_docs():
    body = (
        '<article class="article">'
        "<p>MagzGold — <b>официальный партнёр оператора связи «Безлимит»</b>. Ниже — подтверждающие документы: "
        "договор с оператором и доверенность, по которой мы уполномочены оформлять номера.</p>"
        '<div class="doc-item">'
        "<h2>Доверенность № С-800848-2026</h2>"
        "<p>Выдана <b>ООО «Безлимит»</b> (ОГРН 1197746244750, ИНН 9725007063) в рамках агентского договора с "
        "ПАО «ВымпелКом» («Билайн»). Уполномочивает оформлять и заключать договоры об оказании услуг связи. "
        "Срок — 12 месяцев. Персональные данные уполномоченного лица (паспорт, дата рождения, адрес) на "
        "публикуемой копии скрыты в целях безопасности.</p>"
        '<a href="/docs/doverennost.png" target="_blank" rel="noopener">'
        '<img class="doc-scan" src="/docs/doverennost.png" alt="Доверенность № С-800848-2026 от ООО «Безлимит»" loading="lazy"></a>'
        "</div>"
        '<div class="doc-item">'
        "<h2>Договор с оператором</h2>"
        "<p>Договор возмездного оказания услуг (публичная оферта) ООО «Безлимит», на условиях которого работает "
        "витрина. Открывается для просмотра и скачивания.</p>"
        '<a class="btn-ghost" href="/docs/dogovor-bezlimit.pdf" target="_blank" rel="noopener">Открыть договор (PDF)</a>'
        "</div>"
        "<p>Официальные оферты и политики оператора также опубликованы на его сайте: "
        '<a href="https://bezlimit.ru/legal" target="_blank" rel="noopener">bezlimit.ru/legal</a>.</p>'
        "</article>"
    )
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER,
        title="Документы MagzGold — партнёр оператора «Безлимит»",
        desc="Подтверждающие документы MagzGold: доверенность № С-800848-2026 и договор с оператором ООО «Безлимит». Официальный партнёр.",
        canonical=SITE["base"] + "/dokumenty/",
        page_js="",
        schema=schema_breadcrumb({"name": "Документы", "slug": "dokumenty", "toplevel": True}),
        nav=nav_links(None),
        header_block='    <a href="/" class="brand">Magz<span class="brand-gold">Gold</span></a>',
        main_top='%s\n  <h1 class="page-h1">Документы</h1>' % crumbs("Документы"),
        vitrina=body,
        footnav=nav_links(None) + patnav(),
        scripts="",
    )
    write("dokumenty/index.html", html_out)


def _legal_page(slug, h1, title, desc, body):
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
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
    html_out = render_page(metrika=METRIKA, 
        drawer=_DRAWER,
        title="Красивые номера на %s (+7 %s) | MagzGold" % (pfx, pfx),
        desc="Красивые номера с кодом +7 %s — подбор по маске, категории, тарифу и бронирование онлайн на MagzGold." % pfx,
        canonical=SITE["base"] + "/kod/%s/" % pfx,
        og_image=OG("code"),
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
    html_out = render_page(metrika=METRIKA, 
        drawer=_DRAWER,
        title="Номера по кодам (+7 9XX) — выбор кода | MagzGold",
        desc="Красивые номера по кодам мобильного оператора (+7 900, 916, 999 и другие). Выберите код и подберите номер — MagzGold.",
        canonical=SITE["base"] + "/kody/", page_js="", og_image=OG("code"),
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
    html_out = render_page(metrika=METRIKA, 
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
    html_out = render_page(metrika=METRIKA, drawer=_DRAWER, 
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
            + [SITE["base"] + "/%s/" % l["slug"] for l in LANDINGS]
            + [SITE["base"] + "/kak-eto-rabotaet/", SITE["base"] + "/proverit-nomer/", SITE["base"] + "/vidzhet/", SITE["base"] + "/api-i-vidzhety/", SITE["base"] + "/api/", SITE["base"] + "/skolko-stoit-nomer/", SITE["base"] + "/blog/"]
            + [SITE["base"] + "/blog/%s/" % a["slug"] for a in BLOG]
            + [SITE["base"] + "/o-servise/", SITE["base"] + "/dokumenty/", SITE["base"] + "/tarify/", SITE["base"] + "/politika/", SITE["base"] + "/polzovatelskoe-soglashenie/"]
            + [SITE["base"] + "/tarif/%s/" % t["slug"] for t in TARIFFS]
            + [SITE["base"] + "/kody/", SITE["base"] + "/faq/"]
            + [SITE["base"] + "/kod/%s/" % pfx for pfx in PREFIXES])
    today = date.today().isoformat()
    body = "".join("<url><loc>%s</loc><lastmod>%s</lastmod><changefreq>daily</changefreq></url>" % (u, today) for u in urls)
    write("sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">%s</urlset>' % body)
    write("robots.txt", "User-agent: *\nAllow: /\nSitemap: %s/sitemap.xml\n" % SITE["base"])


def make_numbers_json():
    """Статический JSON-фид красивых номеров (https, referral-safe): dist/api/numbers.json.
       Снимок на момент сборки; бронь идёт через /nomer/ (реф остаётся за нами). Ошибку сети глушим."""
    import urllib.request
    labels = {"brilliant": "Бриллиант", "platinum": "Платина", "gold": "Золото",
              "silver": "Серебро", "bronze": "Бронза"}
    token = "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw=="
    url = ("https://api.store.bezlimit.ru/v2/super-link/phones/mask-category?"
           "expand=tariff&is_reserved=false&per_page=100&phone_pattern=9NNNNNNNNN")
    try:
        req = urllib.request.Request(url, headers={"Authorization": token,
              "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
    except Exception as e:                        # noqa: BLE001
        print("⚠️  numbers.json: не удалось получить номера (%s) — фид пропущен" % e)
        return
    seen, nums = set(), []
    if isinstance(data, dict):
        for key, v in data.items():
            lbl = labels.get(key.split(",")[0].strip(), "")
            for p in (v.get("items") or []) if isinstance(v, dict) else []:
                d = "".join(c for c in str(p.get("phone", "")) if c.isdigit())[-10:]
                if len(d) != 10 or d in seen:
                    continue
                seen.add(d)
                t = p.get("tariff") or {}
                nums.append({"digits": d,
                             "phone": "+7 %s %s-%s-%s" % (d[0:3], d[3:6], d[6:8], d[8:10]),
                             "category": lbl, "tariff": t.get("name", ""), "price": t.get("price"),
                             "url": SITE["base"] + "/nomer/?p=" + d})
    os.makedirs(os.path.join(DIST, "api"), exist_ok=True)
    payload = {"site": SITE["base"], "generated": date.today().isoformat(),
               "count": len(nums), "numbers": nums}
    with open(os.path.join(DIST, "api", "numbers.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print("✅ api/numbers.json: %d номеров" % len(nums))


def copy_assets():
    for f in ("app.js", "styles.css", "config.js", "calc.js", "nav.js", "nomer.js", "checker.js", "widget.js", "favicon.svg"):
        shutil.copy(os.path.join(ROOT, f), os.path.join(DIST, f))
    make_og()
    make_numbers_json()
    copy_docs()
    write("CNAME", "magzgold.ru\n")
    open(os.path.join(DIST, ".nojekyll"), "w").close()


# Публикуемые документы: договор-оферта (публичный) + доверенность (КАРТИНКА с закрашенными перс-данными).
# Источник — _sources/ (gitignore). В dist кладём только публичный договор и уже отредактированный скан.
DOCS_SRC = [
    ("dealer_dogovor-okazaniya-uslug.pdf", "dogovor-bezlimit.pdf"),
    ("dover-public.png", "doverennost.png"),
]


def copy_docs():
    os.makedirs(os.path.join(DIST, "docs"), exist_ok=True)
    for src, dst in DOCS_SRC:
        sp = os.path.join(ROOT, "_sources", src)
        if os.path.exists(sp):
            shutil.copy(sp, os.path.join(DIST, "docs", dst))
        else:
            print("⚠️  нет исходника документа:", sp)


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    os.makedirs(DIST)
    render_home()
    for c in CATEGORIES:
        render_category(c)
    for p in PATTERNS:
        render_pattern(p)
    for l in LANDINGS:
        render_landing(l)
    render_promo()
    render_app()
    render_number_page()
    render_checker()
    render_widget_docs()
    render_tools_hub()
    render_api_docs()
    render_calc()
    render_blog_index()
    for a in BLOG:
        render_article(a)
    render_about()
    render_docs()
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
