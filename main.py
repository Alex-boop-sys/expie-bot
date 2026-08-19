"""
Точка входа: проверка токенов, регистрация команд и событий, запуск бота.
"""

from __future__ import annotations

import asyncio

from logging_setup import log
from src.commands import register_all
from src.events import register_handlers, run_bot
from src.utils import check_tokens


async def main() -> None:
    """Собирает приложение и запускает бота."""
    register_all()  # слэш-команды
    bot_task = asyncio.create_task(run_bot())
    try:
        await bot_task
    except asyncio.CancelledError:
        log.info("Завершение работы")
    except Exception:
        log.exception("Ошибка запуска")


if __name__ == "__main__":
    check_tokens()
    register_handlers()  # on_ready, on_message
    asyncio.run(main())
