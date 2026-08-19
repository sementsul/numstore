# MagzGold (magzgold.ru)

Витрина красивых номеров (реферальная, партнёр Безлимит). Некастодиально — каталог грузится в браузере
посетителя, бронь/оплата на стороне оператора.

- **Сборка:** `python3 build.py` → `dist/` (~50 SEO-страниц: категории, паттерны, тарифы, коды, калькулятор, блог, FAQ, о сервисе, юр, 404, sitemap/robots).
- **Превью:** `cd dist && python3 -m http.server 5173 --bind 0.0.0.0` → http://localhost:5173
- **Стек:** статика (HTML/CSS/JS), тёмная премиум-тема. Витрина: маска-поиск + сайдбар-фильтры + бронь (клиентский API, ban-proof).
- **Детали:** `TZ.md`, `docs/project-notes.md` (карта/решения), `docs/numstore.usecases.md` (сценарии).

🟢 Прод: **https://magzgold.ru** (GitHub Pages, репо sementsul/magzgold public). Редеплой: `GH_TOKEN=… ./deploy.sh`. Источник (этот репо) приватный.
