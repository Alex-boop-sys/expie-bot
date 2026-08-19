"""
Клиент LLM с fallback-цепочкой провайдеров.
Бывший api_client.py. История диалогов пока в памяти (dict).
Интерфейс ask_ai() не меняется — будущая суммаризация/факты спрячутся сюда.
"""

from __future__ import annotations

import random
from typing import Any, Callable, Coroutine, Optional

import aiohttp

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

# ---------------------------------------------------------------------------
# История диалогов (пока в памяти; позже можно подменить на SQLite)
# ---------------------------------------------------------------------------
conversation_history: dict[int, list[dict[str, str]]] = {}


def _build_messages(user_id: int, user_name: str, message: str) -> list[dict[str, str]]:
    """
    Собирает список сообщений для LLM:
    system-промпт + последние MAX_HISTORY сообщений пользователя.
    """
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Обогащаем сообщение именем, чтобы модель могла обращаться по имени
    enriched = f"{user_name}: {message}"
    conversation_history[user_id].append({"role": "user", "content": enriched})

    history = conversation_history[user_id][-MAX_HISTORY:]
    return [{"role": "system", "content": texts.def_prompt}] + history


def _save_response(user_id: int, text: str) -> str:
    """
    Сохраняет ответ ассистента в историю и экранирует * для Discord Markdown.
    """
    conversation_history[user_id].append({"role": "assistant", "content": text})
    return text.replace("*", "\\*")


def clear_history(user_id: int) -> bool:
    """
    Очищает историю диалога пользователя.
    Возвращает True, если история существовала.
    """
    if user_id in conversation_history:
        conversation_history[user_id] = []
        return True
    return False


# ---------------------------------------------------------------------------
# Провайдеры LLM
# ---------------------------------------------------------------------------
async def _call_cloudflare(
    model: str, messages: list[dict[str, str]]
) -> Optional[str]:
    """
    Вызов Cloudflare Workers AI.
    Первый в цепочке fallback: стабильный, редко падает, бесплатный tier.
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

    async with aiohttp.ClientSession() as session:
        log.type("CLOUDFLARE").info(f"Попытка вызвать Cloudflare: {model}")
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

        except Exception as e:
            log.type("CLOUDFLARE").warning(f"Исключение: {e}")
            return None


async def _call_groq(model: str, messages: list[dict[str, str]]) -> Optional[str]:
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


async def _call_openrouter(
    model: str, messages: list[dict[str, str]]
) -> Optional[str]:
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
                    log.type("OPENROUTER").warning(
                        f"{model}: ошибка {response.status}"
                    )
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
    str, Callable[[str, list[dict[str, str]]], Coroutine[Any, Any, Optional[str]]]
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
    """
    messages = _build_messages(user_id, user_name, message)

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

                return _save_response(user_id, result)

        except Exception as e:
            log.type(provider_name).warning(f"Ошибка модели {model}: {e}")
            continue

    # Все провайдеры отказали
    return (
        "😴 *зевнул, потянулся* Устал совсем... "
        "Ухожу спать до завтра, бро. Не будите меня, ладно? 🌙"
    )
