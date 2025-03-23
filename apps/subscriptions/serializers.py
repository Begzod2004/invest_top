from rest_framework import serializers
from .models import Subscription, SubscriptionPlan

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name', 'price', 'duration_days', 'description')

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    
    class Meta:
        model = Subscription
        fields = ('id', 'user', 'plan', 'plan_details', 'is_active', 'start_date', 'end_date', 'created_at')
        read_only_fields = ('created_at', 'start_date')

    def to_representation(self, instance):
        # Deep nested ma'lumotlarni olmasligi kerak
        data = super().to_representation(instance)
        # User ma'lumotlarini cheklab qo'yish
        if 'user' in data and not self.context.get('include_user_details', False):
            data['user'] = instance.user.id
        return data 