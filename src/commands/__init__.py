"""
Регистрация всех слэш-команд.
Вызывается один раз из main.py.
"""

from __future__ import annotations

from bot_instance import bot
from src.commands import admin, ai, art, generation, social


def register_all() -> None:
    """Импортирует и регистрирует все группы команд."""
    ai.register(bot)
    art.register(bot)
    generation.register(bot)
    social.register(bot)
    admin.register(bot)
