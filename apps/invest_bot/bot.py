from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from .bot_config import create_bot, WEB_APP_URL
import logging

# Logging ni sozlaymiz
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va dispatcher ni olish
bot_instance = create_bot()
bot = bot_instance['bot']
dp = bot_instance['dp']

# Start komandasi uchun handler
@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    """Start komandasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(
        text="🌐 Web App'ga kirish",
        web_app={"url": WEB_APP_URL}
    ))
    
    await message.answer(
        "Assalomu alaykum! Top Invest botiga xush kelibsiz.\n"
        "Web App orqali barcha imkoniyatlardan foydalanishingiz mumkin:",
        reply_markup=keyboard
    )

async def start_bot():
    """Botni ishga tushirish"""
    try:
        logger.info("Bot ishga tushirilmoqda...")
        # Polling ni boshlash
        await dp.start_polling(reset_webhook=True)
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
        if bot:
            await bot.close()

def run_bot():
    """Botni asinkron rejimda ishga tushirish"""
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(start_bot())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi")
    finally:
        loop.close()

# API uchun funksiyalar
async def send_message_to_user(user_id: str, message: str) -> bool:
    """Foydalanuvchiga xabar yuborish"""
    try:
        await bot.send_message(
            chat_id=int(user_id),
            text=message,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        logger.error(f"Xabar yuborishda xatolik: {e}")
        return False

async def send_photo_to_user(user_id: str, photo_path: str, caption: str = None) -> bool:
    """Foydalanuvchiga rasm yuborish"""
    try:
        with open(photo_path, 'rb') as photo:
            await bot.send_photo(
                chat_id=int(user_id),
                photo=photo,
                caption=caption,
                parse_mode="Markdown"
            )
        return True
    except Exception as e:
        logger.error(f"Rasm yuborishda xatolik: {e}")
        return False

async def send_signal_to_channel(channel_id: str, signal_text: str, image_path: str = None) -> bool:
    """Kanalga signal yuborish"""
    try:
        await bot.send_message(
            chat_id=channel_id,
            text=signal_text,
            parse_mode="Markdown"
        )
        
        if image_path:
            with open(image_path, 'rb') as photo:
                await bot.send_photo(
                    chat_id=channel_id,
                    photo=photo
                )
        return True
    except Exception as e:
        logger.error(f"Signalni kanalga yuborishda xatolik: {e}")
        return False

async def broadcast_message(user_ids: list, message: str) -> dict:
    """Ko'p foydalanuvchilarga xabar yuborish"""
    stats = {'success': 0, 'failed': 0}
    
    for user_id in user_ids:
        try:
            await bot.send_message(
                chat_id=int(user_id),
                text=message,
                parse_mode="Markdown"
            )
            stats['success'] += 1
        except Exception as e:
            logger.error(f"Broadcast xabar yuborishda xatolik (user_id={user_id}): {e}")
            stats['failed'] += 1
    
    return stats

# Bot instance ni global qilib export qilamiz
__all__ = ['bot', 'dp', 'WEB_APP_URL']