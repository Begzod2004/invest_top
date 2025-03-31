from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SubscriptionPlan, Subscription, Payment, PaymentMethod

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = ['id', 'name', 'number', 'card_holder', 'description', 'is_default']

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'name', 'price', 'duration_days', 'description']

class PaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    payment_method = PaymentMethodSerializer(read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'user', 'subscription_plan', 'amount',
            'payment_method', 'status', 'screenshot',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'status']

class SubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plan = SubscriptionPlanSerializer(read_only=True)
    days_left = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'status', 'is_active',
            'start_date', 'end_date', 'created_at',
            'updated_at', 'days_left'
        ]
        read_only_fields = ['created_at', 'updated_at', 'days_left']
    
    def get_days_left(self, obj):
        return obj.days_left()

class SubscriptionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['plan']

class PaymentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['subscription_plan', 'payment_method', 'amount', 'screenshot', 'description']