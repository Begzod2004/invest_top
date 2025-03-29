import signal
import sys
import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.invest_bot.bot import run_bot
from apps.invest_bot.bot_config import close_bot
import asyncio

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Telegram botni ishga tushirish'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._shutdown = False
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Signal handler for graceful shutdown"""
        self.stdout.write(self.style.WARNING('\nBot to\'xtatilmoqda...'))
        self._shutdown = True

    def handle(self, *args, **options):
        try:
            self.stdout.write(
                self.style.SUCCESS('Bot ishga tushirilmoqda...')
            )
            
            # Bot ni ishga tushirish
            run_bot()
            
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nBot to\'xtatildi (KeyboardInterrupt)')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Xatolik yuz berdi: {e}')
            )
            logger.exception("Bot ishga tushishda xatolik:")
            sys.exit(1)
        finally:
            # Bot va storage ni tozalash
            try:
                loop = asyncio.get_event_loop()
                loop.run_until_complete(close_bot())
                loop.close()
            except Exception as e:
                logger.error(f"Bot to'xtatishda xatolik: {e}")
            
            self.stdout.write(
                self.style.SUCCESS('Bot muvaffaqiyatli to\'xtatildi')
            )
