import asyncio

from Cogs.commands_bot import register_slash_commands
from config import log, env, bot
from Cogs.bot import run_bot
from Cogs.bot import register_handlers
from Cogs.utils import utils

async def main():
    register_slash_commands()
    bot_task = asyncio.create_task(run_bot())
    try:
        await bot_task
    except asyncio.CancelledError:
        log.info("Завершение работы")
    except Exception:
        log.exception("Ошибка запуска")

if __name__ == "__main__":
    utils.check_tokens()
    register_handlers()
    asyncio.run(main())


