import asyncio
from django.core.management.base import BaseCommand
from invest_bot.bot import start_bot

class Command(BaseCommand):
    help = "Run Telegram bot"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🚀 Telegram bot ishga tushmoqda..."))
        
        try:
            asyncio.run(start_bot())
        except KeyboardInterrupt:
            self.stdout.write(self.style.SUCCESS("\n⛔️ Bot to'xtatildi!"))
