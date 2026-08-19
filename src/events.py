"""
События бота: on_ready, on_message, запуск.
Бывший bot.py.
"""

from __future__ import annotations

import discord

from bot_instance import bot
from logging_setup import log
from src.handlers import handlers


def register_handlers() -> None:
    """Регистрирует обработчики событий на экземпляре бота."""

    @bot.event
    async def on_message(message: discord.Message) -> None:
        await handlers.on_msg(message)

    @bot.event
    async def on_ready() -> None:
        log.info(f"Бот запущен ({bot.user})")
        try:
            synced = await bot.tree.sync()
            log.info(f"Синхронизировано {len(synced)} слэш-команд")
        except Exception as e:
            log.error(f"Ошибка синхронизации слэш-команд: {e}")

        # Presence
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Общаюсь с друзьями 🦊",
            )
        )


async def run_bot() -> None:
    """Запускает бота (использует токен из env)."""
    from config import env

    await bot.start(env.discord_token)
