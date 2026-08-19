"""
Модуль подключения к SQLite базе данных.
Использует aiosqlite для асинхронной работы.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import aiosqlite

from config import ROOT_DIR
from logging_setup import log

# Путь к базе данных
DB_PATH: str = Path(ROOT_DIR) / "expie_bot.db"

# Глобальное подключение (ленивая инициализация)
_db: aiosqlite.Database | None = None
_db_lock: asyncio.Lock = asyncio.Lock()


async def get_connection() -> aiosqlite.Database:
    """
    Получает или создаёт подключение к базе данных.
    Использует ленивую инициализацию и lock для потокобезопасности.
    """
    global _db

    if _db is None:
        async with _db_lock:
            # Двойная проверка после получения lock
            if _db is None:
                _db = await aiosqlite.connect(DB_PATH)
                # Включаем WAL режим для лучшей производительности
                await _db.execute("PRAGMA journal_mode=WAL")
                await _db.execute("PRAGMA synchronous=NORMAL")
                await _db.commit()
                log.type("DB").info(f"Подключение к базе данных: {DB_PATH}")

    return _db


async def close_connection() -> None:
    """Закрывает подключение к базе данных."""
    global _db

    if _db is not None:
        async with _db_lock:
            if _db is not None:
                await _db.close()
                _db = None
                log.type("DB").info("Подключение к базе данных закрыто")


async def init_db() -> None:
    """
    Инициализирует структуру базы данных.
    Создаёт таблицы, если они не существуют.
    """
    db = await get_connection()

    # Таблица истории диалогов
    await db.execute("""
        CREATE TABLE IF NOT EXISTS conversation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Индекс для быстрого поиска по пользователю
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_conversation_user_id 
        ON conversation_history(user_id)
    """)

    # Таблица фактов о пользователях
    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            facts TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица настроек серверов
    await db.execute("""
        CREATE TABLE IF NOT EXISTS guild_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            guild_id INTEGER NOT NULL UNIQUE,
            settings TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Таблица настроек пользователей
    await db.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE,
            settings TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    await db.commit()
    log.type("DB").info("База данных инициализирована")


async def execute_query(query: str, params: tuple = ()) -> aiosqlite.Cursor:
    """
    Выполняет SQL-запрос с параметрами.
    Автоматически получает подключение.
    """
    db = await get_connection()
    cursor = await db.execute(query, params)
    await db.commit()
    return cursor


async def fetch_all(query: str, params: tuple = ()) -> list[tuple]:
    """
    Выполняет SELECT-запрос и возвращает все результаты.
    """
    db = await get_connection()
    async with db.execute(query, params) as cursor:
        return await cursor.fetchall()


async def fetch_one(query: str, params: tuple = ()) -> tuple | None:
    """
    Выполняет SELECT-запрос и возвращает первую строку результата.
    """
    db = await get_connection()
    async with db.execute(query, params) as cursor:
        return await cursor.fetchone()
