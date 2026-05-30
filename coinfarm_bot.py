import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ═══════════════════════════════════════════════════════
#  НАСТРОЙКИ
# ═══════════════════════════════════════════════════════
BOT_TOKEN  = "8789040101:AAFRdV6mBjQykZteIVzOO5LKkYLJtnHgtoo"
WEBAPP_URL = "https://olegaffmanager-maker.github.io/coinfarm/"  # URL где хостится coinfarm_webapp.html
# ═══════════════════════════════════════════════════════

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Извлекаем реферальный параметр из /start ref_XXXX
    args = message.text.split()
    start_param = args[1] if len(args) > 1 else ""

    # Передаём start_param в WebApp URL чтобы игра знала реферера
    webapp_url = WEBAPP_URL
    if start_param.startswith("ref_"):
        webapp_url = f"{WEBAPP_URL}?tgWebAppStartParam={start_param}"

    bot_info = await bot.get_me()
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🎮 Play CoinFarm!",
        web_app=WebAppInfo(url=webapp_url)
    ))
    builder.row(InlineKeyboardButton(
        text="👥 Invite Friends",
        url=f"https://t.me/share/url?url=https://t.me/{bot_info.username}%3Fstart%3Dref_{message.from_user.id}&text=🪙+Join+me+in+CoinFarm+and+get+bonus+coins!"
    ))

    # Приветственное сообщение — разное для новых и реферальных пользователей
    if start_param.startswith("ref_"):
        referrer_id = start_param.replace("ref_", "")
        welcome_text = (
            "🎁 <b>You were invited to CoinFarm!</b>\n\n"
            "⛏️ Mine coins by clicking\n"
            "📈 Level up to earn more\n"
            "🔥 Build combos for bonuses\n"
            "👥 Invite friends for rewards\n"
            "🏆 Compete in leaderboard\n\n"
            "🎉 Your friend gets <b>+100 coins</b> bonus!\n\n"
            "Tap the button below to start playing! 👇"
        )
    else:
        welcome_text = (
            "🪙 <b>Welcome to CoinFarm!</b>\n\n"
            "⛏️ Mine coins by clicking\n"
            "📈 Level up to earn more\n"
            "🔥 Build combos for bonuses\n"
            "👥 Invite friends for rewards\n"
            "🏆 Compete in leaderboard\n\n"
            "Tap the button below to start playing! 👇"
        )

    await message.answer(
        welcome_text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


async def main():
    logging.info("CoinFarm Bot started!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
