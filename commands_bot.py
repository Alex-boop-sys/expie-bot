import discord
import aiohttp
import io
import urllib.parse
import random
from api_client import ask_ai, clear_history


def register_commands(bot):
    """Регистрация всех команд бота."""

    @bot.command(name="Экспи")
    async def cmd_expie_ru(ctx, *, message):
        """!Экспи <сообщение>"""
        user_name = ctx.author.display_name
        async with ctx.typing():
            response = await ask_ai(ctx.author.id, user_name, message)
            await ctx.reply(response)

    @bot.command(name="Expie")
    async def cmd_expie_en(ctx, *, message):
        """!Expie <сообщение>"""
        user_name = ctx.author.display_name
        async with ctx.typing():
            response = await ask_ai(ctx.author.id, user_name, message)
            await ctx.reply(response)

    @bot.command(name="забыть")
    async def cmd_forget(ctx):
        """Clear conversation history"""
        user_id = ctx.author.id
        if clear_history(user_id):
            await ctx.reply("*моргает* Э-э-э... кто ты? Шучу-шучу! Начинаем с чистого листа, бро! 🦊")
        else:
            await ctx.reply("*наклоняет голову* А мы с тобой уже разговаривали? Ну, привет тогда! 👋")

    @bot.command(name="lore")
    async def cmd_lore(ctx, *, topic):
        """!lore <тема> — detailed lore about the world"""
        user_name = ctx.author.display_name
        prompt = f"Расскажи подробно про {topic} из мира Casualties: Unknown / Серой Планеты."
        async with ctx.typing():
            response = await ask_ai(ctx.author.id, user_name, prompt)
            await ctx.reply(response)

    @bot.command(name="арт")
    async def cmd_art(ctx, *, query=None):
        """!арт — случайный арт Экспи. !арт <теги> — поиск по e621."""

        if not query:
            search_variants = [
                "expie_(gunsawian)+-rating%3Aexplicit+",
                "casualties:_unknown+-rating%3Aexplicit+",
                "gunsawian+-rating%3Aexplicit+",
                "milky_(gunsawian)+-rating%3Aexplicit+",
                "dune_(gunsawian)+-rating%3Aexplicit+"
            ]
            tags = random.choice(search_variants).replace(" ", "_")
        else:
            tags = query.replace(" ", "_")

        async with ctx.typing():
            try:
                url = f"https://e621.net/posts.json?tags={tags}&limit=300"
                headers = {"User-Agent": "ExpieDiscordBot/1.0 (by Discord user)"}

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status != 200:
                            await ctx.reply(f"*вздрагивает* Сайт отвечает кодом {resp.status}...")
                            return

                        data = await resp.json()
                        posts = data.get("posts", [])

                        if not posts:
                            await ctx.reply("*нюхает воздух* Ничего не нашёл по этому запросу...")
                            return

                        seen_urls = set()
                        valid_posts = []
                        for p in posts:
                            file_data = p.get("file")
                            if not file_data or not file_data.get("url"):
                                continue
                            img_url = file_data["url"]
                            if img_url in seen_urls:
                                continue
                            seen_urls.add(img_url)
                            ext = img_url.split(".")[-1].split("?")[0].lower()
                            if ext in ("webm", "swf", "mp4"):
                                continue
                            valid_posts.append(p)

                        if not valid_posts:
                            await ctx.reply("*наклоняет голову* Нашёл посты, но картинки недоступны или все повторы...")
                            return

                        post = random.choice(valid_posts)
                        image_url = post["file"]["url"]

                        async with session.get(image_url) as img_resp:
                            if img_resp.status != 200:
                                await ctx.reply(f"*виляет хвостом* О, смотри что нашёл!\n{image_url}")
                                return

                            image_data = await img_resp.read()
                            ext = image_url.split(".")[-1].split("?")[0].lower()
                            if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
                                ext = "png"

                            file = discord.File(fp=io.BytesIO(image_data), filename=f"expie_art.{ext}")
                            await ctx.reply(content="Вот, смотри что нашёл! *виляет хвостом*", file=file)

            except Exception as e:
                await ctx.reply(f"*вздрагивает* Ой, что-то сломалось: {str(e)[:80]}")

    @bot.command(name="ген")
    async def cmd_generate(ctx, *, prompt=None):
        """!ген <описание> — сгенерировать картинку. Без промпта — случайный Экспи."""

        if not prompt:
            prompt = "solo, cute, fluffy, black melanistic fur, anthro, furry, wolf-fox hybrid, big eyes, orange sclera, big fluffy tail, orange tip tail, three ears, high quality, kawaii style, beautiful background"

        enhanced_prompt = (
            f"{prompt}, furry art, digital illustration, "
            "high quality, detailed fur, soft lighting, cute expression"
        )

        encoded = urllib.parse.quote(enhanced_prompt)
        seed = random.randint(1, 999999)
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                        if resp.status != 200:
                            await ctx.reply("*прижимает уши* Генератор не отвечает... Попробуй позже!")
                            return

                        image_data = await resp.read()
                        file = discord.File(fp=io.BytesIO(image_data), filename="expie_generated.png")
                        await ctx.reply(
                            content=f"*виляет хвостом* О, я нарисовал! По запросу: `{prompt[:300]}`",
                            file=file
                        )
            except Exception as e:
                await ctx.reply(f"*вздрагивает* Что-то пошло не так: {str(e)[:80]}")
                
    @bot.command(name="фурь")
    async def cmd_fur(ctx, *, query=None):
        """!фурь <теги> — поиск SFW артов на Furbooru."""

        if not query:
            await ctx.reply(
                "*наклоняет голову* Ой, а что искать-то? 🦊\n"
                "Пиши так: `!фурь cute, wolf, solo`\n"
                "Теги — на **английском**, через запятую или пробел.\n"
                "Например: `!фурь expie, anthro` или `!фурь fluffy, fox`"
            )
            return

        # Нормализуем теги: заменяем пробелы на запятые, убираем лишние
        tags_raw = query.replace(" ", ",").replace(",,", ",")
        tags_list = [t.strip().lower() for t in tags_raw.split(",") if t.strip()]
        
        # Автоматически добавляем safe, если его ещё нет (невидимо для пользователя)
        if "safe" not in tags_list:
            tags_list.insert(0, "safe")
        
        tags_clean = ",".join(tags_list)

        comments = [
            "*виляет хвостом* О, смотри-ка что нашёл! 🎨",
            "*приподнимается на задние лапы* Ого, это же... это! 👀",
            "*нюхает экран* Пахнет красивым артом! 🖼️",
            "*заглядывает через плечо* Нашёл кое-что интересненькое~ ✨",
            "*восторженно виляет* Вот это да, крутая картинка? 🦊"
        ]

        async with ctx.typing():
            try:
                encoded = urllib.parse.quote(tags_clean)
                url = f"https://furbooru.org/api/v1/json/search/images?q={encoded}&per_page=50"
                headers = {"User-Agent": "ExpieDiscordBot/1.0 (by Discord user)"}

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if resp.status != 200:
                            await ctx.reply(
                                f"*вздрагивает* Furbooru отвечает кодом **{resp.status}**... "
                                f"Попробуй позже или проверь теги! 📡"
                            )
                            return

                        data = await resp.json()
                        images = data.get("images", [])

                        if not images:
                            await ctx.reply(
                                f"*нюхает воздух* Ничего не нашёл по тегам `{query}`... "
                                f"Попробуй другие слова или проверь написание! 👃"
                            )
                            return

                        image = random.choice(images)
                        img_url = image.get("representations", {}).get("full") or image.get("source_url")

                        if not img_url:
                            await ctx.reply(
                                "*наклоняет голову* Нашёл пост, но ссылка на картинку пустая... Странно! 🫥"
                            )
                            return

                        async with session.get(img_url) as img_resp:
                            if img_resp.status != 200:
                                await ctx.reply(
                                    f"*вздрагивает* Не могу скачать картинку: код **{img_resp.status}**... "
                                    f"Может, она удалилась? 🖼️❌"
                                )
                                return

                            image_data = await img_resp.read()
                            ext = img_url.split(".")[-1].split("?")[0].lower()
                            if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
                                ext = "png"

                            file = discord.File(fp=io.BytesIO(image_data), filename=f"furbooru_art.{ext}")
                            await ctx.reply(content=random.choice(comments), file=file)

            except aiohttp.ClientError as e:
                await ctx.reply(f"*вздрагивает* Сеть хрипит: `{str(e)[:100]}`... Попробуй позже! 📡")
            except Exception as e:
                await ctx.reply(f"*вздрагивает* Что-то сломалось: `{str(e)[:100]}`... Ой. 🛠️")