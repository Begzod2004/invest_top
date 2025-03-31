from rest_framework import serializers
from django.contrib.auth import get_user_model
from apps.signals.models import Signal
from apps.subscriptions.models import Subscription, Payment
from apps.reviews.models import Review

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Foydalanuvchi ma'lumotlari uchun serializer"""
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'is_active', 'is_blocked'
        ]

class UserVerifySerializer(serializers.ModelSerializer):
    """Foydalanuvchi tekshirish uchun serializer"""
    class Meta:
        model = User
        fields = ('id', 'username', 'is_active', 'is_admin')

class UserStatsSerializer(serializers.Serializer):
    """Foydalanuvchilar statistikasi uchun serializer"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    blocked_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    new_users = serializers.IntegerField()

class SignalSerializer(serializers.ModelSerializer):
    """Signal ma'lumotlari uchun serializer"""
    class Meta:
        model = Signal
        fields = [
            'id', 'instrument', 'signal_type', 'description', 'image',
            'is_active', 'is_sent', 'success_rate',
            'created_at', 'updated_at', 'closed_at', 'created_by'
        ]

class SignalStatsSerializer(serializers.Serializer):
    """Signallar statistikasi uchun serializer"""
    total_signals = serializers.IntegerField()
    active_signals = serializers.IntegerField()
    sent_signals = serializers.IntegerField()
    new_signals = serializers.IntegerField()
    avg_success_rate = serializers.FloatField()

class SubscriptionSerializer(serializers.ModelSerializer):
    """Obuna ma'lumotlari uchun serializer"""
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'status', 'is_active',
            'start_date', 'end_date', 'created_at', 'updated_at'
        ]

class SubscriptionStatsSerializer(serializers.Serializer):
    """Obunalar statistikasi uchun serializer"""
    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    new_subscriptions = serializers.IntegerField()

class ReviewSerializer(serializers.ModelSerializer):
    """Sharh ma'lumotlari uchun serializer"""
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'comment', 'rating',
            'is_approved', 'created_at', 'updated_at'
        ]

class ReviewStatsSerializer(serializers.Serializer):
    """Sharhlar statistikasi uchun serializer"""
    total_reviews = serializers.IntegerField()
    approved_reviews = serializers.IntegerField()
    new_reviews = serializers.IntegerField()
    avg_rating = serializers.FloatField()

class BroadcastMessageSerializer(serializers.Serializer):
    """Xabar yuborish uchun serializer"""
    message = serializers.CharField()
    users = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True
    )

class PaymentStatsSerializer(serializers.Serializer):
    """To'lovlar statistikasi uchun serializer"""
    total_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2) 