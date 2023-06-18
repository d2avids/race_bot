import os
import sys
import telegram
from telegram.ext import Updater, CommandHandler
from dotenv import load_dotenv

# TODO: Заменить print на логирование
# TODO: Добавить обработку ошибок

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TG_BOT_TOKEN')


def check_tokens():
    """Проверка наличия токенов."""
    if not TELEGRAM_TOKEN:
        return False
    return True


def reply(update, message, keyboard=None):
    """Reply to the user or log the error."""
    try:
        update.message.reply_text(
            text=message,
            reply_markup=keyboard,
            parse_mode='HTML',
        )
    except telegram.error.TelegramError as e:
        print(e)


def start(update, context):
    """Send a message when the command /start is issued."""
    reply(update, 'Hi!')


def main():
    """Основная логика работы бота."""
    try:
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
    except:
        print('Ошибка авторизации. Проверь токен.')

    dp = updater.dispatcher
    start_handler = CommandHandler('start', start)

    try:
        updater.start_polling()
        print('Бот запущен.')
        updater.idle()
    except telegram.error.TelegramError as e:
        print(e)

print(TELEGRAM_TOKEN)
print(check_tokens())

if __name__ == '__main__':
    if not check_tokens():
        print('Ошибка авторизации. Проверьте токен.')
        sys.exit(1)
    main()
