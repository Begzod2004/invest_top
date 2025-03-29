from rest_framework import serializers
from .models import Subscription, SubscriptionPlan
from apps.users.serializers import UserSerializer

class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = ('id', 'name', 'price', 'duration_days', 'description')

class SubscriptionSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True, required=False)
    plan_details = SubscriptionPlanSerializer(source='plan', read_only=True)
    days_left = serializers.SerializerMethodField()
    payment_screenshot_url = serializers.SerializerMethodField()
    invite_link = serializers.SerializerMethodField()
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'user_details', 'plan', 'plan_details', 
            'status', 'is_active', 'start_date', 'end_date', 
            'amount_paid', 'payment_method', 'payment_date', 
            'payment_screenshot', 'payment_screenshot_url',
            'invite_link', 'days_left', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user_details', 'plan_details', 'is_active', 
            'start_date', 'end_date', 'invite_link', 'days_left', 
            'created_at', 'updated_at', 'payment_screenshot_url'
        ]
    
    def get_days_left(self, obj):
        return obj.days_left()
    
    def get_payment_screenshot_url(self, obj):
        if obj.payment_screenshot:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.payment_screenshot.url)
        return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Admin emas bo'lsa, faqat o'zining ma'lumotlarini ko'rishi kerak
        if request and not getattr(request.user, 'is_staff', False):
            if request.user.id != instance.user.id:
                # O'zganing ma'lumotlarini ko'rish cheklangan
                minimal_data = {
                    'id': data['id'],
                    'is_active': data['is_active'],
                    'status': data['status']
                }
                return minimal_data
        
        return data

class PaymentCreateSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField(required=True)
    payment_method = serializers.CharField(required=True)
    
    def validate_plan_id(self, value):
        try:
            plan = SubscriptionPlan.objects.get(id=value)
            return value
        except SubscriptionPlan.DoesNotExist:
            raise serializers.ValidationError("Berilgan ID bo'yicha obuna rejasi topilmadi")

class PaymentScreenshotSerializer(serializers.Serializer):
    subscription_id = serializers.IntegerField(required=True)
    screenshot = serializers.ImageField(required=True)
    
    def validate_subscription_id(self, value):
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("Autentifikatsiya talab qilinadi")
        
        try:
            subscription = Subscription.objects.get(id=value, user=request.user)
            return value
        except Subscription.DoesNotExist:
            raise serializers.ValidationError("Berilgan ID bo'yicha obuna topilmadi") 