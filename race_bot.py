import os
import sys
import time
from datetime import datetime

import telegram
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          ConversationHandler, MessageHandler, filters)

from modules.constants import (ADD_COORDINATES, ADD_PARTICIPANT, ADD_TASK,
                               ADMIN_BUTTONS, ADMIN_INVALID_KEY_MESSAGE,
                               ADMIN_MESSAGE, ADMIN_PASS_KEY,
                               ADMIN_VALID_KEY_MESSAGE, ALREADY_ADMIN,
                               AUTHORIZATION_ERROR, BOT_START_SUCCESS,
                               COORDINATES_MESSAGE, DEL, DEL_CANCEL,
                               DEL_PARTICIPANTS_CONFIRMATION,
                               DEL_PARTICIPANTS_CONFIRMATION_MESSAGE,
                               DEL_POINTS_MESSAGE,
                               DEL_RES_PROCEDURE_CONFIRMATION,
                               DEL_RESULTS_CONFIRMATION, DEL_SUCCESS,
                               DELETE_POINTS, DELETE_SPECIFIC_POINTS, GET_SEX,
                               GET_TYPE, GO_ALL_SUCCESS, GO_FINISH,
                               GO_FINISH_MESSAGE, GO_LOCATION_LOG, GO_MESSAGE,
                               GO_NO_POINTS, GO_PHOTO_LOG, GO_SUCCESS_MESSAGE,
                               GO_TASK, INVALID_TOKEN, NEW_ADMIN, NEW_POINT,
                               NO_RESULTS, NO_TOKEN, NOT_ADMIN,
                               NOT_RACE_STARTED, NOT_REGISTERED,
                               PARTICIPANT_FINISHED_RACE,
                               PARTICIPANT_SENT_LOCATION,
                               PARTICIPANT_SENT_PHOTO, POINT_MESSAGE,
                               POLLING_ERROR, REGISTER_MESSAGE,
                               REGISTER_POSITION_MESSAGE, REGISTER_SEX_BUTTONS,
                               REGISTER_SEX_MESSAGE, REGISTER_TYPE_BUTTONS,
                               REGISTER_TYPE_MESSAGE, REPLY_TELEGRAM_API_ERROR,
                               RESULT_MESSAGE, RESULTS_SPECIFIC,
                               SEND_MESSAGE_ERROR, START_MESSAGE,
                               START_RACE_LOCATION, START_RACE_LOCATION_LOG,
                               START_RACE_LOCATION_MESSAGE, START_RACE_MESSAGE,
                               START_RACE_PHOTO, START_RACE_PHOTO_LOG,
                               START_RACE_PHOTO_MESSAGE)
from modules.logger import logger
from modules.sql_queries import (database_del_participants,
                                 database_del_points, database_del_results,
                                 database_del_specific_points,
                                 database_get_control_point,
                                 database_get_control_point_id,
                                 database_get_participant_status,
                                 database_get_time, database_overall_results,
                                 database_participants, database_points,
                                 database_register, database_results,
                                 database_results_by_id, database_set_admin,
                                 database_set_coordinates,
                                 database_set_finish_time, database_set_task,
                                 database_start_race, is_registered_or_admin)
from modules.utils import check_tokens, count_time

load_dotenv()

# Переменные окружения
TELEGRAM_TOKEN = os.getenv('TG_BOT_TOKEN')
ADMIN_KEY = os.getenv('ADMIN_KEY')
LOG_CHAT_ID = os.getenv('LOG_CHAT_ID')


async def reply(update, message, keyboard=None, parse_mode='HTML'):
    """Отправляет сообщение пользователю."""
    try:
        await update.message.reply_text(
            text=message,
            reply_markup=keyboard,
            parse_mode=parse_mode,
        )
    except telegram.error.TelegramError as er:
        logger.error(REPLY_TELEGRAM_API_ERROR.format(error=er))


async def log_message(update, context, message):
    """Логирует сообщения в чат администраторов"""
    try:
        await context.bot.send_message(
            chat_id=LOG_CHAT_ID,
            text=message
        )
        await context.bot.forward_message(
            chat_id=LOG_CHAT_ID,
            from_chat_id=update.message.chat_id,
            message_id=update.message['message_id'],
        )
    except telegram.error.TelegramError as er:
        logger.error(SEND_MESSAGE_ERROR.format(error=er))


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stop завершает диалог с ботом."""
    return ConversationHandler.END


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Документация бота и список возможных команд."""
    button = telegram.KeyboardButton(text='/register')
    keyboard = telegram.ReplyKeyboardMarkup([[button]], resize_keyboard=True)
    await reply(update, START_MESSAGE, keyboard)


async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процедуру регистрации участника, запрашивая его ФИО."""
    await reply(update, REGISTER_MESSAGE)
    return GET_SEX


async def register_get_sex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет ФИО участника и запрашивает его пол."""
    context.user_data['name'] = update.message.text
    keyboard = telegram.ReplyKeyboardMarkup(
        [[telegram.KeyboardButton(b)] for b in REGISTER_SEX_BUTTONS],
        resize_keyboard=True
    )
    await reply(update, REGISTER_SEX_MESSAGE, keyboard)
    return GET_TYPE


async def register_get_type(update: Update,
                            context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет пол участника и запрашивает тип велосипеда."""
    context.user_data['sex'] = update.message.text
    keyboard = telegram.ReplyKeyboardMarkup(
        [[telegram.KeyboardButton(b)] for b in REGISTER_TYPE_BUTTONS],
        resize_keyboard=True
    )
    await reply(update, REGISTER_TYPE_MESSAGE, keyboard)
    return ADD_PARTICIPANT


async def register_add_participant(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
    """
    Сохраняет тип велосипеда и сохраняет участника в таблице participants.
    """
    context.user_data['type'] = update.message.text
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']
    number = await database_register(
        user_id,
        username,
        context.user_data['name'],
        context.user_data['sex'],
        context.user_data['type']
    )
    button = telegram.KeyboardButton(text='/start_race')
    keyboard = telegram.ReplyKeyboardMarkup(
        [[button]], resize_keyboard=True, one_time_keyboard=True
    )
    await reply(
        update, REGISTER_POSITION_MESSAGE.format(number=number), keyboard
    )
    return ConversationHandler.END


async def start_race(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинает процедуру старта гонки, запрашивая
    у участника стартовую геолокацию.
    """
    user_id = update.message.from_user['id']

    button = telegram.KeyboardButton(
        text='Отправить локацию', request_location=True
    )
    keyboard = telegram.ReplyKeyboardMarkup(
        [[button]], one_time_keyboard=True, resize_keyboard=True
    )

    if not await is_registered_or_admin(user_id):
        await reply(update, NOT_REGISTERED)
        return ConversationHandler.END

    await reply(update, START_RACE_LOCATION_MESSAGE, keyboard)
    return START_RACE_LOCATION


async def start_race_location(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
    """
    Принимает стартовую локацию участника и запрашивает
    у него селфи для идентификации участника.
    """
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']
    logger.info(PARTICIPANT_SENT_LOCATION.format(
        user_id=user_id,
        username=username
    ))
    await log_message(update, context, START_RACE_LOCATION_LOG.format(
        user_id=user_id, username=username
    ))
    await reply(update, START_RACE_PHOTO_MESSAGE)
    return START_RACE_PHOTO


async def start_race_photo(update: Update,
                           context: ContextTypes.DEFAULT_TYPE):
    """
    Принимает селфи участника и отдает
    инструкцию по прохождению гонки, ожидая /go.
    """

    user_id = update.message.from_user['id']
    username = update.message.from_user['username']
    logger.info(PARTICIPANT_SENT_PHOTO.format(
        user_id=user_id,
        username=username
    ))

    button = telegram.KeyboardButton(text='/go')
    keyboard = telegram.ReplyKeyboardMarkup([[button]], resize_keyboard=True)
    await log_message(update, context, START_RACE_PHOTO_LOG.format(
        user_id=user_id, username=username
    ))
    control_points_amount = await database_start_race(user_id)
    await reply(
        update,
        START_RACE_MESSAGE.format(amount=control_points_amount),
        keyboard
    )
    return ConversationHandler.END


async def go(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинает процедуру прохождения контрольных точек, отдавая пользователю
    первую точку и запрашивая её по прохождению контрольной точки.
    """
    user_id = update.message.from_user['id']
    context.user_data['participant_id'], race_state = (
        await database_get_participant_status(user_id)
    )

    if race_state != 1:
        await reply(update, NOT_RACE_STARTED)
        return ConversationHandler.END
    context.user_data['control_point_id'] = (
        await database_get_control_point_id(
            context.user_data['participant_id']
        )
    )

    if not context.user_data['control_point_id']:
        start_time, finish_time = await database_get_time(
            context.user_data['participant_id']
        )
        if not finish_time or not start_time:
            await reply(update, GO_NO_POINTS)
            return ConversationHandler.END

        final_time = finish_time - start_time

        hours, minutes, seconds = await count_time(final_time)

        logger.info(PARTICIPANT_FINISHED_RACE.format(
            participant_id=context.user_data['participant_id'],
            hours=hours,
            minutes=minutes,
            seconds=seconds
        ))

        await reply(update, GO_ALL_SUCCESS.format(
            hours=hours, minutes=minutes, seconds=seconds
        ))

        return ConversationHandler.END

    (context.user_data['cp_id'],
     context.user_data['cp_coordinates'],
     context.user_data['cp_task']) = await database_get_control_point(
        context.user_data['control_point_id']
    )
    context.user_data['point_info'] = (
        f'ID: {context.user_data["cp_id"]} | '
        f'Coordinates: {context.user_data["cp_coordinates"]} | '
        f'Task: {context.user_data["cp_task"]}'
    )
    button = telegram.KeyboardButton(
        text='Отправить локацию', request_location=True
    )
    keyboard = telegram.ReplyKeyboardMarkup(
        [[button]], one_time_keyboard=True, resize_keyboard=True
    )
    await reply(
        update,
        GO_MESSAGE.format(
            id=context.user_data['cp_id'],
            coordinates=context.user_data['cp_coordinates'],
            task=context.user_data['cp_task']
        ),
        keyboard
    )
    return GO_FINISH


async def go_finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Принимает локацию и логирует её в чате администраторов, а также
    запрашивает фотографию по завершению прохождения контрольной точки.
    """
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']
    await log_message(update, context, GO_LOCATION_LOG.format(
        user_id=user_id,
        username=username,
        point=context.user_data['point_info']
    ))
    logger.info(PARTICIPANT_SENT_LOCATION.format(
        user_id=user_id,
        username=username
    ))
    await reply(update, GO_FINISH_MESSAGE)
    return GO_TASK


async def go_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Принимает фотографию и логирует её в чате администраторов, а также
    завершает прохождение контрольной точки.
    """
    user_id = update.message.from_user['id']
    username = update.message.from_user['username']

    await log_message(update, context, GO_PHOTO_LOG.format(
        user_id=user_id,
        username=username,
        point=context.user_data['point_info']
    ))
    logger.info(PARTICIPANT_SENT_PHOTO.format(
        user_id=user_id,
        username=username
    ))
    finish_time = int(time.time())
    await database_set_finish_time(
        participant_id=context.user_data['participant_id'],
        control_point_id=context.user_data['cp_id'],
        finish_time=finish_time
    )
    await reply(update, GO_SUCCESS_MESSAGE)
    return ConversationHandler.END


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинает процедуру верификации в качестве администратора
    или возвращает список админских команд, если пользователь уже
    является админом.
    """
    user_id = update.message.from_user['id']
    if not await is_registered_or_admin(user_id):
        await reply(update, NOT_REGISTERED)
        return ConversationHandler.END
    elif await is_registered_or_admin(user_id) == 2:
        button_list = [[telegram.KeyboardButton(s)] for s in ADMIN_BUTTONS]
        keyboard = telegram.ReplyKeyboardMarkup(button_list,
                                                resize_keyboard=True)
        await reply(update, ALREADY_ADMIN, keyboard)
        return ConversationHandler.END

    await reply(update, ADMIN_MESSAGE)
    return ADMIN_PASS_KEY


async def admin_key_verification(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    """
    Сравнивает сообщение пользователя с ключом в .env и, если совпадает,
    фиксирует его в таблице participants в качестве администратора.
    """
    user_id = update.message.from_user['id']
    if update.message.text == ADMIN_KEY:
        await database_set_admin(user_id)

        button_list = [[telegram.KeyboardButton(s)] for s in ADMIN_BUTTONS]
        keyboard = telegram.ReplyKeyboardMarkup(button_list,
                                                resize_keyboard=True)

        await reply(update, ADMIN_VALID_KEY_MESSAGE, keyboard)
        logger.info(NEW_ADMIN.format(participant=user_id))
        return ConversationHandler.END

    await reply(update, ADMIN_INVALID_KEY_MESSAGE)
    return ConversationHandler.END


async def participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит список всех участников в чат. Доступно только админам."""
    user_id = update.message.from_user['id']

    if await is_registered_or_admin(user_id) != 2:
        await reply(update, NOT_ADMIN)
        return

    records = await database_participants()
    message = (
        'Список участников:\n\n'
    )
    counter = 0
    for row in records:
        counter += 1
        message += f'ID: <code>{row[0]}</code> | '
        message += f'User_id: {row[1]} | '
        message += f'Username: @{row[2]} | '
        message += f'Имя: {row[3]} | '
        message += f'Пол: {row[4]} | '
        message += f'Тип велосипеда: {row[5]} | '
        message += f'Is_admin {row[7]}\n\n'
        # по 15 записей на сообщение
        if counter == 15:
            counter = 0
            await reply(update, message)
            message = ''
    # оставшиеся записи
    await reply(update, message)


async def points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит список всех контрольных точек в чат. Доступно только админам."""
    user_id = update.message.from_user['id']

    if await is_registered_or_admin(user_id) != 2:
        await reply(update, NOT_ADMIN)
        return

    records = await database_points()
    message = (
        'Список контрольных точек:\n\n'
    )
    counter = 0
    for row in records:
        message += f'ID: <code>{row[0]}</code> | '
        message += f'Coordinates: <code>{row[1]}</code> | '
        message += f'Task: <code>{row[2]}</code>\n\n'
        # по 15 записей на сообщение
        if counter == 15:
            counter = 0
            await reply(update, message)
            message = ''
        # оставшиеся записи
    await reply(update, message)


async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинает процедуру просмотра результатов прохождения участниками
    контрольных точек. Доступно только админам.
    """
    user_id = update.message.from_user['id']

    if await is_registered_or_admin(user_id) != 2:
        await reply(update, NOT_ADMIN)
        return ConversationHandler.END

    button = telegram.KeyboardButton(text='Посмотреть всех участников')
    keyboard = telegram.ReplyKeyboardMarkup(
        [[button]], resize_keyboard=True, one_time_keyboard=True
    )

    await reply(update, RESULT_MESSAGE, keyboard)
    return RESULTS_SPECIFIC


async def results_specific(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Выводит результаты участника по ID или всех участников.
    """
    answer = update.message.text
    message = ''
    if answer.isdigit():
        result = await database_results_by_id(answer)
    else:
        result = await database_results()
    if not result:
        await reply(update, NO_RESULTS)
        return ConversationHandler.END
    counter = 0
    for row in result:
        counter += 1
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
        # по 15 записей на сообщение
        if counter == 15:
            counter = 0
            await reply(update, message)
            message = ''
        # оставшиеся записи
    await reply(update, message)
    return ConversationHandler.END


async def overall_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Просмотр общих результатов прохождения гонки участниками.
    """
    user_id = update.message.from_user['id']
    if await is_registered_or_admin(user_id) != 2:
        await reply(update, NOT_ADMIN)
        return ConversationHandler.END
    result = await database_overall_results()
    message = 'Результаты участников, прошедших испытание:\n\n'
    if result:
        counter = 0
        for row in result:
            counter += 1
            fin_time = row[4]
            hours, minutes, seconds = await count_time(fin_time)
            fin_time = f'{hours} ч. {minutes} мин. {seconds} сек.'
            message += f'Participant ID: <code>{row[0]}</code> | '
            message += f'Имя: <code>{row[1]}</code> | '
            message += f'Пол: {row[2]} | '
            message += f'Тип: {row[3]} | '
            message += f'Finish time: <code>{fin_time}</code>\n\n'
            # выводим по 15 результатов на сообщение
            if counter == 15:
                counter = 0
                await reply(update, message)
                message = ''
    # выводим оставшиеся результаты
    await reply(update, message)


async def add_point(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинает процедуру добавления контрольной точки. Доступно только админам.
    """
    user_id = update.message.from_user['id']
    if await is_registered_or_admin(user_id) != 2:
        await reply(update, NOT_ADMIN)
        return ConversationHandler.END

    await reply(update, POINT_MESSAGE)
    return ADD_COORDINATES


async def add_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Добавляет координаты контрольной точки в таблицу control_points.
    """
    context.user_data['coordinates'] = update.message.text
    await database_set_coordinates(context.user_data['coordinates'])
    await reply(update, COORDINATES_MESSAGE)
    return ADD_TASK


async def add_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
        Добавляет задание контрольной точки в таблицу control_points.
        """
    task = update.message.text
    await database_set_task(task)
    await reply(update, 'Задание добавлено')
    logger.info(NEW_POINT.format(
        coordinates=context.user_data['coordinates'])
    )
    return ConversationHandler.END


async def del_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает процедуру удаления записей из таблицы results."""
    user_id = update.message.from_user['id']

    if await is_registered_or_admin(user_id) != 2:
        await reply(update, NOT_ADMIN)
        return ConversationHandler.END

    buttons = ['Да', 'Нет']
    button_list = [[telegram.KeyboardButton(s)] for s in buttons]
    keyboard = telegram.ReplyKeyboardMarkup(
        button_list, resize_keyboard=True, one_time_keyboard=True
    )
    await reply(update, DEL_RESULTS_CONFIRMATION, keyboard)
    return DEL_RES_PROCEDURE_CONFIRMATION


async def del_results_confirmation(update: Update,
                                   context: ContextTypes.DEFAULT_TYPE):
    """Удаляет все результаты из таблицы results."""
    answer = update.message.text.lower()
    if answer in ('lf', 'да', 'yes', '+'):
        await database_del_results()
        await reply(update, DEL_SUCCESS.format(table='results'))
        logger.warning(DEL.format(table='results'))
        return ConversationHandler.END
    await reply(update, DEL_CANCEL)
    return ConversationHandler.END


async def del_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинает процедуру удаления контрольных точек.
    Доступно только админам.
    """
    user_id = update.message.from_user['id']
    if await is_registered_or_admin(user_id) != 2:
        await reply(update, NOT_ADMIN)
        return ConversationHandler.END
    buttons = ['Все', 'Некоторые']
    button_list = [[telegram.KeyboardButton(s)] for s in buttons]
    keyboard = telegram.ReplyKeyboardMarkup(
        button_list, resize_keyboard=True, one_time_keyboard=True
    )
    await reply(update, DEL_POINTS_MESSAGE, keyboard)
    return DELETE_POINTS


async def del_points_all_or_some(update: Update,
                                 context: ContextTypes.DEFAULT_TYPE):
    """
    Удаляет все контрольные точки или начинает процедуру удаления некоторых.
    """
    answer = update.message.text.lower()
    if answer in ('dct', 'все', 'all', 'clear'):
        await database_del_points()
        await reply(update, DEL_SUCCESS.format(table='points'))
        logger.info(DEL.format(table='control_points'))
        return ConversationHandler.END
    records = await database_points()
    message = (
        'Перечислите через запятую ID тех точек, '
        'которые необходимо удалить в формате: 1, 2, 3\n\n'
    )
    for row in records:
        message += f'ID: <code>{row[0]}</code> | '
        message += f'Coordinates: <code>{row[1]}</code> | '
        message += f'Task: <code>{row[2]}</code>\n\n'
    await reply(update, message)
    return DELETE_SPECIFIC_POINTS


async def del_specific_points(update: Update,
                              context: ContextTypes.DEFAULT_TYPE):
    """Удаляет контрольные точки по ID из сообщения."""
    ids = update.message.text.split(',')
    await database_del_specific_points(ids)
    logger.info(DEL.format(table='control_points'))
    await reply(update, DEL_SUCCESS.format(table='points'))
    return ConversationHandler.END


async def del_participants(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начинает процедуру удаления всех участников.
    Доступно только админам.
    """
    user_id = update.message.from_user['id']
    if await is_registered_or_admin(user_id) != 2:
        await reply(update, NOT_ADMIN)
        return ConversationHandler.END
    buttons = ['Да', 'Нет']
    button_list = [[telegram.KeyboardButton(s)] for s in buttons]
    keyboard = telegram.ReplyKeyboardMarkup(
        button_list, resize_keyboard=True, one_time_keyboard=True
    )
    await reply(update, DEL_PARTICIPANTS_CONFIRMATION_MESSAGE, keyboard)
    return DEL_PARTICIPANTS_CONFIRMATION


async def del_participants_confirmation(update: Update,
                                        context: ContextTypes.DEFAULT_TYPE):
    """Удаляет всех участников из таблицы participants."""
    answer = update.message.text.lower()
    if answer in ('lf', 'да', 'yes', '+'):
        await database_del_participants()
        await reply(update, DEL_SUCCESS.format(table='participants'))
        logger.warning(DEL.format(table='participants'))
        return ConversationHandler.END
    await reply(update, DEL_CANCEL)
    return ConversationHandler.END


if __name__ == '__main__':

    if not check_tokens(TELEGRAM_TOKEN, ADMIN_KEY, LOG_CHAT_ID):
        logger.critical(NO_TOKEN)
        sys.exit(1)
    try:
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    except telegram.error.InvalidToken as err:
        logger.critical(INVALID_TOKEN.format(error=err))
        raise
    except telegram.error.TelegramError as err:
        logger.critical(AUTHORIZATION_ERROR.format(error=err))
        raise

    start_handler = CommandHandler('start', start)
    participants_handler = CommandHandler('participants', participants)
    points_handler = CommandHandler('points', points)
    overall_results = CommandHandler('overall_results', overall_results)
    go_handler = ConversationHandler(
        entry_points=[CommandHandler('go', go)],
        states={
            GO_FINISH: [MessageHandler(
                filters.LOCATION, go_finish
            )],
            GO_TASK: [MessageHandler(
                filters.PHOTO, go_task
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    register_handler = ConversationHandler(
        entry_points=[CommandHandler('register', register)],
        states={
            GET_SEX: [MessageHandler(filters.TEXT, register_get_sex)],
            GET_TYPE: [MessageHandler(filters.TEXT, register_get_type)],
            ADD_PARTICIPANT: [MessageHandler(
                filters.TEXT, register_add_participant
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    start_race_handler = ConversationHandler(
        entry_points=[CommandHandler('start_race', start_race)],
        states={
            START_RACE_LOCATION: [MessageHandler(
                filters.LOCATION, start_race_location
            )],
            START_RACE_PHOTO: [MessageHandler(
                filters.PHOTO, start_race_photo
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    admin_handler = ConversationHandler(
        entry_points=[CommandHandler('admin', admin)],
        states={
            ADMIN_PASS_KEY: [MessageHandler(
                filters.TEXT, admin_key_verification
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    add_point_handler = ConversationHandler(
        entry_points=[CommandHandler('add_point', add_point)],
        states={
            ADD_COORDINATES: [MessageHandler(
                filters.TEXT, add_coordinates,
            )],
            ADD_TASK: [MessageHandler(
                filters.TEXT, add_task,
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    results_handler = ConversationHandler(
        entry_points=[CommandHandler('results', results)],
        states={
            RESULTS_SPECIFIC: [MessageHandler(
                filters.TEXT, results_specific,
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    del_points_handler = ConversationHandler(
        entry_points=[CommandHandler('del_points', del_points)],
        states={
            DELETE_POINTS: [MessageHandler(
                filters.TEXT, del_points_all_or_some
            )],
            DELETE_SPECIFIC_POINTS: [MessageHandler(
                filters.TEXT, del_specific_points
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    del_participants_handler = ConversationHandler(
        entry_points=[CommandHandler('del_participants', del_participants)],
        states={
            DEL_PARTICIPANTS_CONFIRMATION: [MessageHandler(
                filters.TEXT,
                del_participants_confirmation,
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    del_results_handler = ConversationHandler(
        entry_points=[CommandHandler('del_results', del_results)],
        states={
            DEL_RES_PROCEDURE_CONFIRMATION: [MessageHandler(
                filters.TEXT,
                del_results_confirmation,
            )]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(start_handler)
    application.add_handler(register_handler)
    application.add_handler(start_race_handler)
    application.add_handler(go_handler)
    application.add_handler(admin_handler)
    application.add_handler(add_point_handler)
    application.add_handler(participants_handler)
    application.add_handler(points_handler)
    application.add_handler(results_handler)
    application.add_handler(overall_results)
    application.add_handler(del_results_handler)
    application.add_handler(del_points_handler)
    application.add_handler(del_participants_handler)

    try:
        application.run_polling()
        logger.info(BOT_START_SUCCESS)
    except telegram.error.TelegramError as err:
        logger.critical(POLLING_ERROR.format(error=err))
        raise
