"""
Точка входа: проверка токенов, регистрация команд и событий, запуск бота.
"""

from __future__ import annotations

import asyncio

from logging_setup import log
from src.commands import register_all
from src.db import close_connection, init_db
from src.events import register_handlers, run_bot
from src.services.llm_client import init_llm_client
from src.utils import check_tokens


async def main() -> None:
    """Собирает приложение и запускает бота."""
    # Инициализация базы данных
    await init_db()
    log.info("База данных инициализирована")

    # Инициализация клиента LLM (история диалогов)
    await init_llm_client()

    # Регистрация команд
    register_all()  # слэш-команды

    # Запуск бота
    bot_task = asyncio.create_task(run_bot())
    try:
        await bot_task
    except asyncio.CancelledError:
        log.info("Завершение работы")
    except Exception:
        log.exception("Ошибка запуска")
    finally:
        # Закрываем подключение к базе данных при завершении
        await close_connection()
        log.info("Подключение к базе данных закрыто")


if __name__ == "__main__":
    check_tokens()
    register_handlers()  # on_ready, on_message
    asyncio.run(main())
