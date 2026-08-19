"""
Обработка сообщений: пинги, reply на бота, обращение по имени.
Интеграция с системой триггеров для обработки команд в тексте.
"""

from __future__ import annotations

import random

import discord

from bot_instance import bot
from config import env
from logging_setup import log
from src import texts
from src.db.history import save_message_to_db
from src.services.llm_client import ask_ai
from src.services.triggers import match_trigger


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
        - триггерные команды (нарисуй, найди арт, root#)
        """
        content = message.content
        user_name = message.author.display_name
        user_id = message.author.id

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

                    # Проверяем триггеры перед отправкой в LLM
                    trigger = match_trigger(
                        request, user_id, env.owner_id, env.co_owner_id
                    )
                    if trigger:
                        await Handlers._handle_trigger(trigger, message, request)
                        return

                    # Запрос к ИИ
                    async with message.channel.typing():
                        response = await ask_ai(message.author.id, user_name, request)
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

            # Проверяем триггеры перед отправкой в LLM
            trigger = match_trigger(request, user_id, env.owner_id, env.co_owner_id)
            if trigger:
                await Handlers._handle_trigger(trigger, message, request)
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

                # Проверяем триггеры перед отправкой в LLM
                trigger = match_trigger(request, user_id, env.owner_id, env.co_owner_id)
                if trigger:
                    await Handlers._handle_trigger(trigger, message, request)
                    return

                async with message.channel.typing():
                    response = await ask_ai(message.author.id, user_name, request)
                    await message.reply(response)
                    log.info(f"Ответ на сообщение {message.id} отправлен")
                return

    @staticmethod
    async def _handle_trigger(
        trigger, message: discord.Message, original_text: str
    ) -> None:
        """
        Обрабатывает сработавший триггер.

        Args:
            trigger: Объект Trigger с данными о сработавшем триггере
            message: Исходное сообщение Discord
            original_text: Оригинальный текст сообщения
        """
        user_id = message.author.id
        user_name = message.author.display_name

        # 1. Административная команда отклонена (нет прав)
        if trigger.action == "admin_denied":
            await message.reply(
                "Извините, но административные функции доступны только хозяину!"
            )
            return

        # 2. Административная команда (root#)
        if trigger.action == "admin":
            command = trigger.admin_command
            if command == "restart":
                await message.reply(
                    "⚙️ Команда перезагрузки принята. (Заглушка: функционал в разработке)"
                )
            elif command == "delete":
                await message.reply(
                    "🗑️ Команда удаления принята. (Заглушка: функционал в разработке)"
                )
            else:
                await message.reply(f"Неизвестная админ-команда: {command}")
            return

        # 3. Генерация изображения
        if trigger.action == "generate":
            from src.services.image_gen import generate_image_direct

            prompt = trigger.payload
            log.info(f"Триггер генерации: {prompt}")

            # Сохраняем в БД
            await save_message_to_db(
                user_id=user_id,
                username=user_name,
                user_message=original_text,
                bot_response="Меня попросили нарисовать картинку и я сделал это.",
            )

            # Генерируем и отправляем изображение
            try:
                async with message.channel.typing():
                    file = await generate_image_direct(prompt)
                    if file:
                        await message.reply(file=file)
                    else:
                        await message.reply("❌ Не удалось сгенерировать изображение.")
            except Exception as e:
                log.error(f"Ошибка генерации изображения: {e}")
                await message.reply(f"❌ Произошла ошибка при генерации: {str(e)}")
            return

        # 4. Поиск арта
        if trigger.action == "search":
            from src.services.art_search import search_art_direct

            query = trigger.payload
            log.info(f"Триггер поиска арта: {query}")

            # Сохраняем в БД
            await save_message_to_db(
                user_id=user_id,
                username=user_name,
                user_message=original_text,
                bot_response="Меня попросили найти картинку, я сделал это и отдал.",
            )

            # Ищем и отправляем арт
            try:
                async with message.channel.typing():
                    embed = await search_art_direct(query)
                    if embed:
                        await message.reply(embed=embed)
                    else:
                        await message.reply("❌ Ничего не найдено или произошла ошибка.")
            except Exception as e:
                log.error(f"Ошибка поиска арта: {e}")
                await message.reply(f"❌ Произошла ошибка при поиске: {str(e)}")
            return


handlers = Handlers()
