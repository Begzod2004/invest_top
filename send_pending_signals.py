import os
import django
import asyncio
from asgiref.sync import sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.signals.models import Signal

async def send_all():
    """Yuborilmagan signallarni yuborish"""
    signals = await sync_to_async(list)(Signal.objects.filter(is_sent=False))
    
    for signal in signals:
        try:
            await signal.send_to_telegram()
            # Yuborilgan statusini yangilash
            await sync_to_async(Signal.objects.filter(id=signal.id).update)(is_sent=True)
            print(f"Signal #{signal.id} muvaffaqiyatli yuborildi")
        except Exception as e:
            print(f"Signal #{signal.id} yuborishda xatolik: {str(e)}")

if __name__ == '__main__':
    asyncio.run(send_all()) 