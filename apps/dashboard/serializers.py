from rest_framework import serializers
from .models import BroadcastMessage
from apps.users.models import User
from apps.signals.models import Signal
from apps.subscriptions.models import Subscription
from apps.payments.models import Payment
from apps.reviews.models import Review
from apps.instruments.models import Instrument
from apps.signals.serializers import SignalSerializer
from apps.subscriptions.serializers import SubscriptionSerializer
from apps.payments.serializers import PaymentSerializer
from apps.reviews.serializers import ReviewSerializer
from apps.instruments.serializers import InstrumentSerializer
from django.utils import timezone

class UserSerializer(serializers.ModelSerializer):
    """
    Foydalanuvchi ma'lumotlarini serializatsiya qilish
    """
    date_joined = serializers.DateTimeField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    subscription_status = serializers.SerializerMethodField()
    active_subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'phone_number',
            'telegram_user_id', 'balance', 'is_active', 'is_staff',
            'date_joined', 'last_login', 'subscription_status',
            'active_subscription'
        ]
        read_only_fields = ['balance', 'telegram_user_id']
        
    def get_subscription_status(self, obj):
        """Foydalanuvchining obuna statusini qaytaradi"""
        active_sub = obj.subscriptions.filter(
            is_active=True,
            end_date__gt=timezone.now()
        ).first()
        
        if active_sub:
            return {
                'is_active': True,
                'end_date': active_sub.end_date,
                'plan': active_sub.plan.name
            }
        return {
            'is_active': False,
            'end_date': None,
            'plan': None
        }
        
    def get_active_subscription(self, obj):
        """Foydalanuvchining faol obunasini qaytaradi"""
        active_sub = obj.subscriptions.filter(
            is_active=True,
            end_date__gt=timezone.now()
        ).first()
        if active_sub:
            return {
                'id': active_sub.id,
                'plan': active_sub.plan.name,
                'end_date': active_sub.end_date
            }
        return None

class UserVerifySerializer(serializers.ModelSerializer):
    """Foydalanuvchi tekshirish uchun serializer"""
    class Meta:
        model = User
        fields = ('id', 'username', 'is_active', 'is_admin')

class BroadcastMessageSerializer(serializers.Serializer):
    """Xabar yuborish uchun serializer"""
    message = serializers.CharField(help_text="Yuborilishi kerak bo'lgan xabar")
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Xabar yuborilishi kerak bo'lgan foydalanuvchilar IDsi"
    )

    def validate(self, data):
        if not data['user_ids'] and not data['message']:
            raise serializers.ValidationError("Either message or user_ids must be provided")
        return data

    def create(self, validated_data):
        message = validated_data['message']
        user_ids = validated_data.get('user_ids', [])
        success_count = 0
        error_count = 0
        sent_by = self.context['request'].user

        for user_id in user_ids:
            try:
                # Implement the logic to send message to the user
                # This is a placeholder and should be replaced with actual implementation
                success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error sending message to user {user_id}: {str(e)}")

        broadcast_message = BroadcastMessage.objects.create(
            message=message,
            success_count=success_count,
            error_count=error_count,
            sent_by=sent_by
        )
        return broadcast_message

class UserStatsSerializer(serializers.Serializer):
    """Foydalanuvchilar statistikasi uchun serializer"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    telegram_users = serializers.IntegerField()

class PaymentStatsSerializer(serializers.Serializer):
    """To'lovlar statistikasi uchun serializer"""
    total_payments = serializers.IntegerField()
    successful_payments = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    class DailyStats(serializers.Serializer):
        date = serializers.DateField()
        count = serializers.IntegerField()
        amount = serializers.DecimalField(max_digits=10, decimal_places=2)

    daily_stats = DailyStats(many=True, required=False)

class SubscriptionStatsSerializer(serializers.Serializer):
    """Obunalar statistikasi uchun serializer"""
    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()

    class PlanStats(serializers.Serializer):
        plan_name = serializers.CharField(source='plan__name')
        total = serializers.IntegerField()
        active = serializers.IntegerField()

    plan_stats = PlanStats(many=True, required=False) 