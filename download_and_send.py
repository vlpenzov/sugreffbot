#!/usr/bin/env python3
import os
import csv
import asyncio
import tempfile
import paramiko
import logging
import traceback
import getpass
from datetime import datetime
from telegram import Bot, InputFile
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("download_send.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Настройки для подключения к серверу
SSH_HOST = '217.198.13.111'
SSH_PORT = 22
SSH_USERNAME = 'root'
SSH_PASSWORD = getpass.getpass("Введите пароль для SSH: ")

# Настройки Telegram
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    logger.error("Отсутствует токен для Telegram. Установите переменную окружения TELEGRAM_BOT_TOKEN")
    raise ValueError("Отсутствует токен для Telegram. Установите переменную окружения TELEGRAM_BOT_TOKEN")

CHAT_ID = "Избранное"  # Название чата Telegram

# Пути на сервере
REMOTE_DB = "/opt/sugreffbot/bot.db"

# Локальные пути
LOCAL_TEMP_DIR = "temp_data"
LOCAL_DB = f"{LOCAL_TEMP_DIR}/bot.db"
USERS_CSV = f"{LOCAL_TEMP_DIR}/participants.csv"
SCREENSHOTS_CSV = f"{LOCAL_TEMP_DIR}/screenshots.csv"
MERGED_CSV = f"{LOCAL_TEMP_DIR}/merged_data.csv"

def ensure_dir_exists(path):
    """Создает директорию, если она не существует"""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Создана директория: {path}")

def download_from_server():
    """Скачивает файлы с сервера через SSH"""
    logger.info("Подключение к серверу...")
    
    try:
        # Создаем SSH-клиент
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Подключаемся к серверу
        logger.debug(f"Попытка подключения к {SSH_HOST}:{SSH_PORT} как пользователь {SSH_USERNAME}")
        client.connect(
            hostname=SSH_HOST,
            port=SSH_PORT,
            username=SSH_USERNAME,
            password=SSH_PASSWORD
        )
        logger.info("Успешное подключение к серверу")
        
        # Создаем SFTP-клиент
        sftp = client.open_sftp()
        
        # Скачиваем файл базы данных
        logger.info(f"Скачиваем базу данных с сервера из {REMOTE_DB}...")
        sftp.get(REMOTE_DB, LOCAL_DB)
        logger.info(f"База данных успешно скачана: {LOCAL_DB}")
        
        # Закрываем соединение
        sftp.close()
        client.close()
        logger.info("Соединение с сервером закрыто")
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при скачивании файлов с сервера: {e}")
        logger.error(traceback.format_exc())  # Выводим полную трассировку стека
        return False

def export_data_from_db():
    """Экспортирует данные из SQLite в CSV файлы"""
    import sqlite3
    
    try:
        logger.info(f"Подключение к базе данных {LOCAL_DB}...")
        conn = sqlite3.connect(LOCAL_DB)
        cursor = conn.cursor()
        
        # Проверка структуры базы данных
        logger.debug("Проверка структуры базы данных...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.debug(f"Таблицы в базе данных: {tables}")
        
        # Экспорт данных участников
        logger.info(f"Экспорт участников в {USERS_CSV}...")
        with open(USERS_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['user_id', 'username', 'subscribed'])
            
            cursor.execute("SELECT user_id, username, subscribed FROM users")
            rows = cursor.fetchall()
            logger.debug(f"Найдено {len(rows)} пользователей")
            for row in rows:
                writer.writerow(row)
        
        # Экспорт данных скриншотов
        logger.info(f"Экспорт скриншотов в {SCREENSHOTS_CSV}...")
        with open(SCREENSHOTS_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['id', 'user_id', 'file_id', 'verified'])
            
            cursor.execute("SELECT id, user_id, file_id, verified FROM screenshots")
            rows = cursor.fetchall()
            logger.debug(f"Найдено {len(rows)} скриншотов")
            for row in rows:
                writer.writerow(row)
        
        # Добавляем данные о участниках турнира
        logger.info("Получаем данные об участниках турнира...")
        participants_in_raffle = set()
        cursor.execute("SELECT user_id FROM participants")
        rows = cursor.fetchall()
        logger.debug(f"Найдено {len(rows)} участников розыгрыша")
        for row in rows:
            participants_in_raffle.add(row[0])
        
        conn.close()
        logger.info("Данные успешно экспортированы из базы данных")
        
        return participants_in_raffle
    except Exception as e:
        logger.error(f"Ошибка при экспорте данных из базы: {e}")
        logger.error(traceback.format_exc())  # Выводим полную трассировку стека
        return set()

def merge_data(participants_in_raffle):
    """Объединяет данные из CSV файлов в один"""
    try:
        # Загружаем данные пользователей
        users = {}
        logger.info(f"Загрузка данных пользователей из {USERS_CSV}...")
        with open(USERS_CSV, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Пропускаем заголовок
            for row in reader:
                user_id = row[0]
                username = row[1] or "Без имени"
                subscribed = row[2] == '1'
                users[user_id] = {
                    'username': username,
                    'subscribed': subscribed,
                    'in_raffle': user_id in participants_in_raffle,
                    'screenshots': []
                }
        
        # Загружаем данные скриншотов
        logger.info(f"Загрузка данных скриншотов из {SCREENSHOTS_CSV}...")
        with open(SCREENSHOTS_CSV, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Пропускаем заголовок
            for row in reader:
                screenshot_id = row[0]
                user_id = row[1]
                file_id = row[2]
                verified = row[3] == '1'
                
                # Добавляем пользователя, если его нет
                if user_id not in users:
                    users[user_id] = {
                        'username': "Неизвестный",
                        'subscribed': False,
                        'in_raffle': False,
                        'screenshots': []
                    }
                
                # Добавляем скриншот к пользователю
                users[user_id]['screenshots'].append({
                    'id': screenshot_id,
                    'file_id': file_id,
                    'verified': verified
                })
        
        # Создаем единый CSV файл
        logger.info(f"Создание объединенного файла {MERGED_CSV}...")
        with open(MERGED_CSV, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'ID пользователя', 
                'Имя пользователя', 
                'Подписан на канал', 
                'Участвует в розыгрыше', 
                'Кол-во скриншотов',
                'ID скриншотов'
            ])
            
            for user_id, user_data in users.items():
                screenshot_ids = '; '.join([s['id'] for s in user_data['screenshots']])
                writer.writerow([
                    user_id,
                    user_data['username'],
                    'Да' if user_data['subscribed'] else 'Нет',
                    'Да' if user_data['in_raffle'] else 'Нет',
                    len(user_data['screenshots']),
                    screenshot_ids
                ])
        
        logger.info("Данные успешно объединены")
        return users
    except Exception as e:
        logger.error(f"Ошибка при объединении данных: {e}")
        return {}

async def send_to_telegram(users):
    """Отправляет данные в Telegram"""
    try:
        logger.info("Отправка данных в Telegram...")
        bot = Bot(token=TOKEN)
        
        # Отправляем CSV файл
        logger.info(f"Отправка файла {MERGED_CSV}...")
        with open(MERGED_CSV, 'rb') as file:
            await bot.send_document(
                chat_id=CHAT_ID,
                document=InputFile(file.read(), filename="merged_data.csv"),
                caption="📊 Список участников розыгрыша с информацией о скриншотах"
            )
        
        # Подсчитываем статистику
        total_users = len(users)
        users_with_screenshots = sum(1 for user in users.values() if user['screenshots'])
        total_screenshots = sum(len(user['screenshots']) for user in users.values())
        participants_in_raffle = sum(1 for user in users.values() if user['in_raffle'])
        
        # Отправляем статистику
        stats_message = (
            "📊 *Статистика розыгрыша*\n\n"
            f"👥 Всего пользователей: {total_users}\n"
            f"🖼 Пользователей со скриншотами: {users_with_screenshots}\n"
            f"📸 Всего скриншотов: {total_screenshots}\n"
            f"🎯 Участников в розыгрыше: {participants_in_raffle}"
        )
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text=stats_message,
            parse_mode="Markdown"
        )
        
        # Спрашиваем, нужно ли отправлять скриншоты
        keyboard = [
            [{"text": "✅ Да, отправить скриншоты", "callback_data": "send_screenshots"}],
            [{"text": "❌ Нет, не нужно", "callback_data": "no_screenshots"}]
        ]
        
        await bot.send_message(
            chat_id=CHAT_ID,
            text="Отправить скриншоты участников?",
            reply_markup={"inline_keyboard": keyboard}
        )
        
        logger.info("Данные успешно отправлены в Telegram")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке данных в Telegram: {e}")
        return False

async def main():
    logger.info("Скрипт запущен: скачивание и отправка данных")
    
    # Проверяем соединение с Telegram
    logger.info("Проверка соединения с Telegram...")
    try:
        bot = Bot(token=TOKEN)
        me = await bot.get_me()
        logger.info(f"Соединение с Telegram успешно установлено. Бот: {me.username}")
    except Exception as e:
        logger.error(f"Ошибка соединения с Telegram: {e}")
        logger.error(traceback.format_exc())
        return
    
    # Создаем временную директорию для файлов
    ensure_dir_exists(LOCAL_TEMP_DIR)
    
    # Скачиваем файлы с сервера
    if not download_from_server():
        logger.error("Ошибка при скачивании файлов. Прерывание скрипта.")
        return
    
    # Экспортируем данные из базы в CSV
    participants_in_raffle = export_data_from_db()
    
    # Объединяем данные
    users = merge_data(participants_in_raffle)
    
    # Отправляем в Telegram
    await send_to_telegram(users)
    
    logger.info("Скрипт завершил работу")

if __name__ == "__main__":
    asyncio.run(main()) 