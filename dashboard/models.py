from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class BroadcastMessage(models.Model):
    RECIPIENT_TYPES = (
        ('all', 'Barcha foydalanuvchilar'),
        ('subscribed', 'Faqat obuna bo\'lganlar'),
        ('active', 'Faqat faol foydalanuvchilar'),
    )
    
    message = models.TextField()
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPES)
    sent_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='broadcasts')
    success_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_recipient_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Xabar"
        verbose_name_plural = "Xabarlar"
