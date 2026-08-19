"""
Обработка сообщений: пинги, reply на бота, обращение по имени.
"""

from __future__ import annotations

import random

import discord

from bot_instance import bot
from logging_setup import log
from src import texts
from src.services.llm_client import ask_ai


class Handlers:
    """Обработчики событий сообщений."""

    async def on_msg(self, message: discord.Message) -> None:
        """
        Главный обработчик on_message.
        Ранний выход, если сообщение от самого бота (багфикс check_ignore).
        """
        # Багфикс §4.1: бот больше не отвечает сам себе
        if message.author == bot.user:
            return

        await bot.process_commands(message)
        await self.check_ping(message)

    @staticmethod
    async def check_ping(message: discord.Message) -> None:
        """
        Обрабатывает:
        - reply на сообщение бота
        - чистое упоминание / имя бота
        - сообщение, начинающееся с упоминания или имени
        """
        content = message.content
        user_name = message.author.display_name

        # --- Reply на сообщение бота ---
        if message.reference and message.reference.message_id:
            try:
                referenced = await message.channel.fetch_message(
                    message.reference.message_id
                )
                if referenced.author == bot.user:
                    request = content.strip()

                    # Пустой reply с картинкой
                    if not request and message.attachments:
                        await message.reply(
                            random.choice(texts.image_responses),
                            mention_author=False,
                        )
                        return

                    # Пустой reply
                    if not request:
                        await message.reply(
                            random.choice(texts.ping_an),
                            mention_author=False,
                        )
                        return

                    # Запрос к ИИ
                    async with message.channel.typing():
                        response = await ask_ai(
                            message.author.id, user_name, request
                        )
                        await message.reply(response)
                        log.info(f"Ответ на reply {message.id} отправлен")
                    return
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                pass

        # --- Чистое упоминание или имя ---
        is_ping = content.strip() == f"<@{bot.user.id}>"
        is_name = content.lower().strip() in texts.bot_names

        if is_ping or is_name:
            if message.attachments:
                await message.reply(
                    random.choice(texts.image_responses),
                    mention_author=False,
                )
            else:
                await message.reply(
                    random.choice(texts.ping_an),
                    mention_author=False,
                )
            return

        # --- Сообщение начинается с упоминания ---
        if content.startswith(f"<@{bot.user.id}>"):
            request = content.replace(f"<@{bot.user.id}>", "").strip()
            if not request:
                await message.reply(
                    random.choice(texts.ping_an),
                    mention_author=False,
                )
                return
            async with message.channel.typing():
                response = await ask_ai(message.author.id, user_name, request)
                await message.reply(response)
                log.info(f"Ответ на сообщение {message.id} отправлен")
            return

        # --- Сообщение начинается с имени бота ---
        for name in texts.bot_names:
            if content.lower().startswith(name):
                request = content[len(name) :].strip()
                if not request:
                    await message.reply(
                        random.choice(texts.ping_an),
                        mention_author=False,
                    )
                    return
                async with message.channel.typing():
                    response = await ask_ai(
                        message.author.id, user_name, request
                    )
                    await message.reply(response)
                    log.info(f"Ответ на сообщение {message.id} отправлен")
                return


handlers = Handlers()
