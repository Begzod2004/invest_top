from django.core.management.base import BaseCommand
from django.conf import settings
from apps.invest_bot.bot import run_bot, bot_instance

class Command(BaseCommand):
    help = 'Telegram botni ishga tushirish'

    def handle(self, *args, **options):
        try:
            self.stdout.write(
                self.style.SUCCESS('Bot ishga tushirilmoqda...')
            )
            # Bot ni ishga tushirish
            run_bot()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nBot to\'xtatildi')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Xatolik yuz berdi: {e}')
            )
