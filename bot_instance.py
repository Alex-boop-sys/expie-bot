"""
Создание экземпляра discord.ext.commands.Bot.
Вынесено из config.py, чтобы config оставался «чистым» контейнером данных.
"""

from __future__ import annotations

import discord
from discord.ext import commands

# Intents: нужны message_content (чтение текста), members и presences (для /шип и /обнять)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

# Глобальный экземпляр бота — импортируется как `from bot_instance import bot`
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("/"),
    intents=intents,
    case_insensitive=True,
)
