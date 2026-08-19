"""
Настройка логгера.
Вынесено в отдельный модуль, чтобы логгер был доступен раньше остальных компонентов
и не создавал циклических импортов.
"""

from __future__ import annotations

from fsvlog import FSVLog

from config import IS_SERVER, LOGS_DIR


def setup_logging() -> FSVLog:
    """
    Создаёт и возвращает настроенный экземпляр FSVLog.

    На проде (Linux) логи пишутся только в файл.
    Локально — и в файл, и в консоль.
    """
    return FSVLog(
        log_folder_path=LOGS_DIR,
        max_logs=10,
        log_format="{timestamp} [{level}] [{type}] ({filename}:{lineno}) {context} - {message}",
        log_level="DEBUG",
        filename_time_format="%Y%m%d_%H%M%S",
        time_format="[%Y-%m-%dT%H:%M:%S]",
        exception_format="full",
        file_only=IS_SERVER,
    )


# Глобальный логгер — импортируется как `from logging_setup import log`
log = setup_logging()
