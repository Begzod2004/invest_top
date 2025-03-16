from rest_framework import serializers
from .models import Subscription, SubscriptionPlan
from users.serializers import UserSerializer

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    subscription_plan = SubscriptionPlanSerializer(read_only=True)
    remaining_days = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = '__all__'
    
    def get_remaining_days(self, obj):
        """Obuna muddatidan qolgan kunlarni hisoblash"""
        from django.utils.timezone import now
        if obj.expires_at and obj.status == 'active':
            delta = obj.expires_at - now()
            return max(0, delta.days)
        return 0 