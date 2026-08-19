"""
Слэш-команды поиска артов: /арт (e621), /фурь (Furbooru).
Тонкие обёртки: проверки → вызов сервиса → отправка.
"""

from __future__ import annotations

import io
import random

import discord
from discord import app_commands
from discord.ext import commands

from logging_setup import log
from src import texts
from src.services.art_search import search_e621, search_furbooru
from src.utils import get_size_limit, have_nsfw


def register(bot_instance: commands.Bot) -> None:
    """Регистрирует команды этого модуля."""

    @bot_instance.tree.command(name="арт", description="Найти арт на e621")
    @app_commands.describe(query="Теги для поиска (опционально)")
    async def cmd_art(interaction: discord.Interaction, query: str = None) -> None:
        is_nsfw = query and have_nsfw(query)

        # NSFW только в age-restricted каналах
        if is_nsfw:
            if not interaction.channel.is_nsfw():
                await interaction.response.send_message(
                    "\\*поджимает уши\\* NSFW контент доступен только "
                    "в каналах с возрастным ограничением",
                    ephemeral=True,
                )
                return
            # Убираем слово nsfw из запроса (оно уже учтено)
            query = query.lower().replace("nsfw", "").strip() or None

        await interaction.response.defer()
        size_limit = get_size_limit(interaction.guild)

        try:
            result = await search_e621(
                query, is_nsfw=bool(is_nsfw), size_limit=size_limit
            )

            if result.image_bytes:
                file = discord.File(
                    fp=io.BytesIO(result.image_bytes),
                    filename=f"expie_art.{result.ext}",
                )
                await interaction.followup.send(
                    content="Вот, смотри что нашёл! \\*виляет хвостом\\*",
                    file=file,
                )
            elif result.fallback_url:
                await interaction.followup.send(
                    f"\\*виляет хвостом\\* [О, смотри что нашёл!]({result.fallback_url})\n\n"
                    f"*({result.reason})*"
                )
            else:
                reason = result.reason or "Ничего не нашёл..."
                await interaction.followup.send(f"\\*нюхает воздух\\* {reason}")

        except Exception as e:
            log.exception("Ошибка при поиске изображения (e621)")
            await interaction.followup.send(
                f"\\*вздрагивает\\* Ой, что-то сломалось. Надо спросить у создателя, "
                f'что значит "{str(e)[:200]}"...'
            )

    @bot_instance.tree.command(name="фурь", description="Найти SFW арты на Furbooru")
    @app_commands.describe(query="Теги для поиска (на английском)")
    async def cmd_fur(interaction: discord.Interaction, query: str = None) -> None:
        if not query:
            await interaction.response.send_message(
                "\\*наклоняет голову\\* Ой, а что искать-то? 🦊\n"
                "Пиши теги на **английском** через пробел.\n"
                "Пример: `cute wolf solo`"
            )
            return

        await interaction.response.defer()

        try:
            result = await search_furbooru(query)

            if result.image_bytes:
                file = discord.File(
                    fp=io.BytesIO(result.image_bytes),
                    filename=f"furbooru_art.{result.ext}",
                )
                await interaction.followup.send(
                    content=random.choice(texts.pic_comments),
                    file=file,
                )
            else:
                reason = result.reason or "Ничего не нашёл..."
                await interaction.followup.send(f"\\*нюхает воздух\\* {reason}")

        except Exception as e:
            log.exception("Ошибка при поиске на Furbooru")
            await interaction.followup.send(
                f"\\*вздрагивает\\* Что-то сломалось. Нужно спросить у создателя, "
                f"что значит `{str(e)[:100]}`...\nМожет попробуешь позже?"
            )
