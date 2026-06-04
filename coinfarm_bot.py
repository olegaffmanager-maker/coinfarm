import asyncio
import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8789040101:AAFRdV6mBjQykZteIVzOO5LKkYLJtnHgtoo")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://olegaffmanager-maker.github.io/coinfarm/")
API_URL    = os.environ.get("API_URL", "https://coinfarm-production.up.railway.app")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

users = set()
user_langs = {}  # user_id -> language code

# Translations for bot messages
BOT_TRANSLATIONS = {
    "welcome": {
        "en": "🪐 <b>Welcome to XSPACECOIN!</b>\n\n🌌 <b>Conquer the Galaxy!</b>\n⛏️ Mine planets · 🔑 Earn XKEY · 🏆 Reach the Sun\n💰 XSPC token launches Q1 2027 on TON!\n\n🔔 <b>Notifications enabled!</b> You will get reminders about energy, rewards and events.\n\n👇 Tap to start!",
        "ru": "🪐 <b>Добро пожаловать в XSPACECOIN!</b>\n\n🌌 <b>Покоряй Галактику!</b>\n⛏️ Майни планеты · 🔑 Получай XKEY · 🏆 Достигни Солнца\n💰 Токен XSPC запускается Q1 2027 на TON!\n\n🔔 <b>Уведомления включены!</b> Ты будешь получать напоминания об энергии, наградах и событиях.\n\n👇 Нажми чтобы начать!",
        "uk": "🪐 <b>Ласкаво просимо до XSPACECOIN!</b>\n\n🌌 <b>Підкоряй Галактику!</b>\n⛏️ Майни планети · 🔑 Отримуй XKEY · 🏆 Досягни Сонця\n💰 Токен XSPC запускається Q1 2027 на TON!\n\n🔔 <b>Сповіщення увімкнено!</b> Ти будеш отримувати нагадування.\n\n👇 Натисни щоб розпочати!",
        "es": "🪐 <b>¡Bienvenido a XSPACECOIN!</b>\n\n🌌 <b>¡Conquista la Galaxia!</b>\n⛏️ Mina planetas · 🔑 Gana XKEY · 🏆 Llega al Sol\n💰 ¡Token XSPC se lanza Q1 2027 en TON!\n\n🔔 <b>¡Notificaciones activadas!</b> Recibirás recordatorios.\n\n👇 ¡Toca para comenzar!",
        "zh": "🪐 <b>欢迎来到XSPACECOIN！</b>\n\n🌌 <b>征服银河！</b>\n⛏️ 挖掘星球 · 🔑 赚取XKEY · 🏆 到达太阳\n💰 XSPC代币将于2027年Q1在TON上发布！\n\n🔔 <b>通知已启用！</b>您将收到提醒。\n\n👇 点击开始！",
        "ar": "🪐 <b>مرحباً بك في XSPACECOIN!</b>\n\n🌌 <b>اغزو المجرة!</b>\n⛏️ اعدن الكواكب · 🔑 اكسب XKEY · 🏆 ابلغ الشمس\n💰 يُطلق رمز XSPC في Q1 2027 على TON!\n\n🔔 <b>تم تفعيل الإشعارات!</b>\n\n👇 اضغط للبدء!",
        "pt": "🪐 <b>Bem-vindo ao XSPACECOIN!</b>\n\n🌌 <b>Conquiste a Galáxia!</b>\n⛏️ Mine planetas · 🔑 Ganhe XKEY · 🏆 Alcance o Sol\n💰 Token XSPC lança Q1 2027 na TON!\n\n🔔 <b>Notificações ativadas!</b> Você receberá lembretes.\n\n👇 Toque para começar!",
    },
    "play_btn": {
        "en": "🚀 Play XSPACECOIN!", "ru": "🚀 Играть в XSPACECOIN!",
        "uk": "🚀 Грати в XSPACECOIN!", "es": "🚀 ¡Jugar XSPACECOIN!",
        "zh": "🚀 玩XSPACECOIN！", "ar": "🚀 العب XSPACECOIN!", "pt": "🚀 Jogar XSPACECOIN!",
    },
    "invite_btn": {
        "en": "👥 Invite Friends & Earn", "ru": "👥 Пригласить друзей",
        "uk": "👥 Запросити друзів", "es": "👥 Invitar amigos",
        "zh": "👥 邀请朋友", "ar": "👥 دعوة الأصدقاء", "pt": "👥 Convidar amigos",
    },
    "energy_full": {
        "en": "⚡ <b>Energy is FULL!</b>\n\nYour mining energy has fully restored! Come tap now! 🪐",
        "ru": "⚡ <b>Энергия ПОЛНАЯ!</b>\n\nТвоя энергия восстановилась! Заходи майнить! 🪐",
        "uk": "⚡ <b>Енергія ПОВНА!</b>\n\nТвоя енергія відновилась! Заходь майнити! 🪐",
        "es": "⚡ <b>¡Energía LLENA!</b>\n\n¡Tu energía se ha restaurado completamente! 🪐",
        "zh": "⚡ <b>能量已满！</b>\n\n您的挖矿能量已完全恢复！快来点击吧！🪐",
        "ar": "⚡ <b>الطاقة ممتلئة!</b>\n\nاستُعيدت طاقة التعدين بالكامل! تعال للنقر! 🪐",
        "pt": "⚡ <b>Energia CHEIA!</b>\n\nSua energia foi totalmente restaurada! Venha jogar! 🪐",
    },
    "passive_ready": {
        "en": "🪐 <b>Passive Income Ready!</b>\n\nYour mines worked hard! Come collect your XSPC! 💰",
        "ru": "🪐 <b>Пассивный доход готов!</b>\n\nТвои шахты поработали! Заходи собирать XSPC! 💰",
        "uk": "🪐 <b>Пасивний дохід готовий!</b>\n\nТвої шахти попрацювали! Заходь збирати XSPC! 💰",
        "es": "🪐 <b>¡Ingresos pasivos listos!</b>\n\n¡Tus minas trabajaron duro! ¡Ven a recoger tu XSPC! 💰",
        "zh": "🪐 <b>被动收入已就绪！</b>\n\n您的矿场一直在努力工作！来收集XSPC吧！💰",
        "ar": "🪐 <b>الدخل السلبي جاهز!</b>\n\nعملت مناجمك بجد! تعال لجمع XSPC! 💰",
        "pt": "🪐 <b>Renda passiva pronta!</b>\n\nSuas minas trabalharam! Venha coletar seu XSPC! 💰",
    },
    "daily_reminder": {
        "en": "📦 <b>Daily Rewards Waiting!</b>\n\n✅ Daily chest ready\n✅ Free wheel spin\n✅ Combo challenge open\n\nDon\'t break your streak! 🔥",
        "ru": "📦 <b>Ежедневные награды ждут!</b>\n\n✅ Дневной сундук готов\n✅ Бесплатное вращение\n✅ Комбо открыто\n\nНе прерывай серию! 🔥",
        "uk": "📦 <b>Щоденні нагороди чекають!</b>\n\n✅ Скриня готова\n✅ Безкоштовне обертання\n✅ Комбо відкрито\n\nНе переривай серію! 🔥",
        "es": "📦 <b>¡Recompensas diarias esperando!</b>\n\n✅ Cofre listo\n✅ Giro gratis\n✅ Combo abierto\n\n¡No rompas tu racha! 🔥",
        "zh": "📦 <b>每日奖励等待领取！</b>\n\n✅ 宝箱已就绪\n✅ 免费转轮\n✅ 组合挑战开放\n\n不要断开连续！🔥",
        "ar": "📦 <b>المكافآت اليومية تنتظر!</b>\n\n✅ الصندوق جاهز\n✅ دوران مجاني\n✅ الكومبو مفتوح\n\nلا تكسر سلسلتك! 🔥",
        "pt": "📦 <b>Recompensas diárias esperando!</b>\n\n✅ Baú pronto\n✅ Giro grátis\n✅ Combo aberto\n\nNão quebre sua sequência! 🔥",
    },
    "comeback_1d": {
        "en": "👋 <b>We miss you, Commander!</b>\n\nYour planets wait to be mined! Come back and collect passive income! 🚀",
        "ru": "👋 <b>Мы скучаем, Командир!</b>\n\nПланеты ждут майнинга! Вернись и забери доход! 🚀",
        "uk": "👋 <b>Ми сумуємо, Командире!</b>\n\nПланети чекають! Повернись і забери дохід! 🚀",
        "es": "👋 <b>¡Te extrañamos, Comandante!</b>\n\n¡Tus planetas esperan! ¡Vuelve a recoger tus ingresos! 🚀",
        "zh": "👋 <b>我们想念您，指挥官！</b>\n\n星球等待挖掘！回来收集被动收入吧！🚀",
        "ar": "👋 <b>نشتاق إليك يا قائد!</b>\n\nكواكبك تنتظر! عد واجمع دخلك! 🚀",
        "pt": "👋 <b>Sentimos sua falta, Comandante!</b>\n\nSeus planetas esperam! Volte e colete sua renda! 🚀",
    },
    "comeback_3d": {
        "en": "🆘 <b>Your Mines Are Idle!</b>\n\n3 days offline! Use code <code>COMEBACK</code> for +5,000 XSPC! 🎁",
        "ru": "🆘 <b>Шахты простаивают!</b>\n\n3 дня офлайн! Код <code>COMEBACK</code> = +5,000 XSPC! 🎁",
        "uk": "🆘 <b>Шахти простоюють!</b>\n\n3 дні офлайн! Код <code>COMEBACK</code> = +5,000 XSPC! 🎁",
        "es": "🆘 <b>¡Minas inactivas!</b>\n\n¡3 días offline! Código <code>COMEBACK</code> = +5,000 XSPC! 🎁",
        "zh": "🆘 <b>矿场空闲！</b>\n\n离线3天！代码 <code>COMEBACK</code> = +5,000 XSPC！🎁",
        "ar": "🆘 <b>المناجم خاملة!</b>\n\n3 أيام دون اتصال! الرمز <code>COMEBACK</code> = +5,000 XSPC! 🎁",
        "pt": "🆘 <b>Minas paradas!</b>\n\n3 dias offline! Código <code>COMEBACK</code> = +5.000 XSPC! 🎁",
    },
    "comeback_7d": {
        "en": "🌟 <b>Special Gift!</b>\n\nA week offline! Code <code>RETURN2026</code> = +10,000 XSPC! Token Q1 2027! 💎",
        "ru": "🌟 <b>Специальный подарок!</b>\n\nНеделю офлайн! Код <code>RETURN2026</code> = +10,000 XSPC! Токен Q1 2027! 💎",
        "uk": "🌟 <b>Спеціальний подарунок!</b>\n\nТиждень офлайн! Код <code>RETURN2026</code> = +10,000 XSPC! Q1 2027! 💎",
        "es": "🌟 <b>¡Regalo especial!</b>\n\n¡Semana offline! Código <code>RETURN2026</code> = +10,000 XSPC! Q1 2027! 💎",
        "zh": "🌟 <b>特别礼物！</b>\n\n离线一周！代码 <code>RETURN2026</code> = +10,000 XSPC！Q1 2027！💎",
        "ar": "🌟 <b>هدية خاصة!</b>\n\nأسبوع دون اتصال! <code>RETURN2026</code> = +10,000 XSPC! Q1 2027! 💎",
        "pt": "🌟 <b>Presente especial!</b>\n\nSemana offline! Código <code>RETURN2026</code> = +10.000 XSPC! Q1 2027! 💎",
    },
}


TG_LANG_MAP = {
    'ru':'ru','uk':'uk','be':'ru','kk':'ru',
    'es':'es','zh':'zh','zh-hans':'zh','zh-hant':'zh',
    'ar':'ar','pt':'pt','br':'pt','en':'en',
}

def get_lang(user_id):
    return user_langs.get(user_id, 'en')

def tr(key, user_id, fallback=''):
    lang = get_lang(user_id)
    d = BOT_TRANSLATIONS.get(key, {})
    return d.get(lang) or d.get('en') or fallback


DAILY_PROMOS = ["XSPACE2026", "LAUNCH", "SPACE100", "WELCOMEGIFT",
                "XSPC_TG", "MINEHARD", "GALAXY2026", "ASTEROID"]

def get_daily_promo():
    return DAILY_PROMOS[datetime.now().day % len(DAILY_PROMOS)]

def make_play_button(user_id, extra=""):
    webapp_url = f"{WEBAPP_URL}?user_id={user_id}{extra}"
    return InlineKeyboardButton(text="🚀 Play XSPACECOIN!", web_app=WebAppInfo(url=webapp_url))

# ═══ /start ═══
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    uid = message.from_user.id
    users.add(uid)
    # Save user language
    tg_lang = (message.from_user.language_code or 'en').lower().split('-')[0]
    user_langs[uid] = TG_LANG_MAP.get(tg_lang, 'en')
    args = message.text.split()
    ref_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].replace("ref_", ""))
        except:
            pass

    webapp_url = f"{WEBAPP_URL}?user_id={message.from_user.id}"
    if message.from_user.username:
        webapp_url += f"&username={message.from_user.username}"
    if message.from_user.first_name:
        webapp_url += f"&full_name={message.from_user.first_name}"
    if ref_id:
        webapp_url += f"&ref={ref_id}"

    me = await bot.get_me()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=tr("play_btn",uid,"🚀 Play XSPACECOIN!"), web_app=WebAppInfo(url=webapp_url)))
    builder.row(InlineKeyboardButton(
        text=tr("invite_btn",uid,"👥 Invite Friends & Earn"),
        url=f"https://t.me/share/url?url=https://t.me/{me.username}?start=ref_{message.from_user.id}"
            f"&text=🚀 Join me in XSPACECOIN — mine planets and earn XSPC tokens on TON!"
    ))

    await message.answer(
        tr('welcome', uid),
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )

# ═══ /play ═══
@dp.message(Command("play"))
async def cmd_play(message: types.Message):
    uid = message.from_user.id
    users.add(uid)
    tg_lang = (message.from_user.language_code or "en").lower().split("-")[0]
    user_langs[uid] = TG_LANG_MAP.get(tg_lang, "en")
    webapp_url = f"{WEBAPP_URL}?user_id={message.from_user.id}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚀 Open XSPACECOIN", web_app=WebAppInfo(url=webapp_url)))
    await message.answer("🪐 Let's mine some XSPC!", reply_markup=builder.as_markup())

# ═══ /daily ═══
@dp.message(Command("daily"))
async def cmd_daily(message: types.Message):
    code = get_daily_promo()
    builder = InlineKeyboardBuilder()
    builder.row(make_play_button(message.from_user.id))
    await message.answer(
        f"🎁 <b>Today's Free Promo Code!</b>\n\n"
        f"Code: <code>{code}</code>\n\n"
        f"How to use:\n"
        f"1. Open the game\n"
        f"2. Go to <b>Earn → Promo Code</b>\n"
        f"3. Enter the code and tap Redeem\n\n"
        f"Or send: /promo {code}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# ═══ /promo ═══
@dp.message(Command("promo"))
async def cmd_promo(message: types.Message):
    args = message.text.split(maxsplit=1)

    if len(args) < 2 or not args[1].strip():
        code = get_daily_promo()
        await message.answer(
            f"🎁 <b>Promo Codes</b>\n\n"
            f"Today's free code: <code>{code}</code>\n\n"
            f"<b>To activate a code:</b>\n"
            f"Send: /promo YOUR_CODE\n\n"
            f"Example: <code>/promo XSPACE2026</code>\n\n"
            f"Or enter directly in game: Earn → Promo Code",
            parse_mode="HTML"
        )
        return

    code = args[1].strip().upper()
    user_id = message.from_user.id

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_URL}/promo/redeem",
                json={"user_id": user_id, "code": code},
                timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                data = await resp.json()
    except Exception as e:
        logging.error(f"Promo API error: {e}")
        await message.answer(
            f"⚠️ Could not connect. Try in game: Earn → Promo Code → <code>{code}</code>",
            parse_mode="HTML"
        )
        return

    if data.get("status") == "ok":
        builder = InlineKeyboardBuilder()
        builder.row(make_play_button(user_id))
        await message.answer(
            f"✅ <b>Promo Code Activated!</b>\n\n"
            f"Code: <code>{code}</code>\n"
            f"{data.get('msg', '')}\n\n"
            f"Rewards added to your account! 🎉",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
    elif data.get("error") == "already_used":
        await message.answer(
            f"⚠️ <b>Already used!</b>\n\n"
            f"Code <code>{code}</code> was already activated.",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ Invalid code: <code>{code}</code>\n\nGet today's free code with /daily",
            parse_mode="HTML"
        )

# ═══ /notify ═══
@dp.message(Command("notify"))
async def cmd_notify(message: types.Message):
    uid = message.from_user.id
    users.add(uid)
    tg_lang = (message.from_user.language_code or "en").lower().split("-")[0]
    user_langs[uid] = TG_LANG_MAP.get(tg_lang, "en")
    await message.answer(
        "🔔 <b>Notifications enabled!</b>\n\n"
        "You will receive:\n"
        "⚡ Energy full reminder\n"
        "📦 Daily chest reminder\n"
        "🔥 Streak reminder\n"
        "🎰 Fortune wheel reminder\n"
        "🪐 Passive income ready\n\n"
        "Notifications sent daily at 10:00 AM",
        parse_mode="HTML"
    )

# ═══ /stats ═══
@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/stats", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                data = await resp.json()
                total_players = data.get("total_players", len(users))
                total_coins = data.get("total_coins", 0)
    except:
        total_players = len(users)
        total_coins = 0

    await message.answer(
        f"📊 <b>XSPACECOIN Stats</b>\n\n"
        f"👥 Total players: {total_players:,}\n"
        f"🤖 Bot users: {len(users):,}\n"
        f"💰 Total XSPC mined: {total_coins:,}\n"
        f"🚀 Token launch: Q1 2027\n"
        f"🌌 Goal: Conquer the Galaxy!\n\n"
        f"Keep mining! 🪐",
        parse_mode="HTML"
    )

# ═══ Telegram Push Notifications ═══
# These are real Telegram messages sent when player is offline
PUSH_MESSAGES = [
    {
        "type": "energy",
        "title": "⚡ Energy Full!",
        "text": "Your energy is fully restored! Come mine XSPC now before it goes to waste!",
        "hours_offline": 0.5,  # Send after 30 min offline
    },
    {
        "type": "passive",
        "title": "🪐 Passive Income Ready!",
        "text": "Your mines have been working! Come collect your passive XSPC income!",
        "hours_offline": 2,
    },
    {
        "type": "daily",
        "title": "📦 Daily Rewards Waiting!",
        "text": "Your daily chest, combo and streak are ready! Don't break your streak!",
        "hours_offline": 20,
    },
    {
        "type": "expedition",
        "title": "🛸 Expedition Ready!",
        "text": "A new cosmic expedition is available! Explore and earn rare rewards!",
        "hours_offline": 4,
    },
]

async def send_push_to_user(user_id: int, msg_type: str):
    """Send a specific push notification to a user"""
    msg = next((m for m in PUSH_MESSAGES if m["type"] == msg_type), PUSH_MESSAGES[0])
    try:
        builder = InlineKeyboardBuilder()
        builder.row(make_play_button(user_id))
        await bot.send_message(
            user_id,
            f"🪐 <b>XSPACECOIN</b>\n\n"
            f"<b>{msg['title']}</b>\n"
            f"{msg['text']}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        return True
    except Exception as e:
        logging.warning(f"Push failed for {user_id}: {e}")
        users.discard(user_id)
        return False

# ═══ Smart push notification system ═══
async def poll_energy_notifications():
    """Poll server for energy-full notifications every 2 minutes"""
    while True:
        await asyncio.sleep(120)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/notify/pending",
                    timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    data = await resp.json()
                    pending = data.get("users", [])
                    for user_id in pending:
                        await send_notification(user_id, "energy")
                        await asyncio.sleep(0.05)
        except Exception as e:
            logging.error(f"Poll energy notifications error: {e}")

async def run_smart_notifications():
    """Check player activity and send relevant push notifications"""
    while True:
        await asyncio.sleep(1800)  # Check every 30 minutes

        try:
            async with aiohttp.ClientSession() as session:
                # Get all users from API
                async with session.get(f"{API_URL}/top", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    top_players = await resp.json()
        except:
            top_players = []

        now = datetime.now()
        sent = 0

        for user_id in list(users):
            try:
                # Find player data
                player = next((p for p in top_players if p.get("user_id") == user_id), None)

                # Check last save time
                last_save = player.get("last_save", 0) if player else 0
                if last_save == 0:
                    continue

                hours_offline = (now.timestamp() * 1000 - last_save) / 3600000

                # Send appropriate notification based on offline time
                msg_type = None
                if 0.4 <= hours_offline <= 0.6:
                    msg_type = "energy"
                elif 1.8 <= hours_offline <= 2.2:
                    msg_type = "passive"
                elif 3.8 <= hours_offline <= 4.2:
                    msg_type = "expedition"
                elif 19 <= hours_offline <= 21:
                    msg_type = "daily"

                if msg_type:
                    if await send_push_to_user(user_id, msg_type):
                        sent += 1
                        await asyncio.sleep(0.1)

            except Exception as e:
                logging.error(f"Smart push error for {user_id}: {e}")

        if sent > 0:
            logging.info(f"Smart push: sent {sent} notifications")

# ═══ Daily notifications at 10:00 AM ═══
DAILY_MESSAGES = [
    "⚡ Daily combo is waiting! Can you guess the 3 correct cards? 🎯",
    "📦 Your daily chest is ready! Open it for XKEY rewards! 🔑",
    "🎰 Spin the fortune wheel — your daily free spin is available!",
    "🔥 Don't break your streak! Log in now for your daily reward!",
    "⛏️ Your passive income is accumulating! Come collect your XSPC!",
    "🌌 New day, new planet to conquer! Keep mining XSPC!",
    "🚀 XSPC token launches Q1 2027 — every coin counts!",
    "☄️ Expedition available! New cosmic event waiting for you!",
    f"🎁 Today's free promo code: use /daily to get it!",
]

async def send_daily_notifications():
    while True:
        now = datetime.now()
        target = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if now >= target:
            target = target + timedelta(days=1)
        await asyncio.sleep((target - now).total_seconds())

        msg = random.choice(DAILY_MESSAGES)
        sent = 0
        for user_id in list(users):
            try:
                builder = InlineKeyboardBuilder()
                builder.row(make_play_button(user_id))
                await bot.send_message(
                    user_id,
                    f"🪐 <b>XSPACECOIN Daily</b>\n\n{msg}",
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
                sent += 1
                await asyncio.sleep(0.05)
            except:
                users.discard(user_id)
        logging.info(f"Daily notifications sent to {sent} users")

async def main():
    logging.info("🚀 XSPACECOIN Bot started!")
    await bot.set_my_commands([
        types.BotCommand(command="start",  description="🚀 Launch XSPACECOIN"),
        types.BotCommand(command="play",   description="🎮 Open the game"),
        types.BotCommand(command="promo",  description="🎁 Activate promo code"),
        types.BotCommand(command="daily",  description="📅 Today's free promo"),
        types.BotCommand(command="notify", description="🔔 Enable reminders"),
        types.BotCommand(command="stats",  description="📊 Game statistics"),
    ])
    asyncio.create_task(send_daily_notifications())
    asyncio.create_task(run_smart_notifications())
    asyncio.create_task(poll_energy_notifications())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
