import os
import django
import asyncio
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.signals.models import Signal

async def test_send_signal():
    try:
        # Birinchi signalni olish
        signal = await sync_to_async(Signal.objects.first)()
        if not signal:
            print("Signallar topilmadi")
            return
            
        print(f"Signal ID: {signal.id}")
        print(f"Signal type: {signal.signal_type}")
        print(f"Instrument: {await sync_to_async(lambda: signal.instrument.name)()}")
        
        # Xabarni formatlash
        message = await sync_to_async(signal.format_message)()
        print(f"\nFormatted message:\n{message}\n")
        
        # Signalni yuborish
        print("Signalni yuborish boshlandi...")
        result = await signal.send_to_telegram()
        print(f"Yuborish natijasi: {result}")
        
    except ValidationError as e:
        print(f"Validation error: {str(e)}")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == '__main__':
    asyncio.run(test_send_signal()) 