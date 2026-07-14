#!/bin/bash
set -e

MIRRORS_FILE="mirrors.txt"
if [ ! -f "$MIRRORS_FILE" ]; then
    echo "ERROR: $MIRRORS_FILE not found" >&2
    exit 1
fi

BASE_PATH="/download/u/baas/4.0"
AGENT_FILE="CyberProtect_AgentForLinux_x86_64.bin"

TMP_FILE=$(mktemp)

while IFS= read -r mirror || [ -n "$mirror" ]; do
    [[ -z "$mirror" || "$mirror" =~ ^[[:space:]]*# ]] && continue
    mirror=$(echo "$mirror" | sed 's:/*$::')
    echo "Checking $mirror..." >&2

    listing=$(curl -s -L -A "Mozilla/5.0" "$mirror$BASE_PATH/")
    # Извлекаем версии из ссылок
    versions=$(echo "$listing" | grep -oP '(?<=href=")[^"]*[0-9]+\.[0-9]+\.[0-9]+/' | sed 's:/*$::' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | sort -u)

    for v in $versions; do
        echo "  Testing version $v..." >&2
        # Проверяем существование файла через GET (без загрузки тела)
        status=$(curl -s -o /dev/null -w "%{http_code}" -L -A "Mozilla/5.0" --max-time 5 "$mirror$BASE_PATH/$v/$AGENT_FILE")
        if [ "$status" = "200" ]; then
            echo "$v" >> "$TMP_FILE"
            echo "  Found version $v" >&2
        else
            echo "  Version $v not found (HTTP $status)" >&2
        fi
    done
done < "$MIRRORS_FILE"

if [ -s "$TMP_FILE" ]; then
    latest=$(sort -V "$TMP_FILE" | tail -n1)
    echo "$latest"
else
    echo "ERROR: No versions found" >&2
    exit 1
fi

rm -f "$TMP_FILE"
