#!/usr/bin/env python3
import sqlite3
import csv
import os
from datetime import datetime

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

if __name__ == "__main__":
    print("Выберите действие:")
    print("1. Экспорт списка участников")
    print("2. Экспорт информации о скриншотах")
    print("3. Экспорт всех данных")
    
    choice = input("Введите номер действия (1-3): ")
    
    if choice == "1":
        export_participants()
    elif choice == "2":
        export_screenshots()
    elif choice == "3":
        export_participants()
        export_screenshots()
    else:
        print("Неверный выбор. Пожалуйста, введите число от 1 до 3.") 