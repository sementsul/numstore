#!/usr/bin/env python3
"""Предзагрузка каталога: тянет до N номеров каждой категории из API Безлимит → data/catalog.json.

Зачем: API Безлимит медленный (~10-12 сек на запрос). Крон в GitHub Actions прогревает каталог заранее и
кладёт в статику — тогда лендинг/каталог грузятся МГНОВЕННО с нашего CDN, без ожидания живого API.
Наличие номера всё равно проверяется в момент брони (в браузере посетителя) — статика только для показа.

Формат data/catalog.json:
  {"generated_at": <iso>, "unit": "RUB", "cats": {"<slug>": [{"n":<phone>, "t":"<тариф>", "p":<цена/мес>}, ...]}}

Запускать в CI (GitHub Actions) — там IP до API проходит. С локального/контейнерного IP API часто недоступен.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.abspath(__file__))
API_BASE = "https://api.store.bezlimit.ru/v2"
# Публичный Basic-токен из бандла Безлимит (тот же, что в config.js).
API_TOKEN = "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw=="
PATTERN = "9NNNNNNNNN"
PER_CAT = 250          # сколько номеров тянем на категорию
PER_PAGE = 100         # размер страницы API
TIMEOUT = 45           # API медленный (~11с) — таймаут с запасом
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36"

# slug → код mask_categories (совпадает с CATEGORIES в build.py)
CATS = {
    "brilliant": "brilliant,brilliant_super",
    "platinum": "platinum,platinum_lite",
    "gold": "gold",
    "silver": "silver,silver_special,silver_special_2",
    "bronze": "bronze,bronze_vip,bronze AAA",
}


def _get(code, page):
    q = urllib.parse.urlencode({
        "expand": "tariff", "is_reserved": "false",
        "per_page": PER_PAGE, "page": page,
        "phone_pattern": PATTERN, "mask_categories": code,
    })
    url = "%s/super-link/phones/mask-category?%s" % (API_BASE, q)
    req = urllib.request.Request(url, headers={"Authorization": API_TOKEN, "User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read())


def _group_items(j, code):
    """Берём ТОЛЬКО группу, совпадающую с кодом категории. ВАЖНО: эндпоинт mask-category всегда возвращает
    ВСЕ 5 групп (brilliant/platinum/gold/silver/bronze) независимо от фильтра — если брать все (как раньше),
    в «бриллиант» попадают чужие категории. Ключ группы == mask_categories-код (напр. 'brilliant,brilliant_super')."""
    if isinstance(j, dict):
        g = j.get(code)
        if isinstance(g, dict):
            return [it for it in (g.get("items") or []) if isinstance(it, dict) and it.get("phone")]
    return []


def collect_cat(slug, code):
    # API отдаёт ~50 номеров на страницу для группы (per_page не всегда соблюдается) — пагинируем
    # по факту: добираем до PER_CAT или пока страницы не кончатся (пустой batch). MAX_PAGES — потолок.
    seen, items = set(), []
    MAX_PAGES = PER_CAT // 40 + 3
    for page in range(1, MAX_PAGES + 1):
        try:
            j = _get(code, page)
        except Exception as e:
            print("  %s стр.%d: ошибка %s" % (slug, page, e))
            break
        batch = _group_items(j, code)   # только СВОЯ группа, не все категории
        if not batch:
            break                        # страницы группы кончились
        for it in batch:
            ph = it.get("phone")
            if ph in seen:
                continue
            seen.add(ph)
            t = it.get("tariff") or {}
            items.append({"n": ph, "t": (t.get("name") or "")[:60], "p": t.get("price")})
            if len(items) >= PER_CAT:
                break
        if len(items) >= PER_CAT:
            break
        time.sleep(0.4)
    return items


def classify(items):
    """Классифицируем номера по тарифному тиру ОТНОСИТЕЛЬНО текущих данных категории (само-подстраивается
    при смене тарифов): top = 2 самых дорогих тарифа, mid = следующие 3, base = остальные. Поле `c` у номера.
    Список сортируем по тарифу по убыванию (премиальные — первыми)."""
    prices = sorted({x["p"] for x in items if x["p"]}, reverse=True)
    top2, mid3 = set(prices[:2]), set(prices[2:5])
    for x in items:
        p = x["p"]
        x["c"] = "top" if p in top2 else ("mid" if p in mid3 else "base")
    items.sort(key=lambda x: -(x["p"] or 0))
    return items


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "data", "catalog.json")
    cats = {}
    for slug, code in CATS.items():
        items = classify(collect_cat(slug, code))
        cats[slug] = items
        ntop = sum(1 for x in items if x["c"] == "top")
        print("✅ %s: %d номеров (top: %d)" % (slug, len(items), ntop))
    total = sum(len(v) for v in cats.values())
    if total == 0:
        print("⚠️  ноль номеров — API недоступен, catalog.json НЕ перезаписываю")
        sys.exit(1)
    data = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "unit": "RUB", "cats": cats}
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print("✅ %s: %d номеров всего (%.0f КБ)" % (out_path, total, os.path.getsize(out_path) / 1024))


if __name__ == "__main__":
    main()
