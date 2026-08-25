#!/usr/bin/env bash
# MagzGold: сборка + деплой dist в public Pages-репо sementsul/magzgold.
# Использование: GH_TOKEN=ghp_xxx ./deploy.sh
set -e
cd "$(dirname "$0")"
python3 build.py
python3 verify_build.py          # smoke-гейт: битую сборку не деплоим (set -e прервёт)
cd dist
rm -rf .git
git init -q
git config user.name "sementsul"
git config user.email "45505876+sementsul@users.noreply.github.com"
git add -A
git commit -q -m "deploy"
git push -f "https://${GH_TOKEN}@github.com/sementsul/magzgold.git" HEAD:main
echo "✅ deployed → magzgold.ru"
