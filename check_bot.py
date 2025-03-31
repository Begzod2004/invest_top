from django.conf import settings
from aiogram import Bot
import asyncio
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

async def check_bot():
    try:
        bot = Bot(settings.BOT_TOKEN)
        me = await bot.get_me()
        print(f"Bot info: {me.username}")
        
        chat = await bot.get_chat(settings.CHANNEL_ID)
        print(f"Channel info: {chat.title}")
        
        bot_member = await bot.get_chat_member(settings.CHANNEL_ID, me.id)
        print(f"Bot status in channel: {bot_member.status}")
        
        await bot.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    asyncio.run(check_bot()) 