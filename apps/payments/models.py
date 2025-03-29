from django.db import models
from django.contrib.auth import get_user_model
from apps.subscriptions.models import SubscriptionPlan, Subscription
from django.utils.timezone import now, timedelta
from django.utils.html import format_html
from apps.users.models import User

class PaymentMethod(models.Model):
    name = models.CharField(max_length=50)
    number = models.CharField(max_length=20)
    card_holder = models.CharField(max_length=50)
    discription = models.TextField(null=True, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name}" 

class PaymentType(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    discription = models.TextField(blank=True, null=True) 
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}"

    
class Payment(models.Model):
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.ForeignKey(PaymentType, on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    screenshot = models.ImageField(upload_to='media/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} - {self.amount} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "To'lov"
        verbose_name_plural = "To'lovlar"

    def approve(self):
        """To'lovni tasdiqlash"""
        if self.status != 'PENDING':
            raise ValueError("Bu to'lov allaqachon tasdiqlangan yoki rad etilgan")
        
        self.status = 'COMPLETED'
        self.updated_at = now()
        self.save()

        # Obunani faollashtirish
        if self.subscription_plan:
            subscription = Subscription.objects.create(
                user=self.user,
                plan=self.subscription_plan,
                is_active=True,
                start_date=now(),
                end_date=now() + timedelta(days=self.subscription_plan.duration_days)
            )
            
            # Foydalanuvchini obunachi qilish
            self.user.is_subscribed = True
            self.user.save()
            
            return subscription

    def reject(self):
        """To'lovni rad etish"""
        if self.status != 'PENDING':
            raise ValueError("Bu to'lov allaqachon tasdiqlangan yoki rad etilgan")
        
        self.status = 'FAILED'
        self.updated_at = now()
        self.save()

    def mark_as_error(self):
        """To'lovni xatolik sifatida belgilash"""
        self.status = 'FAILED'
        self.updated_at = now()
        self.save()

    def get_status_badge(self):
        """To'lov holatini chiroyli ko'rsatish"""
        badges = {
            'PENDING': 'warning',
            'COMPLETED': 'success',
            'FAILED': 'danger',
            'CANCELLED': 'danger'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            badges.get(self.status, 'secondary'),
            self.get_status_display()
        )
    get_status_badge.short_description = "Status"

    def get_amount_display(self):
        """To'lov miqdorini formatlash"""
        return format_html(
            '<span style="font-family: monospace;">{:,.0f} so\'m</span>',
            self.amount
        )
    get_amount_display.short_description = "To'lov miqdori"

    def get_admin_actions(self):
        """Admin panel uchun amallar"""
        if self.status == 'PENDING':
            return format_html(
                '<div class="d-flex justify-content-start">'
                '<button onclick="approvePayment({})" class="btn btn-success btn-sm mx-1">'
                '<i class="fas fa-check"></i> Tasdiqlash'
                '</button>'
                '<button onclick="rejectPayment({})" class="btn btn-danger btn-sm mx-1">'
                '<i class="fas fa-times"></i> Rad etish'
                '</button>'
                '</div>',
                self.id, self.id
            )
        elif self.status == 'COMPLETED':
            return format_html(
                '<span class="badge bg-success">'
                '<i class="fas fa-check"></i> Tasdiqlangan'
                '</span>'
            )
        elif self.status == 'FAILED':
            return format_html(
                '<span class="badge bg-danger">'
                '<i class="fas fa-times"></i> Rad etilgan'
                '</span>'
            )
        elif self.status == 'CANCELLED':
            return format_html(
                '<span class="badge bg-danger">'
                '<i class="fas fa-times"></i> Bekor qilingan'
                '</span>'
            )
        return ""
    get_admin_actions.short_description = "Amallar"

    def get_screenshot_preview(self):
        """To'lov skrinshotini ko'rsatish"""
        if self.screenshot:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; border-radius: 5px;" />',
                self.screenshot.url
            )
        return "Screenshotsiz"
    get_screenshot_preview.short_description = "To'lov cheki"
