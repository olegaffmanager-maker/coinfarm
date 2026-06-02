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

def make_play_button(user_id):
    webapp_url = f"{WEBAPP_URL}?user_id={user_id}"
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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
