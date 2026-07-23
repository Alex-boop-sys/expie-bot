import discord
from discord.ext import commands
import aiohttp
import os
import io
import aiohttp
import urllib.parse
import random
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
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
HF_IMAGE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"  # или другая модель
GROQ_MODEL = "llama-3.3-70b-versatile"

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

@bot.command(name="арт")
async def cmd_art(ctx, *, query=None):
    """!арт — случайный арт Экспи. !арт <теги> — поиск по e621."""
    
    # Если запрос не указан — выбираем случайный вариант для разнообразия
    if not query:
        search_variants = [
            "expie_(gunsawian)&rating:safe",
            "casualties:_unknown&rating:safe",
            "gunsawian&rating:safe",
            "milky_(gunsawian)&rating:safe",
            "dune_(gunsawian)&rating:safe"
        ]
        tags = random.choice(search_variants).replace(" ", "_")
    else:
        tags = query.replace(" ", "_")
    
    async with ctx.typing():
        try:
            # limit=300 — примерный максим
            url = f"https://e621.net/posts.json?tags={tags}&limit=300"
            
            headers = {
                "User-Agent": "ExpieDiscordBot/1.0 (by Discord user)"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    
                    if resp.status != 200:
                        await ctx.reply(f"*вздрагивает* Сайт отвечает кодом {resp.status}...")
                        return
                    
                    data = await resp.json()
                    posts = data.get("posts", [])
                    
                    if not posts:
                        await ctx.reply("*нюхает воздух* Ничего не нашёл по этому запросу...")
                        return
                    
                    # Фильтруем: только картинки, убираем дубликаты
                    seen_urls = set()
                    valid_posts = []
                    
                    for p in posts:
                        file_data = p.get("file")
                        if not file_data or not file_data.get("url"):
                            continue
                        
                        img_url = file_data["url"]
                        
                        # Пропускаем дубликаты
                        if img_url in seen_urls:
                            continue
                        seen_urls.add(img_url)
                        
                        # Пропускаем видео/анимации
                        ext = img_url.split(".")[-1].split("?")[0].lower()
                        if ext in ("webm", "swf", "mp4"):
                            continue
                        
                        valid_posts.append(p)
                    
                    if not valid_posts:
                        await ctx.reply("*наклоняет голову* Нашёл посты, но картинки недоступны или все повторы...")
                        return
                    
                    post = random.choice(valid_posts)
                    image_url = post["file"]["url"]
                    
                    # СКАЧИВАЕМ картинку и отправляем как файл — без рамки embed!
                    async with session.get(image_url) as img_resp:
                        if img_resp.status != 200:
                            # Fallback: если не скачалось — отправляем ссылкой
                            await ctx.reply(
                                f"*виляет хвостом* О, смотри что нашёл!\\n{image_url}"
                            )
                            return
                        
                        image_data = await img_resp.read()
                        
                        # Определяем расширение
                        ext = image_url.split(".")[-1].split("?")[0].lower()
                        if ext not in ("png", "jpg", "jpeg", "gif", "webp"):
                            ext = "png"
                        
                        # Отправляем как файл — просто текст + картинка, без рамки
                        file = discord.File(
                            fp=io.BytesIO(image_data), 
                            filename=f"expie_art.{ext}"
                        )
                        
                        await ctx.reply(
                            content="Вот, смотри что нашёл! *виляет хвостом*",
                            file=file
                        )
                    
        except Exception as e:
            await ctx.reply(f"*вздрагивает* Ой, что-то сломалось: {str(e)[:80]}")

@bot.command(name="ген")
async def cmd_generate(ctx, *, prompt=None):
    """!ген <описание> — сгенерировать картинку. Без промпта — случайный Экспи."""
    
    if not prompt:
        prompt = "solo, cute, fluffy, black melanistic fur, anthro, furry, wolf-fox hybrid, big eyes, orange sclera, big fluffy tail, orange tip tail, three ears, high quality, kawaii style, beautiful background"
    
    # Улучшаем промпт стилем Экспи
    enhanced_prompt = (
        f"{prompt}, furry art, digital illustration, "
        "high quality, detailed fur, soft lighting, cute expression"
    )
    
    # Кодируем промпт для URL
    encoded = urllib.parse.quote(enhanced_prompt)
    
    # Pollinations генерирует прямо по URL
    seed = random.randint(1, 999999)
    image_url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true&seed={seed}"
    
    async with ctx.typing():
        try:
            async with aiohttp.ClientSession() as session:
                # Проверяем, что картинка реально сгенерировалась
                async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status != 200:
                        await ctx.reply("*прижимает уши* Генератор не отвечает... Попробуй позже!")
                        return
                    
                    image_data = await resp.read()
                    
                    # Отправляем как файл
                    file = discord.File(
                        fp=io.BytesIO(image_data),
                        filename="expie_generated.png"
                    )
                    
                    await ctx.reply(
                        content=f"*виляет хвостом* О, я нарисовал! По запросу: `{prompt[:300]}`",
                        file=file
                    )
                    
        except Exception as e:
            await ctx.reply(f"*вздрагивает* Что-то пошло не так: {str(e)[:80]}")

@bot.command(name="ген2")
async def cmd_generate_hf(ctx, *, prompt=None):
    if not prompt:
        prompt = "solo, cute, fluffy, black melanistic fur, anthro, furry, wolf-fox hybrid, big eyes, orange sclera, big fluffy tail, orange tip tail, three ears, high quality, kawaii style, beautiful background"
    
    if not HF_API_TOKEN:
        await ctx.reply("*прижимает уши* Токен Hugging Face не настроен!")
        return
    
    async with ctx.typing():
        try:
            headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
            payload = {"inputs": prompt}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api-inference.huggingface.co/models/{HF_IMAGE_MODEL}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=45)
                ) as resp:
                    
                    # Модель может "грузиться" — код 503
                    if resp.status == 503:
                        await ctx.reply("*прижимает уши* Модель просыпается... Попробуй через минуту!")
                        return
                    
                    if resp.status != 200:
                        await ctx.reply(f"*вздрагивает* Hugging Face ругается: {resp.status}")
                        return
                    
                    image_data = await resp.read()
                    
                    file = discord.File(fp=io.BytesIO(image_data), filename="expie_art.png")
                    await ctx.reply(
                        content=f"*виляет хвостом* Нарисовал! `{prompt[:300]}`",
                        file=file
                    )
                    
        except Exception as e:
            await ctx.reply(f"*вздрагивает* Ошибка: {str(e)[:80]}")
            
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
