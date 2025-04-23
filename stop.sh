#!/bin/bash

# Переход в директорию с ботом
cd "$(dirname "$0")"

# Проверка наличия файла с ID процесса
if [ -f process_id.txt ]; then
    PID=$(cat process_id.txt)
    
    # Проверка, запущен ли процесс
    if ps -p $PID > /dev/null; then
        echo "Остановка бота (PID: $PID)..."
        kill $PID
        echo "Бот остановлен."
    else
        echo "Процесс с ID $PID не найден."
    fi
    
    # Удаляем файл с ID процесса
    rm process_id.txt
else
    echo "Файл process_id.txt не найден. Бот, вероятно, не запущен."
fi 