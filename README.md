# Expie Bot

Discord-бот персонажа **Экспи** (Эксперимент SAW-01) из вселенной Casualties: Unknown.

Маленький пушистый гибрид с оранжевыми глазами, который общается, ищет арты, генерирует картинки и обнимает друзей.

## Требования

- Python 3.10+
- Discord-бот (токен)
- API-ключи хотя бы одного LLM-провайдера (OpenRouter / Cloudflare / Groq)

## Установка

```bash
git clone <repo>
cd expie-bot
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

## Настройка

Скопируйте `.env.example` → `.env` и заполните
На проде файл можно положить в `/etc/bots/expie-bot/.env` — бот подхватит его автоматически.

## Запуск

```bash
python main.py
```

## Структура проекта

```
expie-bot/
├── main.py              # Точка входа
├── config.py            # Env, пути, константы
├── bot_instance.py      # Экземпляр commands.Bot
├── logging_setup.py     # Логгер
├── .env.example
├── requirements.txt
├── ruff.toml
├── README.md
│
├── resources/
│   ├── prompt.md        # Системный промпт (лор)
│   └── phrases.json     # Реплики
│
├── src/
│   ├── events.py        # on_ready, on_message
│   ├── handlers.py      # Пинги, reply, имена
│   ├── utils.py         # Утилиты + скачивание картинок
│   ├── texts.py         # Загрузка resources/
│   │
│   ├── commands/
│   │   ├── ai.py        # /спросить, /забыть
│   │   ├── art.py       # /арт, /фурь
│   │   ├── generation.py# /ген
│   │   ├── social.py    # /обнять, /шип
│   │   └── admin.py     # Заготовка админ-команд
│   │
│   ├── services/
│   │   ├── llm_client.py    # LLM + fallback
│   │   ├── art_search.py    # e621 / Furbooru
│   │   ├── image_gen.py     # Pollinations
│   │   └── triggers.py      # Заготовка ключевых слов
│   │
│   └── db/                  # Заготовка SQLite
│
└── Logs/
```

## Команды

| Команда     | Описание                          |
|-------------|-----------------------------------|
| `/спросить` | Задать вопрос Экспи               |
| `/забыть`   | Очистить историю диалога          |
| `/арт`      | Найти арт на e621                 |
| `/фурь`     | Найти SFW-арт на Furbooru         |
| `/ген`      | Сгенерировать картинку            |
| `/обнять`   | Обнять кого-то                    |
| `/шип`      | Случайная пара из онлайна         |

Также бот отвечает на упоминания, reply и обращение по имени.

## Разработка

Линтер/форматтер — **Ruff**:

```bash
ruff check --fix .
ruff format .
```
