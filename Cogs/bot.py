import discord
from config import var, log, bot, env
from Cogs.handlers import handlers


def register_handlers():
    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        await handlers.on_msg(message)

    @bot.event
    async def on_ready():
        log.info(f"Бот запущен ({bot.user})")
        try:
            synced = await bot.tree.sync()
            log.info(f"Синхронизировано {len(synced)} слэш-команд")
        except Exception as e:
            log.error(f"Ошибка синхронизации слэш-команд: {e}")

        # Presence
        await var.bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name="Общаюсь с друзьями 🦊"
            )
        )

async def run_bot():
    await bot.start(env.discord_token)