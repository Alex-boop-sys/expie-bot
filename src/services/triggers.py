"""
Заготовка: поиск ключевых слов в сообщениях («нарисуй», «найди» и т.д.).

Контракт:
    match_trigger(text) -> Trigger | None

Trigger — dataclass с полями:
    action  — строка ("generate", "search", "admin", ...)
    payload — очищенный запрос
    is_admin — флаг административной команды
    admin_command — название админ-команды (если is_admin=True)

Хендлеры вызывают match_trigger() после проверок пинга/reply
и делегируют в те же сервисы, что и слэш-команды.
Таблица «ключевое слово → действие» хранится словарём в одном месте.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Trigger:
    """Результат срабатывания ключевого слова."""

    action: str  # "generate" | "search" | "admin" | ...
    payload: str  # очищенный запрос без ключевого слова
    is_admin: bool = False  # флаг административной команды
    admin_command: str | None = None  # название админ-команды


# Таблица «ключевое слово → действие».
# Расширять одной строкой.
TRIGGER_MAP: dict[str, str] = {
    # Генерация изображений
    "нарисуй": "generate",
    "сделай арт": "generate",
    "создай изображение": "generate",
    "изобрази": "generate",
    "генерируй": "generate",
    # Поиск артов
    "найди картинку": "search",
    "найди арт": "search",
    "покажи арт": "search",
    "search art": "search",
    "найти арт": "search",
}

# Административный префикс
ROOT_PREFIX = "root#"


def match_trigger(
    text: str, user_id: int, owner_id: int, co_owner_id: int | None = None
) -> Trigger | None:
    """
    Ищет ключевое слово в тексте (без учёта регистра).
    Проверяет root# префикс для административных команд.

    Args:
        text: Текст сообщения
        user_id: ID пользователя
        owner_id: ID владельца
        co_owner_id: ID со-владельца (опционально)

    Returns:
        Trigger или None, если ничего не найдено.
    """
    text_lower = text.lower().strip()

    # 1. Проверка на административную команду (root#)
    if ROOT_PREFIX in text_lower:
        return _check_root_command(text, user_id, owner_id, co_owner_id)

    # 2. Проверка на обычные триггеры
    for keyword, action in TRIGGER_MAP.items():
        if text_lower.startswith(keyword):
            payload = text[len(keyword) :].strip()
            # Убираем знаки препинания в конце
            payload = payload.rstrip(".,!?")
            if payload:  # Только если есть текст после триггера
                return Trigger(action=action, payload=payload)

    return None


def _check_root_command(
    text: str, user_id: int, owner_id: int, co_owner_id: int | None = None
) -> Trigger | None:
    """
    Проверяет и обрабатывает административную команду root#.

    Returns:
        Trigger с action="admin" если это команда,
        Trigger с action="admin_denied" если нет прав,
        None если это не команда root#.
    """
    import re

    # Проверяем наличие root# в тексте
    pattern = rf"{re.escape(ROOT_PREFIX)}\s*(\w+)"
    match = re.search(pattern, text, re.IGNORECASE)

    if not match:
        return None

    # Проверка прав доступа
    is_owner = (user_id == owner_id) or (co_owner_id and user_id == co_owner_id)

    if not is_owner:
        return Trigger(action="admin_denied", payload="", is_admin=True)

    # Извлекаем команду
    command = match.group(1).lower()

    return Trigger(action="admin", payload=command, is_admin=True, admin_command=command)
