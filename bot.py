import logging
import sqlite3
import asyncio
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ===== КОНФИГУРАЦИЯ =====
TOKEN = "7738250304:AAFFsDvI5dy_pbwHDPYdnd2Nk73gRNv6EMs"  # Токен бота
CHANNEL_NAME = "@Sugrefftea"  # Название канала
CHANNEL_LINK = "https://t.me/Sugrefftea"  # Ссылка на канал для отображения
BOT_USERNAME = "@SugreffTeaBot"  # Имя бота для упоминания в сообщениях
ADMIN_ID = 7971829199  # ID администратора
ADMIN_USERNAME = "tg://user?id=7971829199"  # Ссылка на администратора для контакта
# =======================

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Подключение и инициализация базы данных
conn = sqlite3.connect('bot.db', check_same_thread=False)
cursor = conn.cursor()

# Создание таблиц, если их нет
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
        "🌟 *Привет! Добро пожаловать в розыгрыш призов!* 🌟\n\n"
        "*Как выиграть крутые призы от Сугревъ:*\n"
        "1️⃣ *Оставь отзыв* на товар Сугревъ на Маркетплейсе и *отправь скриншот* отзыва в этот чат\n"
        "   _(загрузи изображение отзыва)_ ⬇️\n\n"
        f"❓ *Вопросы?* Пиши [администратору]({ADMIN_USERNAME})\n"
        "🎁 *Розыгрыш проводится ежемесячно!*"
    ),
    "photo_received": (
        "✅ *Отлично! Твой скриншот успешно получен!*\n\n"
        "Осталось совсем немного:\n"
        "1. *Подпишись* на [наш канал]({channel_link})\n"
        "2. *Нажми* кнопку «Я подписался» ниже\n"
        "3. После подтверждения ты сможешь *участвовать* в розыгрыше\n\n"
        "Мы проверим твой отзыв в течение 24 часов. Удачи! 🍀"
    ),
    "not_subscribed": (
        "🔔 *Подпишись на наш канал!*\n\n"
        "Для участия в розыгрыше необходимо:\n"
        "1. *Перейти* на [наш канал]({channel_link})\n"
        "2. *Нажать* на кнопку «Подписаться»\n"
        "3. *Вернуться* сюда и нажать кнопку «Я подписался»\n\n"
        "Там ты найдешь много полезной информации и анонсы будущих розыгрышей! 📱"
    ),
    "check_subscription": "🔄 Я подписался",
    "participate_success": (
        "🎉 *Поздравляем! Ты в игре!* 🎉\n\n"
        "Твоя заявка на участие принята!\n\n"
        "• Розыгрыш проводится *ежемесячно*\n"
        "• Результаты будут объявлены в [нашем канале]({channel_link})\n"
        "• Мы свяжемся с победителями лично\n\n"
        "Спасибо за участие и удачи! 🍀"
    ),
    "participate_error": (
        "⚠️ *Упс! Не все условия выполнены*\n\n"
        "Для участия в розыгрыше необходимо:\n"
        "1. ✅ Отправить скриншот отзыва\n"
        "2. ✅ Подписаться на [наш канал]({channel_link})\n\n"
        "Пожалуйста, выполни все условия и попробуй снова! 🙏"
    ),
    "subscription_error": (
        "⚠️ *Возникла проблема при проверке подписки*\n\n"
        "Пожалуйста, убедись что:\n"
        "• Ты подписался на [наш канал]({channel_link})\n"
        "• Не отключал уведомления от бота\n\n"
        f"Попробуй еще раз через несколько минут или напиши [администратору]({ADMIN_USERNAME}) для помощи."
    ),
    "already_participating": (
        "✨ *Ты уже участвуешь в розыгрыше!* ✨\n\n"
        "Твоя заявка уже принята, больше ничего делать не нужно.\n"
        "Результаты будут объявлены в [нашем канале]({channel_link}).\n\n"
        "Желаем удачи! 🍀"
    ),
    "channel_announcement": (
        "🎁 *ВНИМАНИЕ! РОЗЫГРЫШ ПРИЗОВ!* 🎁\n\n"
        "Разыгрываем подарки от Сугревъ!\n\n"
        "Для участия:\n"
        "1. Оставьте отзыв на продукцию Сугревъ на Маркетплейсе\n"
        f"2. Напишите нашему боту {BOT_USERNAME}\n"
        "3. Нажмите кнопку «Участвовать» ниже\n\n"
        "Розыгрыш проводится ежемесячно!"
    )
}

# ===== КЛАВИАТУРЫ =====
def get_subscription_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text="📢 Перейти на канал", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text=TEXTS["check_subscription"], callback_data="check_subscription")]
    ])

def get_participate_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(text="🎯 Участвовать", callback_data="participate")]
    ])

# ===== КОМАНДЫ И ОБРАБОТЧИКИ =====
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Сохраняем информацию о пользователе
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                  (user.id, user.username))
    conn.commit()
    
    # Отправляем приветственное сообщение
    await update.message.reply_text(
        TEXTS["start"].format(channel_link=CHANNEL_LINK),
        parse_mode="Markdown"
    )
    logger.info(f"Пользователь {user.id} запустил бота")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик фотографий от пользователя"""
    user = update.effective_user
    
    # Получаем файл с наилучшим разрешением
    photo = update.message.photo[-1]
    file_id = photo.file_id
    
    # Сохраняем информацию о скриншоте
    cursor.execute('INSERT INTO screenshots (user_id, file_id) VALUES (?, ?)',
                  (user.id, file_id))
    conn.commit()
    
    # Отвечаем пользователю
    await update.message.reply_text(
        TEXTS["photo_received"].format(channel_link=CHANNEL_LINK),
        parse_mode="Markdown",
        reply_markup=get_subscription_keyboard()
    )
    logger.info(f"Пользователь {user.id} отправил скриншот")

async def button_check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки проверки подписки"""
    query = update.callback_query
    await query.answer()  # Отвечаем на callback запрос
    
    user = query.from_user
    logger.info(f"Пользователь {user.id} нажал на кнопку проверки подписки")
    
    try:
        # Проверяем, подписан ли пользователь на канал
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_NAME, user_id=user.id)
        logger.info(f"Статус подписки пользователя {user.id}: {chat_member.status}")
        
        if chat_member.status in ['member', 'administrator', 'creator']:
            # Пользователь подписан
            cursor.execute('UPDATE users SET subscribed = 1 WHERE user_id = ?', (user.id,))
            conn.commit()
            logger.info(f"Пользователь {user.id} подтвердил подписку. Статус обновлен в БД.")
            
            # Отправляем новое сообщение вместо редактирования существующего
            await query.message.reply_text(
                text=TEXTS["participate_success"].format(channel_link=CHANNEL_LINK),
                parse_mode="Markdown"
            )
            # Удаляем клавиатуру из исходного сообщения, если возможно
            try:
                await query.edit_message_reply_markup(reply_markup=None)
            except Exception:
                pass
        else:
            # Пользователь не подписан
            logger.info(f"Пользователь {user.id} не подписан на канал. Статус: {chat_member.status}")
            await query.message.reply_text(
                text=TEXTS["not_subscribed"].format(channel_link=CHANNEL_LINK),
                parse_mode="Markdown",
                reply_markup=get_subscription_keyboard()
            )
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки для пользователя {user.id}: {e}", exc_info=True)
        await query.message.reply_text(
            text=TEXTS["subscription_error"].format(channel_link=CHANNEL_LINK),
            parse_mode="Markdown",
            reply_markup=get_subscription_keyboard()
        )

async def button_participate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопки участия в розыгрыше"""
    query = update.callback_query
    await query.answer()  # Отвечаем на callback запрос
    
    user = query.from_user
    logger.info(f"Пользователь {user.id} нажал на кнопку участия в розыгрыше")
    
    # Проверяем, выполнил ли пользователь все условия
    cursor.execute('SELECT subscribed FROM users WHERE user_id = ?', (user.id,))
    sub_result = cursor.fetchone()
    
    # Если пользователя нет в базе, добавляем его
    if not sub_result:
        cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', 
                      (user.id, user.username))
        conn.commit()
        subscribed = False
    else:
        subscribed = sub_result[0] == 1
    
    cursor.execute('SELECT id FROM screenshots WHERE user_id = ?', (user.id,))
    has_screenshot = cursor.fetchone() is not None
    
    # Проверяем, уже участвует ли пользователь
    cursor.execute('SELECT user_id FROM participants WHERE user_id = ?', (user.id,))
    already_participating = cursor.fetchone() is not None
    
    logger.info(f"Статус пользователя {user.id}: подписан = {subscribed}, скриншот = {has_screenshot}, уже участвует = {already_participating}")
    
    if already_participating:
        # Пользователь уже участвует
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=TEXTS["already_participating"].format(channel_link=CHANNEL_LINK),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user.id}: {e}")
            # Показываем всплывающее окно, если личное сообщение не отправляется
            await query.answer("✨ Вы уже участвуете в розыгрыше!", show_alert=True)
    elif subscribed and has_screenshot:
        # Все условия выполнены
        cursor.execute('INSERT OR IGNORE INTO participants (user_id) VALUES (?)', (user.id,))
        conn.commit()
        logger.info(f"Пользователь {user.id} успешно добавлен в участники розыгрыша")
        
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=TEXTS["participate_success"].format(channel_link=CHANNEL_LINK),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user.id}: {e}")
            # Показываем всплывающее окно, если личное сообщение не отправляется
            await query.answer("✅ Поздравляем! Вы участвуете в розыгрыше!", show_alert=True)
    else:
        # Не все условия выполнены
        missing_items = []
        if not subscribed:
            missing_items.append("подписка на канал")
        if not has_screenshot:
            missing_items.append("скриншот отзыва")
        
        missing_text = ", ".join(missing_items)
        logger.info(f"Пользователь {user.id} не выполнил условия: {missing_text}")
        
        try:
            # Сначала пробуем отправить личное сообщение
            await context.bot.send_message(
                chat_id=user.id,
                text=TEXTS["participate_error"].format(channel_link=CHANNEL_LINK),
                parse_mode="Markdown",
                reply_markup=get_subscription_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения пользователю {user.id}: {e}")
            # Если не получается отправить личное сообщение, показываем всплывающее окно
            await query.answer(
                f"⚠️ Не все условия выполнены! Отсутствует: {missing_text}. Напишите боту напрямую.",
                show_alert=True
            )

async def send_channel_message(bot):
    """Отправка сообщения с кнопкой участия в канал"""
    try:
        message = await bot.send_message(
            chat_id=CHANNEL_NAME,
            text=TEXTS["channel_announcement"],
            parse_mode="Markdown",
            reply_markup=get_participate_keyboard()
        )
        logger.info(f"Сообщение с кнопкой участия отправлено в канал {CHANNEL_NAME}, message_id: {message.message_id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения в канал {CHANNEL_NAME}: {e}", exc_info=True)
        return False

async def post_init(application: Application) -> None:
    """Функция, которая запускается после инициализации приложения"""
    logger.info("Бот запущен и инициализирован")
    
    # Добавляем небольшую задержку перед отправкой сообщения в канал
    await asyncio.sleep(5)  # Даем боту время на подключение
    
    # Пробуем отправить сообщение в канал
    success = await send_channel_message(application.bot)
    
    if success:
        logger.info("Сообщение успешно отправлено в канал")
    else:
        logger.warning("Не удалось отправить сообщение в канал. Возможно, у бота нет прав администратора в канале?")
        
    logger.info("Инициализация бота завершена")

def main() -> None:
    """Запуск бота"""
    # Создаем приложение
    application = (
        Application.builder()
        .token(TOKEN)
        .post_init(post_init)
        .build()
    )
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", cmd_start))
    application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    application.add_handler(CallbackQueryHandler(button_check_subscription, pattern="check_subscription"))
    application.add_handler(CallbackQueryHandler(button_participate, pattern="participate"))
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)
    
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        # Закрываем соединение с БД при завершении работы
        conn.close()
        logger.info("Бот остановлен. Соединение с БД закрыто.")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        conn.close()
