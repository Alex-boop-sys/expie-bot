import os
import discord
import platform
from fsvlog import FSVLog
from dotenv import load_dotenv
from discord.ext import commands
from pathlib import Path

env_path = Path('/etc/bots/expie-bot/.env')
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

def is_server():
    """Определяем, запущены ли мы на сервере (Linux) или локально."""
    if platform.system().lower() == "linux":
        return True
    else:
        return False

class Env:
    def __init__(self):
        # ============ API КЛЮЧИ ============
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.discord_token = os.getenv("DISCORD_TOKEN")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        
        # Cloudflare Workers AI — опционально.
        # Если не заданы, бот просто пропустит этот провайдер.
        self.cloudflare_account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.cloudflare_api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        
        # ============ DISCORD IDs ============
        self.owner_id = os.getenv("OWNER_ID")
        self.co_owner_id = os.getenv("CO_OWNER_ID")

        self._cache = {}

    def __iter__(self):
        for attr_name in dir(self):
            if not attr_name.startswith('_') and not callable(getattr(self, attr_name)):
                yield attr_name, getattr(self, attr_name)

env = Env()

class Paths:
    def __init__(self):
        self.root = os.path.dirname(os.path.abspath(__file__))
        self.logs = os.path.join(self.root, "Logs")

paths = Paths()

class Var:
    def __init__(self):
        # ============ ЦЕПОЧКА FALLBACK-МОДЕЛЕЙ ============
        # Порядок имеет значение: сверху вниз — от высшего приоритета к низшему.
        self.fallback_models = [
            ("openrouter", "meta-llama/llama-3.3-70b-instruct"),
            ("openrouter", "mistralai/mistral-large-2407"),
            ("openrouter", "openai/gpt-oss-120b"),
            ("openrouter", "qwen/qwen3.6-27b"),
            ("cloudflare", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
            ("groq", "llama-3.3-70b-versatile"),
            ("groq", "llama-3.1-8b-instant"),
        ]

        # ============ ЛОГГЕР ============
        self.log = FSVLog(
            log_folder_path=paths.logs,
            max_logs=10,
            log_format="{timestamp} [{level}] [{type}] ({filename}:{lineno}) {context} - {message}",
            log_level="DEBUG",
            filename_time_format="%Y%m%d_%H%M%S",
            time_format="[%Y-%m-%dT%H:%M:%S]",
            exception_format="full",
            file_only=is_server()
        )

        # ============ DISCORD БОТ ============
        self.intents = discord.Intents.default()
        self.intents.message_content = True
        self.intents.members = True
        self.intents.presences = True
        
        # case_insensitive=True позволяет командам работать с любым регистром (/Арт = /арт)
        self.bot = commands.Bot(
            command_prefix=commands.when_mentioned_or("/"),
            intents=self.intents,
            case_insensitive=True
        )
        self.bot_ver = "0.3.1 [INDEV]"

        # Лимиты вложений Discord по уровням буста сервера (в байтах)
        self.limits = {
            0: 8 * 1024 * 1024,   # 8 MB  (без буста)
            1: 8 * 1024 * 1024,   # 8 MB
            2: 25 * 1024 * 1024,  # 25 MB
            3: 50 * 1024 * 1024,  # 50 MB
        }

# ============ ГЛОБАЛЬНЫЕ ЭКЗЕМПЛЯРЫ ============
var = Var()
log = var.log
bot = var.bot