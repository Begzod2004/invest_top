from aiogram import types
from aiogram.dispatcher.filters.builtin import CommandStart
from apps.users.models import User
from django.utils import timezone
from ..loader import dp

@dp.message_handler(CommandStart())
async def bot_start(message: types.Message):
    # Foydalanuvchi ma'lumotlarini olamiz
    telegram_id = str(message.from_user.id)
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    try:
        # Foydalanuvchini bazada qidiramiz yoki yangi yaratamiz
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

        if created:
            await message.answer(f"Xush kelibsiz, {user.first_name}! Siz muvaffaqiyatli ro'yxatdan o'tdingiz.")
        else:
            # Agar user mavjud bo'lsa, ma'lumotlarini yangilaymiz
            user.username = username or telegram_id
            user.first_name = first_name
            user.last_name = last_name
            user.is_active = True
            user.save()
            
            await message.answer(f"Qaytganingizdan xursandmiz, {user.first_name}!")

    except Exception as e:
        print(f"Error in bot_start: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.") 