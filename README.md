# Expie Bot — модульная версия

## Структура

| Файл | Назначение |
|------|-----------|
| `main.py` | Точка входа. Запускает бота и веб-сервер для Render. |
| `config.py` | Все ключи API, системный промпт, константы. |
| `api_client.py` | Работа с AI: Groq + OpenRouter fallback, история диалогов. |
| `commands_bot.py` | Все команды: !экспик, !арт, !ген, !lore, !забыть. |
| `handlers.py` | Обработка сообщений: пинги, @упоминания, фильтры, автоответ. |

**Start Command:**
```
python main.py
```
**Environment Variables:**
- `GROQ_API_KEY` — обязательно
- `DISCORD_TOKEN` — обязательно
- `OPENROUTER_API_KEY` — опционально (для fallback-моделей)


