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

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 
            'phone_number', 'telegram_user_id', 'image_url',
            'is_active', 'is_admin', 'is_blocked',
            'balance', 'date_joined', 'updated_at'
        ]
        read_only_fields = ['date_joined', 'updated_at']

class UserVerifySerializer(serializers.Serializer):
    authenticated = serializers.BooleanField(default=True, read_only=True)
    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        return {
            'id': str(obj.id),
            'username': obj.username,
            'role': 'ADMIN' if obj.is_admin else 'USER'
        }

class BroadcastMessageSerializer(serializers.ModelSerializer):
    sent_by = UserSerializer(read_only=True)
    
    class Meta:
        model = BroadcastMessage
        fields = '__all__'
        read_only_fields = ['success_count', 'error_count', 'sent_by', 'created_at'] 