"""
Сервис генерации изображений через Pollinations.ai.
Команда /ген (и будущие триггеры «нарисуй») вызывают generate().
"""

from __future__ import annotations

import random
import urllib.parse
from typing import Optional

import aiohttp

from src.utils import fetch_image


async def generate(prompt: str) -> Optional[bytes]:
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
