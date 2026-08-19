"""
Сервис поиска артов: e621 и Furbooru.
Команды /арт и /фурь вызывают эти функции и только отправляют результат в Discord.
"""

from __future__ import annotations

import io
import random
import urllib.parse
from dataclasses import dataclass

import aiohttp
import discord

from logging_setup import log
from src.utils import fetch_image, get_file_extension


# ---------------------------------------------------------------------------
# Результат поиска
# ---------------------------------------------------------------------------
@dataclass
class ArtResult:
    """
    Унифицированный результат поиска арта.
    Либо image_bytes + ext (можно отправить файлом),
    либо fallback_url + reason (ссылка, если файл слишком большой / не скачался).
    """

    image_bytes: bytes | None = None
    ext: str = "png"
    fallback_url: str | None = None
    reason: str | None = None  # текст для пользователя при fallback


# ---------------------------------------------------------------------------
# e621
# ---------------------------------------------------------------------------
# Базовые теги персонажей из лора (случайный выбор, если query пустой)
_E621_DEFAULT_TAGS = [
    "expie_(gunsawian)",
    "casualties:_unknown",
    "gunsawian",
    "milky_(gunsawian)",
    "dune_(gunsawian)",
]


async def search_e621(
    query: str | None,
    is_nsfw: bool,
    size_limit: int,
) -> ArtResult:
    """
    Ищет пост на e621.
    Возвращает ArtResult с байтами картинки или fallback-ссылкой.
    """
    # Формируем теги
    if not query:
        tags_raw = random.choice(_E621_DEFAULT_TAGS)
        if is_nsfw:
            tags_raw += " -rating:safe"
        else:
            tags_raw += " -rating:explicit"
    else:
        parts = [
            p.strip().replace(" ", "_")
            for p in query.replace(",", " ").split()
            if p.strip()
        ]
        if not any("rating:" in p for p in parts):
            if is_nsfw:
                parts.append("-rating:safe")
            else:
                parts.append("-rating:explicit")
        tags_raw = " ".join(parts)

    tags = urllib.parse.quote(tags_raw, safe="")
    url = f"https://e621.net/posts.json?tags={tags}&limit=250"
    headers = {"User-Agent": "ExpieDiscordBot/1.0 (by Discord user)"}

    async with (
        aiohttp.ClientSession() as session,
        session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
        ) as resp,
    ):
        if not resp.ok:
            log.error(f"e621 ответил кодом {resp.status}")
            return ArtResult(
                reason=f'Сайт ответил какими-то числами. Что-то вроде "{resp.status}"...'
            )

        data = await resp.json()
        posts = data.get("posts", [])

        if not posts:
            return ArtResult(reason="Ничего не нашёл...")

        # Фильтрация: без видео, уникальные URL, по размеру
        valid_posts: list[dict] = []
        fallback_posts: list[dict] = []
        seen_urls: set[str] = set()

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

            fallback_posts.append(p)

            file_size = file_data.get("size", 0)
            if file_size > size_limit:
                continue

            valid_posts.append(p)

        if not valid_posts:
            if fallback_posts:
                post = random.choice(fallback_posts)
                image_url = post["file"]["url"]
                return ArtResult(
                    fallback_url=image_url,
                    reason=(
                        "Картинка слишком тяжёлая для загрузки прямо в чат, "
                        "но ты можешь открыть её по ссылке!"
                    ),
                )
            return ArtResult(reason="Картинки есть, но они недоступны...")

        # Пробуем скачать до 5 случайных постов
        posts_to_try = valid_posts.copy()
        random.shuffle(posts_to_try)
        max_attempts = min(5, len(posts_to_try))

        for i, post in enumerate(posts_to_try[:max_attempts], 1):
            image_url = post["file"]["url"]
            try:
                image_data, error = await fetch_image(session, image_url)
                if error:
                    log.warning(f"Не удалось скачать {image_url}: {error}")
                    continue
                if len(image_data) > size_limit:
                    continue

                ext = get_file_extension(image_url)
                return ArtResult(image_bytes=image_data, ext=ext)
            except Exception as e:
                log.warning(f"Попытка {i}/{max_attempts}: ошибка {e}")
                continue

        # Не удалось скачать — отдаём ссылку
        post = random.choice(valid_posts)
        image_url = post["file"]["url"]
        return ArtResult(
            fallback_url=image_url,
            reason="Не получилось загрузить картинку напрямую, но вот ссылка!",
        )


# ---------------------------------------------------------------------------
# Furbooru
# ---------------------------------------------------------------------------
async def search_furbooru(query: str) -> ArtResult:
    """
    Ищет SFW-арт на Furbooru.
    query обязателен (теги через пробел/запятую).
    """
    tags_list = [
        t.strip().lower() for t in query.replace(" ", ",").split(",") if t.strip()
    ]
    if "safe" not in tags_list:
        tags_list.insert(0, "safe")
    tags_clean = ",".join(tags_list)

    encoded = urllib.parse.quote(tags_clean)
    url = f"https://furbooru.org/api/v1/json/search/images?q={encoded}&per_page=50"
    headers = {"User-Agent": "ExpieDiscordBot/1.0 (by Discord user)"}

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url, headers=headers, timeout=aiohttp.ClientTimeout(total=20)
        ) as resp:
            if resp.status != 200:
                log.error(f"Furbooru ответил кодом {resp.status}")
                return ArtResult(
                    reason=(
                        f'Сайт ответил какими-то числами. Что-то вроде "{resp.status}"...'
                        "Может стоит попробовать позже, или проверить теги?"
                    )
                )

            data = await resp.json()
            images = data.get("images", [])

            if not images:
                return ArtResult(
                    reason=(
                        f"Ничего не нашёл по тегам `{query}`... "
                        "Может стоит попробовать другие слова, или проверить их правильность?"
                    )
                )

            image = random.choice(images)
            img_url = image.get("representations", {}).get("full") or image.get(
                "source_url"
            )

            if not img_url:
                return ArtResult(reason="Странно, я нашёл пост, но ссылка пустая...")

            image_data, error = await fetch_image(session, img_url)
            if error:
                log.warning(f"Ошибка загрузки картинки: {error}")
                return ArtResult(
                    reason=(
                        f'Не могу скачать картинку. Тут какие-то странные числа: "{error}"... '
                        "Может, она удалилась?"
                    )
                )

            ext = get_file_extension(img_url)
            return ArtResult(image_bytes=image_data, ext=ext)


async def search_art_direct(query: str, is_nsfw: bool = False, size_limit: int = 8000000) -> discord.Embed | None:
    """
    Прямая функция поиска арта для использования в trigger_handler.
    Возвращает discord.Embed с картинкой или None при ошибке.
    """
    result = await search_e621(query, is_nsfw=is_nsfw, size_limit=size_limit)
    
    if result.image_bytes:
        file = discord.File(
            fp=io.BytesIO(result.image_bytes),
            filename=f"expie_art.{result.ext}",
        )
        embed = discord.Embed(title="Найденный арт", description="Вот что я нашёл! 🦊")
        embed.set_image(url=f"attachment://expie_art.{result.ext}")
        # Возвращаем embed с привязанным файлом через send
        # Но так как мы не можем вернуть файл отсюда, вернем embed без файла
        # А отправку сделаем отдельно
        return embed
    elif result.fallback_url:
        embed = discord.Embed(
            title="Арт найден",
            description=f"{result.reason}\n[Открыть картинку]({result.fallback_url})"
        )
        return embed
    
    return None
