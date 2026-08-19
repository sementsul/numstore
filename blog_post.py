#!/usr/bin/env python3
"""Автопостинг статей из очереди в Blogger (Google Blogger API v3), раз в ~10 дней.

Очередь — файлы blog_queue/NN-slug.md (первая строка `# Заголовок`, дальше markdown).
Постит СЛЕДУЮЩУЮ неопубликованную, соблюдая интервал 10 дней (blog_state.json). Порядок — по имени файла.

Секреты (GitHub Secrets), в коде их НЕТ:
  BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, BLOGGER_REFRESH_TOKEN  — OAuth Desktop-приложения (scope blogger)
  BLOGGER_BLOG_ID  — числовой id блога (второй блог — свой id, OAuth-приложение можно то же)
Без секретов — сухой прогон: печатает заголовок и HTML, ничего не публикует.
Запускается кроном GitHub Actions ежедневно; скрипт сам решает, пора ли (интервал 10 дней).
"""
import html
import json
import os
import re
import glob
from datetime import date, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
QUEUE_DIR = os.path.join(ROOT, "blog_queue")
STATE_FILE = os.path.join(ROOT, "blog_state.json")
INTERVAL_DAYS = 10
SITE = "https://magzgold.ru"

CID = os.environ.get("BLOGGER_CLIENT_ID")
CSEC = os.environ.get("BLOGGER_CLIENT_SECRET")
RTOK = os.environ.get("BLOGGER_REFRESH_TOKEN")
BLOG = os.environ.get("BLOGGER_BLOG_ID")

import urllib.parse
import urllib.request


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"posted": [], "last": None}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=0)


def due(state):
    """True, если пора публиковать (прошло >= INTERVAL_DAYS с прошлой публикации)."""
    if not state.get("last"):
        return True
    try:
        last = datetime.strptime(state["last"], "%Y-%m-%d").date()
    except ValueError:
        return True
    return (date.today() - last).days >= INTERVAL_DAYS


def next_article(state):
    posted = set(state.get("posted", []))
    for path in sorted(glob.glob(os.path.join(QUEUE_DIR, "*.md"))):
        name = os.path.basename(path)
        if name not in posted:
            return path, name
    return None, None


# --- минимальный markdown -> HTML под наш формат (## подзаголовки, абзацы, [ссылки], **жирный**, - списки) ---
def inline(s):
    s = html.escape(s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", s)
    return s


def md_to_html(body):
    out, para, ul = [], [], []

    def flush_para():
        if para:
            out.append("<p>" + " ".join(para) + "</p>")
            para.clear()

    def flush_ul():
        if ul:
            out.append("<ul>" + "".join("<li>" + inline(x) + "</li>" for x in ul) + "</ul>")
            ul.clear()

    for raw in body.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush_para(); flush_ul(); continue
        if line.startswith("## "):
            flush_para(); flush_ul(); out.append("<h2>" + inline(line[3:].strip()) + "</h2>")
        elif line.startswith(("- ", "* ")):
            flush_para(); ul.append(line[2:].strip())
        else:
            flush_ul(); para.append(inline(line.strip()))
    flush_para(); flush_ul()
    return "\n".join(out)


def parse_article(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    lines = text.splitlines()
    title = "MagzGold — красивые номера"
    start = 0
    for i, l in enumerate(lines):
        if l.strip().startswith("# "):
            title = l.strip()[2:].strip()
            start = i + 1
            break
    body = "\n".join(lines[start:]).strip()
    html_body = md_to_html(body)
    html_body += ('<p><a href="%s/">Смотреть красивые номера на MagzGold</a></p>' % SITE)
    return title, html_body


def access_token():
    data = urllib.parse.urlencode({"client_id": CID, "client_secret": CSEC,
                                   "refresh_token": RTOK, "grant_type": "refresh_token"}).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["access_token"]


def publish(title, content):
    body = json.dumps({"kind": "blogger#post", "title": title, "content": content}).encode()
    req = urllib.request.Request(
        "https://www.googleapis.com/blogger/v3/blogs/%s/posts/" % BLOG,
        data=body, method="POST",
        headers={"Authorization": "Bearer " + access_token(), "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def main():
    state = load_state()
    if not due(state):
        print("ещё не прошло %d дней с прошлой публикации (%s) — пропуск" % (INTERVAL_DAYS, state.get("last")))
        return 0
    path, name = next_article(state)
    if not path:
        print("очередь пуста — все статьи опубликованы")
        return 0
    title, content = parse_article(path)
    if not all([CID, CSEC, RTOK, BLOG]):
        print("Blogger-секреты не заданы — сухой прогон (не публикую).")
        print("--- СЛЕДУЮЩАЯ СТАТЬЯ:", name, "---\nЗаголовок:", title, "\n--- HTML ---\n" + content[:1200])
        return 0
    resp = publish(title, content)
    if not resp.get("url") and not resp.get("id"):
        print("Blogger вернул неожиданный ответ:", resp)
        return 1
    state.setdefault("posted", []).append(name)
    state["last"] = date.today().isoformat()
    save_state(state)
    print("опубликовано:", name, "->", resp.get("url"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
