#!/usr/bin/env python3
import sqlite3
import csv
import os
import asyncio
from datetime import datetime
from telegram import Bot

# Токен бота (такой же, как в bot.py)
TOKEN = "7738250304:AAFFsDvI5dy_pbwHDPYdnd2Nk73gRNv6EMs"

def export_participants():
    """Экспортирует список участников розыгрыша в CSV-файл"""
    # Имя файла включает текущую дату и время
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"participants_{current_time}.csv"
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Получаем данные участников с информацией из таблицы users
    cursor.execute('''
        SELECT p.user_id, u.username, p.timestamp
        FROM participants p
        LEFT JOIN users u ON p.user_id = u.user_id
        ORDER BY p.timestamp
    ''')
    
    participants = cursor.fetchall()
    
    # Записываем данные в CSV-файл
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Заголовки
        csvwriter.writerow(['ID пользователя', 'Имя пользователя', 'Дата регистрации'])
        # Данные
        for participant in participants:
            csvwriter.writerow(participant)
    
    conn.close()
    
    print(f"Экспорт завершен. Список участников сохранен в файл: {filename}")
    print(f"Всего участников: {len(participants)}")
    
    return filename, len(participants)

def export_screenshots():
    """Экспортирует информацию о скриншотах в CSV-файл"""
    # Имя файла включает текущую дату и время
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"screenshots_{current_time}.csv"
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Получаем данные о скриншотах с информацией о пользователях
    cursor.execute('''
        SELECT s.id, s.user_id, u.username, s.file_id, s.verified
        FROM screenshots s
        LEFT JOIN users u ON s.user_id = u.user_id
        ORDER BY s.id
    ''')
    
    screenshots = cursor.fetchall()
    
    # Записываем данные в CSV-файл
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        # Заголовки
        csvwriter.writerow(['ID скриншота', 'ID пользователя', 'Имя пользователя', 'File ID', 'Проверен'])
        # Данные
        for screenshot in screenshots:
            csvwriter.writerow(screenshot)
    
    conn.close()
    
    print(f"Экспорт завершен. Информация о скриншотах сохранена в файл: {filename}")
    print(f"Всего скриншотов: {len(screenshots)}")
    
    return filename, len(screenshots)

async def download_all_screenshots():
    """Загружает все скриншоты из Telegram и сохраняет их локально"""
    # Создаем директорию для скриншотов, если её нет
    screenshots_dir = "downloaded_screenshots"
    os.makedirs(screenshots_dir, exist_ok=True)
    
    # Подключаемся к базе данных
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # Получаем все file_id скриншотов
    cursor.execute('SELECT id, user_id, file_id FROM screenshots')
    screenshots = cursor.fetchall()
    
    print(f"Начинаем загрузку {len(screenshots)} скриншотов...")
    
    # Создаем экземпляр бота
    bot = Bot(token=TOKEN)
    
    # Загружаем каждый скриншот
    downloaded_count = 0
    for screenshot_id, user_id, file_id in screenshots:
        filename = f"{screenshots_dir}/screenshot_{screenshot_id}_user_{user_id}.jpg"
        try:
            # Получаем информацию о файле
            file = await bot.get_file(file_id)
            # Загружаем файл
            await file.download_to_drive(filename)
            downloaded_count += 1
            print(f"Загружен скриншот {screenshot_id} от пользователя {user_id}")
        except Exception as e:
            print(f"Ошибка при загрузке скриншота {screenshot_id}: {e}")
    
    conn.close()
    await bot.close()
    
    print(f"Загрузка завершена. Загружено {downloaded_count} из {len(screenshots)} скриншотов.")
    print(f"Скриншоты сохранены в директории: {screenshots_dir}")
    
    return screenshots_dir, downloaded_count

if __name__ == "__main__":
    print("Выберите действие:")
    print("1. Экспорт списка участников")
    print("2. Экспорт информации о скриншотах")
    print("3. Экспорт всех данных")
    print("4. Загрузка скриншотов из Telegram")
    
    choice = input("Введите номер действия (1-4): ")
    
    if choice == "1":
        export_participants()
    elif choice == "2":
        export_screenshots()
    elif choice == "3":
        export_participants()
        export_screenshots()
    elif choice == "4":
        # Запускаем асинхронную функцию загрузки скриншотов
        asyncio.run(download_all_screenshots())
    else:
        print("Неверный выбор. Пожалуйста, введите число от 1 до 4.") 