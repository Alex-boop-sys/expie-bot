import aiohttp
import random
from config import env, var, log
from Cogs.dicts import dicts

# ============ КОНФИГУРАЦИЯ ============
# Максимальное количество сообщений в истории диалога (чтобы не перегружать контекст LLM)
MAX_HISTORY = 10

# Таймауты для API-провайдеров (в секундах)
TIMEOUT_CLOUDFLARE = 25
TIMEOUT_GROQ = 25
TIMEOUT_OPENROUTER = 25

# История диалогов в оперативной памяти (in-memory, очищается при рестарте)
conversation_history = {}


# ============ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ============

def _build_messages(user_id, user_name, message):
    """
    Собирает список сообщений для LLM:
    системный промпт (персонаж Экспи) + история + текущее сообщение пользователя.
    """
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Экспи видит имя собеседника (требование из системного промпта)
    enriched = f"{user_name}: {message}"
    conversation_history[user_id].append({"role": "user", "content": enriched})

    # Берём только последние N сообщений — старые вытесняются, экономим токены
    history = conversation_history[user_id][-MAX_HISTORY:]
    return [{"role": "system", "content": dicts.def_prompt}] + history


def _save_response(user_id, text):
    """
    Сохраняет ответ ассистента в историю и возвращает безопасный для Discord текст.
    Экранируем звёздочки, чтобы Discord не интерпретировал их как markdown.
    """
    conversation_history[user_id].append({"role": "assistant", "content": text})
    return text.replace("*", "\\*")

def _is_censorship(text: str) -> bool:
    """Проверяет, является ли ответ стандартной цензурной заглушкой LLM."""
    if not text:
        return False
    lowered = text.lower().strip().rstrip(".!")
    return any(phrase in lowered for phrase in dicts.censor_phrases)


# ============ API КЛИЕНТЫ ============

async def _call_cloudflare(model, messages):
    """
    Вызов Cloudflare Workers AI.
    Первый в цепочке fallback: стабильный, редко падает, бесплатный tier.
    """
    # Если ключи не настроены — молча пропускаем этот провайдер
    if not env.cloudflare_account_id or not env.cloudflare_api_token:
        log.type("CLOUDFLARE").warning("Ключи Cloudflare не настроены, пропускаем")
        return None

    url = (
        f"https://api.cloudflare.com/client/v4/accounts/"
        f"{env.cloudflare_account_id}/ai/run/{model}"
    )

    # Cloudflare принимает стандартный OpenAI-compatible chat-формат
    payload = {
        "messages": messages,
        "max_tokens": 500,
        "temperature": 0.85,
        "top_p": 0.9
    }

    async with aiohttp.ClientSession() as session:
        log.type("CLOUDFLARE").info(f"Попытка вызвать Cloudflare: {model}")
        try:
            async with session.post(
                url,
                headers={"Authorization": f"Bearer {env.cloudflare_api_token}"},
                json=payload,
                timeout=aiohttp.ClientTimeout(total=TIMEOUT_CLOUDFLARE)
            ) as response:
                if response.status == 429:
                    log.type("CLOUDFLARE").warning("429 — дневной лимит neurons исчерпан")
                    return None
                if response.status != 200:
                    log.type("CLOUDFLARE").warning(f"Ошибка HTTP {response.status}")
                    return None

                data = await response.json()

                # Cloudflare оборачивает ответ в {success, result, errors}
                if not data.get("success"):
                    err = data.get("errors", [{}])[0]
                    log.type("CLOUDFLARE").warning(f"Ошибка API: {err.get('message', 'unknown')}")
                    return None

                # Текст ответа лежит в result.response (для instruct-моделей)
                result = data.get("result", {})
                return result.get("response")

        except Exception as e:
            log.type("CLOUDFLARE").warning(f"Исключение: {e}")
            return None


async def _call_groq(model, messages):
    """Вызов Groq API"""
    async with aiohttp.ClientSession() as session:
        log.type("GROQ").info(f"Попытка вызвать GROQ: {model}")
        headers = {
            "Authorization": f"Bearer {env.groq_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.85,
            "max_tokens": 500,
            "top_p": 0.9
        }
        try:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=TIMEOUT_GROQ)
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


async def _call_openrouter(model, messages):
    """Вызов OpenRouter API. Финальный fallback, если все остальные упали."""
    if not env.openrouter_api_key:
        return None
    async with aiohttp.ClientSession() as session:
        log.type("OPENROUTER").info(f"Попытка вызвать OpenRouter: {model}")
        headers = {
            "Authorization": f"Bearer {env.openrouter_api_key}",
            "HTTP-Referer": "https://github.com",
            "X-Title": "Expie Bot",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.85,
            "max_tokens": 500,
            "top_p": 0.9
        }
        try:
            async with session.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=TIMEOUT_OPENROUTER)
            ) as response:
                if response.status != 200:
                    log.bind("[OPENROUTER]").warning(f"{model}: ошибка {response.status}")
                    return None
                data = await response.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            log.type("OPENROUTER").warning(f"Исключение: {e}")
            return None


# ============ ОСНОВНАЯ ЛОГИКА ============

async def ask_ai(user_id, user_name, message):
    """
    Отправляет сообщение в AI через цепочку fallback-провайдеров.
    Порядок: OpenRouter → Cloudflare →Groq.
    Если все отказали — возвращает заглушку.
    """
    messages = _build_messages(user_id, user_name, message)

    for provider, model in var.fallback_models:
        try:
            log.type(provider.upper()).info(f"Использование модели {model}")

            # Вызываем соответствующий API-клиент по имени провайдера
            #if provider == "openrouter":
            #    result = await _call_openrouter(model, messages)
            #elif provider == "cloudflare":
            #    result = await _call_cloudflare(model, messages)
            if provider == "groq":
                import inspect
                print(f"DEBUG _call_groq: {type(_call_groq)}")
                print(f"DEBUG module: {_call_groq.__module__ if hasattr(_call_groq, '__module__') else 'N/A'}")
                print(f"DEBUG signature: {inspect.signature(_call_groq)}")
                result = await _call_groq(model, messages)
            else:
                log.warning(f"Неизвестный провайдер: {provider}")
                continue

            # Если получили непустой ответ — сохраняем и возвращаем
            if result:
                # === ФИЛЬТР ЦЕНЗУРНЫХ ЗАГЛУШЕК ===
                if _is_censorship(result):
                    result = random.choice(dicts.expie_censor_replies)
                    log.type("FILTER").info("Цензурная заглушка заменена на реплику Экспи")
                
                return _save_response(user_id, result)

        except Exception as e:
            log.type(provider.upper()).warning(f"Ошибка модели {model}: {e}")
            continue

    # Все провайдеры отказали — бот «засыпает»
    return "😴 *зевнул, потянулся* Устал совсем... Ухожу спать до завтра, бро. Не будите меня, ладно? 🌙"


def clear_history(user_id):
    """Очищает историю диалога пользователя. Возвращает True, если история была."""
    if user_id in conversation_history:
        conversation_history[user_id] = []
        return True
    return False