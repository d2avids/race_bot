import logging
import os
import sqlite3
import sys
import time
from datetime import datetime

import telegram
from dotenv import load_dotenv
from telegram.ext import (CommandHandler, ConversationHandler, Filters,
                          MessageHandler, Updater)

from modules.constants import (ADD_COORDINATES, ADD_PARTICIPANT, ADD_TASK,
                               ADMIN_BUTTONS, ADMIN_INVALID_KEY_MESSAGE,
                               ADMIN_MESSAGE, ADMIN_PASS_KEY,
                               ADMIN_VALID_KEY_MESSAGE, ALREADY_ADMIN,
                               COORDINATES_MESSAGE, DEL, DEL_CANCEL,
                               DEL_PARTICIPANTS_CONFIRMATION,
                               DEL_POINTS_MESSAGE, DEL_SUCCESS, GO_ALL_SUCCESS,
                               GO_FINISH, GO_FINISH_MESSAGE, GO_MESSAGE,
                               GO_SUCCESS_MESSAGE, GO_TASK, LOG_CHAT_ID,
                               NEW_ADMIN, NEW_POINT, NO_TOKEN, NOT_ADMIN,
                               NOT_DATABASE, NOT_RACE_STARTED, NOT_REGISTERED,
                               PARTICIPANT_FINISHED_RACE,
                               PARTICIPANT_REGISTERED,
                               PARTICIPANT_SENT_LOCATION,
                               PARTICIPANT_SENT_PHOTO,
                               PARTICIPANT_STARTED_RACE, POINT_MESSAGE,
                               REGISTER_MESSAGE, REGISTER_POSITION_MESSAGE,
                               REPLY_TELEGRAM_API_ERROR, RESULT_MESSAGE,
                               RESULTS_SPECIFIC, START_MESSAGE,
                               START_RACE_MESSAGE, DEL_RESULTS_CONFIRMATION,
                               DEL_PARTICIPANTS_PROCEDURE_CONFIRMATION,
                               DEL_RES_PROCEDURE_CONFIRMATION)

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TG_BOT_TOKEN')
ADMIN_KEY = os.getenv('ADMIN_KEY')


def check_tokens():
    """Проверка наличия токенов."""
    if not TELEGRAM_TOKEN or not ADMIN_KEY:
        logger.critical(NO_TOKEN)
        return False
    return True


def db_table_val(user_id, username, name):
    """
    Регистрирует участника в таблице participants, если такой записи нет.
    """
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
        logger.info(PARTICIPANT_REGISTERED.format(
            participant=f'{user_id}, {username}, {username}')
        )
    except sqlite3.IntegrityError:
        cursor.execute(
            '''SELECT id FROM main.participants '''
            '''WHERE user_id = ?''',
            (user_id,)
        )
        number = cursor.fetchone()
    except sqlite3.Error as err:
        logger.critical(NOT_DATABASE.format(error=err))
        raise sqlite3.Error(NOT_DATABASE.format(error=err))
    return number[0]


def db_table_all_points():
    """
    Возвращает все записи контрольных точек из таблицы control_points.
    """
    try:
        cursor.execute(
            '''SELECT * from main.control_points'''
        )
        records = cursor.fetchall()
    except sqlite3.Error as err:
        logger.critical(NOT_DATABASE.format(error=err))
        raise sqlite3.Error(NOT_DATABASE.format(error=err))
    return records


def db_table_all_participants():
    """Возвращает все записи участников из таблицы participants."""
    try:
        cursor.execute(
            '''SELECT * from main.participants'''
        )
        records = cursor.fetchall()
    except sqlite3.Error as err:
        logger.critical(NOT_DATABASE.format(error=err))
        raise sqlite3.Error(err)
    return records


def is_registered_or_admin(user_id):
    """
    Проверяет зарегистрирован ли участник, и, если да, является ли он админом.
    False - не зарегистрирован; 
    None - зарегистрирован, но не админ; 
    True - админ.
    """
    is_registered = False
    try:
        cursor.execute(
            '''SELECT is_admin FROM main.participants '''
            '''WHERE user_id = ?''',
            (user_id,)
        )
        result = cursor.fetchone()
    except sqlite3.Error as err:
        logger.critical(NOT_DATABASE.format(error=err))
        raise sqlite3.Error(NOT_DATABASE.format(error=err))
    if result is None:
        return is_registered
    return result[0]


def reply(update, message, keyboard=None, parse_mode='HTML'):
    """Отправляет сообщение пользователю."""
    try:
        update.message.reply_text(
            text=message,
            reply_markup=keyboard,
            parse_mode=parse_mode,
        )
    except telegram.error.TelegramError as err:
        logger.error(REPLY_TELEGRAM_API_ERROR.format(error=err))


def admin(update, context):
    """
    Начинает процедуру верификации в качестве администратора 
    или возвращает список админских команд, если пользователь уже 
    является админом.
    """
    user_id = update.message.from_user['id']
    if is_registered_or_admin(user_id):
        button_list = [[telegram.KeyboardButton(s)] for s in ADMIN_BUTTONS]
        keyboard = telegram.ReplyKeyboardMarkup(button_list,
                                                resize_keyboard=True)
        reply(update, ALREADY_ADMIN, keyboard)
        return ConversationHandler.END

    reply(update, ADMIN_MESSAGE)
    return ADMIN_PASS_KEY


def admin_key_verification(update, context):
    """
    Сравнивает сообщение пользователя с ключом в .env и, если совпадает,
    фиксирует его в таблице participants в качестве администратора.
    """
    user_id = update.message.from_user['id']
    if update.message.text == ADMIN_KEY:
        try:
            cursor.execute(
                '''UPDATE main.participants '''
                '''SET is_admin = 1 '''
                '''WHERE user_id = ?''',
                (user_id,)
            )
            conn.commit()
        except sqlite3.Error as e:
            reply(update, NOT_DATABASE.format(error=e))
            logger.critical(NOT_DATABASE.format(error=err))
            return ConversationHandler.END

        button_list = [[telegram.KeyboardButton(s)] for s in ADMIN_BUTTONS]
        keyboard = telegram.ReplyKeyboardMarkup(button_list,
                                                resize_keyboard=True)
        reply(update, ADMIN_VALID_KEY_MESSAGE, keyboard)
        logger.info(NEW_ADMIN.format(participant=user_id))
        return ConversationHandler.END

    reply(update, ADMIN_INVALID_KEY_MESSAGE)
    return ConversationHandler.END


def add_point(update, context):
    """
    Начинает процедуру добавления контрольной точки. Доступно только админам.
    """
    user_id = update.message.from_user['id']
    if is_registered_or_admin(user_id) is False:
        reply(update, NOT_REGISTERED)
        return ConversationHandler.END
    elif not is_registered_or_admin(user_id):
        reply(update, NOT_ADMIN)
        return ConversationHandler.END

    reply(update, POINT_MESSAGE)
    return ADD_COORDINATES


def add_coordinates(update, context):
    """
    Добавляет координаты контрольной точки в таблицу control_points.
    """
    coordinates = update.message.text
    context.user_data['coordinates'] = coordinates
    try:
        cursor.execute(
            '''INSERT INTO main.control_points (coordinates)'''
            '''VALUES (?)''',
            (coordinates,)
        )
        conn.commit()
        reply(update, COORDINATES_MESSAGE)
        return ADD_TASK
    except sqlite3.Error as err:
        reply(update, NOT_DATABASE.format(error=err))
        logger.critical(NOT_DATABASE.format(error=err))
        return ConversationHandler.END


def add_task(update, context):
    """
    Добавляет задание контрольной точки в таблицу control_points.
    """
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
        logger.info(NEW_POINT.format(
            coordinates=context.user_data['coordinates'])
        )
    except sqlite3.Error as err:
        reply(update, sqlite3.Error(NOT_DATABASE.format(error=err)))
        logger.critical(NOT_DATABASE.format(error=err))
    return ConversationHandler.END


def stop(update, context):
    """Команда /stop завершает диалог с ботом."""
    return ConversationHandler.END


def start(update, context):
    """Документация бота и список возможных команд."""
    button = telegram.KeyboardButton(
        text='/register'
    )
    keyboard = telegram.ReplyKeyboardMarkup([[button]], resize_keyboard=True)

    reply(update, START_MESSAGE, keyboard)


def points(update, context):
    """Выводит список всех контрольных точек в чат. Доступно только админам."""
    user_id = update.message.from_user['id']
    if not is_registered_or_admin(user_id):
        reply(update, NOT_ADMIN)
        return

    records = db_table_all_points()

    reply_message = (
        'Список контрольных точек:\n\n'
    )
    for row in records:
        reply_message += f'ID: <code>{row[0]}</code> | '
        reply_message += f'Coordinates: <code>{row[1]}</code> | '
        reply_message += f'Task: <code>{row[2]}</code>\n\n'
    reply(update, reply_message)


def participants(update, context):
    """Выводит список всех участников в чат. Доступно только админам."""
    user_id = update.message.from_user['id']

    if not is_registered_or_admin(user_id):
        reply(update, NOT_ADMIN)
        return

    records = db_table_all_participants()

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
    """Начинает процедуру удаления контрольных точек. Доступно только админам."""
    user_id = update.message.from_user['id']
    if not is_registered_or_admin(user_id):
        reply(update, NOT_ADMIN)
        return ConversationHandler.END
    buttons = ['Все', 'Некоторые']
    button_list = [[telegram.KeyboardButton(s)] for s in buttons]
    keyboard = telegram.ReplyKeyboardMarkup(
        button_list, resize_keyboard=True, one_time_keyboard=True
    )
    reply(update, DEL_POINTS_MESSAGE, keyboard)
    return 1


def del_points_all_or_specific(update, context):
    """Удаляет все контрольные точки или начинает процедуру удаления некоторых."""
    answer = update.message.text.lower()
    if answer in ('dct', 'все', 'all', 'clear'):
        try:
            cursor.execute(
                '''DELETE from main.control_points'''
            )
            conn.commit()
            reply(update, DEL_SUCCESS.format(rows_count=cursor.rowcount))
            logger.info(DEL.format(table='control_points'))
            return ConversationHandler.END
        except sqlite3.Error as err:
            logger.critical(NOT_DATABASE.format(error=err))
            reply(update, NOT_DATABASE.format(error=err))
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
        except sqlite3.Error as err:
            reply(update, NOT_DATABASE.format(error=err))
            logger.critical(NOT_DATABASE.format(error=err))
            return ConversationHandler.END


def del_specific_points(update, context):
    """Удаляет контрольные точки по ID из сообщения."""
    ids = update.message.text.split(',')
    try:
        cursor.execute(
            '''DELETE FROM main.control_points '''
            '''WHERE id IN ({})'''.format(','.join('?' * len(ids))),
            tuple(ids)
        )
        conn.commit()
        logger.info(DEL.format(table='control_points'))
        reply(update, DEL_SUCCESS.format(rows_count=cursor.rowcount))
        return ConversationHandler.END
    except sqlite3.Error as err:
        reply(update, NOT_DATABASE.format(error=err))
        logger.critical(NOT_DATABASE.format(error=err))
        return ConversationHandler.END


def del_participants(update, context):
    """Начинает процедуру удаления всех участников. Доступно только админам."""
    user_id = update.message.from_user['id']

    if not is_registered_or_admin(user_id):
        reply(update, NOT_ADMIN)
        return ConversationHandler.END

    buttons = ['Да', 'Нет']
    button_list = [[telegram.KeyboardButton(s)] for s in buttons]
    keyboard = telegram.ReplyKeyboardMarkup(
        button_list, resize_keyboard=True, one_time_keyboard=True
    )
    reply(update, DEL_PARTICIPANTS_CONFIRMATION, keyboard)
    return DEL_PARTICIPANTS_PROCEDURE_CONFIRMATION


def del_participants_confirmation(update, context):
    """Удаляет всех участников из таблицы participants."""
    answer = update.message.text.lower()
    if answer in ('lf', 'да', 'yes', '+'):
        try:
            cursor.execute(
                '''DELETE from main.participants '''
                '''WHERE is_admin = 0'''
            )
            conn.commit()
            reply(update, DEL_SUCCESS.format(rows_count=cursor.rowcount))
            logger.warning(DEL.format(table='participants'))
            return ConversationHandler.END
        except sqlite3.Error as err:
            reply(update, NOT_DATABASE.format(error=err))
            logger.critical(NOT_DATABASE.format(error=err))
            return ConversationHandler.END
    else:
        reply(update, DEL_CANCEL)
        return ConversationHandler.END


def register(update, context):
    """Начинает процедуру регистрации участника."""
    reply(update, REGISTER_MESSAGE)
    return ADD_PARTICIPANT


def register_add_participant(update, context):
    """Регистрирует участника в таблице participants."""
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']
    name = update.message.text
    number = db_table_val(user_id=user_id, username=username, name=name)
    button = telegram.KeyboardButton(text='/start_race')
    keyboard = telegram.ReplyKeyboardMarkup(
        [[button]], resize_keyboard=True, one_time_keyboard=True
    )
    reply(update, REGISTER_POSITION_MESSAGE.format(number=number), keyboard)
    return ConversationHandler.END


def start_race(update, context):
    """Начинает гонку для участника и выводит инструкцию."""
    user_id = update.message.from_user['id']
    button = telegram.KeyboardButton(text='/go')
    keyboard = telegram.ReplyKeyboardMarkup([[button]], resize_keyboard=True)

    if is_registered_or_admin(user_id) is False:
        reply(update, NOT_REGISTERED)
        return

    try:
        cursor.execute(
            '''UPDATE participants SET race_started = 1 WHERE user_id = ?''',
            (user_id,)
        )
        conn.commit()

        cursor.execute(
            '''SELECT id FROM participants WHERE user_id = ?''',
            (user_id,)
        )
        participant_id = cursor.fetchone()[0]

        cursor.execute('''SELECT id FROM control_points''')
        control_point_ids = [row[0] for row in cursor.fetchall()]
        start_time = int(time.time())
        context.user_data['start_time'] = start_time

        for control_point_id in control_point_ids:
            cursor.execute(
                '''INSERT OR IGNORE INTO results '''
                '''(participant_id, control_point_id, start_time) '''
                '''VALUES (?, ?, ?)''',
                (participant_id, control_point_id, start_time)
            )

        conn.commit()
        logger.info(PARTICIPANT_STARTED_RACE.format(id=participant_id))
        reply(
            update,
            START_RACE_MESSAGE.format(amount=len(control_point_ids)),
            keyboard
        )

    except sqlite3.Error as err:
        reply(update, NOT_DATABASE.format(error=err))
        logger.critical(NOT_DATABASE.format(error=err))


def go(update, context):
    """
    Начинает процедуру прохождения контрольных точек, отдавая пользователю
    первую точку и запрашивая локацию.
    """
    user_id = update.message.from_user['id']

    try:
        cursor.execute(
            '''SELECT id FROM participants WHERE user_id = ?''',
            (user_id,)
        )
        participant_id = cursor.fetchone()[0]
        cursor.execute(
            '''SELECT race_started FROM participants WHERE user_id = ?''',
            (user_id,)
        )
        race_started = cursor.fetchone()

    except sqlite3.Error as err:
        reply(update, NOT_DATABASE.format(error=err))
        logger.critical(NOT_DATABASE.format(error=err))
        return ConversationHandler.END

    if not race_started or race_started[0] != 1:
        reply(update, NOT_RACE_STARTED)
        return ConversationHandler.END

    try:
        cursor.execute(
            '''SELECT control_point_id FROM results '''
            '''WHERE participant_id = ? AND finish_time IS NULL '''
            '''ORDER BY control_point_id '''
            '''LIMIT 1''',
            (participant_id,)
        )

        next_control_point = cursor.fetchone()

        if not next_control_point:
            cursor.execute(
                '''SELECT finish_time FROM results '''
                '''WHERE participant_id = ? '''
                '''ORDER BY finish_time DESC '''
                '''LIMIT 1''',
                (participant_id,)
            )

            finish_time = cursor.fetchone()[0]

            cursor.execute(
                '''SELECT start_time FROM results '''
                '''WHERE participant_id = ? '''
                '''ORDER BY start_time '''
                '''LIMIT 1''',
                (participant_id,)
            )

            start_time = cursor.fetchone()[0]

            final_time = finish_time - start_time
            print(final_time)

            hours = final_time // 3600
            remaining_seconds = final_time % 3600
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60

            logger.info(PARTICIPANT_FINISHED_RACE.format(
                participant_id=participant_id,
                hours=hours,
                minutes=minutes,
                seconds=seconds
            ))

            reply(update, GO_ALL_SUCCESS.format(
                hours=hours, minutes=minutes, seconds=seconds
            ))

            return ConversationHandler.END

        cursor.execute(
            '''SELECT id, coordinates, task '''
            '''FROM control_points '''
            '''WHERE id = ?''',
            (next_control_point[0],)
        )
        next_control_point = cursor.fetchone()

        context.user_data['participant_id'] = participant_id
        context.user_data['control_point_id'] = next_control_point[0]
        context.user_data['point'] = (
            f'ID: {next_control_point[0]} | '
            f'Coordinates: {next_control_point[1]} | '
            f'Task: {next_control_point[2]}'
        )
        button = telegram.KeyboardButton(
            text='Отправить локацию', request_location=True
        )
        keyboard = telegram.ReplyKeyboardMarkup(
            [[button]], one_time_keyboard=True, resize_keyboard=True)
        reply(
            update,
            GO_MESSAGE.format(
                id=next_control_point[0],
                coordinates=next_control_point[1],
                task=next_control_point[2]
            ),
            keyboard
        )

        return GO_FINISH
    except sqlite3.Error as err:
        reply(update, NOT_DATABASE.format(error=err))
        logger.critical(NOT_DATABASE.format(error=err))
        return ConversationHandler.END


def go_finish(update, context):
    """
    Принимает локацию и логирует её в чате администраторов, а также
    запрашивает фотографию по завершению прохождения контрольной точки.
    """
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']

    bot.send_message(
         chat_id=LOG_CHAT_ID,
         text=f'Локация участника {user_id}, {username}, проходящего точку\n'
              f'{context.user_data["point"]}'
    )
    bot.forward_message(
         chat_id=LOG_CHAT_ID,
         from_chat_id=update.message.chat['id'],
         message_id=update.message['message_id'],
     )
    logger.info(PARTICIPANT_SENT_LOCATION.format(
        user_id=user_id,
        username=username
    ))

    reply(update, GO_FINISH_MESSAGE)
    return GO_TASK


def go_task(update, context):
    """
    Принимает фотографию и логирует её в чате администраторов, а также
    завершает прохождение контрольной точки.
    """
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']

    bot.send_message(
         chat_id=LOG_CHAT_ID,
         text=f'Фотография участника {user_id}, {username}, выполнившего '
              f'задание следующей контрольной точки:\n'
              f'{context.user_data["point"]}'
    )
    bot.forward_message(
         chat_id=LOG_CHAT_ID,
         from_chat_id=update.message.chat['id'],
         message_id=update.message['message_id'],
    )
    finish_time = int(time.time())

    logger.info(PARTICIPANT_SENT_PHOTO.format(
        user_id=user_id,
        username=username
    ))

    try:
        cursor.execute(
            '''UPDATE results SET finish_time = ? '''
            '''WHERE participant_id = ? AND control_point_id = ?''',
            (
                finish_time,
                context.user_data['participant_id'],
                context.user_data['control_point_id'],
            )
        )
        conn.commit()
        reply(update, GO_SUCCESS_MESSAGE)
        return ConversationHandler.END
    except sqlite3.Error as err:
        reply(update, NOT_DATABASE.format(error=err))
        logger.critical(NOT_DATABASE.format(error=err))


def results(update, context):
    """
    Начинает процедуру просмотра результатов участника по ID или всех участников
    Доступно только админам.
    """
    button = telegram.KeyboardButton(text='Посмотреть всех участников')
    keyboard = telegram.ReplyKeyboardMarkup(
        [[button]], resize_keyboard=True, one_time_keyboard=True
    )
    reply(update, RESULT_MESSAGE, keyboard)
    return RESULTS_SPECIFIC


def results_specific(update, context):
    """
    Выводит результаты участника по ID или всех участников.
    """
    user_id = update.message.from_user['id']

    if not is_registered_or_admin(user_id):
        reply(update, NOT_ADMIN)
        return ConversationHandler.END

    answer = update.message.text
    message = ''

    if answer.isdigit():
        try:
            cursor.execute(
                '''SELECT * from results '''
                '''WHERE participant_id = ?''',
                (answer,)
            )

        except sqlite3.Error as err:
            reply(update, NOT_DATABASE.format(error=err))
            logger.critical(NOT_DATABASE.format(error=err))
            return ConversationHandler.END
    else:
        try:
            cursor.execute(
                '''SELECT * FROM results'''
            )
        except sqlite3.Error as err:
            reply(update, NOT_DATABASE.format(error=err))
            logger.critical(NOT_DATABASE.format(error=err))
            return ConversationHandler.END

    result = cursor.fetchall()

    if not result:
        reply(update, 'Записей результатов участника с таким ID нет.')

    for row in result:
        start_time = datetime.fromtimestamp(row[3])
        finish_time = None
        if row[4]:
            finish_time = datetime.fromtimestamp(row[4])
        message += (
            f'ID контрольной точки: {row[1]} | '
            f'ID участника: {row[2]} | '
            f'Дата старта: {start_time} | '
            f'Дата завершения: {finish_time}\n\n'
        )

    reply(update, message)

    return ConversationHandler.END


def del_results(update, context):
    """Начинает процедуру удаления записей из таблицы results."""

    user_id = update.message.from_user['id']

    if not is_registered_or_admin(user_id):
        reply(update, NOT_ADMIN)
        return ConversationHandler.END

    buttons = ['Да', 'Нет']
    button_list = [[telegram.KeyboardButton(s)] for s in buttons]
    keyboard = telegram.ReplyKeyboardMarkup(
        button_list, resize_keyboard=True, one_time_keyboard=True
    )
    reply(update, DEL_RESULTS_CONFIRMATION, keyboard)
    return DEL_RES_PROCEDURE_CONFIRMATION


def del_results_confirmation(update, context):
    """Удаляет все результаты из таблицы results."""
    answer = update.message.text.lower()
    if answer in ('lf', 'да', 'yes', '+'):
        try:
            cursor.execute(
                '''DELETE from main.results '''
            )
            conn.commit()
            reply(update, DEL_SUCCESS.format(rows_count=cursor.rowcount))
            logger.warning(DEL.format(table='results'))
            return ConversationHandler.END
        except sqlite3.Error as err:
            reply(update, NOT_DATABASE.format(error=err))
            logger.critical(NOT_DATABASE.format(error=err))
            return ConversationHandler.END
    else:
        reply(update, DEL_CANCEL)
        return ConversationHandler.END


def main():
    """Основная логика работы бота."""
    dp = updater.dispatcher

    start_handler = CommandHandler('start', start)
    participants_handler = CommandHandler('participants', participants)
    points_handler = CommandHandler('points', points)

    start_race_handler = CommandHandler('start_race', start_race)

    results_handler = ConversationHandler(
        entry_points=[CommandHandler('results', results)],
        states={
            RESULTS_SPECIFIC: [MessageHandler(
                Filters.text, results_specific, pass_user_data=True
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    go_handler = ConversationHandler(
        entry_points=[CommandHandler('go', go)],
        states={
            GO_FINISH: [MessageHandler(
                Filters.location, go_finish, pass_user_data=True
            )],
            GO_TASK: [MessageHandler(
                Filters.photo, go_task, pass_user_data=True
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
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

    del_participants_handler = ConversationHandler(
        entry_points=[CommandHandler('del_participants', del_participants)],
        states={
            DEL_PARTICIPANTS_PROCEDURE_CONFIRMATION: [MessageHandler(
                Filters.text,
                del_participants_confirmation,
                pass_user_data=True
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    del_results_handler = ConversationHandler(
        entry_points=[CommandHandler('del_results', del_results)],
        states={
            DEL_RES_PROCEDURE_CONFIRMATION: [MessageHandler(
                Filters.text,
                del_results_confirmation,
                pass_user_data=True
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    dp.add_handler(start_race_handler)
    dp.add_handler(go_handler)
    dp.add_handler(start_handler)
    dp.add_handler(register_handler)
    dp.add_handler(admin_handler)
    dp.add_handler(points_handler)
    dp.add_handler(point_handler)
    dp.add_handler(participants_handler)
    dp.add_handler(results_handler)
    dp.add_handler(del_points_handler)
    dp.add_handler(del_participants_handler)
    dp.add_handler(del_results_handler)

    try:
        updater.start_polling()
        print('Бот запущен.')
        updater.idle()
    except telegram.error.TelegramError as err:
        logger.critical(f'Ошибка при запуске бота {err}')


if __name__ == '__main__':
    
    # Логирование
    logger = logging.getLogger('race_bot')

    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    logger = logging.getLogger('race_bot')
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(console_handler)

    # Проверка наличия токенов
    if not check_tokens():
        sys.exit(1)

    # Подключение API Telegram, инициализация бота
    try:
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
    except telegram.error.InvalidToken as err:
        logger.critical(f'Неверный токен {err}')
    except telegram.error.TelegramError as err:
        logger.critical(f'Ошибка авторизации бота {err}')

    # Подключение к БД
    try:
        conn = sqlite3.connect('db.sqlite', check_same_thread=False)
        cursor = conn.cursor()
    except sqlite3.Error as err:
        logger.critical(NOT_DATABASE.format(error=err))

    main()
