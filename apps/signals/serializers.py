from rest_framework import serializers
from .models import Signal, PricePoint
from apps.instruments.models import Instrument

class PricePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricePoint
        fields = ['price_type', 'price', 'order', 'description']

class SignalCreateSerializer(serializers.ModelSerializer):
    """Signal yaratish uchun serializer"""
    entry_points = PricePointSerializer(many=True, required=False)
    take_profits = PricePointSerializer(many=True, required=True)
    stop_losses = PricePointSerializer(many=True, required=True)

    class Meta:
        model = Signal
        fields = [
            'instrument', 'signal_type', 'description', 
            'image', 'entry_points', 'take_profits', 
            'stop_losses'
        ]
    
    def create(self, validated_data):
        entry_points = validated_data.pop('entry_points', [])
        take_profits = validated_data.pop('take_profits', [])
        stop_losses = validated_data.pop('stop_losses', [])

        signal = Signal.objects.create(**validated_data)

        # Entry pointlarni yaratish
        for entry in entry_points:
            PricePoint.objects.create(
                signal=signal,
                price_type='ENTRY',
                **entry
            )
        
        # TP nuqtalarini yaratish
        for tp in take_profits:
            PricePoint.objects.create(
                signal=signal,
                price_type='TP',
                **tp
            )
        
        # SL nuqtalarini yaratish
        for sl in stop_losses:
            PricePoint.objects.create(
                signal=signal,
                price_type='SL',
                **sl
            )

        return signal

class SignalSerializer(serializers.ModelSerializer):
    """Signal ko'rish uchun serializer"""
    entry_points = PricePointSerializer(many=True, read_only=True)
    take_profits = PricePointSerializer(many=True, read_only=True)
    stop_losses = PricePointSerializer(many=True, read_only=True)
    risk_reward = serializers.SerializerMethodField()

    class Meta:
        model = Signal
        fields = [
            'id', 'instrument', 'signal_type', 'description',
            'image', 'entry_points', 'take_profits', 'stop_losses',
            'is_active', 'is_sent', 'success_rate', 'risk_reward',
            'created_at', 'updated_at', 'closed_at'
        ]
    
    def get_risk_reward(self, obj):
        return obj.calculate_risk_reward()

