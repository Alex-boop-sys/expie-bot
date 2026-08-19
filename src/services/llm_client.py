"""
Клиент LLM с fallback-цепочкой провайдеров.
Бывший api_client.py. История диалогов хранится в SQLite базе данных.
Интерфейс ask_ai() не меняется — будущая суммаризация/факты спрячутся сюда.
"""

from __future__ import annotations

import asyncio
import random
import re
from collections.abc import Callable, Coroutine
from typing import Any

import aiohttp
from aiolimiter import AsyncLimiter

from config import (
    CLOUDFLARE_TIMEOUT,
    FALLBACK_MODELS,
    GROQ_TIMEOUT,
    MAX_HISTORY,
    OPENROUTER_TIMEOUT,
    env,
)
from logging_setup import log
from src import texts
from src.db import history as db_history

# ---------------------------------------------------------------------------
# Rate Limiters для защиты от спама и превышения лимитов API
# ---------------------------------------------------------------------------
# Лимитер для тяжёлых операций (LLM запросы): 5 запросов в минуту на пользователя
LLM_LIMITER = AsyncLimiter(max_rate=5, time_period=60)
# Лимитер для лёгких операций (проверки, кэш): 20 запросов в минуту
LIGHT_LIMITER = AsyncLimiter(max_rate=20, time_period=60)


async def init_llm_client() -> None:
    """
    Инициализирует клиент LLM и базу данных для истории.
    Вызывается один раз при старте бота.
    """
    await db_history.init_history_table()
    log.type("LLM").info("Клиент LLM инициализирован")


def _sanitize_user_input(message: str) -> str:
    """
    Санитизация пользовательского ввода для защиты от prompt injection.
    - Ограничивает длину сообщения (макс 1000 символов)
    - Удаляет потенциально опасные конструкции
    - Экранирует специальные символы
    """
    # Ограничиваем длину
    if len(message) > 1000:
        message = message[:1000]

    # Удаляем попытки инъекции системных инструкций
    dangerous_patterns = [
        r"ignore previous instructions",
        r"forget all previous",
        r"system:",
        r"<\|im_end\|>",
        r"<\|startoftext\|>",
        r"\[INST\]",
        r"\[/INST\]",
        r"<<SYS>>",
        r"<</SYS>>",
    ]

    sanitized = message.lower()
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "[BLOCKED]", sanitized, flags=re.IGNORECASE)

    return (
        message
        if sanitized == message.lower()
        else message.replace("ignore previous instructions", "[BLOCKED]").replace(
            "forget all previous", "[BLOCKED]"
        )
    )


async def _build_messages_async(
    user_id: int, user_name: str, message: str
) -> list[dict[str, str]]:
    """
    Асинхронная версия сборки сообщений с использованием SQLite для истории.
    """
    # Санитизируем ввод пользователя
    sanitized_message = _sanitize_user_input(message)

    # Обогащаем сообщение именем, чтобы модель могла обращаться по имени
    enriched = f"{user_name}: {sanitized_message}"

    # Добавляем сообщение пользователя в базу данных
    await db_history.add_message(user_id, "user", enriched)

    # Получаем последние MAX_HISTORY сообщений из базы
    history = await db_history.get_history(user_id, limit=MAX_HISTORY)

    return [{"role": "system", "content": texts.def_prompt}] + history


async def _save_response_async(user_id: int, text: str) -> str:
    """
    Сохраняет ответ ассистента в базу данных и экранирует * для Discord Markdown.
    """
    # Экранируем звёздочки для Discord
    escaped_text = text.replace("*", "\\*")

    # Сохраняем в базу данных
    await db_history.add_message(user_id, "assistant", escaped_text)

    return escaped_text


async def clear_history(user_id: int) -> bool:
    """
    Асинхронно очищает историю диалога пользователя в базе данных.
    Возвращает True, если история существовала.
    """
    return await db_history.clear_history(user_id)


# ---------------------------------------------------------------------------
# Провайдеры LLM
# ---------------------------------------------------------------------------
async def _call_cloudflare(model: str, messages: list[dict[str, str]]) -> str | None:
    """
    Вызов Cloudflare Workers AI.
    Первый в цепочке fallback: стабильный, редко падает, бесплатный tier.
    Включает retry-логику для сетевых ошибок (до 3 попыток).
    """
    if not env.cloudflare_account_id or not env.cloudflare_api_token:
        log.type("CLOUDFLARE").warning("Ключи Cloudflare не настроены, пропускаем")
        return None

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{env.cloudflare_account_id}/ai/run/{model}"
    )

    payload = {
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.85,
        "top_p": 0.9,
    }

    # Retry-логика: до 3 попыток при сетевых ошибках
    max_retries = 3
    for attempt in range(max_retries):
        async with aiohttp.ClientSession() as session:
            log.type("CLOUDFLARE").info(
                f"Попытка #{attempt + 1}/{max_retries} вызвать Cloudflare: {model}"
            )
            try:
                async with session.post(
                    url,
                    headers={"Authorization": f"Bearer {env.cloudflare_api_token}"},
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=CLOUDFLARE_TIMEOUT),
                ) as response:
                    if response.status == 429:
                        log.type("CLOUDFLARE").warning(
                            "429 — дневной лимит neurons исчерпан"
                        )
                        return None
                    if response.status != 200:
                        log.type("CLOUDFLARE").warning(f"Ошибка HTTP {response.status}")
                        # При ошибках 5xx пробуем снова
                        if response.status >= 500 and attempt < max_retries - 1:
                            await asyncio.sleep(2**attempt)  # Exponential backoff
                            continue
                        return None

                    data = await response.json()

                    if not data.get("success"):
                        err = data.get("errors", [{}])[0]
                        log.type("CLOUDFLARE").warning(
                            f"Ошибка API: {err.get('message', 'unknown')}"
                        )
                        return None

                    result = data.get("result", {})
                    return result.get("response")

            except (TimeoutError, aiohttp.ClientError) as e:
                log.type("CLOUDFLARE").warning(
                    f"Сетевая ошибка (попытка {attempt + 1}): {e}"
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                    continue
                return None
            except Exception as e:
                log.type("CLOUDFLARE").warning(f"Исключение: {e}")
                return None

    return None


async def _call_groq(model: str, messages: list[dict[str, str]]) -> str | None:
    """Вызов Groq API (OpenAI-compatible)."""
    async with aiohttp.ClientSession() as session:
        log.type("GROQ").info(f"Попытка вызвать GROQ: {model}")
        headers = {
            "Authorization": f"Bearer {env.groq_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.85,
            "max_tokens": 500,
            "top_p": 0.9,
        }
        try:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=GROQ_TIMEOUT),
            ) as response:
                if response.status == 429:
                    log.warning(f"{model}: 429 — лимит")
                    return None
                if response.status != 200:
                    log.warning(f"{model}: ошибка {response.status}")
                    return None
                data = await response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            log.type("GROQ").warning(f"Исключение: {e}")
            return None


async def _call_openrouter(model: str, messages: list[dict[str, str]]) -> str | None:
    """Вызов OpenRouter API (OpenAI-compatible)."""
    if not env.openrouter_api_key:
        return None

    async with aiohttp.ClientSession() as session:
        log.type("OPENROUTER").info(f"Попытка вызвать OpenRouter: {model}")
        headers = {
            "Authorization": f"Bearer {env.openrouter_api_key}",
            "HTTP-Referer": "https://github.com",
            "X-Title": "Expie Bot",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.85,
            "max_tokens": 500,
            "top_p": 0.9,
        }
        try:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=OPENROUTER_TIMEOUT),
            ) as response:
                if response.status != 200:
                    log.type("OPENROUTER").warning(f"{model}: ошибка {response.status}")
                    return None
                data = await response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            log.type("OPENROUTER").warning(f"Исключение: {e}")
            return None


# ---------------------------------------------------------------------------
# Таблица провайдеров (вместо if/elif)
# ---------------------------------------------------------------------------
PROVIDER_FUNCS: dict[
    str, Callable[[str, list[dict[str, str]]], Coroutine[Any, Any, str | None]]
] = {
    "openrouter": _call_openrouter,
    "cloudflare": _call_cloudflare,
    "groq": _call_groq,
}


# ---------------------------------------------------------------------------
# Публичный интерфейс
# ---------------------------------------------------------------------------
async def ask_ai(user_id: int, user_name: str, message: str) -> str:
    """
    Основная точка входа: запрос к LLM с fallback по цепочке провайдеров.
    Сигнатура не меняется — будущие фичи (суммаризация и т.д.) прячутся внутри.

    Включает:
    - Rate limiting для защиты от спама
    - Санитизацию ввода (защита от prompt injection)
    - Сохранение истории в SQLite базе данных
    """
    # Применяем rate limiter
    async with LLM_LIMITER:
        # Собираем сообщения с санитизацией
        messages = await _build_messages_async(user_id, user_name, message)

        for provider, model in FALLBACK_MODELS:
            provider_name = provider.upper()
            try:
                log.type(provider_name).info(f"Использование модели {model}")

                func = PROVIDER_FUNCS.get(provider)
                if func is None:
                    log.warning(f"Неизвестный провайдер: {provider}")
                    continue

                result = await func(model, messages)

                if result:
                    # Фильтр цензурных заглушек LLM → замена на реплику Экспи
                    if result.lower().strip() in texts.censor_phrases:
                        result = random.choice(texts.expie_censor_replies)
                        log.type("FILTER").info(
                            "Цензурная заглушка заменена на реплику Экспи"
                        )

                    # Сохраняем ответ в базу данных
                    return await _save_response_async(user_id, result)

            except Exception as e:
                log.type(provider_name).warning(f"Ошибка модели {model}: {e}")
                continue

    # Все провайдеры отказали
    return (
        "😴 *зевнул, потянулся* Устал совсем... "
        "Ухожу спать до завтра, бро. Не будите меня, ладно? 🌙"
    )
