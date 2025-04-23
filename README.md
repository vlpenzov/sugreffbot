# Sugrefftea Bot

Telegram-бот для проведения розыгрыша среди подписчиков канала.

## Функциональность

- Сбор скриншотов с отзывами от пользователей
- Проверка подписки на канал
- Регистрация участников для розыгрыша
- Отправка сообщений в канал

## Требования

- Python 3.8+
- python-telegram-bot 22.0+
- pytz

## Установка

1. Клонировать репозиторий:
```
git clone https://github.com/yourusername/SugreffBot.git
cd SugreffBot
```

2. Установить зависимости:
```
pip install -r requirements.txt
```

3. Настроить токен бота и другие параметры в файле `bot.py`

4. Запустить бота:
```
python bot.py
```

## Настройка автозапуска через systemd (Linux)

1. Скопируйте файл systemd сервиса:
```
sudo cp sugrefftea-bot.service /etc/systemd/system/
```

2. Перезагрузите конфигурацию systemd:
```
sudo systemctl daemon-reload
```

3. Включите автозапуск:
```
sudo systemctl enable sugrefftea-bot
```

4. Запустите сервис:
```
sudo systemctl start sugrefftea-bot
```

5. Проверьте статус:
```
sudo systemctl status sugrefftea-bot
```

## Структура проекта

- `bot.py` - основной файл с кодом бота
- `bot.db` - SQLite база данных для хранения информации
- `requirements.txt` - зависимости проекта
- `start.sh`, `stop.sh` - скрипты для управления ботом
- `sugrefftea-bot.service` - файл конфигурации systemd
- `README.md` - документация

## Лицензия

MIT 