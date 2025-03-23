from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class PaymentStatusSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['COMPLETED', 'REJECTED'])

    def validate_status(self, value):
        if value not in ['COMPLETED', 'REJECTED']:
            raise serializers.ValidationError("Status noto'g'ri. COMPLETED yoki REJECTED bo'lishi kerak")
        return value

    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value)
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Bunday to'lov topilmadi")
        return value 