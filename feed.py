#!/usr/bin/env python3
"""Подборка красивых номеров → пост в Telegram-канал (со ссылками на /nomer/).

Тянет номера из API Безлимита (тот же публичный токен, что и на сайте), отбирает свежую подборку
по категориям, форматирует предложение и постит в канал. Дедуп через feed_state.json (не повторяем
номера, что уже слали). Запускается кроном GitHub Actions (.github/workflows/tg.yml).

Секреты (GitHub → Settings → Secrets and variables → Actions):
  TELEGRAM_TOKEN    — токен бота от @BotFather
  TELEGRAM_CHANNEL  — @username канала (бот должен быть его администратором)
Без секретов — «сухой» прогон: печатает готовый пост, ничего не публикует.
"""
import json
import os
import urllib.parse
import urllib.request

API_BASE = "https://api.store.bezlimit.ru/v2"
# Публичный Basic-токен витрины (не секрет — он же захардкожен в config.js сайта).
API_TOKEN = os.environ.get("BEZLIMIT_TOKEN", "Basic YXBpU3RvcmU6VkZ6WFdOSmhwNTVtc3JmQXV1dU0zVHBtcnFTRw==")
SITE = "https://magzgold.ru"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.environ.get("TELEGRAM_CHANNEL")

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feed_state.json")
STATE_KEEP = 400          # сколько последних отправленных номеров помним (для дедупа)
PER_CAT = 2               # сколько номеров берём из каждой категории
MAX_ITEMS = 10            # всего в одном посте

# порядок и подписи категорий (ключ ответа API → бейдж)
CAT_ORDER = [("brilliant", "Бриллиант"), ("platinum", "Платина"), ("gold", "Золото"),
             ("silver", "Серебро"), ("bronze", "Бронза")]


def digits_of(phone):
    return "".join(ch for ch in str(phone) if ch.isdigit())[-10:]


def fmt_phone(phone):
    s = digits_of(phone)
    if len(s) != 10:
        return "+7 " + s
    return "+7 %s %s-%s-%s" % (s[0:3], s[3:6], s[6:8], s[8:10])


def fmt_money(n):
    try:
        return "{:,}".format(int(n)).replace(",", " ") + " ₽"
    except (ValueError, TypeError):
        return ""


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"sent": []}


def save_state(state):
    state["sent"] = state["sent"][-STATE_KEEP:]
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=0)


def fetch_numbers():
    """Возвращает {cat_key: [phone_obj, ...]} по верхнеуровневым категориям ответа."""
    q = urllib.parse.urlencode({
        "expand": "tariff", "is_reserved": "false", "per_page": "100",
        "phone_pattern": "9NNNNNNNNN",
    })
    # UA обязателен: WAF Безлимита режет "Python-urllib" (403), браузерный UA проходит.
    req = urllib.request.Request(API_BASE + "/super-link/phones/mask-category?" + q,
                                 headers={"Authorization": API_TOKEN,
                                          "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                                                        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    out = {}
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, dict) and isinstance(v.get("items"), list):
                out[k] = v["items"]
    return out


def pick(groups, sent):
    """Отбираем свежую подборку: до PER_CAT из каждой категории по порядку, не повторяя отправленные."""
    seen = set(sent)
    chosen = []
    for key, label in CAT_ORDER:
        # находим ключ ответа, начинающийся с этой категории (напр. "brilliant,brilliant_super")
        items = []
        for gk, gitems in groups.items():
            if gk.split(",")[0].strip() == key:
                items = gitems
                break
        taken = 0
        for p in items:
            d = digits_of(p.get("phone", ""))
            if len(d) != 10 or d in seen:
                continue
            t = p.get("tariff") or {}
            chosen.append({"d": d, "phone": p.get("phone"), "cat": label,
                           "tariff": t.get("name", ""), "price": t.get("price")})
            seen.add(d)
            taken += 1
            if taken >= PER_CAT or len(chosen) >= MAX_ITEMS:
                break
        if len(chosen) >= MAX_ITEMS:
            break
    return chosen


def build_message(items):
    lines = ["💎 <b>Красивые номера — свежая подборка</b>", ""]
    for it in items:
        price = fmt_money(it["price"])
        meta = " · ".join(x for x in [it["cat"], (("тариф " + price + "/мес") if price else "")] if x)
        url = "%s/nomer/?p=%s" % (SITE, it["d"])
        lines.append('🔹 <a href="%s"><b>%s</b></a>\n    %s' % (url, fmt_phone(it["phone"]), meta))
    lines += ["", "Оформление онлайн · доставка SIM по РФ бесплатно",
              '🔗 <a href="%s/">magzgold.ru</a>' % SITE]
    return "\n".join(lines)


def post_telegram(text):
    api = "https://api.telegram.org/bot%s/sendMessage" % TELEGRAM_TOKEN
    payload = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHANNEL, "text": text,
        "parse_mode": "HTML", "disable_web_page_preview": "true",
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(api, data=payload), timeout=30) as r:
        return json.load(r)


def main():
    state = load_state()
    try:
        groups = fetch_numbers()
    except Exception as e:                       # noqa: BLE001 — сеть/парсинг, не валим воркфлоу
        print("не удалось получить номера:", e)
        return 0
    items = pick(groups, state["sent"])
    if not items:
        print("свежих номеров нет (все уже слали) — пропуск")
        return 0
    text = build_message(items)
    if not TELEGRAM_TOKEN or not TELEGRAM_CHANNEL:
        print("TELEGRAM_TOKEN/TELEGRAM_CHANNEL не заданы — сухой прогон (не публикую).\n--- пост ---\n")
        print(text)
        return 0
    resp = post_telegram(text)
    if not resp.get("ok"):
        print("Telegram вернул ошибку:", resp)
        return 1
    state["sent"].extend(it["d"] for it in items)
    save_state(state)
    print("опубликовано номеров:", len(items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
