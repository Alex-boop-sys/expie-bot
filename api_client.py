import aiohttp
from config import GROQ_API_KEY, OPENROUTER_API_KEY, SYSTEM_PROMPT, FALLBACK_MODELS

# Conversation history storage (in-memory)
conversation_history = {}


async def _call_groq(model, messages):
    """Вызов Groq API. Возвращает текст или None при ошибке/лимите."""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.85,
            "max_tokens": 600,
            "top_p": 0.9
        }
        async with session.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=20)
        ) as response:
            if response.status == 429:
                print(f"[Groq] {model}: 429 — лимит")
                return None
            if response.status != 200:
                print(f"[Groq] {model}: ошибка {response.status}")
                return None
            data = await response.json()
            return data["choices"][0]["message"]["content"]


async def _call_openrouter(model, messages):
    """Вызов OpenRouter API. Возвращает текст или None при ошибке."""
    if not OPENROUTER_API_KEY:
        return None
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com",
            "X-Title": "Expie Bot",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.85,
            "max_tokens": 600,
            "top_p": 0.9
        }
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=25)
        ) as response:
            if response.status != 200:
                print(f"[OpenRouter] {model}: ошибка {response.status}")
                return None
            data = await response.json()
            return data["choices"][0]["message"]["content"]


async def ask_ai(user_id, user_name, message):
    """Отправка в AI с fallback по моделям."""

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    enriched_message = f"{user_name}: {message}"
    conversation_history[user_id].append({"role": "user", "content": enriched_message})

    history = conversation_history[user_id][-10:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    for provider, model in FALLBACK_MODELS:
        try:
            if provider == "groq":
                result = await _call_groq(model, messages)
            else:
                result = await _call_openrouter(model, messages)

            if result:
                conversation_history[user_id].append({
                    "role": "assistant",
                    "content": result
                })
                return result
        except Exception as e:
            print(f"[Fallback] {provider}/{model} failed: {e}")
            continue

    return "😴 *зевнул, потянулся* Устал совсем... Ухожу спать до завтра, бро. Не будите меня, ладно? 🌙"


def clear_history(user_id):
    """Очистить историю диалога пользователя."""
    if user_id in conversation_history:
        conversation_history[user_id] = []
        return True
    return False
