# Стартовое сообщение с документацией
START_MESSAGE = (
    'Это бот, призванный помочь при проведении гонок в форме аллейкэта.\n\n'
    '<b>Основные команды:</b>\n\n'
    '/start - документация со списком команд\n'
    '/register - регистрация для участия в гонке\n'
    '/start_race - получение инструкции и старт гонки\n'
    '/go - получение и прохождение контрольных точек\n\n'
    '<b>Команды для организаторов:</b>\n\n'
    '/admin - получение прав администратора\n'
    '/participants - зарегистрировавшиеся участники\n'
    '/points - список контрольных точек\n'
    '/results - список с результатами прохождения контрольных точек '
    'участников\n'
    '/overall_results - список с финальным временем прошедших гонку\n\n'
    '<b>Управление точками и участниками (для организаторов):</b>\n\n'
    '/add_point - добавление контрольной точки\n'
    '/del_points - удаление нескольких или всех точек\n'
    '/del_participants - удаление всех участников (кроме админов)\n'
    '/del_results - удаление записей всех результатов'
)

# Ограничение доступа
NOT_REGISTERED = (
    'Это может сделать только зарегистрированный пользователь.\n'
    'Зарегистрируйтесь при помощи /register'
)
NOT_RACE_STARTED = (
    'Прежде, чем получить контрольную точку для прохождения, '
    'начните гонку командой /start_race.'
)
NOT_ADMIN = 'Только админ может выполнить это действие.'

# Регистрация участника
GET_SEX, GET_TYPE, ADD_PARTICIPANT = range(3)
REGISTER_MESSAGE = 'Привет! Для регистрации на гонку укажи свои ФИО.'
REGISTER_SEX_MESSAGE = 'Укажи свой пол: М или Ж.'
REGISTER_SEX_BUTTONS = ['М', 'Ж']
REGISTER_TYPE_MESSAGE = (
    'Укажи свой тип велосипеда: Fix, Singlespeed, Multispeed'
)
REGISTER_TYPE_BUTTONS = ['Fix', 'Singlespeed', 'Multispeed', 'Другой']
REGISTER_POSITION_MESSAGE = (
    'Вы зарегистрированы на участие в гонке. '
    'Твой номер участника гонки: {number}\n'
    'Для прохождения контрольных точек выполните команду '
    '/start_race и следуйте инструкциям.'
)

# Функционал для админа
ADMIN_PASS_KEY = 1
ADMIN_MESSAGE = (
    'Для того, чтобы получить права на добавление, редактирование и '
    'удаление гонок, введи секретный ключ.'
)
ADMIN_VALID_KEY_MESSAGE = 'Права доступа предоставлены.'
ALREADY_ADMIN = 'Вы уже являетесь администратором.'
ADMIN_INVALID_KEY_MESSAGE = 'Неверный ключ доступа.'
ADMIN_BUTTONS = [
    '/participants', '/points', '/results',
    '/add_point', '/del_points', '/del_participants'
]

ADD_COORDINATES, ADD_TASK = range(2)
POINT_MESSAGE = (
    'Введите координаты точки через запятую в следующем '
    'формате (по примеру): 55.796343, 49.108606'
)
COORDINATES_MESSAGE = (
    'Координаты добавлены.\n'
    'Укажите текст задания, необходимого к выполнению по достижении '
    'указанных координат.'
)

# Прохождение точки
GO_FINISH, GO_TASK = range(2)
GO_MESSAGE = (
    'Контрольная точка для прохождения: \n\n'
    'ID: {id} | '
    'Coordinates: <code>{coordinates}</code> | '
    'Task: {task}\n\n'
    'После прохождения точки '
    'пришлите свою геолокацию в этот чат (включите геолокацию на телефоне), '
    'не вызывая никаких других команд. '
)
GO_SUCCESS_MESSAGE = (
    'Поздравляю! Контрольная точка пройдена, выполнение задания '
    'зафиксировано. Проверьте на наличие следующих контрольных точек '
    'командой /go'
)
GO_FINISH_MESSAGE = (
    'Локация зафиксирована! Пришлите также '
    'в чат фотографию с выполненным заданием, '
    'не вызывая никаких других команд.'
)
GO_ALL_SUCCESS = (
    'Поздравляю! Ты прошел все контрольные точки за {hours} часов '
    '{minutes} минут {seconds} секунд.'
)
GO_NO_POINTS = (
    'Кажется, контрольных точек нет. '
    'Перезапустите команду /start_race, пройдите процедуру старта'
    ' и снова пропишите команду /go. '
    'Если это сообщение появится вновь - значит, организаторы еще не добавили '
    'контрольные точки'
)

# Старт гонки
START_RACE_LOCATION, START_RACE_PHOTO = range(2)
START_RACE_LOCATION_MESSAGE = (
    'Отправьте геолокацию, находясь на стартовой точке. '
    'Кнопка работает только при включенном GPS на телефоне.'
)
START_RACE_PHOTO_MESSAGE = (
    'Отправьте селфи для идентификации личности участника гонок.'
)
START_RACE_MESSAGE = (
    'Поздравляю! Ты зарегистрирован и можешь начать участвовать в гонках. '
    'Всего предполагается {amount} контрольных точек для прохождения. '
    'После прохождения каждой из контрольных точек тебе будет '
    'необходимо отправить геолокацию и фотографию '
    'с успешно выполненным заданием. Это будет проверяться '
    'организаторами. Победит тот, кто пройдет все контрольные точки и '
    'выполнит все задания за кратчайший промежуток времени.\n\n'
    'Если ознакомился и готов начать - отправь команду /go.\n'
    'Если передумал участвовать или вызвал команду по ошибке - нажми /stop.'
)

# Результаты
RESULTS_SPECIFIC = 1
RESULT_MESSAGE = (
    'Введите ID участника, чтобы посмотреть результаты определенного '
    'участника или любой символ, чтобы увидеть все результаты'
)
NO_RESULTS = 'Записей результатов участника с таким ID нет.'

# Удаление
DELETE_POINTS, DELETE_SPECIFIC_POINTS = range(2)
DEL_PARTICIPANTS_CONFIRMATION = 1
DEL_RES_PROCEDURE_CONFIRMATION = 1
DEL_SUCCESS = 'Удалены записи из таблицы: {table}. Таблица изменена.'
DEL_POINTS_MESSAGE = 'Удаляем все контрольные точки или только некоторые ?'
DEL_PARTICIPANTS_CONFIRMATION_MESSAGE = (
    'Вы уверены, что хотите удалить всех участников? Данная команда '
    'безвозвратно удалит всех участников из базы данных кроме администраторов.'
)
DEL_RESULTS_CONFIRMATION = (
    'Вы уверены, что хотите удалить все результаты? Данная команда '
    'безвозвратно удалит результаты всех участников из базы данных.'
)
DEL_CANCEL = 'Удаление отменено.'

# Сообщения для логов
START_RACE_LOCATION_LOG = (
    'Локация участника {user_id}, {username}, на точке старта '
)
START_RACE_PHOTO_LOG = (
    'Селфи участника {user_id}, {username}, на точке старта:'
)
GO_LOCATION_LOG = (
    'Локация участника {user_id}, {username}, прошедшего точку\n'
    '{point}'
)
GO_PHOTO_LOG = (
    'Фотография участника {user_id}, {username}, выполнившего '
    'задание следующей контрольной точки:\n'
    '{point}'
)
INVALID_TOKEN = 'Неверный токен Telegram: {error}'
AUTHORIZATION_ERROR = 'Ошибка при авторизации Telegram-бота: {error}'
POLLING_ERROR = 'Ошибка Application при старте поллинга: {error}'
SEND_MESSAGE_ERROR = (
    'Ошибка Telegram API при отправке сообщения участнику: {error}'
)
BOT_START_SUCCESS = 'Бот успешно запущен!'
NO_TOKEN = 'Отсутствует один из двух или оба токена'
NOT_DATABASE = 'Ошибка при работе с базой данных: {error}'
PARTICIPANT_REGISTERED = 'Зарегистрирован новый участник {participant}.'
PARTICIPANT_STARTED_RACE = 'Участник с participant id {id} начал гонку.'
PARTICIPANT_SENT_LOCATION = (
    'Участник {user_id}, {username} отправил локацию. '
    'Зафикисировано в чате логов'
)
PARTICIPANT_SENT_PHOTO = (
    'Участник {user_id}, {username} отправил фото. '
    'Зафикисировано в чате логов'
)
PARTICIPANT_FINISHED_RACE = (
    'Участник c participant_id {participant_id} завершил гонку '
    'за {hours} часов {minutes} минут {seconds} секунд.'
)
REPLY_TELEGRAM_API_ERROR = (
    'Сообщение не отправлено. Ошибка при работе с API Telegram: {error}'
)
NEW_ADMIN = 'Пользователь {participant} получил права администратора.'
NEW_POINT = 'Добавлена новая контрольная точка с координатами {coordinates}'
DEL = 'Удалены записи из таблицы {table}'
