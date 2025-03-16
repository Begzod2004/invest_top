from django.db import models
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio
import logging
from contextlib import suppress

logger = logging.getLogger(__name__)

class Signal(models.Model):
    ORDER_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
    ]

    instrument = models.CharField(max_length=255)
    order_type = models.CharField(max_length=4, choices=ORDER_TYPES)
    target_position = models.DecimalField(max_digits=10, decimal_places=2)
    stop_loss = models.DecimalField(max_digits=10, decimal_places=2)
    take_profit = models.DecimalField(max_digits=10, decimal_places=2)
    is_posted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.instrument} - {self.order_type} at {self.target_position}"

    async def send_to_telegram(self):
        from invest_bot.bot import bot, CHANNEL_ID
        
        text = (
            f"📊 *YANGI SIGNAL* 📊\n\n"
            f"🎯 *{self.instrument}*\n"
            f"📈 Order: {self.order_type.upper()}\n"
            f"💰 Narx: {self.target_position}\n"
            f"🛑 Stop Loss: {self.stop_loss}\n"
            f"✅ Take Profit: {self.take_profit}\n\n"
            f"⏰ {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        )
        
        try:
            async with asyncio.timeout(10):  # 10 sekund timeout
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                    parse_mode="Markdown"
                )
                return True
        except asyncio.TimeoutError:
            logger.error("Signal yuborish vaqti tugadi (timeout)")
            return False
        except Exception as e:
            logger.error(f"Signal yuborishda xatolik: {e}")
            return False

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        
        if is_new and not self.is_posted:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            async def send_with_retry(max_retries=3):
                for attempt in range(max_retries):
                    if await self.send_to_telegram():
                        return True
                    if attempt < max_retries - 1:
                        await asyncio.sleep(1)  # 1 sekund kutish
                return False
            
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(send_with_retry(), loop)
                try:
                    if future.result(timeout=15):  # 15 sekund kutish
                        self.is_posted = True
                        self.save(update_fields=['is_posted'])
                except Exception as e:
                    logger.error(f"Signal yuborishda xatolik: {e}")
            else:
                with suppress(Exception):
                    success = loop.run_until_complete(send_with_retry())
                    if success:
                        self.is_posted = True
                        self.save(update_fields=['is_posted'])
