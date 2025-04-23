import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes
)

# ===== CONFIG =====
TOKEN = "7738250304:AAFFsDvI5dy_pbwHDPYdnd2Nk73gRNv6EMs"  # Замените на токен от BotFather
CHANNEL_NAME = "@Sugrefftea"  # Ваш канал
ADMIN_ID = 7971829199  # Ваш ID для админ-уведомлений
# ===================

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация БД (синхронная - требует доработки для async)
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        subscribed BOOLEAN DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS screenshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        file_id TEXT,
        verified BOOLEAN DEFAULT 0
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS participants (
        user_id INTEGER PRIMARY KEY,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

# ===== ТЕКСТЫ =====
TEXTS = {
    "start": (
        "🌟 *Добро пожаловать!* 🌟\n\n"
        "Хочешь выиграть крутые призы? Просто выполни 3 шага:\n"
        "1️⃣ Оставь отзыв о товаре на Wildberries\n"
        "2️⃣ Отправь скриншот отюда\n"
        "3️⃣ Подпишись на наш канал {channel} и нажми «Участвовать» в закрепленном посте\n\n"
        "*Призы разыгрываются каждый месяц!* 🎁"
    ),
    "photo_received": (
        "✅ *Скриншот получен!*\n\n"
        "Теперь:\n"
        "1. Подпишись на канал {channel}\n"
        "2. Нажми кнопку «Участвовать» в закрепленном посте\n\n"
        "Проверка займет до 24 часов. Удачи! 🍀"
    ),
    "not_subscribed": (
        "🔔 *Подпишись на канал!*\n\n"
        "Чтобы участвовать, нужно присоединиться к {channel}\n\n"
        "После подписки нажми кнопку ниже 👇"
    ),
    "check_subscription": "🔄 Я подписался",
    "participate_success": (
        "✨ *Ты в игре!*\n\n"
        "Победитель будет объявлен в этом канале. Удачи! 🎉"
    ),
    "participate_error": (
        "🚫 *Не все условия выполнены!*\n\n"
        "Нужно:\n"
        "1. Отправить скриншот отзыва\n"
        "2. Быть подписанным на канал {channel}"
    )
}

# ===== КНОПКИ =====
def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(TEXTS["check_subscription"], callback_data="check_subscription")]
    ])

# ===== ОСНОВНЫЕ ФУНКЦИИ =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                  (user.id, user.username))
    conn.commit()
    
    text = TEXTS["start"].format(channel=CHANNEL_NAME)
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    photo_id = update.message.photo[-1].file_id
    
    # Сохраняем скриншот
    cursor.execute('INSERT INTO screenshots (user_id, file_id) VALUES (?, ?)',
                  (user.id, photo_id))
    conn.commit()
    
    # Отправляем ответ
    text = TEXTS["photo_received"].format(channel=CHANNEL_NAME)
    await update.message.reply_text(text, 
                                   parse_mode="Markdown",
                                   reply_markup=main_keyboard())

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    try:
        member = await context.bot.get_chat_member(CHANNEL_NAME, user.id)
        if member.status in ["member", "administrator"]:
            cursor.execute('UPDATE users SET subscribed = 1 WHERE user_id = ?', (user.id,))
            conn.commit()
            await query.answer("✅ Подписка подтверждена!")
            await query.edit_message_text(TEXTS["participate_success"], parse_mode="Markdown")
        else:
            await query.answer("❌ Вы всё ещё не подписаны!")
    except Exception as e:
        await query.answer("⚠️ Ошибка проверки подписки")

async def participate_button(context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎯 Участвовать", callback_data="participate")]
    ])
    await context.bot.send_message(
        chat_id=CHANNEL_NAME,
        text="🎁 *Розыгрыш призов!* Нажми кнопку ниже, чтобы участвовать:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

async def handle_participate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user = query.from_user
    
    # Проверяем условия
    cursor.execute('SELECT subscribed FROM users WHERE user_id = ?', (user.id,))
    subscribed = cursor.fetchone()
    
    cursor.execute('SELECT id FROM screenshots WHERE user_id = ?', (user.id,))
    has_screenshot = cursor.fetchone()
    
    if subscribed and subscribed[0] and has_screenshot:
        cursor.execute('INSERT OR IGNORE INTO participants (user_id) VALUES (?)', (user.id,))
        conn.commit()
        await query.answer("✅ Вы участвуете в розыгрыше!")
        await query.edit_message_text(TEXTS["participate_success"], parse_mode="Markdown")
    else:
        await query.answer("❌ Сначала выполните все условия!")
        await query.edit_message_text(
            TEXTS["participate_error"].format(channel=CHANNEL_NAME),
            parse_mode="Markdown"
        )

# ===== ЗАПУСК =====
if __name__ == '__main__':
    application = Application.builder().token(TOKEN).build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(check_subscription, pattern="check_subscription"))
    application.add_handler(CallbackQueryHandler(handle_participate, pattern="participate"))

    # Создаем кнопку участия в канале
    application.job_queue.run_once(participate_button, when=5)

    # Запуск бота
    application.run_polling()
