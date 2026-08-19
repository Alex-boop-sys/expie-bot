"""
Регистрация всех слэш-команд.
Вызывается один раз из main.py.
Административные команды НЕ регистрируются как слэш-команды — они доступны только через текстовые триггеры.
"""

from __future__ import annotations

from bot_instance import bot
from src.commands import ai, art, generation, social


def register_all() -> None:
    """Импортирует и регистрирует все группы команд."""
    ai.register(bot)
    art.register(bot)
    generation.register(bot)
    social.register(bot)
    # admin.register(bot)  # Админ-команды не регистрируются как слэш-команды
