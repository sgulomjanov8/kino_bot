import asyncio
import logging
import os
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiohttp import web

# Bot tokeningiz
BOT_TOKEN = "8974629165:AAEqb1feOKJomWLui2TNJs79w8cOJBj_fmU"

# Majburiy obuna kanali va Admin ID
CHANNEL_USERNAME = "@MediaUzkinolar"
ADMIN_ID = 7349877336

# Baza (Vaqtinchalik xotira)
movie_db = {}

# Logging sozlamasi
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Render Port Scan uchun kichik veb-server
async def handle(request):
    return web.Response(text="Bot muvaffaqiyatli ishlayapti!")


async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()


# Majburiy obunani tekshiruvchi funksiya
async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception as e:
        logging.error(f"Obuna tekshirishda xatolik: {e}")
        return True


# Obuna bo'lish tugmasi
def get_sub_keyboard():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalimizga obuna bo'lish", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton(text="✅ Obunani tekshirish", callback_data="check_sub")]
        ]
    )
    return keyboard


# /start buyrug'i
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    
    welcome_text = (
        f"Assalomu alaykum, {message.from_user.first_name}! 👋\n\n"
        f"Kino olamidagi botimizga xush kelibsiz! 🍿✨\n"
        f"Bu yerda siz eng so'nggi va sara kinolarni yuqori sifatda tomosha qilishingiz mumkin.\n\n"
    )

    if not is_subscribed:
        await message.answer(
            welcome_text + f"Botdan to'liq foydalanish uchun iltimos, rasmiy {CHANNEL_USERNAME} kanalimizga obuna bo'ling va pastdagi <b>'✅ Obunani tekshirish'</b> tugmasini bosing.",
            reply_markup=get_sub_keyboard(),
            parse_mode=ParseMode.HTML
        )
        return

    await message.answer(
        welcome_text + "🎥 Kinoni ko'rish uchun uning <b>kodini</b> yuboring (masalan: <code>09</code> yoki <code>2012</code>).",
        parse_mode=ParseMode.HTML
    )


# Inline tugma bosilganda obunani tekshirish
@dp.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: types.CallbackQuery):
    is_subscribed = await check_subscription(callback.from_user.id)
    if is_subscribed:
        await callback.message.delete()
        await callback.message.answer(
            "✅ Rahmat! Obuna muvaffaqiyatli tekshirildi.\n\n"
            "🍿 Endi tomosha qilmoqchi bo'lgan kino kodini yuborishingiz mumkin!"
        )
    else:
        await callback.answer("❌ Siz hali kanalga obuna bo'lmadingiz!", show_alert=True)


# 1. ADMIN VIDEO YUBORGANDA SAQLASH
@dp.message(F.video, F.from_user.id == ADMIN_ID)
async def add_movie_handler(message: types.Message):
    caption = message.caption or ""
    file_id = message.video.file_id

    match = re.search(r"Kino kodi:\s*`?([^\s\n`]+)`?", caption, re.IGNORECASE)

    if match:
        code = match.group(1).strip()

        movie_db[code] = {
            "file_id": file_id,
            "caption": caption
        }

        await message.reply(
            f"🎉 ✅ <b>Video botga muvaffaqiyatli joylandi!</b>\n\n"
            f"🔑 <b>Muvaffaqiyatli saqlangan kino kodi:</b> <code>{code}</code>\n\n"
            f"Endi foydalanuvchilar <code>{code}</code> deb yozsa, ushbu kino chiqadi.",
            parse_mode=ParseMode.HTML
        )
    else:
        await message.reply(
            "⚠️ Video izohida (caption) <code>Kino kodi:</code> topilmadi!\n\n"
            "Matn ichida quyidagicha yozilganiga ishonch hosil qiling:\n"
            "🍿 Kino kodi: 2012",
            parse_mode=ParseMode.HTML
        )


# 2. FOYDALANUVCHILAR KOD YUBORGANDA KINONI CHIQARISH
@dp.message(F.text & ~F.text.startswith("/"))
async def get_movie_handler(message: types.Message):
    is_subscribed = await check_subscription(message.from_user.id)
    if not is_subscribed:
        await message.answer(
            f"⛔️ Kinoni ko'rish uchun avval {CHANNEL_USERNAME} kanaliga obuna bo'lishingiz kerak!",
            reply_markup=get_sub_keyboard()
        )
        return

    code = message.text.strip()

    if code in movie_db:
        movie = movie_db[code]
        await message.answer_video(
            video=movie["file_id"],
            caption=movie["caption"]
        )
    else:
        await message.answer(
            "❌ Afsuski, bunday kodli kino topilmadi.\n"
            "Kodni to'g'ri kiritganingizni qayta tekshirib ko'ring."
        )


# Botni va Veb-serverni birgalikda ishga tushirish
async def main():
    print("Veb-server va Bot ishga tushmoqda...")
    await start_web_server()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
