"""
Заготовка: поиск ключевых слов в сообщениях («нарисуй», «найди» и т.д.).

Контракт:
    match_trigger(text) -> Trigger | None

Trigger — dataclass с полями:
    action  — строка ("generate", "search", ...)
    payload — очищенный запрос

Хендлеры вызывают match_trigger() после проверок пинга/reply
и делегируют в те же сервисы, что и слэш-команды.
Таблица «ключевое слово → действие» хранится словарём в одном месте.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Trigger:
    """Результат срабатывания ключевого слова."""

    action: str  # "generate" | "search" | ...
    payload: str  # очищенный запрос без ключевого слова


# Таблица «ключевое слово → действие».
# Расширять одной строкой.
# Пока пустая — реализация на будущее.
TRIGGER_MAP: dict[str, str] = {
    # "нарисуй": "generate",
    # "draw": "generate",
    # "найди арт": "search",
}


def match_trigger(text: str) -> Optional[Trigger]:
    """
    Ищет ключевое слово в начале текста (без учёта регистра).
    Возвращает Trigger или None, если ничего не найдено.
    """
    text_lower = text.lower().strip()

    for keyword, action in TRIGGER_MAP.items():
        if text_lower.startswith(keyword):
            payload = text[len(keyword) :].strip()
            return Trigger(action=action, payload=payload)

    return None
