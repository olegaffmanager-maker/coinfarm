import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime
import random

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8789040101:AAFRdV6mBjQykZteIVzOO5LKkYLJtnHgtoo")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://olegaffmanager-maker.github.io/coinfarm/")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

users = set()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    users.add(message.from_user.id)
    ref_id = None
    args = message.text.split()
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
        url=f"https://t.me/share/url?url=https://t.me/{me.username}?start=ref_{message.from_user.id}&text=🚀 Join me in XSPACECOIN — mine planets and earn XSPC tokens on TON blockchain!"
    ))

    await message.answer(
        f"🪐 <b>Welcome to XSPACECOIN!</b>\n\n"
        f"🌌 <b>Conquer the Galaxy!</b>\n"
        f"⛏️ Mine planets · 🔑 Earn XKEY · 🏆 Reach the Sun\n"
        f"💰 XSPC token launches Q4 2026 on TON!\n\n"
        f"<b>📋 Commands:</b>\n"
        f"/promo — daily promo code 🎁\n"
        f"/notify — enable reminders 🔔\n"
        f"/stats — game statistics 📊\n\n"
        f"👇 Tap to start your space journey!",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )

@dp.message(Command("play"))
async def cmd_play(message: types.Message):
    users.add(message.from_user.id)
    webapp_url = f"{WEBAPP_URL}?user_id={message.from_user.id}"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚀 Open XSPACECOIN", web_app=WebAppInfo(url=webapp_url)))
    await message.answer("🪐 Let's mine some XSPC!", reply_markup=builder.as_markup())

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

@dp.message(Command("promo"))
async def cmd_promo(message: types.Message):
    codes = ["XSPACE2026", "LAUNCH", "SPACE100", "WELCOMEGIFT"]
    code = codes[datetime.now().day % len(codes)]
    await message.answer(
        f"🎁 <b>Daily Promo Code!</b>\n\n"
        f"Today's code: <code>{code}</code>\n\n"
        f"Enter in game: Earn → Promo Code",
        parse_mode="HTML"
    )

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    await message.answer(
        f"📊 <b>XSPACECOIN Stats</b>\n\n"
        f"👥 Bot users: {len(users)}\n"
        f"🚀 Token launch: Q4 2026\n"
        f"💰 Total supply: 21,000,000,000 XSPC\n"
        f"🌌 Goal: Conquer the Galaxy!\n\n"
        f"Keep mining! 🪐",
        parse_mode="HTML"
    )

DAILY_MESSAGES = [
    "⚡ Daily combo is waiting! Can you guess the 3 correct cards? 🎯",
    "📦 Your daily chest is ready! Open it for XKEY rewards! 🔑",
    "🎰 Spin the fortune wheel — your daily free spin is available!",
    "🔥 Don't break your streak! Log in now for your daily reward!",
    "⛏️ Your passive income is accumulating! Come collect your XSPC!",
    "🌌 New day, new planet to conquer! Keep mining XSPC!",
    "🚀 XSPC token launches Q4 2026 — every coin counts!",
    "☄️ Asteroid event incoming! x5 coins for 30 seconds! Tap now!",
]

async def send_daily_notifications():
    while True:
        now = datetime.now()
        target = now.replace(hour=10, minute=0, second=0, microsecond=0)
        if now >= target:
            from datetime import timedelta
            target = target + timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        msg = random.choice(DAILY_MESSAGES)
        sent = 0
        for user_id in list(users):
            try:
                webapp_url = f"{WEBAPP_URL}?user_id={user_id}"
                builder = InlineKeyboardBuilder()
                builder.row(InlineKeyboardButton(text="🚀 Play Now", web_app=WebAppInfo(url=webapp_url)))
                await bot.send_message(
                    user_id,
                    f"🪐 <b>XSPACECOIN Daily</b>\n\n{msg}",
                    reply_markup=builder.as_markup(),
                    parse_mode="HTML"
                )
                sent += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                users.discard(user_id)
        logging.info(f"Sent daily notifications to {sent} users")

async def main():
    logging.info("🚀 XSPACECOIN Bot started!")
    await bot.set_my_commands([
        types.BotCommand(command="start",  description="🚀 Launch XSPACECOIN"),
        types.BotCommand(command="play",   description="🎮 Open the game"),
        types.BotCommand(command="promo",  description="🎁 Daily promo code"),
        types.BotCommand(command="notify", description="🔔 Enable reminders"),
        types.BotCommand(command="stats",  description="📊 Game statistics"),
    ])
    asyncio.create_task(send_daily_notifications())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
