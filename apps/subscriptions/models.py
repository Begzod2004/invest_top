from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from django.utils.html import format_html
from django.utils.timezone import now, timedelta
from django.conf import settings
from django.core.exceptions import ValidationError
import secrets
import asyncio
from aiogram import Bot
from django.contrib.auth import get_user_model

User = get_user_model()

def get_default_end_date():
    return timezone.now() + timezone.timedelta(days=30)

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    description = models.TextField(default="Obuna rejasi")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Obuna rejasi"
        verbose_name_plural = "Obuna rejalari"
    
    def __str__(self):
        return self.name

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)
    number = models.CharField(max_length=20)
    card_holder = models.CharField(max_length=50)
    description = models.TextField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "To'lov usuli"
        verbose_name_plural = "To'lov usullari"
    
    def __str__(self):
        return f"{self.name}"


class Subscription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('waiting_admin', 'Admin tasdiqlashi kutilmoqda'),
        ('active', 'Aktiv'),
        ('expired', 'Muddati tugagan'),
        ('cancelled', 'Bekor qilingan'),
        ('rejected', 'Rad etilgan')
    ]
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=get_default_end_date)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Obuna"
        verbose_name_plural = "Obunalar"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    def activate(self):
        """Obunani faollashtirish"""
        self.is_active = True
        self.status = 'active'
        self.start_date = timezone.now()
        self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        self.save(update_fields=['is_active', 'status', 'start_date', 'end_date'])
        
        # Foydalanuvchining statusini ham yangilash
        self.user.is_subscribed = True
        self.user.save(update_fields=['is_subscribed'])
        
        return True

    def cancel(self):
        """Obunani bekor qilish"""
        self.is_active = False
        self.status = 'cancelled'
        self.save(update_fields=['is_active', 'status'])
        return True
        
    def reject(self):
        """Obunani rad etish"""
        self.is_active = False
        self.status = 'rejected'
        self.save(update_fields=['is_active', 'status'])
        return True

    def generate_invite_link(self):
        """Maxsus kanal uchun havola yaratish"""
        # Bu yerda havola yaratish logikasi bo'ladi
        return f"https://t.me/+abcdefghijklmnopqrst"
        
    def is_expired(self):
        """Obuna muddati tugaganmi yoki yo'qmi"""
        return self.end_date < timezone.now()
        
    def days_left(self):
        """Obuna tugashiga qancha kun qolganini hisoblash"""
        if self.is_expired():
            return 0
        delta = self.end_date - timezone.now()
        return max(0, delta.days)



class PaymentType(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True) 
    is_active = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "To'lov turi"
        verbose_name_plural = "To'lov turlari"
    
    def __str__(self):
        return f"{self.name}"

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Kutilmoqda'),
        ('COMPLETED', 'Tasdiqlangan'),
        ('FAILED', 'Rad etilgan'),
        ('CANCELLED', 'Bekor qilingan')
    ]


    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    screenshot = models.ImageField(upload_to='payment_screenshots/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.get_status_display()})"

    def get_status_badge(self):
        badges = {
            'PENDING': 'warning',
            'COMPLETED': 'success',
            'FAILED': 'danger',
            'CANCELLED': 'danger'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            badges[self.status],
            self.get_status_display()
        )

    def get_amount_display(self):
        return format_html(
            '<span class="text-success">{:,.2f} UZS</span>',
            self.amount
        )

    def get_screenshot_preview(self):
        if self.screenshot:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" width="100" /></a>',
                self.screenshot.url, self.screenshot.url
            )
        return "Rasm yuklanmagan"

    async def generate_invite_link(self):
        """Telegram kanal uchun invite link yaratish"""
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            # 24 soatlik link yaratish
            invite_link = await bot.create_chat_invite_link(
                chat_id=settings.CHANNEL_ID,
                expire_date=int((timezone.now() + timezone.timedelta(days=1)).timestamp()),
                member_limit=1
            )
            await bot.session.close()
            return invite_link.invite_link
        except Exception as e:
            return None

    async def send_telegram_message(self, message):
        """Telegram xabar yuborish"""
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            await bot.send_message(
                chat_id=self.user.telegram_user_id,
                text=message,
                parse_mode='HTML'
            )
            await bot.session.close()
            return True
        except Exception as e:
            return False

    def approve(self):
        """To'lovni tasdiqlash"""
        if self.status != 'PENDING':
            raise ValidationError("Faqat kutilayotgan to'lovlarni tasdiqlash mumkin")

        # To'lovni tasdiqlash
        self.status = 'COMPLETED'
        self.save()

        # Obunani aktivlashtirish
        subscription = Subscription.objects.create(
            user=self.user,
            plan=self.subscription_plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=self.subscription_plan.duration_days),
            status='active',
            is_active=True
        )

        # Foydalanuvchining obuna statusini yangilash
        self.user.is_subscribed = True
        self.user.save()

        # Telegram xabar va invite link yuborish
        if self.user.telegram_user_id:
            async def send_approval():
                invite_link = await self.generate_invite_link()
                message = (
                    f"✅ Hurmatli {self.user.first_name},\n\n"
                    f"Sizning to'lovingiz tasdiqlandi!\n"
                    f"To'lov miqdori: {self.amount} so'm\n"
                    f"Obuna muddati: {self.subscription_plan.duration_days} kun\n"
                    f"Tugash sanasi: {subscription.end_date.strftime('%d.%m.%Y')}\n\n"
                )
                
                if invite_link:
                    message += f"🔗 Kanal uchun havola: {invite_link}\n"
                    message += "⚠️ Havola 24 soatdan keyin yaroqsiz bo'ladi!"
                
                await self.send_telegram_message(message)
            
            asyncio.run(send_approval())

    def reject(self):
        """To'lovni rad etish"""
        if self.status != 'PENDING':
            raise ValidationError("Faqat kutilayotgan to'lovlarni rad etish mumkin")

        self.status = 'FAILED'
        self.save()

        # Telegram xabar yuborish
        if self.user.telegram_user_id:
            message = (
                f"❌ Hurmatli {self.user.first_name},\n\n"
                f"Sizning to'lovingiz rad etildi.\n"
                f"To'lov miqdori: {self.amount} so'm\n\n"
                f"Iltimos, to'lov ma'lumotlarini tekshirib, qayta urinib ko'ring."
            )
            
            async def send_rejection():
                await self.send_telegram_message(message)

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_rejection())
            loop.close()
