from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from django.conf import settings
import asyncio
import os
import logging

# Logger sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot tokeni
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Kanal ID si
CHANNEL_ID = os.getenv('CHANNEL_ID')

# Web app URL
WEB_APP_URL = os.getenv('WEB_APP_URL')

# Bot va dispatcher instance larini saqlash uchun
_bot_instance = None
_dp_instance = None
_storage_instance = None
_lock = asyncio.Lock()

async def get_bot_instance():
    """Bot instance ni olish"""
    global _bot_instance, _dp_instance, _storage_instance
    
    if _bot_instance is None:
        async with _lock:
            if _bot_instance is None:
                try:
                    # Storage yaratish
                    _storage_instance = MemoryStorage()
                    
                    # Bot yaratish
                    _bot_instance = Bot(token=BOT_TOKEN)
                    
                    # Webhook ni o'chirish
                    await _bot_instance.delete_webhook(drop_pending_updates=True)
                    
                    # Dispatcher yaratish
                    _dp_instance = Dispatcher(_bot_instance, storage=_storage_instance)
                    
                    logger.info("Bot va dispatcher muvaffaqiyatli yaratildi")
                except Exception as e:
                    logger.error(f"Bot yaratishda xatolik: {e}")
                    raise
    
    return {
        'bot': _bot_instance,
        'dp': _dp_instance,
        'storage': _storage_instance
    }

async def close_bot():
    """Bot va storage ni to'g'ri yopish"""
    global _bot_instance, _dp_instance, _storage_instance
    
    if _storage_instance:
        await _storage_instance.close()
        await _storage_instance.wait_closed()
        _storage_instance = None
    
    if _bot_instance:
        session = await _bot_instance.get_session()
        await session.close()
        _bot_instance = None
    
    _dp_instance = None
    logger.info("Bot va storage muvaffaqiyatli yopildi")

# Bot va dispatcher ni yaratish uchun sinxron wrapper
def create_bot():
    """Bot va dispatcher ni yaratish"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(get_bot_instance())
    except Exception as e:
        logger.error(f"Bot yaratishda xatolik: {e}")
        raise

# Export qilinadigan o'zgaruvchilar
__all__ = ['BOT_TOKEN', 'CHANNEL_ID', 'WEB_APP_URL', 'create_bot', 'close_bot']
