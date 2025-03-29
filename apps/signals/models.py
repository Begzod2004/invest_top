from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.users.models import User
from apps.instruments.models import Instrument
import requests
import logging
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class PricePoint(models.Model):
    """Signal uchun narx nuqtasi"""
    PRICE_TYPES = [
        ('ENTRY', _('Kirish narxi')),
        ('TP', _('Take-profit')),
        ('SL', _('Stop-loss')),
    ]

    signal = models.ForeignKey(
        'Signal',
        on_delete=models.CASCADE,
        related_name='price_points',
        verbose_name=_('Signal')
    )
    price_type = models.CharField(
        max_length=10,
        choices=PRICE_TYPES,
        verbose_name=_('Narx turi')
    )
    price = models.CharField(
        max_length=50,
        verbose_name=_('Narx')
    )
    order = models.PositiveSmallIntegerField(
        default=0,
        verbose_name=_('Tartib raqami')
    )
    description = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name=_('Izoh')
    )
    is_reached = models.BooleanField(
        default=False,
        verbose_name=_('Yetib borildimi')
    )
    reached_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Yetib borilgan vaqt')
    )

    class Meta:
        verbose_name = _('Narx nuqtasi')
        verbose_name_plural = _('Narx nuqtalari')
        ordering = ['order']

    def __str__(self):
        return f"{self.get_price_type_display()}: {self.price}"

class Signal(models.Model):
    """Signal modeli"""
    
    SIGNAL_TYPES = [
        ('BUY', _('Sotib olish')),
        ('SELL', _('Sotish')),
    ]
    
    # Asosiy maydonlar
    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name='signals',
        verbose_name=_('Instrument')
    )
    signal_type = models.CharField(
        max_length=4,
        choices=SIGNAL_TYPES,
        verbose_name=_('Signal turi')
    )
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Tavsif')
    )
    image = models.ImageField(
        upload_to='signals/',
        null=True,
        blank=True,
        verbose_name=_('Rasm')
    )
    
    # Status maydonlari
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Faol')
    )
    is_sent = models.BooleanField(
        default=False,
        verbose_name=_('Yuborilgan')
    )
    success_rate = models.FloatField(
        default=0,
        verbose_name=_('Muvaffaqiyat darajasi')
    )
    
    # Vaqt maydonlari
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Yaratilgan vaqt')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Yangilangan vaqt')
    )
    closed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Yopilgan vaqt')
    )
    
    # Muallif
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='signals',
        verbose_name=_('Yaratuvchi')
    )
    
    class Meta:
        verbose_name = _('Signal')
        verbose_name_plural = _('Signallar')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.instrument.name} - {self.get_signal_type_display()}"

    @property
    def entry_points(self):
        """Kirish narxlari"""
        return self.price_points.filter(price_type='ENTRY').order_by('order')

    @property
    def take_profits(self):
        """Take-profit narxlari"""
        return self.price_points.filter(price_type='TP').order_by('order')

    @property
    def stop_losses(self):
        """Stop-loss narxlari"""
        return self.price_points.filter(price_type='SL').order_by('order')

    def calculate_risk_reward(self):
        """Risk/Reward nisbatini hisoblash"""
        try:
            # Birinchi entry point va TP/SL larni olish
            entry = self.entry_points.first()
            tp = self.take_profits.first()
            sl = self.stop_losses.first()
            
            if not all([entry, tp, sl]):
                return None
            
            entry_price = float(entry.price)
            tp_price = float(tp.price)
            sl_price = float(sl.price)
            
            if self.signal_type == 'BUY':
                risk = entry_price - sl_price
                reward = tp_price - entry_price
            else:  # SELL
                risk = sl_price - entry_price
                reward = entry_price - tp_price
            
            if risk <= 0:
                return None
                
            return round(reward / risk, 2)
            
        except (ValueError, ZeroDivisionError, AttributeError):
            return None

    def format_message(self):
        """Signal xabarini formatlash"""
        signal_emoji = "🟢" if self.signal_type == "BUY" else "🔴"
        signal_type = "SOTIB OLISH" if self.signal_type == "BUY" else "SOTISH"
        
        message = f"{signal_emoji} #{self.instrument.name} #{signal_type}\n\n"
        
        # Entry pointlarni formatlash
        message += "📍 Kirish narxlari:\n"
        for entry in self.entry_points:
            message += f"• {entry.price}\n"
        message += "\n"
        
        # Take-profit larni formatlash
        message += "🎯 Take-Profit:\n"
        for tp in self.take_profits:
            message += f"• {tp.price}\n"
        message += "\n"
        
        # Stop-loss larni formatlash
        message += "🛑 Stop-Loss:\n"
        for sl in self.stop_losses:
            message += f"• {sl.price}\n"
        message += "\n"
        
        # Qo'shimcha ma'lumotlar
        if self.description:
            message += f"ℹ️ {self.description}\n\n"
        
        # Risk/Reward
        risk_reward = self.calculate_risk_reward()
        if risk_reward:
            message += f"📊 Risk/Reward: {risk_reward:.2f}\n\n"
        
        message += "#trading #signals"
        return message

    async def send_to_telegram(self):
        """Signalni telegram kanaliga yuborish"""
        try:
            bot_token = settings.BOT_TOKEN
            channel_id = settings.CHANNEL_ID
            
            if not bot_token or not channel_id:
                raise ValidationError("Bot token yoki kanal ID topilmadi")
            
            base_url = f"https://api.telegram.org/bot{bot_token}"
            
            # Format message using sync_to_async
            message = await sync_to_async(self.format_message)()
            
            # Rasm bor bo'lsa, rasm bilan yuborish
            if self.image:
                photo_url = f"{base_url}/sendPhoto"
                data = {
                    "chat_id": channel_id,
                    "photo": self.image.url,
                    "caption": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(photo_url, data=data)
            else:
                # Faqat xabar yuborish
                message_url = f"{base_url}/sendMessage"
                data = {
                    "chat_id": channel_id,
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(message_url, data=data)
            
            if response.status_code == 200:
                self.is_sent = True
                await sync_to_async(self.save)()
                logger.info(f"Signal #{self.id} muvaffaqiyatli yuborildi")
                return True
            else:
                error_msg = f"Telegram API xatosi: {response.text}"
                logger.error(error_msg)
                raise ValidationError(error_msg)
                
        except Exception as e:
            error_msg = f"Signal yuborishda xatolik: {str(e)}"
            logger.error(error_msg)
            raise ValidationError(error_msg)
