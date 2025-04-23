#!/bin/bash

# Обновление системы
echo "Обновление системы..."
apt-get update
apt-get upgrade -y

# Установка необходимых пакетов
echo "Установка необходимых пакетов..."
apt-get install -y python3 python3-pip git

# Клонирование репозитория
echo "Клонирование репозитория..."
# Если репозиторий уже есть локально, закомментируйте следующую строку
# git clone https://github.com/yourusername/SugreffBot.git
# cd SugreffBot

# Установка зависимостей
echo "Установка зависимостей..."
pip3 install -r requirements.txt

# Настройка прав на выполнение скриптов
echo "Настройка прав на выполнение скриптов..."
chmod +x start.sh stop.sh

echo "Настройка завершена. Теперь вы можете запустить бота с помощью ./start.sh" 