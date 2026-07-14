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
    echo "--- LISTING START ---" >&2
    echo "$listing" | head -c 1000 >&2
    echo -e "\n--- LISTING END ---" >&2

    # Извлекаем версии (попробуем несколько паттернов)
    versions=$(echo "$listing" | grep -oP '(?<=href=")[^"]*[0-9]+\.[0-9]+\.[0-9]+/' | sed 's:/*$::' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | sort -u)
    if [ -z "$versions" ]; then
        versions=$(echo "$listing" | grep -oP '/[0-9]+\.[0-9]+\.[0-9]+/' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | sort -u)
    fi
    if [ -z "$versions" ]; then
        # Попробуем просто найти числа с точками в тексте
        versions=$(echo "$listing" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | sort -u)
    fi

    if [ -n "$versions" ]; then
        echo "Found versions: $versions" >&2
    else
        echo "No versions found in listing" >&2
    fi

    for v in $versions; do
        echo "  Testing version $v..." >&2
        if curl -s -I -L -A "Mozilla/5.0" --fail "$mirror$BASE_PATH/$v/$AGENT_FILE" >/dev/null 2>&1; then
            echo "$v" >> "$TMP_FILE"
            echo "  Found version $v" >&2
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
