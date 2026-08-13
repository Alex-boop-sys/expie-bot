import random
import discord
from Cogs.api_client import ask_ai
from Cogs.dicts import dicts
from config import log, bot

# Хендлеры. Осуществляют обработку событий происходящих в боте
class Handlers:
    async def on_msg(self, message):
        # Игнорируем свои сообщения (чтобы не отвечать самому себе)
        if message.author == bot.user:
            return
        
        # Сначала обрабатываем команды (чтобы !команды работали даже внутри reply)
        await bot.process_commands(message)
        await self.check_ping(message)

    # Обработка упоминаний и reply
    @staticmethod
    async def check_ping(message):
        content = message.content
        user_name = message.author.display_name

        # === 1. ОТВЕТ НА СООБЩЕНИЕ БОТА (Reply / "Ответить") ===
        # Если пользователь нажал "Ответить" на сообщение бота — message.reference не None
        if message.reference and message.reference.message_id:
            try:
                # Получаем сообщение, на которое ответили
                referenced = await message.channel.fetch_message(message.reference.message_id)
                
                # Проверяем, что автор того сообщения — сам бот
                if referenced.author == bot.user:
                    request = content.strip()
                    
                    # Пустой reply, но с картинкой/файлом
                    if not request and message.attachments:
                        await message.reply(random.choice(dicts.image_responses), mention_author=False)
                        return
                    
                    # Совсем пустой reply
                    if not request:
                        await message.reply(random.choice(dicts.ping_an), mention_author=False)
                        return
                    
                    # Отправляем текст в AI и отвечаем
                    async with message.channel.typing():
                        response = await ask_ai(message.author.id, user_name, request)
                        await message.reply(response)
                        log.info(f"Ответ на reply {message.id} отправлен")
                    return
                    
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                # Сообщение удалено или недоступно — пропускаем, пойдём дальше
                pass

        # === 2. ПУСТОЙ ПИНГ (только @Экспи без текста) ===
        is_ping = content.strip() == f"<@{bot.user.id}>"
        is_name = content.lower().strip() in dicts.bot_names

        if is_ping or is_name:
            if message.attachments:
                await message.reply(random.choice(dicts.image_responses), mention_author=False)
            else:
                await message.reply(random.choice(dicts.ping_an), mention_author=False)
            return

        # === 3. ПИНГ С ТЕКСТОМ (@Экспи привет) ===
        if content.startswith(f"<@{bot.user.id}>"):
            request = content.replace(f'<@{bot.user.id}>', '').strip()
            if not request:
                await message.reply(random.choice(dicts.ping_an), mention_author=False)
                return
            async with message.channel.typing():
                response = await ask_ai(message.author.id, user_name, request)
                await message.reply(response)
                log.info(f"Ответ на сообщение {message.id} отправлен")
            return

        # === 4. ТЕКСТОВОЕ УПОМИНАНИЕ (Экспи привет) ===
        for name in dicts.bot_names:
            if content.lower().startswith(name):
                request = content[len(name):].strip()
                if not request:
                    await message.reply(random.choice(dicts.ping_an), mention_author=False)
                    return
                async with message.channel.typing():
                    response = await ask_ai(message.author.id, user_name, request)
                    await message.reply(response)
                    log.info(f"Ответ на сообщение {message.id} отправлен")
                return


handlers = Handlers()