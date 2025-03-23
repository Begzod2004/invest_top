from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from django.conf import settings
import asyncio

# Bot tokenini olish
BOT_TOKEN = settings.BOT_TOKEN
CHANNEL_ID = settings.CHANNEL_ID
WEB_APP_URL = settings.WEB_APP_URL

# Bot holatini saqlash uchun
_instance = None
_lock = asyncio.Lock()

async def get_bot_instance():
    global _instance
    async with _lock:
        if _instance is None:
            # Bot va dispatcher yaratish
            storage = MemoryStorage()
            bot = Bot(token=BOT_TOKEN)
            # Webhook ni o'chirish
            await bot.delete_webhook(drop_pending_updates=True)
            dp = Dispatcher(bot, storage=storage)
            _instance = {
                'bot': bot,
                'dp': dp
            }
        return _instance

# Bot va dispatcher ni yaratish uchun sinxron wrapper
def create_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(get_bot_instance())

# Export qilinadigan o'zgaruvchilar
__all__ = ['BOT_TOKEN', 'CHANNEL_ID', 'WEB_APP_URL', 'create_bot']
