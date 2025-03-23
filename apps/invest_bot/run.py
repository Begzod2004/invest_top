import asyncio
from .bot import dp, bot, start_checking, start_posting
from aiogram import executor

async def main():
    await start_checking()  # Obunani tekshirish
    await start_posting()  # Signallarni kanalga joylash

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    executor.start_polling(dp, skip_updates=True)
