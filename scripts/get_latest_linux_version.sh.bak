#!/bin/bash
set -e

MIRRORS_FILE="mirrors.txt"
if [ ! -f "$MIRRORS_FILE" ]; then
    echo "ERROR: $MIRRORS_FILE not found" >&2
    exit 1
fi

BASE_PATH="/download/u/baas/4.0"

# Временный файл для сбора всех версий
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
        echo "$v" >> "$TMP_FILE"
    done
done < "$MIRRORS_FILE"

if [ ! -s "$TMP_FILE" ]; then
    echo "ERROR: No versions found" >&2
    exit 1
fi

# Берём максимальную версию (семантическая сортировка)
latest=$(sort -V "$TMP_FILE" | tail -n1)
echo "$latest"

rm -f "$TMP_FILE"
