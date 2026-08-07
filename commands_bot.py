import discord
import aiohttp
import io
import urllib.parse
import random
from api_client import ask_ai, clear_history
from config import OWNER_ID
import base64
from config import GEMINI_API_KEY, CLOUDFLARE_ACCOUNT_ID, CLOUDFLARE_API_TOKEN

def register_commands(bot):
    """Регистрация всех команд бота."""

    @bot.command(name="Экспик")
    async def cmd_expie_ru(ctx, *, message):
        """!Экспик <сообщение>"""
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

    @bot.command(name="забыть", aliases=["забудь"])
    async def cmd_forget(ctx):
        """Clear conversation history"""
        user_id = ctx.author.id
        if clear_history(user_id):
            await ctx.reply("*моргает* Э-э-э... кто ты? Шучу-шучу! Начинаем с чистого листа, бро! 🦊")
        else:
            await ctx.reply("*наклоняет голову* А мы с тобой уже разговаривали? Ну, привет тогда! 👋")

    @bot.command(name="lore", aliases=["лор"])
    async def cmd_lore(ctx, *, topic):
        """!lore <тема> — detailed lore about the world"""
        user_name = ctx.author.display_name
        prompt = f"Расскажи подробно про {topic} из мира Casualties: Unknown / Серой Планеты."
        async with ctx.typing():
            response = await ask_ai(ctx.author.id, user_name, prompt)
            await ctx.reply(response)

    @bot.command(name="арт", aliases=["art"])
    async def cmd_art(ctx, *, query=None):
        """!арт — случайный арт Экспи. !арт <теги> — поиск по e621."""

        if not query:
            search_variants = [
                "expie_(gunsawian) -rating:explicit",
                "casualties:_unknown -rating:explicit",
                "gunsawian -rating:explicit",
                "milky_(gunsawian) -rating:explicit",
                "dune_(gunsawian) -rating:explicit"
            ]
            tags_raw = random.choice(search_variants)
        else:
            # Нормализуем ввод: запятые → пробелы, разбиваем, внутри тега пробел → _
            parts = [p.strip().replace(" ", "_") for p in query.replace(",", " ").split() if p.strip()]
            
            # Добавляем safe-фильтр, если пользователь сам не указал рейтинг
            if not any("rating:" in p for p in parts):
                parts.append("rating:safe")
            
            tags_raw = " ".join(parts)

        # URL-кодируем всё: пробелы → %20, двоеточия → %3A, скобки и прочее
        tags = urllib.parse.quote(tags_raw, safe='')

        async with ctx.typing():
            try:
                url = f"https://e621.net/posts.json?tags={tags}&limit=250"
                headers = {"User-Agent": "ExpieDiscordBot/1.0 (by Discord user)"}

                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                        if not resp.ok:
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
                            if not file_data:
                                continue
                            img_url = file_data.get("url")
                            if not img_url or img_url in seen_urls:
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
                            if not img_resp.ok:
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
                
    @bot.command(name="ген", aliases=["gen"])
    async def cmd_generate(ctx, *, prompt=None):
        """!ген <описание> — сгенерировать картинку. Без промпта — случайный Экспи."""

        if not prompt:
            prompt = "solo, cute, fluffy, black melanistic fur, anthro, furry, wolf-fox hybrid, big eyes, orange sclera, big fluffy tail, orange tip tail, three ears, high quality, kawaii style, beautiful background"

        enhanced_prompt = (
            f"{prompt}, detailed, soft lighting, expression"
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
                
    @bot.command(name="фурь", aliases=["furry", "fur", "фурри"])
    async def cmd_fur(ctx, *, query=None):
        """!фурь <теги> — поиск SFW артов на Furbooru."""

        if not query:
            await ctx.reply(
                "*наклоняет голову* Ой, а что искать-то? 🦊\n"
                "Пиши так: `!фурь cute, wolf, solo`\n"
                "Теги — на **английском**, через запятую или пробел.\n"
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

    print(">>> DEBUG: registering гем")
    @bot.command(name="гем")
    async def cmd_generate_gemini(ctx, *, prompt=None):
        """!гем <описание> — сгенерировать картинку через Gemini"""

        if not prompt:
            prompt = "solo, cute, fluffy, black melanistic fur, anthro, furry, wolf-fox hybrid, big eyes, orange sclera, big fluffy tail, orange tip tail, three ears, high quality, kawaii style, beautiful background"

        if not GEMINI_API_KEY:
            await ctx.reply("*прижимает уши* Ключ Gemini не настроен... Скажи хозяину! 🛠️")
            return

        enhanced = (
            f"{prompt}, furry art, digital illustration, "
            "high quality, detailed fur, soft lighting, cute expression"
        )

        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.5-flash-image:generateContent?key={GEMINI_API_KEY}"
        )

        payload = {
            "contents": [{
                "role": "user",
                "parts": [{"text": enhanced}]
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": 0.85
            }
        }

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as resp:
                        if resp.status == 429:
                            err_text = await resp.text()
                            print(f"[Gemini 429] {err_text[:300]}")  # ← увидишь в логах Render
                            await ctx.reply(
                                f"*вздрагивает* Gemini не пускает... "
                                f"Код 429, подробности в логах хозяина! 🛡️"
                            )
                            return

                        if resp.status != 200:
                            text = await resp.text()
                            await ctx.reply(
                                f"*вздрагивает* Gemini отвечает кодом {resp.status}: "
                                f"{text[:100]}..."
                            )
                            return

                        data = await resp.json()
                        candidates = data.get("candidates", [])
                        if not candidates:
                            await ctx.reply(
                                "*наклоняет голову* Gemini ничего не нарисовал... 🫥"
                            )
                            return

                        parts = candidates[0].get("content", {}).get("parts", [])
                        image_part = None
                        for part in parts:
                            if "inlineData" in part:
                                image_part = part["inlineData"]
                                break

                        if not image_part:
                            await ctx.reply(
                                "*наклоняет голову* В ответе нет картинки... "
                                "Только текст? 🫥"
                            )
                            return

                        image_bytes = base64.b64decode(image_part["data"])
                        mime = image_part.get("mimeType", "image/png")
                        ext = mime.split("/")[-1]
                        if ext == "jpeg":
                            ext = "jpg"

                        file = discord.File(
                            fp=io.BytesIO(image_bytes),
                            filename=f"expie_gemini.{ext}"
                        )
                        await ctx.reply(
                            content=f"*виляет хвостом* О, я нарисовал! "
                            f"По запросу: `{prompt[:300]}`",
                            file=file
                        )

            except Exception as e:
                await ctx.reply(
                    f"*вздрагивает* Что-то сломалось: {str(e)[:80]} 🛠️"
                )

    @bot.command(name="удали")
    async def cmd_delete(ctx, channel_id: str = None, message_id: str = None):
        """!удали ID_канала ID_сообщения — удалить сообщение бота"""

        # Ограничение: только владелец бота (замени ID на свой)
        if ctx.author.id != OWNER_ID:
            await ctx.reply("*прижимает уши* Это только для хозяина... 🛡️")
            return
        
        # Проверка формата
        if not channel_id or not message_id:
            await ctx.reply(
                "*наклоняет голову* Неправильный формат!\n"
                "Пиши так: `!удали ID_канала ID_сообщения`\n"
                "Например: `!удали 1103257073095028798 1261234567890123456`"
            )
            return

        # Проверка, что оба аргумента — цифры
        if not channel_id.isdigit() or not message_id.isdigit():
            await ctx.reply(
                "*вздрагивает* ID должны состоять только из цифр!\n"
                "Правильный формат: `!удали ID_канала ID_сообщения`"
            )
            return

        try:
            # discord.py уже авторизован — используем его внутренний HTTP-клиент
            await bot.http.delete_message(int(channel_id), int(message_id))
            await ctx.reply("*моргает* Удалено! Сообщение испарилось... ✨")

        except discord.NotFound:
            await ctx.reply("*нюхает воздух* Не нашёл такого сообщения... Может, уже удалили? 👃")

        except discord.Forbidden:
            await ctx.reply("*прижимает уши* Нет прав удалять это сообщение... Точно оно моё? 🛡️")

        except discord.HTTPException as e:
            await ctx.reply(
                f"*вздрагивает* Не вышло... "
                f"Код: `{e.status}` | Discord: `{e.code}` | {str(e)[:60]} 🛠️"
            )

        except Exception as e:
            await ctx.reply(f"*вздрагивает* Что-то сломалось: `{str(e)[:100]}` 🛠️")

    @bot.command(name="напиши")
    async def cmd_say(ctx, channel_id: str = None, *, message: str = None):
        """!напиши ID_канала текст — написать от лица бота в указанный канал"""

        # Проверка на владельца
        if ctx.author.id != OWNER_ID:
            await ctx.reply("*прижимает уши* Это только для хозяина... 🛡️")
            return

        # Проверка формата
        if not channel_id or not message:
            await ctx.reply(
                "*наклоняет голову* Неправильный формат!\n"
                "Пиши так: `!напиши ID_канала текст сообщения`\n"
                "Например: `!напиши 1103257073095028798 Привет, друзья! 🦊`"
            )
            return

        # Проверка, что ID канала — цифры
        if not channel_id.isdigit():
            await ctx.reply(
                "*вздрагивает* ID канала должен состоять только из цифр!\n"
                "Правильный формат: `!напиши ID_канала текст сообщения`"
            )
            return

        try:
            channel = await bot.fetch_channel(int(channel_id))
            await channel.send(message)
            await ctx.reply(f"*виляет хвостом* Отправлено в <#{channel_id}>! ✉️")

        except discord.NotFound:
            await ctx.reply("*нюхает воздух* Не нашёл такой канал... Точно правильный ID? 👃")

        except discord.Forbidden:
            await ctx.reply("*прижимает уши* Нет прав писать в этот канал... 🛡️")

        except discord.HTTPException as e:
            await ctx.reply(
                f"*вздрагивает* Не вышло... "
                f"Код: `{e.status}` | Discord: `{e.code}` | {str(e)[:60]} 🛠️"
            )

        except Exception as e:
            await ctx.reply(f"*вздрагивает* Что-то сломалось: `{str(e)[:100]}` 🛠️")

    @bot.command(name="пара")
    async def cmd_pair(ctx):
        """!пара — выбрать случайную пару из онлайн-пользователей"""

        if not ctx.guild:
            await ctx.reply("*прижимает уши* Это работает только на сервере, бро! 🏠")
            return

        # Собираем живых людей онлайн (не ботов, не оффлайн)
        online_users = [
            m for m in ctx.guild.members
            if not m.bot
            and m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
        ]

        if len(online_users) < 2:
            await ctx.reply("*нюхает воздух* Недостаточно людей онлайн для пары... 👃")
            return

        u1, u2 = random.sample(online_users, 2)

        phrases = [
            f"*виляет хвостом* Ого, смотрите-ка! **{u1.display_name}** и **{u2.display_name}** — ваша судьба связана! 💕",
            f"*приподнимается на задние лапы* Я провёл сложные расчёты... **{u1.display_name}** + **{u2.display_name}** = ❤️",
            f"*фыркает* Я чувствую запах любви! **{u1.display_name}** и **{u2.display_name}**, вы точно созданы друг для друга! 🦊💘",
            f"*восторженно виляет* Ребята, смотрите! **{u1.display_name}** и **{u2.display_name}** так мило смотрятся вместе! 🐾",
        ]

        await ctx.reply(random.choice(phrases))

    @bot.command(name="обними")
    async def cmd_hug(ctx, member: discord.Member = None):
        """!обними @ник — обнять кого-то. Без ника — обнимает случайного."""

        if not ctx.guild:
            await ctx.reply("*прижимает уши* Это работает только на сервере, бро! 🏠")
            return

        # Если ник не указан — выбираем случайного живого человека онлайн
        if not member:
            candidates = [
                m for m in ctx.guild.members
                if not m.bot
                and m != ctx.author
                and m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
            ]
            if not candidates:
                await ctx.reply("*нюхает воздух* Некого обнимать... Все разбежались!")
                return
            member = random.choice(candidates)

        # Защита от обнимания самого себя
        #if member == ctx.author:
        #    await ctx.reply("*наклоняет голову* Самому себя обнять? Я попробую... *обнимает себя лапками*")
        #    return

        # Обнимание бота
        if member == bot.user:
            await ctx.reply("*виляет хвостом* Ох, этот железный тоже хочет обниматься? *пытается осторожно обнять бота*")
            return

        phrases = [
            f"*тихо подкрадывается сзади и обнимает {member.mention} лапками за талию*\n"
            f"Ты такой тёплый... *трётся мордочкой о спину* И такой мягкий.\n"
            f"*прижимает уши от счастья* Я тут побуду, хорошо? 🐾",

            f"*подбегает и с разбега прыгает к {member.mention} на колени.*\n"
            f"Оп! *устраивается поудобнее, сворачиваясь калачиком* Тут так тепло и приятно...\n"
            f"*мурчит как котёнок* Теперь я буду сидеть здесь. Лучшее место! 🧡",

            f"*залезает на плечи к {member.mention} и садится свесив лапки.*\n"
            f"Смотри, я выше всех! *услбается и шевелит хвостом, обнимая шею оранжевым кончиком*\n"
            f"*кладёт свою мордочку на твою голову* Так удобно! Можно  посидеть тут ещё немножко? *шепчет в ухо* 🦊",

            f"*подползает ближе и тихо кладёт голову на колени к {member.mention}*\n"
            f"*смотрит своими большими оранжевыми глазами снизу вверх* Ты хороший...\n"
            f"*шевелит ушками, то которое сзади тоже поворачивается*\n"
            f"Не уходи пока, ладно? Я тут посижу с тобой. *мягко обнимает лапками* 🧡",
        ]

        await ctx.reply(random.choice(phrases))

    @bot.command(name="ген3")
    async def cmd_generate_cf(ctx, *, prompt=None):
        """!ген3 <описание> — сгенерировать картинку через Cloudflare SDXL"""

        if not prompt:
            prompt = "cute fluffy anthro fox character, digital art, soft lighting, high quality, detailed fur"

        if not CLOUDFLARE_ACCOUNT_ID or not CLOUDFLARE_API_TOKEN:
            await ctx.reply("*прижимает уши* Cloudflare не настроен... Скажи хозяину! 🛠️")
            return

        model = "@cf/stabilityai/stable-diffusion-xl-base-1.0"
        url = f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/{model}"

        # SDXL payload: просто prompt + опциональные параметры
        payload = {
            "prompt": prompt,
            "height": 1024,
            "width": 1024,
            # "num_steps": 20,  # по умолчанию 20, можно убрать для скорости
            # "guidance": 7.5,  # по умолчанию 7.5
            # "negative_prompt": "blurry, low quality"  # если нужно
        }

        async with ctx.typing():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        headers={"Authorization": f"Bearer {CLOUDFLARE_API_TOKEN}"},
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=45)  # SDXL чуть медленнее Flux
                    ) as resp:
                        if resp.status == 429:
                            await ctx.reply("*вздрагивает* Лимит Cloudflare на сегодня исчерпан! Попробуй завтра! ⏳")
                            return

                        if resp.status != 200:
                            text = await resp.text()
                            await ctx.reply(f"*вздрагивает* Cloudflare отвечает {resp.status}: {text[:100]}")
                            return

                        data = await resp.json()

                        # Проверяем success
                        if not data.get("success"):
                            err = data.get("errors", [{}])[0]
                            await ctx.reply(f"*вздрагивает* Ошибка Cloudflare: {err.get('message', 'unknown')}")
                            return

                        image_b64 = data.get("result", {}).get("image")
                        if not image_b64:
                            await ctx.reply("*наклоняет голову* В ответе нет картинки... 🫥")
                            return

                        image_bytes = base64.b64decode(image_b64)
                        file = discord.File(fp=io.BytesIO(image_bytes), filename="expie_sdxl.png")
                        await ctx.reply(
                            content=f"*виляет хвостом* Нарисовал через SDXL! По запросу: `{prompt[:300]}`",
                            file=file
                        )

            except Exception as e:
                await ctx.reply(f"*вздрагивает* Ой: {str(e)[:80]} 🛠️")
        