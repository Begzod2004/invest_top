import logging
from aiogram import Dispatcher

# Logger sozlaymiz
logger = logging.getLogger(__name__)

logger.info("Handlers paketi yuklandi")

# Handlerlarni to'g'ri tartibda yuklaymiz
from .start import register_handlers as register_start_handlers
from .help import register_handlers as register_help_handlers
from .profile import register_handlers as register_profile_handlers
# Boshqa handlerlar uchun import

def register_all_handlers(dp: Dispatcher):
    """Barcha handlerlarni ro'yxatdan o'tkazish"""
    logger.info("Barcha handlerlarni ro'yxatdan o'tkazish boshlandi")
    register_start_handlers(dp)
    register_help_handlers(dp)
    register_profile_handlers(dp)
    # Boshqa handlerlar uchun registratsiya

    logger.info(f"Handlers ro'yxatdan o'tkazildi. Handlers soni: {len(dp.message_handlers.handlers)}")
    
    return dp 