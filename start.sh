#!/bin/bash

# Переход в директорию с ботом
cd "$(dirname "$0")"

# Активация виртуального окружения (если используется)
# source venv/bin/activate

# Запуск бота
python3 bot.py > bot.log 2>&1 &

echo "Бот запущен. Логи записываются в bot.log"
echo "ID процесса: $!"

# Сохраняем ID процесса для возможности остановки
echo $! > process_id.txt 