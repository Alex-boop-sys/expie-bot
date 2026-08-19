"""
Слэш-команды ИИ: /спросить, /забыть.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from src.services.llm_client import ask_ai, clear_history


def register(bot_instance: commands.Bot) -> None:
    """Регистрирует команды этого модуля."""

    @bot_instance.tree.command(name="спросить", description="Отправить вопрос Экспи")
    @app_commands.describe(question="Ваш вопрос для Экспи")
    async def ask(interaction: discord.Interaction, question: str) -> None:
        """
        Задаёт вопрос LLM.
        Багфикс §4.2: больше не делаем response.replace(user_name, mention) —
        это ломало слова. Просто отправляем ответ как есть.
        """
        user_name = interaction.user.display_name
        await interaction.response.defer()
        response = await ask_ai(interaction.user.id, user_name, question)
        # Отправляем ответ без опасной подмены имени на mention
        await interaction.followup.send(response)

    @bot_instance.tree.command(name="забыть", description="Забыть контекст")
    async def forget(interaction: discord.Interaction) -> None:
        """Очищает историю диалога текущего пользователя."""
        user_id = interaction.user.id
        # clear_history теперь async функция
        if await clear_history(user_id):
            await interaction.response.send_message(
                "\\*Моргает\\* Э-э-э... похоже, теперь я ничего о тебе не помню."
            )
        else:
            await interaction.response.send_message(
                "\\*Наклоняет голову\\* А мы с тобой уже разговаривали?"
            )
