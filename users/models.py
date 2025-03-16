from django.db import models
import uuid

def generate_uuid():
    """Unique UUID yaratish"""
    return str(uuid.uuid4())

class User(models.Model):
    user_id = models.BigIntegerField(unique=True)
    telegram_user_id = models.FloatField(unique=True)
    image_url = models.URLField(blank=True, null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=255, unique=True, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_subscribed = models.BooleanField(default=False)
    referral_code = models.CharField(max_length=36, default=generate_uuid, unique=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    temp_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.first_name

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"

    def get_referral_link(self):
        """Referral havolani qaytarish"""
        from invest_bot.bot_config import BOT_USERNAME
        return f"https://t.me/{BOT_USERNAME}?start=ref_{self.referral_code}"

    def add_referral(self, referred_user):
        """Yangi referral qo'shish"""
        if referred_user != self:
            referred_user.referred_by = self
            referred_user.save()