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
    'участников\n\n'
    '<b>Управление точками и участниками (для организаторов):</b>\n\n'
    '/add_point - добавление контрольной точки\n'
    '/del_points - удаление нескольких или всех точек\n'
    '/del_participants - удаление всех участников (кроме админов)\n'
    '/del_results - удаление записей всех результатов'
)

NOT_REGISTERED = (
    'Это может сделать только зарегистрированный пользователь.\n'
    'Зарегистрируйтесь при помощи /register'
)
NOT_RACE_STARTED = (
    'Прежде, чем получить контрольную точку для прохождения, '
    'начните гонку командой /race_start.'
)
NOT_ADMIN = 'Только админ может выполнить это действие.'
NOT_DATABASE = 'Ошибка при работе с базой данных: {error}'

ADD_PARTICIPANT = 1
REGISTER_MESSAGE = 'Привет! Для регистрации на гонку укажи свои ФИО.'
REGISTER_POSITION_MESSAGE = (
    'Вы зарегистрированы на участие в гонке. '
    'Порядковый номер участника гонки: {number}\n'
    'Для прохождения контрольных точек выполните команду '
    '/start_race и следуйте инструкциям.'
)

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

GO_FINISH, GO_TASK = range(2)
START_RACE_MESSAGE = (
    'Привет! Ты зарегистрирован и можешь начать участвовать в гонках. '
    'Всего предполагается {amount} контрольных точек для прохождения. '
    'Перед началом прохождения каждой из контрольных точек тебе будет '
    'необходимо отправить геолокацию, а после прохождения контрольной точки - '
    'фотографию с успешно выполненным заданием. Это будет проверяться '
    'организаторами. Победит тот, кто пройдет все контрольные точки и '
    'выполнит все задания за кратчайший промежуток времени.\n\n'
    'Если ознакомился и готов начать - отправь команду /go.\n'
    'Если передумал участвовать или вызвал команду по ошибке - нажми /stop.'
)
GO_MESSAGE = (
    'Контрольная точка для прохождения: \n\n'
    'ID: {id} | '
    'Coordinates: <code>{coordinates}</code> | '
    'Task: {task}\n\n'
    'Прежде, чем приступить к прохождению контрольной точки, '
    'пришлите свою геолокацию в этот чат (включите геолокацию на телефоне). '
)
GO_SUCCESS_MESSAGE = (
    'Поздравляю! Контрольная точка пройдена, выполнение задания '
    'зафиксировано. Проверьте на наличие следующих контрольных точек '
    'командой /go'
)
GO_FINISH_MESSAGE = (
    'Локация зафиксирована! После прохождения контрольной точки пришлите '
    'в чат фотографию с выполненным заданием, не вызывая никаких других команд'
)
GO_ALL_SUCCESS = (
    'Поздравляю! Ты прошел все контрольные точки за {hours} часов '
    '{minutes} минут {seconds} секунд.'
)

RESULTS_SPECIFIC = 1
RESULT_MESSAGE = (
    'Введите ID участника, чтобы посмотреть результаты определенного '
    'участника или любой символ, чтобы увидеть все результаты'
)

DEL_ALL_POINTS, DEL_SPECIFIC_POINT = range(2)
DEL_PARTICIPANTS_CONFIRMATION = 1
DEL_RES_PROCEDURE_CONFIRMATION = 1
DEL_SUCCESS = 'Удалено записей: {rows_count}. Таблица изменена.'
DEL_POINTS_MESSAGE = 'Удаляем все контрольные точки или только некоторые ?'
DEL_PARTICIPANTS_PROCEDURE_CONFIRMATION = (
    'Вы уверены, что хотите удалить всех участников? Данная команда '
    'безвозвратно удалит всех участников из базы данных кроме администраторов.'
)
DEL_RESULTS_CONFIRMATION = (
    'Вы уверены, что хотите удалить все результаты? Данная команда '
    'безвозвратно удалит результаты всех участников из базы данных.'
)
DEL_CANCEL = 'Удаление отменено.'

# Сообщения для логов
NO_TOKEN = 'Отсутствует один из двух или оба токена'
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

# чат с логами (локации и фото) в телеграмм
LOG_CHAT_ID = -1001876751051