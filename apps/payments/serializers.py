from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'status']

class PaymentStatusSerializer(serializers.Serializer):
    payment_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=['COMPLETED', 'FAILED'])

    def validate_status(self, value):
        if value not in ['COMPLETED', 'FAILED']:
            raise serializers.ValidationError("Status noto'g'ri. COMPLETED yoki FAILED bo'lishi kerak")
        return value

    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value)
            if payment.status != 'PENDING':
                raise serializers.ValidationError("Bu to'lov allaqachon tasdiqlangan yoki rad etilgan")
        except Payment.DoesNotExist:
            raise serializers.ValidationError("Bunday to'lov topilmadi")
        return value 