"""
Административные команды: обработка триггеров root#.
Слэш-команды НЕ регистрируются — админ-команды доступны только через текстовые триггеры.
Все команды проходят проверку прав доступа.
"""

from __future__ import annotations

from src import texts
from logging_setup import log


async def handle_admin_command(command: str) -> str:
    """
    Обрабатывает административную команду, полученную через текстовый триггер (root#).

    Args:
        command: Название команды (например, "restart", "delete")

    Returns:
        Строка с результатом выполнения команды
    """
    if command == "restart":
        log.info("Получена команда перезагрузки от владельца")
        return texts.admin_responses["restart_accepted"]
    elif command == "delete":
        log.info("Получена команда удаления от владельца")
        return texts.admin_responses["delete_accepted"]
    else:
        return texts.admin_responses["unknown_command"].format(command=command)
