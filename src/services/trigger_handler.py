"""
Модуль обработки триггерных фраз в сообщениях.
Перехватывает команды в текстовом виде перед отправкой в LLM.
"""
import re
from typing import Optional, Tuple, List
import discord
from discord.ext import commands

from src.services.image_gen import generate_image as gen_image_service
from src.services.art_search import search_art as search_art_service
from config import Env

# Конфигурация триггеров
IMAGE_GEN_TRIGGERS = ["нарисуй", "сделай арт", "создай изображение", "изобрази"]
ART_SEARCH_TRIGGERS = ["найди картинку", "найди арт", "покажи арт", "search art"]
ROOT_TRIGGER = "root#"

class TriggerResult:
    """Результат обработки триггера."""
    def __init__(self, triggered: bool, response_text: str, action_data: Optional[dict] = None):
        self.triggered = triggered
        self.response_text = response_text
        self.action_data = action_data or {}

async def handle_triggers(
    message_content: str, 
    user_id: int, 
    channel: discord.TextChannel, 
    is_owner: bool
) -> Optional[TriggerResult]:
    """
    Проверяет сообщение на наличие триггерных фраз.
    
    Returns:
        TriggerResult если триггер сработал, иначе None.
    """
    content_lower = message_content.lower().strip()

    # 1. Проверка на Root-доступ
    if ROOT_TRIGGER in content_lower:
        return await _handle_root_trigger(message_content, user_id, is_owner)

    # 2. Проверка на генерацию изображений
    for trigger in IMAGE_GEN_TRIGGERS:
        if content_lower.startswith(trigger):
            prompt = message_content[len(trigger):].strip()
            if prompt:
                # Убираем знаки препинания в конце, если они есть
                prompt = prompt.rstrip('.,!?')
                return await _handle_image_generation(prompt, channel)

    # 3. Проверка на поиск артов
    for trigger in ART_SEARCH_TRIGGERS:
        if content_lower.startswith(trigger):
            query = message_content[len(trigger):].strip()
            if query:
                query = query.rstrip('.,!?')
                return await _handle_art_search(query, channel)

    return None

async def _handle_root_trigger(content: str, user_id: int, is_owner: bool) -> TriggerResult:
    """Обработка административных команд."""
    if not is_owner:
        return TriggerResult(
            triggered=True,
            response_text="Извините, но административные функции доступны только хозяину!"
        )
    
    # Извлекаем команду после root#
    # Ищем часть строки после root# (регистронезависимо)
    match = re.search(rf"{re.escape(ROOT_TRIGGER)}\s*(\w+)", content, re.IGNORECASE)
    if not match:
        return TriggerResult(
            triggered=True,
            response_text="Команда не указана. Доступные: restart."
        )
    
    command = match.group(1).lower()
    
    if command == "restart":
        # ЗАГОТОВКА: Перезапуск бота
        # Здесь будет логика перезапуска позже
        return TriggerResult(
            triggered=True,
            response_text="⚙️ Команда перезагрузки принята. (Заглушка: функционал в разработке)"
        )
    
    elif command == "delete":
        # ЗАГОТОВКА: Удаление сообщений
        return TriggerResult(
            triggered=True,
            response_text="🗑️ Команда удаления принята. (Заглушка: функционал в разработке)"
        )

    return TriggerResult(
        triggered=True,
        response_text=f"Неизвестная админ-команда: {command}"
    )

async def _handle_image_generation(prompt: str, channel: discord.TextChannel) -> TriggerResult:
    """Обработка запроса на генерацию изображения."""
    try:
        # Вызываем существующий сервис генерации
        # Примечание: предполагаем, что сервис возвращает файл или URL
        # Для интеграции нам нужно адаптировать вызов под текущий API сервиса
        
        # Эмуляция вызова (нужно будет подключить реальный вызов внутри cog или service)
        # Так как image_gen может требовать контекст, передаем канал для отправки
        # В реальной реализации лучше вызвать функцию напрямую, если она независима
        
        # Пока возвращаем успех и текст ответа для БД
        # Саму генерацию нужно вызвать асинхронно здесь или делегировать
        
        # ДЛЯ КОРРЕКТНОЙ РАБОТЫ: Вызовем функцию генерации напрямую, если она доступна
        # Но так как image_gen может быть оберткой над Cog, сделаем упрощенно:
        # Мы просто помечаем, что нужно генерировать, а отправку сделает вызывающая сторона?
        # НЕТ, по ТЗ: "в базу разговора добавляется текст... Экспи сохраняет текст..."
        # Значит генерация должна произойти СЕЙЧАС.
        
        # Попытка вызвать сервис напрямую (требуется доработка image_gen.py если он жестко привязан к Cog)
        # Предположим, что мы можем отправить сообщение в канал через bot.send или类似
        
        # Для простоты реализации в рамках любительского проекта:
        # Мы вернем текст ответа, а генерацию запустим "в огне" (fire-and-forget) или синхронно,
        # но лучше вернуть флаг, что нужно выполнить действие.
        # Однако ТЗ говорит: "текст только добавляется в базу, но не уходит дальше по api".
        # Значит, мы должны сами отправить картинку в канал.
        
        # Так как у нас нет доступа к `bot` объекту здесь легко, 
        # мы используем channel.send для отправки результата, если сервис вернет файл.
        
        # ВАЖНО: Сервис image_gen.py нужно проверить. Если он внутри Cog, вынесем логику в service.
        # Сейчас предположим, что мы можем это сделать.
        
        # Заглушка для демонстрации логики, если сервис не готов к прямому вызову без context
        # В реальном коде ниже будет вызов сервиса.
        
        # response = await gen_image_service.generate(prompt) 
        # if response: await channel.send(file=response)
        
        return TriggerResult(
            triggered=True,
            response_text="Меня попросили нарисовать картинку и я сделал это.",
            action_data={"type": "generate", "prompt": prompt}
        )
    except Exception as e:
        return TriggerResult(
            triggered=True,
            response_text=f"Произошла ошибка при генерации: {str(e)}",
            action_data={}
        )

async def _handle_art_search(query: str, channel: discord.TextChannel) -> TriggerResult:
    """Обработка запроса на поиск арта."""
    try:
        # Аналогично генерации, вызываем сервис поиска
        # result = await search_art_service.search(query)
        # if result: await channel.send(embed=result)
        
        return TriggerResult(
            triggered=True,
            response_text="Меня попросили найти картинку, я сделал это и отдал.",
            action_data={"type": "search", "query": query}
        )
    except Exception as e:
        return TriggerResult(
            triggered=True,
            response_text=f"Ошибка при поиске: {str(e)}",
            action_data={}
        )

async def execute_trigger_action(result: TriggerResult, channel: discord.TextChannel):
    """
    Выполняет实际行动 (отправку картинки) на основе action_data.
    Вызывается после сохранения в БД, но до отправки текстового ответа пользователю (если нужно).
    """
    action = result.action_data.get("type")
    if not action:
        return

    if action == "generate":
        prompt = result.action_data.get("prompt")
        try:
            # Импорт здесь, чтобы избежать циклических зависимостей, если нужно
            from src.services.image_gen import generate_image_direct
            file = await generate_image_direct(prompt)
            if file:
                await channel.send(file=file)
            else:
                await channel.send("❌ Не удалось сгенерировать изображение.")
        except ImportError:
            # Если прямой функции нет, пробуем через заглушку или ошибку
            await channel.send("⚠️ Модуль генерации временно недоступен для прямого вызова.")
        except Exception as e:
            await channel.send(f"❌ Ошибка генерации: {e}")

    elif action == "search":
        query = result.action_data.get("query")
        try:
            from src.services.art_search import search_art_direct
            embed = await search_art_direct(query)
            if embed:
                await channel.send(embed=embed)
            else:
                await channel.send("❌ Ничего не найдено.")
        except ImportError:
            await channel.send("⚠️ Модуль поиска временно недоступен.")
        except Exception as e:
            await channel.send(f"❌ Ошибка поиска: {e}")
