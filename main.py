import discord
from discord.ext import commands
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import DISCORD_TOKEN
from commands_bot import register_commands
from handlers import register_handlers


# ============ ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ============
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Expie is alive!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()


def run_dummy_server():
    server = HTTPServer(("0.0.0.0", 10000), DummyHandler)
    server.serve_forever()


threading.Thread(target=run_dummy_server, daemon=True).start()
print("🌐 Фейковый сервер запущен на порту 10000 для Render")


# ============ BOT SETUP ============
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    activity = discord.Activity(
        type=discord.ActivityType.playing,
        name="!экспи | Общаюсь с друзьями 🦊"
    )
    await bot.change_presence(activity=activity)
    print(f"🦊 Экспи на месте! Логин: {bot.user}")
    print("------")


# ============ REGISTER MODULES ============
register_commands(bot)
register_handlers(bot)


# ============ RUN ============
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
