#!/usr/bin/env python3
"""
Скрипт для поиска последней версии Acronis Agent на нескольких зеркалах.
Сохраняет полный список версий для всех ОС в JSON-файл (для истории).
"""

import os
import re
import json
import argparse
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError
from packaging.version import Version, InvalidVersion

# Список зеркал (можно переопределить через переменную окружения MIRRORS, разделённые запятой)
DEFAULT_MIRRORS = [
    "https://eu-cloud.acronis.com",
    "https://us-cloud.acronis.com",
    "https://au-cloud.acronis.com",
]

# Шаблоны имён файлов для разных ОС (ключ - идентификатор ОС, значение - regex для поиска в листинге)
# Вы можете добавлять новые ОС по мере необходимости
OS_PATTERNS = {
    "linux": r'CyberProtect_AgentForLinux.*\.bin',
    "windows": r'CyberProtect_AgentForWindows.*\.exe',
    "macos": r'CyberProtect_AgentForMac.*\.dmg',
}

def get_version_dirs(mirror):
    """Получить список подкаталогов (версий) на зеркале по пути /download/u/baas/4.0/"""
    base_url = f"{mirror}/download/u/baas/4.0/"
    try:
        with urlopen(base_url, timeout=10) as resp:
            html = resp.read().decode('utf-8')
    except URLError as e:
        print(f"Warning: Cannot fetch {base_url}: {e}")
        return []
    # Ищем все ссылки вида href="X.Y.Z/" (числа и точки)
    versions = re.findall(r'href="([0-9]+\.[0-9]+\.[0-9]+)/"', html)
    return set(versions)  # уникальные

def check_file_exists(mirror, version, pattern):
    """Проверяет, существует ли файл, соответствующий pattern, в каталоге версии"""
    url = f"{mirror}/download/u/baas/4.0/{version}/"
    try:
        with urlopen(url, timeout=10) as resp:
            html = resp.read().decode('utf-8')
    except URLError:
        return False
    # Ищем любой файл, подходящий под regex
    match = re.search(pattern, html)
    return match is not None

def get_all_versions(mirrors):
    """
    Собирает все версии для всех ОС со всех зеркал.
    Возвращает словарь вида:
    {
        "linux": ["26.6.42659", "26.6.42660", ...],
        "windows": [...],
        ...
    }
    """
    result = {os_name: set() for os_name in OS_PATTERNS}
    for mirror in mirrors:
        versions = get_version_dirs(mirror)
        for v in versions:
            for os_name, pattern in OS_PATTERNS.items():
                if check_file_exists(mirror, v, pattern):
                    result[os_name].add(v)
    # Преобразуем set в список и сортируем семантически
    for os_name in result:
        # Сортируем с помощью packaging.version
        try:
            sorted_versions = sorted(result[os_name], key=lambda v: Version(v))
        except InvalidVersion:
            # если какая-то версия не соответствует формату, игнорируем её
            sorted_versions = sorted([v for v in result[os_name] if re.match(r'^\d+\.\d+\.\d+$', v)], key=lambda v: Version(v))
        result[os_name] = sorted_versions
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mirrors', help='Список зеркал через запятую', default=os.environ.get('MIRRORS', ''))
    parser.add_argument('--output', help='Файл для сохранения полного списка версий (JSON)', default='versions.json')
    parser.add_argument('--os', help='ОС для выбора последней версии (по умолчанию linux)', default='linux')
    args = parser.parse_args()

    # Определяем список зеркал
    if args.mirrors:
        mirrors = [m.strip() for m in args.mirrors.split(',') if m.strip()]
    else:
        mirrors = DEFAULT_MIRRORS

    print(f"Using mirrors: {mirrors}")

    all_versions = get_all_versions(mirrors)

    # Сохраняем полную историю в JSON с меткой времени
    if args.output:
        # Читаем существующий файл, если есть
        history = []
        if os.path.exists(args.output):
            with open(args.output, 'r') as f:
                try:
                    history = json.load(f)
                except json.JSONDecodeError:
                    history = []
        # Добавляем новую запись
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "mirrors": mirrors,
            "versions": all_versions
        }
        history.append(entry)
        with open(args.output, 'w') as f:
            json.dump(history, f, indent=2)
        print(f"Updated history in {args.output}")

    # Для сборки образа нужна последняя версия для указанной ОС (по умолчанию linux)
    target_os = args.os.lower()
    if target_os not in all_versions or not all_versions[target_os]:
        print(f"ERROR: No versions found for OS '{target_os}'")
        exit(1)
    latest = all_versions[target_os][-1]  # уже отсортированы
    print(f"Latest version for {target_os}: {latest}")

    # Выводим только последнюю версию для использования в workflow (можно захватить через GITHUB_OUTPUT)
    print(f"LATEST_VERSION={latest}")
    # Также выводим весь JSON для отладки (опционально)
    # print(json.dumps(all_versions, indent=2))

if __name__ == "__main__":
    main()
