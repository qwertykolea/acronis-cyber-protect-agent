#!/bin/bash
set -e

MIRRORS_FILE="mirrors.txt"
if [ ! -f "$MIRRORS_FILE" ]; then
    echo "ERROR: $MIRRORS_FILE not found" >&2
    exit 1
fi

BASE_PATH="/download/u/baas/4.0"

# Временный файл для сбора всех версий и их зеркал
TMP_FILE=$(mktemp)

while IFS= read -r mirror || [ -n "$mirror" ]; do
    [[ -z "$mirror" || "$mirror" =~ ^[[:space:]]*# ]] && continue
    mirror=$(echo "$mirror" | sed 's:/*$::')
    echo "Checking $mirror..." >&2

    # Получаем листинг каталога
    listing=$(curl -s -L -A "Mozilla/5.0" --max-time 10 "$mirror$BASE_PATH/")
    # Извлекаем все версии (числа с точками) из ссылок
    versions=$(echo "$listing" | grep -oP '(?<=href=")[^"]*[0-9]+\.[0-9]+\.[0-9]+/' | sed 's:/*$::' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | sort -u)
    
    for v in $versions; do
        # Сохраняем связку версия|зеркало
        echo "$v|$mirror" >> "$TMP_FILE"
    done
done < "$MIRRORS_FILE"

if [ ! -s "$TMP_FILE" ]; then
    echo "ERROR: No versions found" >&2
    exit 1
fi

# Берём максимальную версию (благодаря формату "версия|зеркало" sort -V сработает идеально)
latest_line=$(sort -V "$TMP_FILE" | tail -n1)
latest_version=$(echo "$latest_line" | cut -d'|' -f1)
latest_mirror=$(echo "$latest_line" | cut -d'|' -f2)

rm -f "$TMP_FILE"

# Если скрипт запущен в GitHub Actions, пишем в GITHUB_OUTPUT оба параметра
if [ -n "$GITHUB_OUTPUT" ]; then
    echo "version=$latest_version" >> "$GITHUB_OUTPUT"
    echo "mirror=$latest_mirror" >> "$GITHUB_OUTPUT"
else
    echo "version=$latest_version"
    echo "mirror=$latest_mirror"
fi
