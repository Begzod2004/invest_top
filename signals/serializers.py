from rest_framework import serializers
from .models import Signal

class SignalSerializer(serializers.ModelSerializer):
    admin = serializers.StringRelatedField(read_only=True)
    instrument = serializers.StringRelatedField()

    class Meta:
        model = Signal
        fields = '__all__'
        read_only_fields = ['is_posted', 'created_at', 'updated_at']

class SignalCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Signal
        fields = ['instrument', 'order_type', 'target_position', 'stop_loss', 'take_profit']
