"""
Конфигурация бота: переменные окружения, пути, константы и лимиты.
Здесь НЕТ создания логгера и экземпляра Bot — они вынесены в отдельные модули.
"""

from __future__ import annotations

import os
import platform
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Загрузка .env
# ---------------------------------------------------------------------------
# На проде файл лежит в /etc/bots/expie-bot/.env, локально — рядом с проектом
env_path = Path("/etc/bots/expie-bot/.env")
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


# ---------------------------------------------------------------------------
# Определение окружения
# ---------------------------------------------------------------------------
# True, если бот запущен на Linux-сервере (прод)
IS_SERVER: bool = platform.system().lower() == "linux"


# ---------------------------------------------------------------------------
# Переменные окружения (секреты)
# ---------------------------------------------------------------------------
class Env:
    """Контейнер секретов из .env. Имеет __iter__ для check_tokens()."""

    # Ключи, которые нельзя логировать (токены, API-ключи)
    SENSITIVE_KEYS = frozenset({
        "groq_api_key",
        "openrouter_api_key",
        "cloudflare_account_id",
        "cloudflare_api_token",
        "discord_token",
    })

    def __init__(self) -> None:
        # API-ключи LLM-провайдеров
        self.groq_api_key: str | None = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY")
        self.cloudflare_account_id: str | None = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.cloudflare_api_token: str | None = os.getenv("CLOUDFLARE_API_TOKEN")

        # Discord
        self.discord_token: str | None = os.getenv("DISCORD_TOKEN")

        # Владельцы (для админ-команд)
        self.owner_id: str | None = os.getenv("OWNER_ID")
        self.co_owner_id: str | None = os.getenv("CO_OWNER_ID")

    def __iter__(self):
        """Итерация по (имя, значение) для проверки наличия токенов.
        Исключает чувствительные ключи (токены, API-ключи) из логирования."""
        for attr_name in dir(self):
            if not attr_name.startswith("_") and not callable(getattr(self, attr_name)):
                # Пропускаем служебные атрибуты и чувствительные данные
                if attr_name in self.SENSITIVE_KEYS:
                    continue
                yield attr_name, getattr(self, attr_name)

    def get_token(self, key: str) -> str | None:
        """Безопасное получение токена по имени ключа.
        Используйте этот метод вместо прямого доступа к атрибутам."""
        return getattr(self, key, None)


env = Env()


# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------
# Корень проекта (папка, где лежит этот файл)
ROOT_DIR: str = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR: str = os.path.join(ROOT_DIR, "Logs")
RESOURCES_DIR: str = os.path.join(ROOT_DIR, "resources")


# ---------------------------------------------------------------------------
# Константы бота
# ---------------------------------------------------------------------------
BOT_VER: str = "0.4.1 [INDEV]"

# Максимальная длина истории диалога (сообщений) на одного пользователя
MAX_HISTORY: int = 10

# Таймауты HTTP-запросов к LLM-провайдерам (секунды)
CLOUDFLARE_TIMEOUT: int = 25
GROQ_TIMEOUT: int = 25
OPENROUTER_TIMEOUT: int = 25

# Цепочка fallback-моделей: (провайдер, имя_модели)
# Порядок важен — сначала пробуем OpenRouter, потом Cloudflare, потом Groq
FALLBACK_MODELS: list[tuple[str, str]] = [
    ("openrouter", "meta-llama/llama-3.3-70b-instruct"),
    ("openrouter", "mistralai/mistral-large-2407"),
    ("openrouter", "openai/gpt-oss-120b"),
    ("openrouter", "qwen/qwen3.6-27b"),
    ("cloudflare", "@cf/meta/llama-3.3-70b-instruct-fp8-fast"),
    ("groq", "llama-3.3-70b-versatile"),
    ("groq", "llama-3.1-8b-instant"),
]

# Лимиты размера вложений Discord по уровню буста сервера
# tier 0/1 → 8 MB, tier 2 → 25 MB, tier 3 → 50 MB
ATTACHMENT_LIMITS: dict[int, int] = {
    0: 8 * 1024 * 1024,
    1: 8 * 1024 * 1024,
    2: 25 * 1024 * 1024,
    3: 50 * 1024 * 1024,
}
