#!/bin/bash

echo "=========================================================="
echo "Container started. Checking Acronis Agent state..."
echo "=========================================================="

CONFIG_FILE="/etc/Acronis/BackupAndRecovery.config"
PERSISTENT_MACHINE_ID="/etc/Acronis/machine-id"

    # Если файла конфигурации нет в смонтированном volume — это ПЕРВЫЙ запуск
    # If there is no configuration file on the mounted volume, this is the FIRST time the programme is being run
if [ ! -f "$CONFIG_FILE" ]; then
    echo "First launch for this tenant. Populating volumes from clean template..."

    # 1. Генерируем уникальный системный machine-id и дублируем на постоянный том
	# 1. Generate a unique system machine-ID and copy it to a persistent volume
    echo "Generating unique system machine-id..."
    cat /proc/sys/kernel/random/uuid | tr -d '-' > "$PERSISTENT_MACHINE_ID"
    cp "$PERSISTENT_MACHINE_ID" /etc/machine-id

    # 2. Копируем чистую установку из шаблона во внешние volumes
	# 2. Copy a clean installation from the template to external volumes
    cp -rp /opt/acronis_template/etc/* /etc/Acronis/ 2>/dev/null
    cp -rp /opt/acronis_template/var/* /var/lib/Acronis/ 2>/dev/null
    cp -rp /opt/acronis_template/opt_var/* /opt/acronis/var/ 2>/dev/null

    # 3. СБРОС ИДЕНТИФИКАТОРОВ AAKORE И SIEM
	# 3. RESET AAKORE AND SIEM IDENTIFIERS
    # Удаляем старые привязки баз данных, чтобы компоненты сгенерировали новые чистые UUID
	# Remove old database bindings so that the components can generate new, clean UUIDs
    rm -rf /opt/acronis/var/aakore/*.db*
    rm -rf /opt/acronis/var/siem-connector/*.db*
    rm -f /etc/Acronis/aakore.reg

    # 4. Генерируем уникальные ID для MMS агента
	# 4. Generate unique IDs for the MMS agent
    NEW_MMS_ID=$(cat /proc/sys/kernel/random/uuid | tr 'a-f' 'A-F')
    NEW_INSTANCE_ID=$(cat /proc/sys/kernel/random/uuid | tr 'a-f' 'A-F')

    echo "Applying unique IDs using native Acronis tool..."
    acropsh /usr/lib/Acronis/PyShell/site-tools/change_machine_id.py -m "$NEW_MMS_ID" -i "$NEW_INSTANCE_ID"

else
    echo "Persistent volume found. Keeping existing Acronis IDs."
    
    # Восстанавливаем сохраненный ранее machine-id, чтобы он совпадал с зарегистрированным в облаке
	# Restore the previously saved machine-id so that it matches the one registered in the cloud
    if [ -f "$PERSISTENT_MACHINE_ID" ]; then
        echo "Restoring persistent system machine-id..."
        cp "$PERSISTENT_MACHINE_ID" /etc/machine-id
    fi
fi

    # Отключаем Active Protection превентивно
	# Disable Active Protection as a precaution
if [ -f /etc/init.d/acronis_active_protection ]; then
    /etc/init.d/acronis_active_protection stop 2>/dev/null
    chmod -x /etc/init.d/acronis_active_protection
fi

    # Запускаем основные службы Акрониса
	# Launch the main Acronis services
echo "Starting Acronis daemons..."

    # Запуск основного движка микрослужб (aakore) напрямую в фоне
	# Launch the main microservices engine (aakore) directly in the background
if [ -f /etc/init.d/aakore ]; then
    /etc/init.d/aakore start
elif [ -f /opt/acronis/aakore ]; then
    echo "Starting aakore core engine manually in background..."
    /opt/acronis/aakore run &
else
    echo "ERROR: aakore binary not found! SIEM connector will not work."
fi

    # Запускаем остальные legacy службы, у которых есть init.d скрипты
	# Start the remaining legacy services that have init.d scripts
for service in acronis_mms acronis_schedule; do
    if [ -f /etc/init.d/$service ]; then
        /etc/init.d/$service start
    fi
done

echo "Waiting 10 seconds for services to stabilize..."
sleep 10

echo "Container is fully stabilized and ready."
exec tail -f /dev/null