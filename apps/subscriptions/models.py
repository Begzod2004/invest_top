from django.db import models
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User

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
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    is_active = models.BooleanField(default=True)
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
        self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        self.save(update_fields=['is_active', 'end_date'])

    def generate_invite_link(self):
        """24 soatlik havola yaratish"""
        # Bu yerda havola yaratish logikasi bo'ladi
        return f"https://t.me/your_channel?invite={self.id}"
