from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Permission, AbstractUser
from django.utils import timezone
import uuid

def generate_uuid():
    """Unique UUID yaratish"""
    return str(uuid.uuid4())

class Permission(models.Model):
    name = models.CharField(max_length=255, unique=True)
    codename = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=255, unique=True)
    permissions = models.ManyToManyField(Permission, related_name="roles")

    def __str__(self):
        return self.name


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError('Username kiritilishi shart')

        user = self.model(
            username=username,
            **extra_fields
        )

        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_admin', True)

        return self.create_user(username, password, **extra_fields)

    def get_by_natural_key(self, username):
        return self.get(username=username)


class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    user_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    telegram_user_id = models.CharField(max_length=100, null=True, blank=True)

    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True, unique=True)
    image_url = models.CharField(max_length=255, null=True, blank=True)

    is_admin = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    roles = models.ManyToManyField(Role, related_name='users', blank=True)

    password = models.CharField(max_length=128)

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        permissions = [
            # Foydalanuvchilar uchun ruxsatlar
            ("can_view_users", "Can view users"),
            ("can_edit_users", "Can edit users"),
            ("can_block_users", "Can block users"),
            
            # Signallar uchun ruxsatlar
            ("can_view_signals", "Can view signals"),
            ("can_create_signals", "Can create signals"),
            ("can_edit_signals", "Can edit signals"),
            ("can_delete_signals", "Can delete signals"),
            
            # To'lovlar uchun ruxsatlar
            ("can_view_payments", "Can view payments"),
            ("can_approve_payments", "Can approve payments"),
            ("can_reject_payments", "Can reject payments"),
            
            # Obunalar uchun ruxsatlar
            ("can_view_subscriptions", "Can view subscriptions"),
            ("can_manage_subscriptions", "Can manage subscriptions"),
            
            # Sharhlar uchun ruxsatlar
            ("can_view_reviews", "Can view reviews"),
            ("can_manage_reviews", "Can manage reviews"),
            
            # Xabarlar uchun ruxsatlar
            ("can_send_broadcasts", "Can send broadcast messages"),
        ]

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        return self.username

    def __str__(self):
        return self.full_name
