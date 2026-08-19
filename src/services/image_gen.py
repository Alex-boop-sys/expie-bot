"""
Сервис генерации изображений через Pollinations.ai.
Команда /ген (и будущие триггеры «нарисуй») вызывают generate().
"""

from __future__ import annotations

import io
import random
import urllib.parse

import aiohttp
import discord

from src.utils import fetch_image


async def generate(prompt: str) -> bytes | None:
    """
    Генерирует картинку по текстовому промпту.
    Возвращает байты PNG или None при ошибке.
    """
    # Добавляем общие улучшения качества
    enhanced_prompt = f"{prompt}, detailed, soft lighting, expression"
    encoded = urllib.parse.quote(enhanced_prompt)
    seed = random.randint(1, 999999)

    image_url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width=1024&height=1024&nologo=true&seed={seed}"
    )

    async with aiohttp.ClientSession() as session:
        image_data, error = await fetch_image(session, image_url, timeout=60)
        if error:
            return None
        return image_data


async def generate_image_direct(prompt: str) -> discord.File | None:
    """
    Прямая функция генерации для использования в trigger_handler.
    Возвращает discord.File или None при ошибке.
    """
    image_data = await generate(prompt)
    if not image_data:
        return None
    
    return discord.File(
        fp=io.BytesIO(image_data),
        filename="expie_generated.png",
    )
