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
    users.add(message.from_user.id)
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
    builder.row(InlineKeyboardButton(text="🚀 Play XSPACECOIN!", web_app=WebAppInfo(url=webapp_url)))
    builder.row(InlineKeyboardButton(
        text="👥 Invite Friends & Earn",
        url=f"https://t.me/share/url?url=https://t.me/{me.username}?start=ref_{message.from_user.id}"
            f"&text=🚀 Join me in XSPACECOIN — mine planets and earn XSPC tokens on TON!"
    ))

    await message.answer(
        f"🪐 <b>Welcome to XSPACECOIN!</b>\n\n"
        f"🌌 <b>Conquer the Galaxy!</b>\n"
        f"⛏️ Mine planets · 🔑 Earn XKEY · 🏆 Reach the Sun\n"
        f"💰 XSPC token launches Q1 2027 on TON!\n\n"
        f"<b>📋 Commands:</b>\n"
        f"/promo CODE — activate promo code 🎁\n"
        f"/daily — today's free promo code 📅\n"
        f"/notify — enable reminders 🔔\n"
        f"/stats — game statistics 📊\n\n"
        f"👇 Tap to start your space journey!",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )

# ═══ /play ═══
@dp.message(Command("play"))
async def cmd_play(message: types.Message):
    users.add(message.from_user.id)
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
    users.add(message.from_user.id)
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

# ═══ SMART NOTIFICATION SYSTEM ═══

# Messages by type — each with multiple variants for variety
NOTIFICATION_MESSAGES = {
    "energy": [
        "⚡ <b>Energy is FULL!</b>\n\nYour mining energy is bursting! Come tap now before it goes to waste! 🪐",
        "⚡ <b>Energy Restored!</b>\n\nFull tank ready! Every second offline = lost XSPC. Mine now! ⛏️",
        "⚡ <b>Ready to Mine!</b>\n\nYour energy is 100%! Don't let it overflow — tap and earn! 🚀",
    ],
    "passive": [
        "🪐 <b>Passive Income Ready!</b>\n\nYour mines have been working hard! Come collect your accumulated XSPC! 💰",
        "⛏️ <b>Coins Waiting!</b>\n\nPassive income has been building up while you were away. Come grab it! 🤑",
        "💎 <b>Your Mines Worked!</b>\n\nXSPC has been accumulating! Open the game to collect your passive income. 🪐",
    ],
    "daily": [
        "📦 <b>Daily Rewards Waiting!</b>\n\n✅ Daily chest ready\n✅ Free wheel spin available\n✅ Combo challenge open\n\nDon't break your streak! 🔥",
        "🎁 <b>Free Rewards Today!</b>\n\nYour daily chest, fortune wheel and combo are all waiting. Log in to claim! 🎯",
        "🔥 <b>Streak Alert!</b>\n\nDon't lose your daily streak! Log in now to keep your rewards growing every day! 📈",
    ],
    "expedition": [
        "🛸 <b>Expedition Complete!</b>\n\nYour space expedition has returned with rewards! Open the game to collect rare items! 🌟",
        "🌌 <b>Cosmic Discovery!</b>\n\nA new expedition result is waiting for you! Rare planets and artifacts discovered! 🪐",
    ],
    "comeback_1day": [
        "👋 <b>We miss you, Commander!</b>\n\nYour planets are waiting to be mined. Come back and collect your passive income! 🚀\n\n💡 Tip: Check the EARN tab for free daily rewards!",
        "🌌 <b>The Galaxy Needs You!</b>\n\nIt's been a day since your last mining session. Your XSPC passive income is piling up! ⛏️",
    ],
    "comeback_3day": [
        "🆘 <b>Your Mines Are Idle!</b>\n\nYou haven't mined in 3 days! Your passive income needs collection and your streak is at risk! 😱\n\n🎁 Use promo code <code>COMEBACK</code> for 5,000 bonus XSPC!",
        "💤 <b>Wake Up, Commander!</b>\n\n3 days offline means you've missed tons of XSPC! Come back — the galaxy can't conquer itself! 🪐",
    ],
    "comeback_7day": [
        "🌟 <b>Special Comeback Gift!</b>\n\nWe haven't seen you in a week! Come back now and use promo code <code>RETURN2026</code> for 10,000 XSPC bonus! 🎁\n\nToken launches Q1 2027 — every coin counts!",
        "🚀 <b>Don't Miss the Launch!</b>\n\nXSPC token launches Q1 2027! You've been away 7 days — come back and stack coins before launch! 💎",
    ],
    "level_up_push": [
        "🎉 <b>You're so close to leveling up!</b>\n\nJust a few more taps and you'll unlock a new planet! Come mine now! ⭐",
    ],
    "weekly_recap": [
        "📊 <b>Your Weekly XSPC Report</b>\n\n",
    ]
}

DAILY_MESSAGES = [
    "⚡ Daily combo is waiting! Can you guess the 3 correct cards? 🎯",
    "📦 Your daily chest is ready! Open it for XKEY rewards! 🔑",
    "🎰 Spin the fortune wheel — your daily free spin is available!",
    "🔥 Don't break your streak! Log in now for your daily reward!",
    "⛏️ Your passive income is accumulating! Come collect your XSPC!",
    "🌌 New day, new planet to conquer! Keep mining XSPC!",
    "🚀 XSPC token launches Q1 2027 — every coin counts!",
    "☄️ Expedition available! New cosmic event waiting for you!",
    f"🎁 Today\'s free promo code: use /daily to get it!",
    "💎 Have you checked your artifacts today? They give permanent bonuses!",
    "🏆 Check the leaderboard — are you in the Top 10?",
    "👥 Invite a friend and earn +5,000 XSPC! Share your link now!",
]

async def send_notification(user_id: int, msg_type: str, extra: str = ""):
    """Send a notification to a user by type"""
    msgs = NOTIFICATION_MESSAGES.get(msg_type, [])
    if not msgs:
        return False
    msg = random.choice(msgs)
    if extra:
        msg += extra
    try:
        builder = InlineKeyboardBuilder()
        builder.row(make_play_button(user_id))
        await bot.send_message(
            user_id,
            f"🪐 <b>XSPACECOIN</b>\n\n{msg}",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        return True
    except Exception as e:
        logging.warning(f"Notification failed for {user_id}: {e}")
        users.discard(user_id)
        return False

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
            logging.error(f"Poll energy error: {e}")

async def run_smart_notifications():
    """Smart notifications based on player activity"""
    while True:
        await asyncio.sleep(1800)  # every 30 min

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/top",
                    timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    top_players = await resp.json()
        except:
            top_players = []

        now = datetime.now()
        sent = 0

        for user_id in list(users):
            try:
                player = next((p for p in top_players if p.get("user_id") == user_id), None)
                last_save = player.get("last_save", 0) if player else 0
                if last_save == 0:
                    continue

                hours_offline = (now.timestamp() * 1000 - last_save) / 3600000

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
                    if await send_notification(user_id, msg_type):
                        sent += 1
                        await asyncio.sleep(0.1)

            except Exception as e:
                logging.error(f"Smart push error for {user_id}: {e}")

        if sent > 0:
            logging.info(f"Smart push: sent {sent} notifications")

async def run_comeback_notifications():
    """Send comeback messages to inactive players"""
    while True:
        await asyncio.sleep(3600)  # Check every hour

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/top",
                    timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    all_players = await resp.json()
        except:
            all_players = []

        now = datetime.now()
        sent = 0

        for user_id in list(users):
            try:
                player = next((p for p in all_players if p.get("user_id") == user_id), None)
                last_save = player.get("last_save", 0) if player else 0
                if last_save == 0:
                    continue

                hours_offline = (now.timestamp() * 1000 - last_save) / 3600000

                # Comeback messages — send once per interval
                msg_type = None
                # 24-26 hours offline
                if 24 <= hours_offline <= 26:
                    msg_type = "comeback_1day"
                # 71-73 hours (3 days)
                elif 71 <= hours_offline <= 73:
                    msg_type = "comeback_3day"
                # 167-169 hours (7 days)
                elif 167 <= hours_offline <= 169:
                    msg_type = "comeback_7day"

                if msg_type:
                    if await send_notification(user_id, msg_type):
                        sent += 1
                        await asyncio.sleep(0.3)

            except Exception as e:
                logging.error(f"Comeback push error for {user_id}: {e}")

        if sent > 0:
            logging.info(f"Comeback: sent {sent} notifications")

async def send_weekly_recap():
    """Send weekly stats recap every Sunday at 12:00"""
    while True:
        now = datetime.now()
        # Next Sunday 12:00
        days_until_sunday = (6 - now.weekday()) % 7
        if days_until_sunday == 0 and now.hour >= 12:
            days_until_sunday = 7
        target = now.replace(hour=12, minute=0, second=0, microsecond=0)
        target = target + timedelta(days=days_until_sunday)
        await asyncio.sleep((target - now).total_seconds())

        # Get stats
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/stats",
                    timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    stats = await resp.json()
                    total_players = stats.get("total_players", 0)
                    total_coins = stats.get("total_coins", 0)
        except:
            total_players = 0
            total_coins = 0

        sent = 0
        for user_id in list(users):
            try:
                builder = InlineKeyboardBuilder()
                builder.row(make_play_button(user_id))
                await bot.send_message(
                    user_id,
                    f"📊 <b>XSPACECOIN Weekly Report</b>\n\n"
                    f"🌍 Total Commanders: <b>{total_players:,}</b>\n"
                    f"💰 Total XSPC Mined: <b>{total_coins:,}</b>\n"
                    f"🚀 Token Launch: <b>Q1 2027</b>\n\n"
                    f"Keep mining — every XSPC counts at launch! ⭐",
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
                sent += 1
                await asyncio.sleep(0.05)
            except:
                users.discard(user_id)
        logging.info(f"Weekly recap sent to {sent} users")

async def send_daily_notifications():
    """Daily notification at 10:00 AM"""
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
    asyncio.create_task(run_comeback_notifications())
    asyncio.create_task(send_weekly_recap())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
