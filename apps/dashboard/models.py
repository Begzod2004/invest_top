from django.db import models
from django.conf import settings
from apps.users.models import User

# Create your models here.

class BroadcastMessage(models.Model):
    RECIPIENT_TYPES = (
        ('all', 'Barcha foydalanuvchilar'),
        ('subscribed', 'Faqat obuna bo\'lganlar'),
        ('active', 'Faqat faol foydalanuvchilar'),
    )
    
    message = models.TextField()
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPES)
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_recipient_type_display()} - {self.sent_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = "Xabar"
        verbose_name_plural = "Xabarlar"
