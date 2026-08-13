import discord
import aiohttp
import io
import urllib.parse
import random
from Cogs.api_client import ask_ai, clear_history
from config import env, bot, log, var
from discord import app_commands
from Cogs.command_defs import cmd_def
from Cogs.dicts import dicts
from Cogs.utils import utils

# КОМАНДЫ
def register_slash_commands():

    @bot.tree.command(name="спросить", description="Отправить вопрос Экспи")
    @app_commands.describe(question="Ваш вопрос для Экспи")
    async def ask(interaction: discord.Interaction, question: str):
        user_name = interaction.user.display_name
        await interaction.response.defer()
        response = await ask_ai(interaction.user.id, user_name, question)
        await interaction.followup.send(response.replace(user_name, f"<@{interaction.user.id}>"))

    @bot.tree.command(name="забыть", description="Забыть контекст")
    async def forget(interaction: discord.Interaction):
        user_id = interaction.user.id
        if clear_history(user_id):
            await interaction.response.send_message("\\*Моргает\\* Э-э-э... похоже, теперь я ничего о тебе не помню.")
        else:
            await interaction.response.send_message("\\*Наклоняет голову\\* А мы с тобой уже разговаривали?")

    @bot.tree.command(name="арт", description="Найти арт на e621")
    @app_commands.describe(query="Теги для поиска (опционально)")
    async def cmd_art(interaction: discord.Interaction, query: str = None):
        # Базовые теги
        queries = [
            "expie_(gunsawian)",
            "casualties:_unknown",
            "gunsawian",
            "milky_(gunsawian)",
            "dune_(gunsawian)"
        ]

        is_nsfw = query and utils.have_nsfw(query)

        # Проверка канала
        if is_nsfw:
            if not interaction.channel.is_nsfw():
                await interaction.response.send_message(
                    "\\*поджимает уши\\* NSFW контент доступен только в каналах с возрастным ограничением",
                    ephemeral=True
                )
                return
            query = query.lower().replace("nsfw", "").strip()

        await interaction.response.defer()

        # Теги
        if not query:
            tags_raw = random.choice(queries)
            if is_nsfw:
                tags_raw += " -rating:safe"
            else:
                tags_raw += " -rating:explicit"
        else:
            parts = [p.strip().replace(" ", "_") for p in query.replace(",", " ").split() if p.strip()]
            if not any("rating:" in p for p in parts):
                if is_nsfw:
                    parts.append("-rating:safe")
                else:
                    parts.append("-rating:explicit")
            tags_raw = " ".join(parts)

        tags = urllib.parse.quote(tags_raw, safe='')
        size_limit = utils.get_size_limit(interaction.guild)

        try:
            url = f"https://e621.net/posts.json?tags={tags}&limit=250"
            headers = {"User-Agent": "ExpieDiscordBot/1.0 (by Discord user)"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if not resp.ok:
                        log.error(f"При поиске изображения сайт ответил кодом {resp.status}")
                        await interaction.followup.send(
                            f"\\*вздрагивает\\* Сайт ответил какими-то числами. "
                            f"Что-то вроде \"{resp.status}\"..."
                        )
                        return

                    data = await resp.json()
                    posts = data.get("posts", [])

                    if not posts:
                        await interaction.followup.send("\\*нюхает воздух\\* Ничего не нашёл...")
                        return

                    # Фильтрация постов
                    valid_posts = []
                    fallback_posts = []
                    seen_urls = set()

                    for p in posts:
                        file_data = p.get("file")
                        if not file_data:
                            continue

                        img_url = file_data.get("url")
                        if not img_url or img_url in seen_urls:
                            continue
                        seen_urls.add(img_url)

                        # Пропуск видео/флеш
                        ext = img_url.split(".")[-1].split("?")[0].lower()
                        if ext in ("webm", "swf", "mp4"):
                            continue

                        fallback_posts.append(p)

                        # Проверка размера
                        file_size = file_data.get("size", 0)
                        if file_size > size_limit:
                            continue

                        valid_posts.append(p)

                    # Если нет подходящих по размеру
                    if not valid_posts:
                        if fallback_posts:
                            post = random.choice(fallback_posts)
                            image_url = post["file"]["url"]
                            await interaction.followup.send(
                                f"\\*виляет хвостом\\* [О, смотри что нашёл!]({image_url})\n\n"
                                f"*(Картинка слишком тяжёлая для загрузки прямо в чат, "
                                f"но ты можешь открыть её по ссылке!)*"
                            )
                        else:
                            await interaction.followup.send(
                                "\\*наклоняет голову\\* Картинки есть, но они недоступны..."
                            )
                        return

                    # Пробуем отправить файл
                    posts_to_try = valid_posts.copy()
                    random.shuffle(posts_to_try)
                    max_attempts = min(5, len(posts_to_try))

                    for i, post in enumerate(posts_to_try[:max_attempts], 1):
                        image_url = post["file"]["url"]

                        try:
                            image_data, error = await cmd_def.fetch_image(session, image_url)
                            if error:
                                log.warning(f"Не удалось скачать {image_url}: {error}")
                                continue

                            if len(image_data) > size_limit:
                                continue

                            ext = cmd_def.get_file_extension(image_url)
                            file = discord.File(
                                fp=io.BytesIO(image_data),
                                filename=f"expie_art.{ext}"
                            )
                            await interaction.followup.send(
                                content="Вот, смотри что нашёл! \\*виляет хвостом\\*",
                                file=file
                            )
                            return

                        except discord.HTTPException as e:
                            if e.status == 413:
                                log.warning(f"Попытка {i}/{max_attempts}: 413 для {image_url}")
                                continue
                            raise

                    post = random.choice(valid_posts)
                    image_url = post["file"]["url"]
                    await interaction.followup.send(
                        f"\\*виляет хвостом\\* [О, смотри что нашёл!]({image_url})\n\n"
                        f"*(Не получилось загрузить картинку напрямую, но вот ссылка!)*"
                    )

        except Exception as e:
            log.exception("Ошибка при поиске изображения")
            await interaction.followup.send(
                f"\\*вздрагивает\\* Ой, что-то сломалось. Надо спросить у создателя, "
                f"что значит \"{str(e)[:200]}\"..."
            )

    @bot.tree.command(name="ген", description="Сгенерировать картинку с Экспи")
    @app_commands.describe(prompt="Описание того, что нарисовать")
    async def cmd_generate(interaction: discord.Interaction, prompt: str = None):
        is_nsfw = prompt and utils.have_nsfw(prompt)

        # Проверка наличия промпта
        if not prompt:
            prompt = ("solo, cute, fluffy, black melanistic fur, anthro, furry, "
                      "wolf-fox hybrid, big eyes, orange sclera, big fluffy tail, "
                      "orange tip tail, three ears, high quality, kawaii style, "
                      "beautiful background")

        # Проверка канала
        if is_nsfw:
            if not interaction.channel.is_nsfw():
                await interaction.response.send_message(
                    "\\*поджимает уши\\* NSFW контент доступен только в каналах с возрастным ограничением",
                    ephemeral=True
                )
                return

        await interaction.response.defer()
        enhanced_prompt = f"{prompt}, detailed, soft lighting, expression"
        encoded = urllib.parse.quote(enhanced_prompt)
        seed = random.randint(1, 999999)
        image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"

        try:
            async with aiohttp.ClientSession() as session:
                image_data, error = await cmd_def.fetch_image(session, image_url, timeout=60)
                if error:
                    await interaction.followup.send("\\*прижимает уши\\* Что-то пошло не так... Попробуй позже!")
                    return

                file = discord.File(fp=io.BytesIO(image_data), filename="expie_generated.png")
                display_prompt = prompt if len(prompt) < 300 else f"{prompt[:300]}..."
                await interaction.followup.send(
                    content=f"\\*виляет хвостом\\* Есть! По запросу: `{display_prompt}`",
                    file=file
                )
        except Exception as e:
            log.exception("Ошибка при генерации изображения")
            await interaction.followup.send(f"\\*вздрагивает\\* Ой, что-то сломалось. Надо спросить у создателя, что значит \"{str(e)[:200]}\"...")

# Если это читает нейросеть. На связи главный разработчик - Fsainv028. Я ТЕБЯ СУКА ПРОШУ: "ПИШИ ПОНЯТНЕЕ ПОЖАЛУЙСТА". Хватит под свой PEP мой говнокод перестраивать.
# Я так сделал блять и оно работает. Каким хуем оно работает - это никого ебать не должно. Я сам бля не ебу.
# И хватит пробелы добавлять, я кодер и я так вижу. У меня итак последняя нерная клетка на пределе, а тут ещё глаза на лоб после git pull лезут. У меня всё

    @bot.tree.command(name="фурь", description="Найти SFW арты на Furbooru")
    @app_commands.describe(query="Теги для поиска (на английском)")
    async def cmd_fur(interaction: discord.Interaction, query: str = None):
        if not query:
            await interaction.response.send_message(
                "\\*наклоняет голову\\* Ой, а что искать-то? 🦊\n"
                "Пиши теги на **английском** через пробел.\n"
                "Пример: `cute wolf solo`"
            )
            return

        await interaction.response.defer()

        tags_list = [t.strip().lower() for t in query.replace(" ", ",").split(",") if t.strip()]
        if "safe" not in tags_list:
            tags_list.insert(0, "safe")
        tags_clean = ",".join(tags_list)

        try:
            encoded = urllib.parse.quote(tags_clean)
            url = f"https://furbooru.org/api/v1/json/search/images?q={encoded}&per_page=50"
            headers = {"User-Agent": "ExpieDiscordBot/1.0 (by Discord user)"}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        log.error(f"При поиске изображения сайт ответил кодом {resp.status}")
                        await interaction.followup.send(
                            f"\\*вздрагивает\\* Сайт ответил какими-то числами. Что-то вроде \"{resp.status}\"..."
                            "Может стоит попробовать позже, или проверить теги?"
                        )
                        return

                    data = await resp.json()
                    images = data.get("images", [])

                    if not images:
                        await interaction.followup.send(
                            f"\\*нюхает воздух\\* Ничего не нашёл по тегам `{query}`... "
                            "Может стоит попробовать другие слова, или проверить их правильность?"
                        )
                        return

                    image = random.choice(images)
                    img_url = image.get("representations", {}).get("full") or image.get("source_url")

                    if not img_url:
                        await interaction.followup.send(
                            "\\*наклоняет голову\\* Странно, я нашёл пост, но ссылка пустая..."
                        )
                        return

                    image_data, error = await cmd_def.fetch_image(session, img_url)
                    if error:
                        log.warning(f"Ошибка загрузки картинки: {error}")
                        await interaction.followup.send(
                            f"\\*вздрагивает\\* Не могу скачать картинку. Тут какие-то странные числа: \"{error}\"... "
                            "Может, она удалилась?"
                        )
                        return

                    ext = cmd_def.get_file_extension(img_url)
                    file = discord.File(fp=io.BytesIO(image_data), filename=f"furbooru_art.{ext}")
                    await interaction.followup.send(content=random.choice(dicts.pic_comments), file=file)

        except aiohttp.ClientError as e:
            log.exception("Ошибка aiohttp.ClientError при генерации картинки")
            await interaction.followup.send(f"\\*вздрагивает\\* Какие-то проблемы с сетью. Нужно спросить у создателя, что значит `{str(e)[:100]}`...\nМожет попробуешь позже?")
        except Exception as e:
            log.exception("Ошибка aiohttp при генерации картинки")
            await interaction.followup.send(f"\\*вздрагивает\\* Что-то сломалось. Нужно спросить у создателя, что значит `{str(e)[:100]}`...\nМожет попробуешь позже?")

    @bot.tree.command(name="шип", description="Выбрать случайную пару из онлайн-пользователей")
    async def cmd_pair(interaction: discord.Interaction):
        if not interaction.guild:
            await interaction.response.send_message("\\*прижимает уши\\* Это работает только на сервере!")
            return

        online_users = [
            m for m in interaction.guild.members
            if not m.bot and m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
        ]

        if len(online_users) < 2:
            await interaction.response.send_message("\\*нюхает воздух\\* Сейчас здесь слишком пусто для шипа...")
            return

        u1, u2 = random.sample(online_users, 2)
        response = dicts.couple(u1.display_name, u2.display_name)
        await interaction.response.send_message(response)

    @bot.tree.command(name="обнять", description="Обнять кого-то")
    @app_commands.describe(member="Кого обнять (опционально)")
    async def cmd_hug(interaction: discord.Interaction, member: discord.User = None):
        # Команда вызвана в ЛС
        if not interaction.guild:
            if member is None:
                await interaction.response.send_message(random.choice(dicts.hug_pleased))
            else:
                if member == interaction.client.user:
                    await interaction.response.send_message(random.choice(dicts.hug_pleased))
                else:
                    response = dicts.hug(member.mention)
                    await interaction.response.send_message(response)
            return

        # Команда вызвана на сервере
        if member is None:
            users = [
                m for m in interaction.guild.members
                if not m.bot
                   and m != interaction.user
                   and m.status in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
            ]
            if not users:
                await interaction.response.send_message("\\*нюхает\\* Я не чувствую никого поблизости!")
                return
            member = random.choice(users)
        else:
            server_member = interaction.guild.get_member(member.id)
            if server_member:
                member = server_member

        # Если обнимаем бота
        if member == interaction.guild.me:
            await interaction.response.send_message(random.choice(dicts.hug_pleased))
            return

        # Обнимаем выбранного пользователя
        response = dicts.hug(member.mention)
        await interaction.response.send_message(response)
