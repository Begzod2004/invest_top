from django.db import models
from django.utils.timezone import now, timedelta
from users.models import User

class SubscriptionPlan(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.price} so'm"

    def create_subscription(self, user):
        """Yangi obuna yaratish"""
        return Subscription.objects.create(
            user=user,
            subscription_plan=self,
            amount_paid=self.price,
            status="pending"
        )

class Subscription(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Kutilmoqda'),
        ('waiting_admin', 'Admin tekshiruvi'),
        ('active', 'Faol'),
        ('expired', 'Muddati tugagan'),
        ('rejected', 'Rad etilgan'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_screenshot = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=now)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.first_name} - {self.subscription_plan.title}"

    def activate(self):
        """Obunani faollashtirish"""
        self.status = "active"
        self.expires_at = now() + timedelta(days=self.subscription_plan.duration_days)
        self.save(update_fields=['status', 'expires_at'])

    def generate_invite_link(self):
        """24 soatlik havola yaratish"""
        # Bu yerda havola yaratish logikasi bo'ladi
        return f"https://t.me/your_channel?invite={self.id}"
