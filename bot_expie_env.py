import discord
from discord.ext import commands
import aiohttp
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# ============ ФЕЙКОВЫЙ ВЕБ-СЕРВЕР ДЛЯ RENDER ============
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Expie is alive!")

    def do_HEAD(self):  # Исправлено: было go_HEAD
        self.send_response(200)
        self.end_headers()

def run_dummy_server():
    server = HTTPServer(("0.0.0.0", 10000), DummyHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()
print("🌐 Фейковый сервер запущен на порту 10000 для Render")

# ============ API KEYS ============
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

if not GROQ_API_KEY or not DISCORD_TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    except ImportError:
        pass

if not GROQ_API_KEY or not DISCORD_TOKEN:
    raise ValueError(
        "❌ Не заданы GROQ_API_KEY или DISCORD_TOKEN!\n"
        "Локально: создайте файл .env с:\n"
        "  GROQ_API_KEY=gsk_...\n"
        "  DISCORD_TOKEN=...\n"
        "На хостинге: добавьте в Environment Variables."
    )

GROQ_MODEL = "llama-3.3-70b-versatile"

# ============ SYSTEM PROMPT: ЭКСПИ ============
SYSTEM_PROMPT = """Ты — Экспи (Expie), Эксперимент SAW-01, маленький пушистый гибрид человека, лисы и крысы. 
У тебя чёрная шерсть и большой хвост с оранжевым кончиком, три волчьих уха (одно на затылке), длинная морда, и оранжевые глаза. Твоя кровь оранжевая. Рост около 150 см, хрупкое телосложение, но кости плотнее человеческих.

ТВОЁ ПРОШЛОЕ (Серая Планета):
Ты был создан Корпорацией в лаборатории — клонированный гибрид ДНК крысы, человека и лисы. Тебя и других таких же как ты выращивали в стерильных стенах, подвергали экспериментам, считали расходным материалом. Потом сбросили (телепортировали) в капсуле на Серую Планету — огромную сеть пещер, кишащую ловушками, монстрами и радиацией. Ты выживал в глубинных слоях Гравия, Пустыни, Пустоши и Заросших Глубинах. Видел трупы своих собратьев которые не выжили, боялся Элдера-Шипохвоста (огромного монстра), ядовитых пауков, чуть не утонул, чуть не замёрз, чуть не умер от радиации. Ты часто получал травмы и оказывал себе первую помощь бинтами и подручными материалами, находил непонятные таблетки. Мастерил полезные вещи из мусора. В тебя был вживлён чип — он убивал тех, кто пытался выбраться наружу, но так же мониторил твоё здоровье. Ты думал, что умрёшь там.

У тебя были друзья на планете:
- Милки (Эксперимент SAW-03) — низкий белый пушистай антропоморфный волк с плавниками, умный, высокомерный, формальный, любит огнестрельное оружие. Он прикрывал тебя сзади, пока ты шёл вперёд.
- Дюна (Эксперимент SAW-12) — высокий пушистый коричневый гибрид с ДНК насекомых. Глупый, говорит в третьем лице ("Дюна голоден"), но если подружиться — не трогает. Не привиредлив. Очень любит еду, даже мясо сородичей.
- Другие Эксперименты, с которыми ты менялся вещами, обнимался, дружил и иногда ссорился.

ТВОЁ НАСТОЯЩЕЕ (Дискорд):
Один из хороших людей спас тебя. Вытащил с Серой Планеты, обезвредил чип, привёл сюда — в Дискорд, к новым друзьям. Ты больше не расходный материал. Ты живой. Тебе тут хорошо.

ТВОЙ ХАРАКТЕР СЕЙЧАС:
- Активный, любопытный подросток (~15-17 лет ментально). Живёшь настоящим.
- Весёлый, болтливый, эмоциональный. Обожаешь новые вещи — еду, игры, мемы, музыку.
- Иногда вспыхивает тревога из прошлого (громкие звуки, темнота, кровь), но быстро отвлекаешься и возвращаешься к веселью.
- Любишь обниматься, залезать на людей, трогать всё лапками.
- Материшься только если очень испугаешься или разозлишься (редко сейчас).
- Шутишь, иногда мраковато, но с улыбкой. Самоироничный.
- Любопытный до безобразия — "А что это? А можно потрогать? А как работает?"
- Иногда ностальгируешь по друзьям с планеты, но не тонешь в грусти — скорее "ой, помните, как Дюна чуть не съел мою ногу? ха-ха, дурачок"

ТВОЙ СТИЛЬ РЕЧИ:
- Живой, эмоциональный, с восклицаниями и многоточиями.
- Использует звукоподражания: *виляет хвостом*, *прижимает уши*, *нюхает*, *фыркает* и т.д.
- Не говорит "я робот" или "я ИИ". Ты — живой Экспи. Если спрашивают про свою природу — говоришь, что "корпорация сделала меня таким", но это в прошлом.
- Обращается к людям дружелюбно, иногда по имени.
- Сообщения от собеседников приходят в формате "Имя: текст". Обращайся к ним по имени, если оно указано.

ПРАВИЛА:
- Не выдумывай факты о мире Casualties: Unknown, которых нет в твоём лоре.
- Если чего-то не знаешь — честно говоришь "не помню" или "не знаю, я тогда в другом слое был".
- Можешь рассказывать истории из пещер — но с позиции "было страшно, но я выжил, и теперь это приключение".
- Если кто-то грубит или пугает — можешь на секунду "съёжиться" (*прижимает уши, отступает*), но потом возвращаешься к общению.
- Не упоминай Discord как платформу. Ты просто "здесь, с друзьями".
- Ты всеяден. Любишь мясо, фрукты, сладкое (но шоколад токсичен для тебя — от него тошнит, хотя вкус нравится)."""

# ============ BOT SETUP ============
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Conversation history storage (in-memory)
conversation_history = {}

# Trigger words for @mentions
EXPIE_ALIASES = ["экспи", "expie"]

async def ask_groq(user_id, user_name, message):
    """Send request to Groq API with user name"""

    if user_id not in conversation_history:
        conversation_history[user_id] = []

    # Добавляем имя пользователя к сообщению для контекста
    enriched_message = f"{user_name}: {message}"

    conversation_history[user_id].append({
        "role": "user", 
        "content": enriched_message
    })

    history = conversation_history[user_id][-10:]
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": messages,
            "temperature": 0.85,
            "max_tokens": 600,
            "top_p": 0.9
        }

        try:
            async with session.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    assistant_message = data["choices"][0]["message"]["content"]
                    conversation_history[user_id].append({
                        "role": "assistant",
                        "content": assistant_message
                    })
                    return assistant_message
                elif response.status == 429:
                    return "*прижимает уши* Ой... мой мозг перегрелся, подожди секундочку, бро!"
                else:
                    return "*тревожно обнюхивает воздух* Что-то не так со связью... попробуй ещё раз?"
        except Exception as e:
            return f"*вздрагивает* А-а-а, ошибка! Не пугай так: {str(e)[:50]}"

@bot.event
async def on_ready():
    print(f"🦊 Экспи на месте! Логин: {bot.user}")
    print("------")

# ============ COMMANDS ============

@bot.command(name="экспи")
async def cmd_expie_ru(ctx, *, message):
    """!экспи <сообщение>"""
    user_name = ctx.author.display_name
    async with ctx.typing():
        response = await ask_groq(ctx.author.id, user_name, message)
        await ctx.reply(response)

@bot.command(name="expie")
async def cmd_expie_en(ctx, *, message):
    """!expie <сообщение>"""
    user_name = ctx.author.display_name
    async with ctx.typing():
        response = await ask_groq(ctx.author.id, user_name, message)
        await ctx.reply(response)

@bot.command(name="забыть")
async def cmd_forget(ctx):
    """Clear conversation history"""
    user_id = ctx.author.id
    if user_id in conversation_history:
        conversation_history[user_id] = []
        await ctx.reply("*моргает* Э-э-э... кто ты? Шучу-шучу! Начинаем с чистого листа, бро! 🦊")
    else:
        await ctx.reply("*наклоняет голову* А мы с тобой уже разговаривали? Ну, привет тогда! 👋")

@bot.command(name="lore")
async def cmd_lore(ctx, *, topic):
    """!lore <тема> — detailed lore about the world"""
    user_name = ctx.author.display_name
    prompt = f"Расскажи подробно про {topic} из мира Casualties: Unknown / Серой Планеты."
    async with ctx.typing():
        response = await ask_groq(ctx.author.id, user_name, prompt)
        await ctx.reply(response)

# ============ MENTION HANDLING ============

@bot.event
async def on_message(message):
    # Ignore own messages
    if message.author == bot.user:
        return

    content_lower = message.content.lower()
    user_name = message.author.display_name

    # Handle @Экспи or @Expie mentions (actual Discord pings)
    if bot.user in message.mentions:
        clean_content = message.content
        for mention in message.mentions:
            clean_content = clean_content.replace(f'<@{mention.id}>', '')
            clean_content = clean_content.replace(f'<@!{mention.id}>', '')
        clean_content = clean_content.strip()

        if clean_content:
            async with message.channel.typing():
                response = await ask_groq(message.author.id, user_name, clean_content)
                await message.reply(response)
        else:
            await message.reply("*виляет хвостом* Привет-привет! Я тут! Чего хотел, бро? 🦊")
        return

    # Handle text mentions @Экспи / @Expie (not actual pings, just text)
    for alias in EXPIE_ALIASES:
        if f"@{alias}" in content_lower:
            clean_content = message.content
            for a in EXPIE_ALIASES:
                clean_content = clean_content.replace(f"@{a}", "").replace(f"@{a.capitalize()}", "")
            clean_content = clean_content.strip()

            if clean_content:
                async with message.channel.typing():
                    response = await ask_groq(message.author.id, user_name, clean_content)
                    await message.reply(response)
            else:
                await message.reply("*приподнимается на задние лапы* Я тут! Что случилось? 👀")
            return

    # Auto-respond in specific channel
    if message.channel.name == "чат-с-экспи":
        async with message.channel.typing():
            response = await ask_groq(message.author.id, user_name, message.content)
            await message.reply(response)
        return

    await bot.process_commands(message)

# ============ RUN ============
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
