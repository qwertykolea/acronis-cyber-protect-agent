#!/usr/bin/env python3
"""
Скрипт для поиска последней версии Acronis Agent и списка доступных установочных файлов.
"""

import os
import re
import json
import argparse
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError
from packaging.version import Version, InvalidVersion

# Список зеркал по умолчанию (можно переопределить через MIRRORS)
DEFAULT_MIRRORS = [
    "https://eu-cloud.acronis.com",
    "https://us-cloud.acronis.com",
    "https://au-cloud.acronis.com",
]

# Полный список имён файлов (как они называются на сервере)
# Взято из предоставленного списка (все уникальные имена)
ALL_FILENAMES = [
    "AcronisCyberProtect_AgentForAD_web.exe",
    "AcronisCyberProtect_AgentForESX_web.exe",
    "AcronisCyberProtect_AgentForExchange_web.exe",
    "AcronisCyberProtect_AgentForHyperV_web.exe",
    "AcronisCyberProtect_AgentForLegacyWindows_x64.exe",
    "AcronisCyberProtect_AgentForLegacyWindows_x86.exe",
    "AcronisCyberProtect_AgentForMac_arm64.dmg",
    "AcronisCyberProtect_AgentForMac_web.dmg",
    "AcronisCyberProtect_AgentForMac_x64.dmg",
    "AcronisCyberProtect_AgentForOffice_365_web.exe",
    "AcronisCyberProtect_AgentForOracle_web.exe",
    "AcronisCyberProtect_AgentForSQL_web.exe",
    "AcronisCyberProtect_AgentForSaS_web.exe",
    "AcronisCyberProtect_AgentForWindows_arm64.exe",
    "AcronisCyberProtect_AgentForWindows_web.exe",
    "AcronisCyberProtect_AgentForWindows_x64.exe",
    "AcronisCyberProtect_AgentForWindows_x86.exe",
    "AzureAppliance.vhd",
    "AzureAppliance.vhd.yml",
    "AzureDRWorker.vhd",
    "AzureDRWorker.vhd.yml",
    "Boot_media.iso",
    "Boot_media_arm64.iso",
    "CyberProtect_AgentForAD_web.exe",
    "CyberProtect_AgentForESX_web.exe",
    "CyberProtect_AgentForExchange_web.exe",
    "CyberProtect_AgentForHyperV_web.exe",
    "CyberProtect_AgentForLegacyWindows_x64.exe",
    "CyberProtect_AgentForLegacyWindows_x86.exe",
    "CyberProtect_AgentForLinux_x86.bin",
    "CyberProtect_AgentForLinux_x86_64.bin",
    "CyberProtect_AgentForMac_arm64.dmg",
    "CyberProtect_AgentForMac_web.dmg",
    "CyberProtect_AgentForMac_x64.dmg",
    "CyberProtect_AgentForOffice_365_web.exe",
    "CyberProtect_AgentForOracle_web.exe",
    "CyberProtect_AgentForSQL_web.exe",
    "CyberProtect_AgentForSaS_web.exe",
    "CyberProtect_AgentForSynology7_42659.spk",
    "CyberProtect_AgentForSynology_42659.spk",
    "CyberProtect_AgentForWindows_arm64.exe",
    "CyberProtect_AgentForWindows_web.exe",
    "CyberProtect_AgentForWindows_x64.exe",
    "CyberProtect_AgentForWindows_x86.exe",
    "ESXAppliance.zip",
    "NutanixAppliance.zip",
    "OVirtAppliance.zip",
    "ScaleAppliance.zip",
    "VHIAppliance.zip",
    "baas_installers.json",
    "vCDCyberProtectAgent.zip",
    "vCDManagementAgent.zip",
]


def get_available_versions(mirror):
    """Возвращает set всех версий (каталогов) на зеркале."""
    base_url = f"{mirror}/download/u/baas/4.0/"
    try:
        req = Request(base_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=15) as resp:
            html = resp.read().decode('utf-8')
    except URLError as e:
        print(f"Warning: Cannot fetch {base_url}: {e}")
        return set()
    # Ищем каталоги вида X.Y.Z/
    versions = re.findall(r'href="([0-9]+\.[0-9]+\.[0-9]+)/"', html)
    return set(versions)


def file_exists_on_mirror(mirror, version, filename):
    """Проверяет, существует ли конкретный файл на зеркале."""
    url = f"{mirror}/download/u/baas/4.0/{version}/{filename}"
    try:
        req = Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
        with urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except URLError:
        return False


def get_all_versions_and_assets(mirrors):
    """
    Для каждого зеркала собирает все версии.
    Затем для каждой версии проверяет наличие всех файлов (на любом зеркале).
    Возвращает словарь:
        {
            'versions': { 'X.Y.Z': [list_of_filenames], ... },
            'latest': 'X.Y.Z'   # максимальная версия по семантике
        }
    """
    # Сначала соберём все версии со всех зеркал
    all_versions = set()
    for mirror in mirrors:
        all_versions.update(get_available_versions(mirror))

    # Отсортируем версии
    try:
        sorted_versions = sorted(all_versions, key=lambda v: Version(v))
    except InvalidVersion:
        # Отфильтруем только корректные
        valid = [v for v in all_versions if re.match(r'^\d+\.\d+\.\d+$', v)]
        sorted_versions = sorted(valid, key=lambda v: Version(v))

    if not sorted_versions:
        return {'versions': {}, 'latest': None}

    # Для каждой версии соберём список файлов, доступных на любом зеркале
    result_versions = {}
    for version in sorted_versions:
        available_files = []
        for fname in ALL_FILENAMES:
            # Проверяем все зеркала, пока не найдём файл
            found = False
            for mirror in mirrors:
                if file_exists_on_mirror(mirror, version, fname):
                    found = True
                    break
            if found:
                available_files.append(fname)
        result_versions[version] = available_files

    return {
        'versions': result_versions,
        'latest': sorted_versions[-1]
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mirrors', help='Список зеркал через запятую', default=os.environ.get('MIRRORS', ''))
    parser.add_argument('--output', help='Файл для сохранения истории (JSON)', default='versions.json')
    parser.add_argument('--latest-only', help='Вывести только последнюю версию', action='store_true')
    args = parser.parse_args()

    # Определяем зеркала
    if args.mirrors:
        mirrors = [m.strip() for m in args.mirrors.split(',') if m.strip()]
    else:
        mirrors = DEFAULT_MIRRORS

    print(f"Using mirrors: {mirrors}")

    data = get_all_versions_and_assets(mirrors)
    latest = data['latest']
    if not latest:
        print("ERROR: No versions found")
        exit(1)

    print(f"Latest version: {latest}")

    # Если нужно только последнюю версию (для использования в workflow)
    if args.latest_only:
        print(f"LATEST_VERSION={latest}")
        # Также выводим список файлов для этой версии (можно через GITHUB_OUTPUT)
        files_for_latest = data['versions'].get(latest, [])
        print(f"FILES_COUNT={len(files_for_latest)}")
        # Сохраняем список файлов в переменную окружения для последующих шагов
        # (можно записать в файл, который потом прочитает workflow)
        with open('latest_files.txt', 'w') as f:
            f.write('\n'.join(files_for_latest))
        print("Saved file list to latest_files.txt")
        return

    # Обновляем историю в versions.json
    history = []
    if os.path.exists(args.output):
        with open(args.output, 'r') as f:
            try:
                history = json.load(f)
            except json.JSONDecodeError:
                history = []

    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "mirrors": mirrors,
        "latest": latest,
        "files": data['versions'].get(latest, [])
    }
    history.append(entry)

    with open(args.output, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"Updated history in {args.output}")


if __name__ == "__main__":
    main()
