"""
Слэш-команда генерации изображений: /ген.
"""

from __future__ import annotations

import io

import discord
from discord import app_commands
from discord.ext import commands

from logging_setup import log
from src.services.image_gen import generate
from src.utils import have_nsfw


# Промпт по умолчанию (когда пользователь ничего не указал)
_DEFAULT_PROMPT = (
    "solo, cute, fluffy, black melanistic fur, anthro, furry, "
    "wolf-fox hybrid, big eyes, orange sclera, big fluffy tail, "
    "orange tip tail, three ears, high quality, kawaii style, "
    "beautiful background"
)


def register(bot_instance: commands.Bot) -> None:
    """Регистрирует команды этого модуля."""

    @bot_instance.tree.command(name="ген", description="Сгенерировать картинку с Экспи")
    @app_commands.describe(prompt="Описание того, что нарисовать")
    async def cmd_generate(
        interaction: discord.Interaction, prompt: str = None
    ) -> None:
        if not prompt:
            prompt = _DEFAULT_PROMPT

        is_nsfw = have_nsfw(prompt)

        # NSFW только в age-restricted каналах
        if is_nsfw:
            if not interaction.channel.is_nsfw():
                await interaction.response.send_message(
                    "\\*поджимает уши\\* NSFW контент доступен только "
                    "в каналах с возрастным ограничением",
                    ephemeral=True,
                )
                return

        await interaction.response.defer()

        try:
            image_data = await generate(prompt)
            if not image_data:
                await interaction.followup.send(
                    "\\*прижимает уши\\* Что-то пошло не так... Попробуй позже!"
                )
                return

            file = discord.File(
                fp=io.BytesIO(image_data),
                filename="expie_generated.png",
            )
            display_prompt = prompt if len(prompt) < 300 else f"{prompt[:300]}..."
            await interaction.followup.send(
                content=f"\\*виляет хвостом\\* Есть! По запросу: `{display_prompt}`",
                file=file,
            )
        except Exception as e:
            log.exception("Ошибка при генерации изображения")
            await interaction.followup.send(
                f'\\*вздрагивает\\* Ой, что-то сломалось. Надо спросить у создателя, '
                f'что значит "{str(e)[:200]}"...'
            )
