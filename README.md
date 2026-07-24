# Expie Bot — модульная версия

## Структура

| Файл | Назначение |
|------|-----------|
| `main.py` | Точка входа. Запускает бота и веб-сервер для Render. |
| `config.py` | Все ключи API, системный промпт, константы. |
| `api_client.py` | Работа с AI: Groq + OpenRouter fallback, история диалогов. |
| `commands_bot.py` | Все команды: !экспи, !арт, !ген, !lore, !забыть. |
| `handlers.py` | Обработка сообщений: пинги, @упоминания, фильтры, автоответ. |

## Что изменилось на Render

**Start Command:**
```
python main.py
```

(было `python bot_expie_env.py`, стало `python main.py`)

**Environment Variables:**
- `GROQ_API_KEY` — обязательно
- `DISCORD_TOKEN` — обязательно
- `OPENROUTER_API_KEY` — опционально (для fallback-моделей)

## Как добавить новую команду

1. Откройте `commands_bot.py`
2. Добавьте функцию внутри `register_commands(bot)`:
```python
@bot.command(name="моя_команда")
async def cmd_mine(ctx, *, arg):
    await ctx.reply(f"Ответ: {arg}")
```
3. Перезалейте на GitHub → Render обновит автоматически.
