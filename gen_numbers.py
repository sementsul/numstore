#!/usr/bin/env python3
"""Генерация JSON-фида красивых номеров (для авто-обновления кроном GitHub Actions).

Тянет актуальные номера из API Безлимита и пишет numbers.json (тот же формат, что build.py).
Путь вывода — аргумент (по умолчанию ./numbers.json). Без секретов: публичный токен витрины.
UA обязателен (WAF Безлимита режет Python-urllib).
"""
import json
import sys
import urllib.request
from datetime import date, datetime, timezone

SITE = "https://magzgold.ru"
TOKEN = "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw=="
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
LABELS = {"brilliant": "Бриллиант", "platinum": "Платина", "gold": "Золото",
          "silver": "Серебро", "bronze": "Бронза"}


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "numbers.json"
    url = ("https://api.store.bezlimit.ru/v2/super-link/phones/mask-category?"
           "expand=tariff&is_reserved=false&per_page=100&phone_pattern=9NNNNNNNNN")
    req = urllib.request.Request(url, headers={"Authorization": TOKEN, "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        data = json.load(r)
    seen, nums = set(), []
    if isinstance(data, dict):
        for key, v in data.items():
            lbl = LABELS.get(key.split(",")[0].strip(), "")
            for p in (v.get("items") or []) if isinstance(v, dict) else []:
                d = "".join(c for c in str(p.get("phone", "")) if c.isdigit())[-10:]
                if len(d) != 10 or d in seen:
                    continue
                seen.add(d)
                t = p.get("tariff") or {}
                nums.append({"digits": d,
                             "phone": "+7 %s %s-%s-%s" % (d[0:3], d[3:6], d[6:8], d[8:10]),
                             "category": lbl, "tariff": t.get("name", ""), "price": t.get("price"),
                             "url": SITE + "/nomer/?p=" + d})
    payload = {"site": SITE, "generated": date.today().isoformat(),
               "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
               "count": len(nums), "numbers": nums}
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print("numbers.json: %d номеров -> %s" % (len(nums), out_path))


if __name__ == "__main__":
    raise SystemExit(main())
