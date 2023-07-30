def check_tokens(telegram_token: str,
                 admin_key: str,
                 log_chat_id: str) -> bool:
    """Проверка наличия токенов."""
    if not any([telegram_token, admin_key, log_chat_id]):
        return False
    return True


async def count_time(fin_time: int) -> tuple[int, int, int]:
    """Переводит unix-time в часы, минуты и секунды."""
    hours = fin_time // 3600
    remaining_seconds = fin_time % 3600
    minutes = remaining_seconds // 60
    seconds = remaining_seconds % 60
    return hours, minutes, seconds
