import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv
from yandex_disk import YandexDiskClient

# Загружаем переменные окружения (если есть .env файл)
load_dotenv()

# Пытаемся импортировать config (для локальной разработки, опционально)
try:
    import config
    HAS_CONFIG = True
except ImportError:
    HAS_CONFIG = False
    config = None

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Инициализация клиента Яндекс Диска
yandex_disk_token = os.getenv('YANDEX_DISK_TOKEN')
yandex_disk_folder = os.getenv('YANDEX_DISK_FOLDER', '/wisdom_card')

# Fallback на config только для локальной разработки
if not yandex_disk_token and HAS_CONFIG:
    yandex_disk_token = getattr(config, 'YANDEX_DISK_TOKEN', None)
if yandex_disk_folder == '/wisdom_card' and HAS_CONFIG:
    yandex_disk_folder = getattr(config, 'YANDEX_DISK_FOLDER', '/wisdom_card')

yandex_disk = YandexDiskClient(
    token=yandex_disk_token,
    folder_path=yandex_disk_folder
)


def get_welcome_message():
    """Формирует приветственное сообщение"""
    welcome_text = """✨ Здравствуйте!

Иногда одна вовремя услышанная фраза может изменить очень многое.

Я здесь, чтобы давать вам такие подсказки. Нажимайте «Получить подсказку» — и вашей личной мудростью на сегодня станет случайно выбранная цитата.

📚 Как это работает?
Это не гадалка! Психологическая польза основана на научных данных о работе нашего мозга. Неожиданная глубокая мысль прерывает мыслительный «автопилот» и:
• Останавливает автоматизм, заставляя сфокусироваться на моменте
• Активирует ассоциативную память, связывая ваш опыт с мудростью веков
• Работает как проективный тест: мы находим в цитате именно то, что актуально для нас сейчас

💬 Присоединяйтесь к нашему сообществу «Психосоматика Души» в ВКонтакте, где мы делимся мудростью и размышляем о жизни:
👉 https://vk.com/club220155225

Нажмите кнопку, чтобы получить подсказку! Вы можете использовать цитату как подсказку дня или сформулировать в уме волнующий вопрос перед нажатием."""
    return welcome_text


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [
        [InlineKeyboardButton("Получить подсказку", callback_data='get_hint')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = get_welcome_message()
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        disable_web_page_preview=False
    )


async def send_sleep_message(query):
    """Отправляет сообщение о том, что бот отдыхает"""
    sleep_image_path = os.path.join(os.path.dirname(__file__), 'images', 'sleep-cat.png')
    sleep_text = "Извините, бот пока отдыхает, ведь здоровый сон очень важен для психологического здоровья. 🌙"
    
    # Кнопки для действий
    keyboard = [
        [InlineKeyboardButton("Получить новую подсказку", callback_data='get_hint')],
        [InlineKeyboardButton("🏠 Вернуться к началу", callback_data='back_to_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        # Проверяем, существует ли файл с картинкой
        if os.path.exists(sleep_image_path):
            # Отправляем картинку с текстом (передаем путь к файлу)
            await query.message.reply_photo(
                photo=sleep_image_path,
                caption=sleep_text,
                reply_markup=reply_markup
            )
            logger.info("Отправлено сообщение о сне с картинкой")
        else:
            # Если файл не найден, отправляем только текст
            logger.warning(f"Файл {sleep_image_path} не найден, отправляем только текст")
            await query.message.reply_text(sleep_text, reply_markup=reply_markup)
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения о сне: {e}")
        # В крайнем случае отправляем только текст
        try:
            await query.message.reply_text(sleep_text, reply_markup=reply_markup)
        except Exception as e2:
            logger.error(f"Критическая ошибка при отправке сообщения: {e2}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'get_hint':
        try:
            # Получаем случайную картинку
            image_url = yandex_disk.get_random_image()
            
            # Кнопки для действий после получения картинки
            keyboard = [
                [InlineKeyboardButton("Получить новую подсказку", callback_data='get_hint')],
                [InlineKeyboardButton("🏠 Вернуться к началу", callback_data='back_to_start')]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if image_url:
                try:
                    # Отправляем картинку пользователю с кнопками
                    await query.message.reply_photo(photo=image_url, reply_markup=reply_markup)
                    logger.info(f"Отправлена картинка: {image_url}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке картинки из Яндекс Диска: {e}")
                    # Если не удалось отправить картинку, отправляем сообщение о сне
                    await send_sleep_message(query)
            else:
                # Если картинка не получена, отправляем сообщение о сне
                logger.warning("Не удалось получить картинку из Яндекс Диска")
                await send_sleep_message(query)
        except Exception as e:
            logger.error(f"Ошибка при получении картинки: {e}")
            # При любой ошибке отправляем сообщение о сне
            await send_sleep_message(query)
    
    elif query.data == 'back_to_start':
        # Возврат к приветственному сообщению
        welcome_text = get_welcome_message()
        keyboard = [
            [InlineKeyboardButton("Получить подсказку", callback_data='get_hint')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )


def main():
    """Основная функция запуска бота"""
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Fallback на config только для локальной разработки
    if not bot_token and HAS_CONFIG:
        bot_token = getattr(config, 'TELEGRAM_BOT_TOKEN', None)
    
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен! Проверьте переменные окружения на Bothost или config.py для локальной разработки")
    
    # Создаем приложение
    application = Application.builder().token(bot_token).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Запускаем бота
    logger.info("Бот запущен...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

