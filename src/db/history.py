"""
Модуль для работы с историей диалогов в SQLite.
Заменяет хранение истории в памяти (dict) на персистентное хранилище.
"""

from __future__ import annotations

from typing import Any

from config import MAX_HISTORY, MAX_HISTORY_DB
from logging_setup import log

from . import connection as db


async def init_history_table() -> None:
    """
    Инициализирует таблицу истории диалогов.
    Вызывается один раз при старте бота.
    """
    await db.init_db()
    log.type("DB.HISTORY").info("Таблица истории диалогов готова")


async def add_message(user_id: int, role: str, content: str) -> None:
    """
    Добавляет сообщение в историю диалога пользователя.

    Args:
        user_id: ID пользователя Discord
        role: Роль сообщения ('user' или 'assistant')
        content: Содержание сообщения
    """
    await db.execute_query(
        "INSERT INTO conversation_history (user_id, role, content) VALUES (?, ?, ?)",
        (user_id, role, content),
    )

    # Очищаем старые сообщения, если их больше MAX_HISTORY_DB
    await db.execute_query(
        """
        DELETE FROM conversation_history 
        WHERE user_id = ? AND id NOT IN (
            SELECT id FROM conversation_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        )
        """,
        (user_id, user_id, MAX_HISTORY_DB),
    )


async def get_history(user_id: int, limit: int = MAX_HISTORY) -> list[dict[str, str]]:
    """
    Получает последние сообщения из истории диалога пользователя.

    Args:
        user_id: ID пользователя Discord
        limit: Количество последних сообщений для возврата (по умолчанию MAX_HISTORY)

    Returns:
        Список сообщений в формате [{"role": "...", "content": "..."}, ...]
    """
    rows = await db.fetch_all(
        """
        SELECT role, content FROM conversation_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
        """,
        (user_id, limit),
    )

    # Переворачиваем список, чтобы сообщения были в хронологическом порядке
    history = [{"role": row[0], "content": row[1]} for row in reversed(rows)]
    return history


async def clear_history(user_id: int) -> bool:
    """
    Очищает всю историю диалога пользователя.

    Args:
        user_id: ID пользователя Discord

    Returns:
        True, если история существовала и была очищена, False иначе
    """
    # Проверяем, есть ли история
    existing = await db.fetch_one(
        "SELECT 1 FROM conversation_history WHERE user_id = ? LIMIT 1",
        (user_id,),
    )

    if existing is None:
        return False

    await db.execute_query(
        "DELETE FROM conversation_history WHERE user_id = ?",
        (user_id,),
    )

    log.type("DB.HISTORY").info(f"История диалога пользователя {user_id} очищена")
    return True


async def get_user_conversation_count(user_id: int) -> int:
    """
    Возвращает количество сообщений в истории пользователя.

    Args:
        user_id: ID пользователя Discord

    Returns:
        Количество сообщений
    """
    result = await db.fetch_one(
        "SELECT COUNT(*) FROM conversation_history WHERE user_id = ?",
        (user_id,),
    )

    return result[0] if result else 0


async def save_conversation_batch(messages: list[dict[str, Any]], user_id: int) -> None:
    """
    Сохраняет пакет сообщений в базу данных.
    Используется для массовой записи.

    Args:
        messages: Список сообщений [{"role": "...", "content": "..."}, ...]
        user_id: ID пользователя Discord
    """
    db_conn = await db.get_connection()

    for msg in messages:
        await db_conn.execute(
            "INSERT INTO conversation_history (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, msg["role"], msg["content"]),
        )

    await db_conn.commit()

    # Очищаем старые сообщения
    await db.execute_query(
        """
        DELETE FROM conversation_history 
        WHERE user_id = ? AND id NOT IN (
            SELECT id FROM conversation_history 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        )
        """,
        (user_id, user_id, MAX_HISTORY_DB),
    )


async def save_message_to_db(
    user_id: int,
    username: str,
    user_message: str,
    bot_response: str,
) -> None:
    """
    Сохраняет пару сообщений (запрос пользователя и ответ бота) в базу данных.
    Удобная обёртка для триггерных команд.

    Args:
        user_id: ID пользователя Discord
        username: Имя пользователя (для логирования, не сохраняется в БД)
        user_message: Текст сообщения от пользователя
        bot_response: Текст ответа бота
    """
    # Сохраняем сообщение пользователя
    await add_message(user_id, "user", user_message)
    # Сохраняем ответ бота
    await add_message(user_id, "assistant", bot_response)
    log.type("DB.HISTORY").info(
        f"Сохранён диалог пользователя {username} ({user_id}): '{user_message[:30]}...'"
    )
