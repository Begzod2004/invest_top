from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from .bot_config import BOT_TOKEN, CHANNEL_ID, WEB_APP_URL, create_bot, close_bot
from .handlers import register_all_handlers
import asyncio
import logging
from apps.users.models import User
from django.utils import timezone
from asgiref.sync import sync_to_async
from typing import Optional, Dict

# Logging ni sozlaymiz
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def send_message_to_user(user_id: str, message: str) -> bool:
    """Foydalanuvchiga xabar yuborish"""
    try:
        bot_instance = await create_bot()
        bot = bot_instance['bot']
        
        await bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode="Markdown"
        )
        return True
    except Exception as e:
        logger.error(f"Xabar yuborishda xatolik: {e}")
        return False
    finally:
        await close_bot()

async def send_photo_to_user(user_id: str, photo_path: str, caption: str = None) -> bool:
    """Foydalanuvchiga rasm yuborish"""
    try:
        bot_instance = await create_bot()
        bot = bot_instance['bot']
        
        with open(photo_path, 'rb') as photo:
            await bot.send_photo(
                chat_id=user_id,
                photo=photo,
                caption=caption,
                parse_mode="Markdown"
            )
        return True
    except Exception as e:
        logger.error(f"Rasm yuborishda xatolik: {e}")
        return False
    finally:
        await close_bot()

async def send_signal_to_channel(channel_id: str, signal_text: str, image_path: Optional[str] = None) -> bool:
    """Kanalga signal yuborish"""
    try:
        bot_instance = await create_bot()
        bot = bot_instance['bot']
        
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
    finally:
        await close_bot()

async def broadcast_message(user_ids: list, message: str) -> Dict:
    """Ko'p foydalanuvchilarga xabar yuborish"""
    if not isinstance(user_ids, list) or not message:
        return {
            'success': False,
            'error': 'Invalid parameters',
            'stats': {'total': 0, 'success': 0, 'failed': 0}
        }

    stats = {
        'total': len(user_ids),
        'success': 0,
        'failed': 0
    }

    try:
        bot_instance = await create_bot()
        bot = bot_instance['bot']
        
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode="Markdown"
                )
                stats['success'] += 1
            except Exception as e:
                logger.error(f"Foydalanuvchi {user_id}ga xabar yuborishda xatolik: {e}")
                stats['failed'] += 1
                continue
        
        return {
            'success': True,
            'stats': stats
        }
    except Exception as e:
        logger.error(f"Broadcast xatolik: {e}")
        return {
            'success': False,
            'error': str(e),
            'stats': stats
        }
    finally:
        await close_bot()

def run_bot():
    """Botni ishga tushirish"""
    try:
        # Bot va dispatcher yaratish
        bot_instance = create_bot()
        dp = bot_instance['dp']
        
        # Handlerlarni ro'yxatdan o'tkazish
        register_all_handlers(dp)
        
        # Polling ni boshlash
        logger.info("Bot ishga tushirildi")
        
        # Asosiy loop ni ishga tushirish
        loop = asyncio.get_event_loop()
        loop.create_task(dp.start_polling(reset_webhook=True))
        loop.run_forever()
        
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi")
    except Exception as e:
        logger.error(f"Botni ishga tushirishda xatolik: {e}")
    finally:
        # Bot va storage ni tozalash
        loop = asyncio.get_event_loop()
        loop.run_until_complete(close_bot())
        loop.close()

# Bot instance ni global qilib export qilamiz
__all__ = ['bot', 'dp', 'WEB_APP_URL', 'run_bot']