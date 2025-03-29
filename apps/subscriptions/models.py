from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User
from apps.payments.models import Payment

def get_default_end_date():
    return timezone.now() + timedelta(days=30)

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    description = models.TextField(default="Obuna rejasi")
    
    class Meta:
        verbose_name = "Obuna rejasi"
        verbose_name_plural = "Obuna rejalari"
    
    def __str__(self):
        return self.name

class Subscription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('waiting_admin', 'Admin tasdiqlashi kutilmoqda'),
        ('active', 'Aktiv'),
        ('expired', 'Muddati tugagan'),
        ('cancelled', 'Bekor qilingan'),
        ('rejected', 'Rad etilgan')
    ]
    
    PAYMENT_METHODS = [
        ('uzcard', 'Uzcard'),
        ('humo', 'Humo'),
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('crypto', 'Cryptocurrency'),
        ('other', 'Boshqa')
    ]
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(default=get_default_end_date)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # To'lov ma'lumotlari
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, null=True, blank=True)
    payment_screenshot = models.ImageField(upload_to='payment_screenshots/', null=True, blank=True)
    payment_date = models.DateTimeField(null=True, blank=True)
    
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
