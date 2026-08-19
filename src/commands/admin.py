"""
Заготовка админ-команд: /обновить, /рестарт, /логи.
Все команды проходят через декоратор owner_only().

Реализация — на будущее. Сейчас только структура и соглашения.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any

import discord
from discord.ext import commands

from config import env
from logging_setup import log


def owner_only() -> Callable:
    """
    Декоратор: разрешает выполнение только владельцу / со-владельцу.
    Проверка owner_id / co_owner_id в одном месте — критично для безопасности.
    """

    def decorator(
        func: Callable[..., Coroutine[Any, Any, Any]],
    ) -> Callable[..., Coroutine[Any, Any, Any]]:
        @wraps(func)
        async def wrapper(
            interaction: discord.Interaction, *args: Any, **kwargs: Any
        ) -> Any:
            allowed = {
                str(env.owner_id) if env.owner_id else None,
                str(env.co_owner_id) if env.co_owner_id else None,
            }
            if str(interaction.user.id) not in allowed:
                await interaction.response.send_message(
                    "\\*прижимает уши\\* У тебя нет прав на это...",
                    ephemeral=True,
                )
                return None
            return await func(interaction, *args, **kwargs)

        return wrapper

    return decorator


def register(bot_instance: commands.Bot) -> None:
    """
    Регистрирует админ-команды.
    Пока команды закомментированы — раскомментировать при реализации.
    """
    # Пример будущей команды:
    #
    # @bot_instance.tree.command(name="рестарт", description="Перезапустить бота")
    # @owner_only()
    # async def cmd_restart(interaction: discord.Interaction) -> None:
    #     await interaction.response.send_message("Перезапускаюсь...")
    #     # systemctl restart ... или os.execv
    #     pass
    #
    # @bot_instance.tree.command(name="логи", description="Показать последние логи")
    # @owner_only()
    # async def cmd_logs(interaction: discord.Interaction) -> None:
    #     ...
    #
    # @bot_instance.tree.command(name="обновить", description="git pull + рестарт")
    # @owner_only()
    # async def cmd_update(interaction: discord.Interaction) -> None:
    #     ...

    log.info("Админ-команды: заготовка загружена (команды пока не активны)")
