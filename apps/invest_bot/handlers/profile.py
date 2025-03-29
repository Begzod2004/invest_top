from aiogram import types
from aiogram.dispatcher.filters import Command
from apps.users.models import User
from asgiref.sync import sync_to_async
import logging

# Logger sozlaymiz
logger = logging.getLogger(__name__)

logger.info("profile.py fayli yuklandi")

@sync_to_async
def get_user(telegram_user_id):
    """Foydalanuvchini olish"""
    try:
        return User.objects.get(telegram_user_id=str(telegram_user_id))
    except User.DoesNotExist:
        logger.error(f"User not found: {telegram_user_id}")
        return None
    except Exception as e:
        logger.error(f"Error while getting user: {e}")
        return None

async def profile_command(message: types.Message):
    """Profile komandasi uchun handler"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.answer("Siz hali ro'yxatdan o'tmagansiz. /start buyrug'ini bosing.")
            return
            
        profile_text = f"""
👤 Sizning profilingiz:

Ism: {user.first_name or "Ko'rsatilmagan"}
Familiya: {user.last_name or "Ko'rsatilmagan"}
Username: @{user.username or "Ko'rsatilmagan"}
Balans: {user.balance} so'm
Ro'yxatdan o'tgan sana: {user.date_joined.strftime('%d.%m.%Y')}
"""
        await message.answer(profile_text)
        logger.info(f"Profile komandasi yuborildi: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Profile komandasi xatoligi: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

def register_handlers(dp):
    """Profile uchun handlerlarni ro'yxatdan o'tkazish"""
    logger.info("Profile handlerlarini ro'yxatdan o'tkazish")
    dp.register_message_handler(profile_command, commands=['profile'])
    logger.info("Profile handleri ro'yxatdan o'tkazildi") 