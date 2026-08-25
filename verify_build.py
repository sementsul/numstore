#!/usr/bin/env python3
"""Smoke-проверка собранного dist/ ПЕРЕД деплоем magzgold.
Ловит логически битую, но «собравшуюся» сборку (пустые/сломанные страницы, остаточные шаблон-токены,
невалидный JSON-LD, полу-пустой билд). exit 1 → deploy.sh (set -e) / catalog.yml (bash -e) прерываются →
на magzgold.ru остаётся прошлая версия. keep-alive-пуш numstore идёт ВЫШЕ по порядку → не страдает.
"""
import os, sys, re, json, glob

DIST = "dist"
errors = []

def need(cond, msg):
    if not cond:
        errors.append(msg)

# 1) Ключевые файлы есть и не подозрительно малы
for f, minsize in [("index.html", 2000), ("sitemap.xml", 300), ("robots.txt", 30), ("llms.txt", 200)]:
    p = os.path.join(DIST, f)
    need(os.path.exists(p) and os.path.getsize(p) >= minsize, f"{f}: отсутствует или слишком мал")

# 2) Главная содержит бренд
idx = os.path.join(DIST, "index.html")
if os.path.exists(idx):
    need("MagzGold" in open(idx, encoding="utf-8").read(), "index.html: нет 'MagzGold'")

# 3) Пример страницы категории: answer-first строка + модель «бесплатно/тариф»
cat = os.path.join(DIST, "kategoriya/brilliant/index.html")
if os.path.exists(cat):
    h = open(cat, encoding="utf-8").read()
    need('class="cat-facts"' in h, "kategoriya/brilliant: нет строки-факта cat-facts")
    need("бесплатно" in h and "₽/мес" in h, "kategoriya/brilliant: нет модели 'бесплатно + тариф ₽/мес'")
else:
    errors.append("kategoriya/brilliant/index.html отсутствует")

# 4) Sitemap содержит URL
sm = os.path.join(DIST, "sitemap.xml")
if os.path.exists(sm):
    need("<loc>" in open(sm, encoding="utf-8").read(), "sitemap.xml без <loc>")

# 5) Нет остаточных шаблон-токенов/битых значений (выборка страниц)
BAD = ["{{", "None ₽", "{tmin}", "{slug}", ">None<", "от  ₽/мес"]
sample = (glob.glob(os.path.join(DIST, "kategoriya/*/index.html"))
          + glob.glob(os.path.join(DIST, "blog/*/index.html"))[:50]
          + [idx])
for p in sample:
    if not os.path.exists(p):
        continue
    h = open(p, encoding="utf-8", errors="ignore").read()
    for m in BAD:
        if m in h:
            errors.append(f"{os.path.relpath(p, DIST)}: битый маркер '{m}'")
            break

# 6) JSON-LD парсится на ключевых страницах
for p in [idx, cat]:
    if not os.path.exists(p):
        continue
    h = open(p, encoding="utf-8").read()
    for block in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            json.loads(block)
        except Exception as e:
            errors.append(f"{os.path.relpath(p, DIST)}: невалидный JSON-LD ({str(e)[:40]})")
            break

# 7) Защита от полу-пустой сборки
n = len(glob.glob(os.path.join(DIST, "**", "index.html"), recursive=True))
need(n >= 50, f"подозрительно мало страниц: {n}")

if errors:
    print("🔴 SMOKE-ПРОВЕРКА dist/ ПРОВАЛЕНА — деплой отменяется:")
    for e in errors[:20]:
        print("  •", e)
    sys.exit(1)
print(f"✅ smoke-проверка dist/ пройдена ({n} страниц)")
