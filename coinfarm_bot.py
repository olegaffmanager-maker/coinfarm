import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

BOT_TOKEN  = "8789040101:AAFRdV6mBjQykZteIVzOO5LKkYLJtnHgtoo"
WEBAPP_URL = "https://olegaffmanager-maker.github.io/coinfarm/"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    args = message.text.split()
    start_param = args[1] if len(args) > 1 else ""
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.first_name or ""

    # Передаём user_id и referrer прямо в URL
    webapp_url = f"{WEBAPP_URL}?user_id={user_id}&username={username}&full_name={full_name}"
    if start_param.startswith("ref_"):
        webapp_url += f"&ref={start_param.replace('ref_', '')}"

    bot_info = await bot.get_me()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🎮 Play CoinFarm!", web_app=WebAppInfo(url=webapp_url)))
    builder.row(InlineKeyboardButton(
        text="👥 Invite Friends",
        url=f"https://t.me/share/url?url=https://t.me/{bot_info.username}%3Fstart%3Dref_{user_id}&text=🪙+Join+me+in+CoinFarm!"
    ))

    if start_param.startswith("ref_"):
        text = "🎁 <b>You were invited to CoinFarm!</b>\n\n⛏️ Mine coins by clicking\n📈 Level up to earn more\n🔥 Build combos for bonuses\n\n🎉 Your friend gets <b>+100 coins</b> bonus!\n\nTap the button below to start! 👇"
    else:
        text = "🪙 <b>Welcome to CoinFarm!</b>\n\n⛏️ Mine coins by clicking\n📈 Level up to earn more\n🔥 Build combos for bonuses\n👥 Invite friends for rewards\n🏆 Compete in leaderboard\n\nTap the button below to start playing! 👇"

    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="HTML")

async def main():
    logging.info("CoinFarm Bot started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
