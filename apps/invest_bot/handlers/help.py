from aiogram import types
from aiogram.dispatcher.filters import Command
from asgiref.sync import sync_to_async
import logging

# Logger sozlaymiz
logger = logging.getLogger(__name__)

logger.info("help.py fayli yuklandi")

HELP_TEXT = """
🤖 Top Invest Bot buyruqlari:

/start - Botni ishga tushirish
/help - Yordam olish
/profile - Profil malumotlarini korish

Savollaringiz bo'lsa, @admin ga murojaat qiling!
"""

async def help_command(message: types.Message):
    """Help komandasi uchun handler"""
    try:
        await message.answer(HELP_TEXT)
        logger.info(f"Help komandasi yuborildi: {message.from_user.id}")
    except Exception as e:
        logger.error(f"Help komandasi xatoligi: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

async def help_callback(callback_query: types.CallbackQuery):
    """Help callback uchun handler"""
    try:
        await callback_query.message.edit_text(
            HELP_TEXT,
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_start")
            )
        )
        await callback_query.answer()
        logger.info(f"Help callback yuborildi: {callback_query.from_user.id}")
    except Exception as e:
        logger.error(f"Help callback xatoligi: {e}")
        await callback_query.answer("❌ Xatolik yuz berdi", show_alert=True)

def register_handlers(dp):
    """Help uchun handlerlarni ro'yxatdan o'tkazish"""
    logger.info("Help handlerlarini ro'yxatdan o'tkazish")
    dp.register_message_handler(help_command, commands=['help'])
    dp.register_callback_query_handler(help_callback, lambda c: c.data == 'help')
    logger.info("Help handleri ro'yxatdan o'tkazildi") 