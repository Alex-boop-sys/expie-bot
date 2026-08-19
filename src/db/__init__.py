"""
База данных бота.
Экспортирует основные функции для работы с БД.
"""

from .connection import (
    close_connection,
    execute_query,
    fetch_all,
    fetch_one,
    get_connection,
    init_db,
)
from .history import (
    add_message,
    clear_history,
    get_history,
    get_user_conversation_count,
    init_history_table,
    save_conversation_batch,
)

__all__ = [
    # Connection
    "get_connection",
    "close_connection",
    "init_db",
    "execute_query",
    "fetch_all",
    "fetch_one",
    # History
    "init_history_table",
    "add_message",
    "get_history",
    "clear_history",
    "get_user_conversation_count",
    "save_conversation_batch",
]
