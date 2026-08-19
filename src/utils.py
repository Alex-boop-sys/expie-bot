"""
Утилиты бота + бывший command_defs.py.
Проверка токенов, NSFW, лимиты вложений, скачивание изображений.
"""

from __future__ import annotations

import re
import sys
from typing import Optional

import aiohttp
import discord

from config import ATTACHMENT_LIMITS, env
from logging_setup import log
from src import texts


# ---------------------------------------------------------------------------
# Лимиты вложений Discord
# ---------------------------------------------------------------------------
def get_size_limit(guild: Optional[discord.Guild]) -> int:
    """
    Возвращает максимальный размер вложения для сервера (в байтах).
    Зависит от уровня Nitro-буста (premium_tier).
    """
    if guild is None:
        return 8 * 1024 * 1024  # 8 MB по умолчанию (DM / без буста)
    return ATTACHMENT_LIMITS.get(guild.premium_tier, 8 * 1024 * 1024)


# ---------------------------------------------------------------------------
# NSFW-детектор
# ---------------------------------------------------------------------------
def have_nsfw(text: str) -> bool:
    """Проверяет, содержит ли текст NSFW-ключевые слова (по regex из texts)."""
    text_lower = text.lower()
    for pattern in texts.nsfw_patterns:
        if re.search(pattern, text_lower):
            return True
    return False


# ---------------------------------------------------------------------------
# Проверка токенов при старте
# ---------------------------------------------------------------------------
def check_tokens() -> None:
    """
    Проверяет наличие всех обязательных переменных окружения.
    При отсутствии любого токена — логирует fatal и завершает процесс.
    """
    for name, value in env:
        if value is None:
            log.fatal(f"Токен {name} не найден!")
            sys.exit(1)


# ---------------------------------------------------------------------------
# Скачивание изображений (бывший command_defs)
# ---------------------------------------------------------------------------
async def fetch_image(
    session: aiohttp.ClientSession,
    url: str,
    timeout: int = 20,
) -> tuple[Optional[bytes], Optional[int]]:
    """
    Скачивает изображение по URL.
    Возвращает (data, None) при успехе или (None, status_code) при ошибке.
    """
    async with session.get(
        url, timeout=aiohttp.ClientTimeout(total=timeout)
    ) as resp:
        if resp.status != 200:
            return None, resp.status
        data = await resp.read()
        return data, None


def get_file_extension(url: str) -> str:
    """
    Извлекает расширение файла из URL.
    Возвращает одно из: png, jpg, jpeg, gif, webp (по умолчанию png).
    """
    ext = url.split(".")[-1].split("?")[0].lower()
    return ext if ext in ("png", "jpg", "jpeg", "gif", "webp") else "png"
