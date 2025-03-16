from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'user', 'subscription_plan', 'amount', 'payment_method', 
                 'status', 'screenshot', 'created_at', 'updated_at']
        read_only_fields = ['status', 'created_at', 'updated_at'] 