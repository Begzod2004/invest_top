from aiogram import types, Dispatcher
from aiogram.dispatcher.filters.builtin import CommandStart
from apps.users.models import User
from django.utils import timezone
from asgiref.sync import sync_to_async

@sync_to_async
def get_or_create_user(telegram_id: str, username: str, first_name: str, last_name: str):
    """Foydalanuvchini bazadan olish yoki yaratish"""
    user, created = User.objects.get_or_create(
        telegram_user_id=telegram_id,
        defaults={
            'username': username or telegram_id,
            'first_name': first_name,
            'last_name': last_name,
            'user_id': telegram_id,
            'is_active': True,
            'date_joined': timezone.now()
        }
    )
    
    if not created:
        # Agar user mavjud bo'lsa, ma'lumotlarini yangilaymiz
        user.username = username or telegram_id
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = True
        user.save()
    
    return user, created

async def bot_start(message: types.Message):
    """Start komandasi uchun handler"""
    try:
        # Foydalanuvchi ma'lumotlarini olamiz
        telegram_id = str(message.from_user.id)
        username = message.from_user.username
        first_name = message.from_user.first_name
        last_name = message.from_user.last_name

        # Foydalanuvchini bazada qidiramiz yoki yangi yaratamiz
        user, created = await get_or_create_user(telegram_id, username, first_name, last_name)

        # Inline tugmalarni yaratamiz
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        web_app_button = types.InlineKeyboardButton(
            text="🌐 Web ilovaga kirish",
            web_app=types.WebAppInfo(url="https://top-invest-webapp.vercel.app")
        )
        help_button = types.InlineKeyboardButton(
            text="📚 Yordam",
            callback_data="help"
        )
        keyboard.add(web_app_button, help_button)

        # Xabar yuborish
        await message.answer(
            f"Yana qaytganingizdan xursandmiz, {user.first_name}!\n\nQuyidagi tugmalardan foydalanishingiz mumkin:",
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"Error in bot_start: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

async def back_to_start_callback(callback_query: types.CallbackQuery):
    """Orqaga qaytish uchun handler"""
    try:
        # Inline tugmalarni yaratamiz
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        web_app_button = types.InlineKeyboardButton(
            text="🌐 Web ilovaga kirish",
            web_app=types.WebAppInfo(url="https://top-invest-webapp.vercel.app")
        )
        help_button = types.InlineKeyboardButton(
            text="📚 Yordam",
            callback_data="help"
        )
        keyboard.add(web_app_button, help_button)

        # Xabarni yangilash
        await callback_query.message.edit_text(
            f"Yana qaytganingizdan xursandmiz!\n\nQuyidagi tugmalardan foydalanishingiz mumkin:",
            reply_markup=keyboard
        )
        await callback_query.answer()
    except Exception as e:
        logger.error(f"Back to start xatoligi: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi", show_alert=True)

def register_handlers(dp: Dispatcher):
    """Start komandasi uchun handlerni ro'yxatdan o'tkazish"""
    dp.register_message_handler(bot_start, CommandStart())
    dp.register_callback_query_handler(back_to_start_callback, lambda c: c.data == "back_to_start") 