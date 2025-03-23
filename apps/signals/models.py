from django.db import models
from django.conf import settings
from asgiref.sync import sync_to_async
import asyncio
import logging
import json
from contextlib import suppress
from apps.users.models import User
from apps.instruments.models import Instrument
from django.utils import timezone

logger = logging.getLogger(__name__)

class Signal(models.Model):
    SIGNAL_TYPES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )

    instrument = models.ForeignKey(
        Instrument, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    custom_instrument = models.CharField(
        max_length=50, 
        null=True, 
        blank=True,
        help_text="Instrument bazada bo'lmasa"
    )
    signal_type = models.CharField(
        max_length=4, 
        choices=SIGNAL_TYPES,
        null=True,
        blank=True
    )
    entry_price = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )
    take_profits = models.TextField(
        null=True,
        blank=True,
        help_text="Take profit darajalari JSON formatida"
    )
    stop_loss = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )
    risk_percentage = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )
    description = models.TextField(
        null=True,
        blank=True
    )
    image = models.ImageField(
        upload_to='signals/',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_signals')
    is_active = models.BooleanField(default=True)
    is_posted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_instrument_name()} - {self.signal_type}"

    def get_instrument_name(self):
        return self.instrument.name if self.instrument else self.custom_instrument

    def get_take_profits(self):
        """Take profit larni list ko'rinishida qaytaradi"""
        if not self.take_profits:
            return []
        try:
            return json.loads(self.take_profits)
        except:
            return []

    def set_take_profits(self, profits):
        """Take profit larni JSON formatida saqlaydi"""
        self.take_profits = json.dumps(profits) if profits else None

    async def send_to_telegram(self):
        from invest_bot.bot import bot, CHANNEL_ID
        
        take_profits = self.get_take_profits()
        take_profits_text = "\n".join([f"✅ Take Profit {i+1}: {tp}" for i, tp in enumerate(take_profits)]) if take_profits else "❌ Take Profit belgilanmagan"
        
        text = (
            f"📊 *YANGI SIGNAL* 📊\n\n"
            f"🎯 *{self.get_instrument_name()}*\n"
            f"📈 Order: {self.signal_type.upper()}\n"
            f"💰 Narx: {self.entry_price}\n"
            f"🛑 Stop Loss: {self.stop_loss}\n"
            f"{take_profits_text}\n"
        )

        if self.risk_percentage:
            text += f"❕ Risk: {self.risk_percentage}\n"
        
        if self.description:
            text += f"\n📝 {self.description}\n"
            
        text += f"\n⏰ {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        
        try:
            async with asyncio.timeout(10):
                await bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=text,
                    parse_mode="Markdown"
                )
                
                if self.image:
                    await bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=open(self.image.path, 'rb')
                    )
                return True
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
                        await asyncio.sleep(1)
                return False
            
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(send_with_retry(), loop)
                try:
                    if future.result(timeout=15):
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

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Signal'
        verbose_name_plural = 'Signallar'
