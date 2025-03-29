from .bot_config import create_bot
import logging

# Logger sozlaymiz
logger = logging.getLogger(__name__)

# Bot va dispatcher ni yaratish
try:
    bot_instance = create_bot()
    bot = bot_instance['bot']
    dp = bot_instance['dp']
    logger.info("Bot va dispatcher muvaffaqiyatli yaratildi")
except Exception as e:
    logger.error(f"Botni yaratishda xatolik: {e}") 