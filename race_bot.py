import os
import sqlite3
import sys

import telegram
from dotenv import load_dotenv
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TG_BOT_TOKEN')

NOT_REGISTERED = (
    'Это может сделать только зарегистрированный пользователь.\n'
    'Зарегистрируйтесь при помощи /register'
)
NOT_ADMIN = 'Только админ может выполнить это действие.'
NOT_DATABASE = 'Ошибка при работе с базой данных: {error}'

ADD_PARTICIPANT = 1
REGISTER_MESSAGE = 'Привет! Для регистрации на гонку укажи свои ФИО.'
REGISTER_POSITION_MESSAGE = (
    'Вы зарегистрированы на участие в гонке. '
    'Порядковый номер участника гонки: {number}\n'
    'Для прохождения контрольных точек выполните команду '
    '/next и следуйте инструкциям.'
)

ADMIN_PASS_KEY = 1
ADMIN_KEY = os.getenv('ADMIN_KEY')
ADMIN_MESSAGE = (
    'Для того, чтобы получить права на добавление, редактирование и '
    'удаление гонок, введи секретный ключ.'
)
ADMIN_VALID_KEY_MESSAGE = 'Права доступа предоставлены.'
ADMIN_INVALID_KEY_MESSAGE = 'Неверный ключ доступа.'

ADD_COORDINATES, ADD_TASK = range(2)
POINT_MESSAGE = 'Введите координаты точки'
COORDINATES_MESSAGE = (
    'Координаты добавлены.\n'
    'Укажите текст задания, необходимого к выполнению по достижении '
    'указанных координат.'
)

DEL_ALL_POINTS, DEL_SPECIFIC_POINT = range(2)
DEL_SUCCESS = 'Удалено записей: {rows_count}. Таблица изменена.'
DEL_POINTS_MESSAGE = 'Удаляем все (отправь "все") или некоторые ("некоторые")?'


def check_tokens():
    """Проверка наличия токенов."""
    if not TELEGRAM_TOKEN:
        return False
    return True


def db_table_val(user_id, username, name):
    try:
        cursor.execute(
            '''INSERT INTO main.participants (user_id, username, name) '''
            '''VALUES (?, ?, ?)''',
            (user_id, username, name))
        conn.commit()
        cursor.execute(
            '''SELECT id FROM main.participants '''
            '''WHERE user_id = ?''',
            (user_id,)
        )
        number = cursor.fetchone()
    except sqlite3.IntegrityError as e:
        cursor.execute(
            '''SELECT id FROM main.participants '''
            '''WHERE user_id = ?''',
            (user_id,)
        )
        print('юзер уже зареган')
        number = cursor.fetchone()
    except sqlite3.Error as e:
        raise sqlite3.Error(NOT_DATABASE.format(error=e))

    return number[0]


def is_admin(user_id):
    flag = False
    try:
        cursor.execute(
            '''SELECT is_admin FROM main.participants '''
            '''WHERE user_id = ?''',
            (user_id,)
        )
        result = cursor.fetchone()
    except sqlite3.Error as e:
        raise sqlite3.Error(NOT_DATABASE.format(error=e))
    if result is None:
        return flag
    return result[0]


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


def admin(update, context):
    reply(update, ADMIN_MESSAGE)
    return ADMIN_PASS_KEY


def admin_key_verification(update, context):
    print(update.message.text)
    print(ADMIN_KEY)
    if update.message.text == ADMIN_KEY:
        try:
            cursor.execute(
                '''UPDATE main.participants '''
                '''SET is_admin = 1 '''
                '''WHERE user_id = ?''',
                (update.message.from_user['id'],)
            )
            conn.commit()
        except sqlite3.Error as e:
            reply(update, NOT_DATABASE.format(error=e))
            return ConversationHandler.END

        reply(update, ADMIN_VALID_KEY_MESSAGE)
        return ConversationHandler.END

    reply(update, ADMIN_INVALID_KEY_MESSAGE)
    return ConversationHandler.END


def add_point(update, context):
    user_id = update.message.from_user['id']
    print(is_admin(user_id))
    if is_admin(user_id) is False:
        reply(update, NOT_REGISTERED)
        return ConversationHandler.END
    elif not is_admin(user_id):
        reply(update, NOT_ADMIN)
        return ConversationHandler.END

    reply(update, POINT_MESSAGE)
    return ADD_COORDINATES


def add_coordinates(update, context):
    coordinates = update.message.text
    try:
        cursor.execute(
            '''INSERT INTO main.control_points (coordinates)'''
            '''VALUES (?)''',
            (coordinates,)
        )
        conn.commit()
        reply(update, COORDINATES_MESSAGE)
        return ADD_TASK
    except sqlite3.Error as e:
        reply(update, NOT_DATABASE.format(error=e))
        return ConversationHandler.END


def add_task(update, context):
    task = update.message.text
    try:
        cursor.execute(
            '''UPDATE main.control_points '''
            '''SET task = ? '''
            '''WHERE id = last_insert_rowid()''',
            (task,)
        )
        conn.commit()
        reply(update, 'Задание добавлено')
    except sqlite3.Error as e:
        reply(update, sqlite3.Error(NOT_DATABASE.format(error=e)))

    return ConversationHandler.END


def stop(update, context):
    return ConversationHandler.END


def start(update, context):
    """Send a message when the command /start is issued."""
    reply(update, update.message.location)


def points(update, context):
    cursor.execute(
        '''SELECT * from main.control_points'''
    )
    records = cursor.fetchall()
    reply_message = (
        'Список контрольных точек:\n\n'
    )
    for row in records:
        reply_message += f'ID: <code>{row[0]}</code> | '
        reply_message += f'Coordinates: <code>{row[1]}</code> | '
        reply_message += f'Task: <code>{row[2]}</code>\n\n'
    reply(update, reply_message)


def participants(update, context):
    cursor.execute(
        '''SELECT * from main.participants'''
    )
    records = cursor.fetchall()
    reply_message = (
        'Список участников:\n\n'
    )
    for row in records:
        reply_message += f'ID: <code>{row[0]}</code> | '
        reply_message += f'User_id: {row[1]} | '
        reply_message += f'Username: @{row[2]} | '
        reply_message += f'Name: {row[3]} | '
        reply_message += f'Is_admin {row[4]}\n\n'

    reply(update, reply_message)


def del_points(update, context):
    user_id = update.message.from_user['id']
    if not is_admin(user_id):
        reply(update, NOT_ADMIN)
        return ConversationHandler.END
    reply(update, DEL_POINTS_MESSAGE)
    return 1


def del_points_all_or_specific(update, context):
    answer = update.message.text.lower()
    if answer in ('dct', 'все', 'all', 'clear'):
        try:
            cursor.execute(
                '''DELETE from main.control_points'''
            )
            conn.commit()
            reply(update, DEL_SUCCESS.format(rows_count=cursor.rowcount))
            return ConversationHandler.END
        except sqlite3.Error as e:
            reply(update, NOT_DATABASE.format(error=e))
            return ConversationHandler.END
    else:
        try:
            cursor.execute(
                '''SELECT * from main.control_points'''
            )
            records = cursor.fetchall()
            reply_message = (
                'Перечислите через запятую ID тех точек, '
                'которые необходимо удалить:\n\n'
            )
            for row in records:
                reply_message += f'ID: <code>{row[0]}</code> | '
                reply_message += f'Coordinates: {row[1]} | '
                reply_message += f'Task: {row[2]}\n\n'
            reply(update, reply_message)
            return 2
        except sqlite3.Error as e:
            reply(update, NOT_DATABASE.format(error=e))
            return ConversationHandler.END


def del_specific_points(update, context):
    ids = update.message.text.split(',')
    try:
        cursor.execute(
            '''DELETE FROM main.control_points '''
            '''WHERE id IN ({})'''.format(','.join('?' * len(ids))),
            tuple(ids)
        )
        conn.commit()
        reply(update, DEL_SUCCESS.format(rows_count=cursor.rowcount))
        return ConversationHandler.END
    except sqlite3.Error as e:
        reply(update, NOT_DATABASE.format(error=e))
        return ConversationHandler.END


def del_participants(update, context):
    user_id = update.message.from_user['id']
    if not is_admin(user_id):
        reply(update, NOT_ADMIN)
        return
    try:
        cursor.execute(
            '''DELETE from main.participants '''
            '''WHERE is_admin = 0'''
        )
        conn.commit()
        reply(update, DEL_SUCCESS.format(rows_count=cursor.rowcount))
    except sqlite3.Error as e:
        reply(update, NOT_DATABASE.format(error=e))


def register(update, context):
    reply(update, REGISTER_MESSAGE)
    print('исполняется register')
    return ADD_PARTICIPANT


def register_add_participant(update, context):
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']
    name = update.message.text
    number = db_table_val(user_id=user_id, username=username, name=name)
    reply(update, REGISTER_POSITION_MESSAGE.format(number=number))
    return ConversationHandler.END


def next_add_location(update, context):
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']
    bot.send_message(
        chat_id=601334258,
        text=f'Локация участника {user_id}, {username}'
    )
    bot.forward_message(
        chat_id=601334258,
        from_chat_id=update.message.chat['id'],
        message_id=update.message['message_id'],
    )
    reply(update, 'отправляю локацию')
    return ConversationHandler.END


def main():
    """Основная логика работы бота."""
    dp = updater.dispatcher
    start_handler = CommandHandler('start', start)
    participants_handler = CommandHandler('participants', participants)
    points_handler = CommandHandler('points', points)
    del_participants_handler = CommandHandler(
        'del_participants', del_participants
    )
    register_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register)],
        states={
            ADD_PARTICIPANT: [MessageHandler(
                Filters.text, register_add_participant, pass_user_data=True
            )],
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    admin_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin)],
        states={
            ADMIN_PASS_KEY: [MessageHandler(
                Filters.text, admin_key_verification, pass_user_data=True
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    point_handler = ConversationHandler(
        entry_points=[CommandHandler('add_point', add_point)],
        states={
            ADD_COORDINATES: [MessageHandler(
                Filters.text, add_coordinates, pass_user_data=True
            )],
            ADD_TASK: [MessageHandler(
                Filters.text, add_task, pass_user_data=True
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    del_points_handler = ConversationHandler(
        entry_points=[CommandHandler('del_points', del_points)],
        states={
            1: [MessageHandler(
                Filters.text, del_points_all_or_specific, pass_user_data=True
            )],
            2: [MessageHandler(
                Filters.text, del_specific_points, pass_user_data=True
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(start_handler)
    dp.add_handler(register_handler)
    dp.add_handler(admin_handler)
    dp.add_handler(points_handler)
    dp.add_handler(point_handler)
    dp.add_handler(participants_handler)
    dp.add_handler(del_points_handler)
    dp.add_handler(del_participants_handler)

    try:
        updater.start_polling()
        print('Бот запущен.')
        updater.idle()
    except telegram.error.TelegramError as e:
        print(e)


if __name__ == '__main__':
    if not check_tokens():
        sys.exit(1)

    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
    except telegram.error.InvalidToken as e:
        print('некорректный токен')
    except telegram.error.TelegramError as e:
        print('Ошибка авторизации.')

    conn = sqlite3.connect('db.sqlite', check_same_thread=False)
    cursor = conn.cursor()

    main()
