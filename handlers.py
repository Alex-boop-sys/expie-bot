import discord
import random
from config import EXPIE_ALIASES, IMAGE_RESPONSES
from api_client import ask_ai


async def register_handlers(bot):
    """Регистрация обработчиков сообщений."""

    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return

        user_name = message.author.display_name
        content_lower = message.content.lower()

        # === ФИЛЬТР: вложения (картинки, гифки, видео, файлы) ===
        if message.attachments:
            if bot.user in message.mentions or message.channel.name == "чат-с-экспи":
                await message.reply(random.choice(IMAGE_RESPONSES))
            return

        # === ФИЛЬТР: мусорные сообщения ≤3 символов (для канала без упоминаний) ===
        stripped = message.content.strip()
        if len(stripped) <= 3 and stripped:
            if message.channel.name == "чат-с-экспи":
                await message.reply(stripped)
            return

        # === @Экспи / @Expie пинги ===
        if bot.user in message.mentions:
            clean_content = message.content
            for mention in message.mentions:
                clean_content = clean_content.replace(f'<@{mention.id}>', '')
                clean_content = clean_content.replace(f'<@!{mention.id}>', '')
            clean_content = clean_content.strip()

            # Пустой пинг
            if not clean_content:
                await message.reply("*виляет хвостом* Привет-привет! Я тут! Чего хотел, бро? 🦊")
                return

            # ФИЛЬТР: мусор после очистки пинга
            if len(clean_content) <= 3:
                await message.reply(clean_content)
                return

            async with message.channel.typing():
                response = await ask_ai(message.author.id, user_name, clean_content)
                await message.reply(response)
            return

        # === Текстовые упоминания @Экспи / @Expie ===
        for alias in EXPIE_ALIASES:
            if f"@{alias}" in content_lower:
                clean_content = message.content
                for a in EXPIE_ALIASES:
                    clean_content = clean_content.replace(f"@{a}", "").replace(f"@{a.capitalize()}", "")
                clean_content = clean_content.strip()

                # Пустое упоминание
                if not clean_content:
                    await message.reply("*приподнимается на задние лапы* Я тут! Что случилось? 👀")
                    return

                # ФИЛЬТР: мусор после очистки @Экспи
                if len(clean_content) <= 3:
                    await message.reply(clean_content)
                    return

                async with message.channel.typing():
                    response = await ask_ai(message.author.id, user_name, clean_content)
                    await message.reply(response)
                return

        # === Автоответ в канале #чат-с-экспи ===
        if message.channel.name == "чат-с-экспи":
            async with message.channel.typing():
                response = await ask_ai(message.author.id, user_name, message.content)
                await message.reply(response)
            return

        await bot.process_commands(message)
