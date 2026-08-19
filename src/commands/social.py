"""
Социальные слэш-команды: /обнять, /шип.
"""

from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

from src import texts


def register(bot_instance: commands.Bot) -> None:
    """Регистрирует команды этого модуля."""

    @bot_instance.tree.command(
        name="шип", description="Выбрать случайную пару из онлайн-пользователей"
    )
    async def cmd_pair(interaction: discord.Interaction) -> None:
        if not interaction.guild:
            await interaction.response.send_message(
                "\\*прижимает уши\\* Это работает только на сервере!"
            )
            return

        online_users = [
            m
            for m in interaction.guild.members
            if not m.bot
            and m.status
            in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
        ]

        if len(online_users) < 2:
            await interaction.response.send_message(
                "\\*нюхает воздух\\* Сейчас здесь слишком пусто для шипа..."
            )
            return

        u1, u2 = random.sample(online_users, 2)
        response = texts.couple(u1.display_name, u2.display_name)
        await interaction.response.send_message(response)

    @bot_instance.tree.command(name="обнять", description="Обнять кого-то")
    @app_commands.describe(member="Кого обнять (опционально)")
    async def cmd_hug(
        interaction: discord.Interaction, member: discord.User = None
    ) -> None:
        # --- Вызов в ЛС ---
        if not interaction.guild:
            if member is None or member == interaction.client.user:
                await interaction.response.send_message(
                    random.choice(texts.hug_pleased)
                )
            else:
                response = texts.hug(member.mention)
                await interaction.response.send_message(response)
            return

        # --- Вызов на сервере ---
        if member is None:
            users = [
                m
                for m in interaction.guild.members
                if not m.bot
                and m != interaction.user
                and m.status
                in (discord.Status.online, discord.Status.idle, discord.Status.dnd)
            ]
            if not users:
                await interaction.response.send_message(
                    "\\*нюхает\\* Я не чувствую никого поблизости!"
                )
                return
            member = random.choice(users)
        else:
            server_member = interaction.guild.get_member(member.id)
            if server_member:
                member = server_member

        # Обнимаем бота
        if member == interaction.guild.me:
            await interaction.response.send_message(
                random.choice(texts.hug_pleased)
            )
            return

        response = texts.hug(member.mention)
        await interaction.response.send_message(response)
