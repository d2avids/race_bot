import os
import sqlite3
import time

import aiosqlite
from modules.constants import NOT_DATABASE, PARTICIPANT_STARTED_RACE
from modules.logger import logger

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(CURRENT_DIR, '..', 'db.sqlite')


async def database_query(query: str, *args) -> aiosqlite.core.Iterable:
    """
    Запрос query к базе данных с заданными *args, логированием и обработкой
    ошибок в одном месте
    """
    logger.debug(f'database_query args: {args}')
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(query, (*args,))
            await db.commit()
            result = await cursor.fetchall()
            return result
    except aiosqlite.Error as err:
        logger.critical(NOT_DATABASE.format(error=err))
        raise


async def is_registered_or_admin(user_id: object) -> int:
    """
     Проверяет зарегистрирован ли участник, и, если да, является ли он админом.
     0 - не зарегистрирован;
     1 - зарегистрирован, но не админ;
     2 - админ.
     """
    result = await database_query(
        '''SELECT is_admin FROM main.participants '''
        '''WHERE user_id = ?''',
        user_id
    )
    if not result:
        return 0

    return 2 if result[0][0] == 1 else 1


async def database_participants() -> aiosqlite.core.Iterable:
    return await database_query('''SELECT * from participants''')


async def database_points() -> aiosqlite.core.Iterable:
    return await database_query('''SELECT * from control_points''')


async def database_results_by_id(
        participant_id: str
) -> aiosqlite.core.Iterable:
    return await database_query(
        '''SELECT * from results '''
        '''WHERE participant_id = ? '''
        '''ORDER BY control_point_id''',
        participant_id,
    )


async def database_results() -> aiosqlite.core.Iterable:
    return await database_query(
        '''SELECT * FROM results '''
        '''ORDER BY participant_id, control_point_id'''
    )


async def database_overall_results() -> aiosqlite.core.Iterable:
    return await database_query(
        '''SELECT results.participant_id, name, sex, type, '''
        '''(MAX(finish_time) - MIN(start_time)) AS final_time '''
        '''FROM results '''
        '''JOIN participants ON participants.id = results.participant_id '''
        '''GROUP BY participant_id '''
        '''HAVING COUNT(finish_time) = COUNT(results.participant_id) '''
        '''ORDER BY final_time'''
    )


async def database_del_results() -> None:
    await database_query('''DELETE from results''')


async def database_del_points() -> None:
    await database_query('''DELETE from control_points''')


async def database_del_specific_points(ids) -> aiosqlite.core.Iterable:
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(
                '''DELETE FROM control_points '''
                '''WHERE id IN ({})'''.format(','.join('?' * len(ids))),
                tuple(ids)
            )
            await db.commit()
            result = await cursor.fetchall()
            return result
    except aiosqlite.Error as err:
        logger.critical(NOT_DATABASE.format(error=err))
        raise


async def database_del_participants() -> None:
    await database_query(
        '''DELETE from main.participants '''
        '''WHERE is_admin IS NOT 1'''
    )


async def database_register(user_id: object,
                            username: object,
                            name: str,
                            sex: str,
                            bicycle_type: str) -> aiosqlite.core.Iterable:
    """
    Регистрирует участника в таблице participants, если такой записи нет.
    """
    query = '''SELECT id FROM participants WHERE user_id = ?'''
    try:
        db = await aiosqlite.connect(DATABASE_PATH)
        await db.execute(
            '''INSERT INTO participants '''
            '''(user_id, username, name, sex, type) '''
            '''VALUES (?, ?, ?, ?, ?)''',
            (user_id, username, name, sex, bicycle_type)
        )
        await db.commit()
        cursor = await db.execute(query, (user_id,))
    except aiosqlite.IntegrityError:
        db = await aiosqlite.connect(DATABASE_PATH)
        cursor = await db.execute(query, (user_id,))
    except sqlite3.Error as err:
        logger.critical(NOT_DATABASE.format(error=err))
        raise
    finally:
        number = await cursor.fetchone()
        await cursor.close()
        await db.close()

    return number[0]


async def database_start_race(user_id: object) -> int:
    await database_query(
        '''UPDATE participants SET race_started =1 WHERE user_id = ?''',
        user_id
    )
    participant_id = await database_query(
        '''SELECT id FROM participants WHERE user_id = ?''',
        user_id
    )
    control_points = await database_query(
        '''SELECT id FROM control_points'''
    )
    print(control_points)
    if control_points:
        control_points = [row[0] for row in control_points]
        start_time = int(time.time())
        for control_point in control_points:
            await database_query(
                '''INSERT OR IGNORE INTO results '''
                '''(participant_id, control_point_id, start_time) '''
                '''VALUES (?, ?, ?)''',
                participant_id[0][0], control_point, start_time
            )
    else:
        return 0
    logger.info((PARTICIPANT_STARTED_RACE.format(id=participant_id)))
    return len(control_points)


async def database_get_participant_status(user_id: object) -> tuple:
    participant_id = await database_query(
        '''SELECT id FROM participants WHERE user_id = ?''',
        user_id,
    )
    race_started = await database_query(
        '''SELECT race_started FROM participants WHERE user_id = ?''',
        user_id,
    )
    return participant_id[0][0], race_started[0][0]


async def database_get_control_point_id(participant_id: int):
    control_point_id = await database_query(
        '''SELECT control_point_id FROM results '''
        '''WHERE participant_id = ? AND finish_time IS NULL '''
        '''ORDER BY control_point_id '''
        '''LIMIT 1''',
        participant_id,
    )
    if control_point_id:
        return control_point_id[0][0]
    return None


async def database_get_control_point(control_point_id: int) -> tuple:
    control_point = await database_query(
        '''SELECT id, coordinates, task '''
        '''FROM control_points '''
        '''WHERE id = ?''',
        control_point_id
    )
    return control_point[0][0], control_point[0][1], control_point[0][2]


async def database_get_time(participant_id: int) -> tuple:
    finish_time = await database_query(
        '''SELECT finish_time FROM results '''
        '''WHERE participant_id = ? '''
        '''ORDER BY finish_time DESC '''
        '''LIMIT 1''',
        participant_id,
    )
    start_time = await database_query(
        '''SELECT start_time FROM results '''
        '''WHERE participant_id = ? '''
        '''ORDER BY start_time '''
        '''LIMIT 1''',
        participant_id,
    )
    if not any([start_time, finish_time]):
        return None, None
    return start_time[0][0], finish_time[0][0]


async def database_set_finish_time(participant_id: int,
                                   control_point_id: int,
                                   finish_time: int):
    await database_query(
        '''UPDATE results SET finish_time = ? '''
        '''WHERE participant_id = ? AND control_point_id = ?''',
        finish_time,
        participant_id,
        control_point_id,
    )


async def database_set_admin(user_id: object):
    await database_query(
        '''UPDATE main.participants '''
        '''SET is_admin = 1 '''
        '''WHERE user_id = ?''',
        user_id,
    )


async def database_set_coordinates(coordinates: int):
    await database_query(
        '''INSERT INTO control_points (coordinates)'''
        '''VALUES (?)''',
        coordinates,
    )


async def database_set_task(task: str):
    last_inserted_row = await database_query(
        '''SELECT id FROM control_points ORDER BY id DESC LIMIT 1'''
    )
    await database_query(
            '''UPDATE control_points SET task = ? WHERE id = ?''',
            task, last_inserted_row[0][0]
        )
