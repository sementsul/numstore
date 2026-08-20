#!/usr/bin/env python3
"""Сбор истории средней абонплаты тарифа по категориям номеров (для крона GitHub Actions).

Тянет каталог из API Безлимита, считает среднюю цену тарифа (₽/мес) по каждой категории
(бронза…бриллиант) и дописывает точку с сегодняшней датой в history-файл (одна точка на дату,
при повторном запуске за тот же день — перезапись). Формат читает график на сайте.

Использование: python3 collect_prices.py data/price_history.json
UA обязателен (WAF Безлимита режет Python-urllib). Токен публичный (витрина).
"""
import json
import os
import sys
import urllib.request
from datetime import date

TOKEN = "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw=="
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
LABELS = {"brilliant": "Бриллиант", "platinum": "Платина", "gold": "Золото",
          "silver": "Серебро", "bronze": "Бронза"}
ORDER = ["Бронза", "Серебро", "Золото", "Платина", "Бриллиант"]
BAD = ("Анадыр", "Норильск")  # региональные тарифы не учитываем


def avg_by_category(data):
    agg = {}
    if isinstance(data, dict):
        for key, v in data.items():
            lbl = LABELS.get(key.split(",")[0].strip())
            if not lbl or not isinstance(v, dict):
                continue
            for p in (v.get("items") or []):
                t = p.get("tariff") or {}
                pr = t.get("price")
                name = t.get("name") or ""
                if pr is None or any(b in name for b in BAD):
                    continue
                agg.setdefault(lbl, []).append(pr)
    return {c: round(sum(a) / len(a)) for c, a in agg.items() if a}


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "data/price_history.json"
    url = ("https://api.store.bezlimit.ru/v2/super-link/phones/mask-category?"
           "expand=tariff&is_reserved=false&per_page=100&phone_pattern=9NNNNNNNNN")
    req = urllib.request.Request(url, headers={"Authorization": TOKEN, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.load(r)
    avg = avg_by_category(data)
    if not avg:
        print("нет данных — точка не добавлена")
        return

    hist = {"unit": "₽/мес (средняя абонплата тарифа)", "categories": ORDER, "points": []}
    if os.path.exists(path):
        try:
            hist = json.load(open(path, encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    hist.setdefault("categories", ORDER)
    hist.setdefault("points", [])
    hist["unit"] = "₽/мес (средняя абонплата тарифа)"

    today = date.today().isoformat()
    hist["points"] = [pt for pt in hist["points"] if pt.get("date") != today]  # без дублей за день
    hist["points"].append({"date": today, "avg": avg})
    hist["points"].sort(key=lambda p: p["date"])

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(hist, f, ensure_ascii=False, separators=(",", ":"))
    print("точка %s добавлена: %s (всего точек: %d)" % (today, avg, len(hist["points"])))


if __name__ == "__main__":
    main()
