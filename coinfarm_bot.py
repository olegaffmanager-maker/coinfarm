import asyncio
import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8789040101:AAFRdV6mBjQykZteIVzOO5LKkYLJtnHgtoo")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://olegaffmanager-maker.github.io/coinfarm/")
API_URL    = os.environ.get("API_URL", "https://coinfarm-production.up.railway.app")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

users = set()

# ═══ Daily promo rotation ═══
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
        f"/promo — activate promo code 🎁\n"
        f"/daily — today's free promo code\n"
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

# ═══ /daily — показать сегодняшний промокод ═══
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

# ═══ /promo — активация промокода через бота ═══
@dp.message(Command("promo"))
async def cmd_promo(message: types.Message):
    args = message.text.split(maxsplit=1)

    # No code provided — show daily code
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

    # Activate via API
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
            f"⚠️ Could not connect to server. Try activating in the game directly.\n"
            f"Earn → Promo Code → enter <code>{code}</code>",
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
            f"⚠️ <b>Code already used!</b>\n\n"
            f"You already activated <code>{code}</code>.\n"
            f"Each code can only be used once per account.",
            parse_mode="HTML"
        )
    elif data.get("error") == "invalid_code":
        await message.answer(
            f"❌ <b>Invalid Code</b>\n\n"
            f"<code>{code}</code> is not a valid promo code.\n\n"
            f"Get today's free code with /daily",
            parse_mode="HTML"
        )
    else:
        await message.answer(
            f"❌ Error: {data.get('msg', 'Something went wrong')}",
            parse_mode="HTML"
        )

# ═══ /notify ═══
@dp.message(Command("notify"))
async def cmd_notify(message: types.Message):
    users.add(message.from_user.id)
    await message.answer(
        "🔔 <b>Notifications enabled!</b>\n\n"
        "You'll receive daily reminders to:\n"
        "📦 Open your daily chest\n"
        "🎰 Spin the fortune wheel\n"
        "⚡ Claim daily combo\n"
        "🔥 Keep your streak alive!",
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
    except:
        total_players = len(users)

    await message.answer(
        f"📊 <b>XSPACECOIN Stats</b>\n\n"
        f"👥 Total players: {total_players:,}\n"
        f"🤖 Bot users: {len(users):,}\n"
        f"🚀 Token launch: Q1 2027\n"
        f"💰 Total supply: 21,000,000,000 XSPC\n"
        f"🌌 Goal: Conquer the Galaxy!\n\n"
        f"Keep mining! 🪐",
        parse_mode="HTML"
    )

# ═══ Daily notifications ═══
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
            from datetime import timedelta
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
        logging.info(f"Sent daily notifications to {sent} users")

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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
