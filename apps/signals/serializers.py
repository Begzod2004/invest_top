from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Signal
from apps.instruments.serializers import InstrumentSerializer

# class SignalSerializer(serializers.ModelSerializer):
#     admin = serializers.StringRelatedField(read_only=True)
#     instrument = serializers.StringRelatedField()
#     instrument_details = InstrumentSerializer(source='instrument', read_only=True)

#     class Meta:
#         model = Signal
#         fields = ('id', 'instrument', 'instrument_details', 'entry_price', 'signal_type', 'description', 'is_active', 'is_sent', 'created_at')
#         read_only_fields = ('created_at', 'is_sent')

#     def to_representation(self, instance):
#         # Deep nested ma'lumotlarni olmasligi kerak
#         data = super().to_representation(instance)
#         # Instrument ma'lumotlarini qisqartirish
#         if 'instrument_details' in data and isinstance(data['instrument_details'], dict):
#             data['instrument_details'] = {
#                 'id': instance.instrument.id,
#                 'name': instance.instrument.name,
#                 'symbol': instance.instrument.symbol
#             }
#         return data

class SignalCreateSerializer(serializers.ModelSerializer):
    take_profits = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True,
        write_only=True
    )
    
    class Meta:
        model = Signal
        fields = (
            'instrument', 'custom_instrument', 'signal_type',
            'entry_price', 'take_profits', 'stop_loss',
            'risk_percentage', 'description', 'image'
        )

    def validate(self, data):
        if not data.get('instrument') and not data.get('custom_instrument'):
            raise serializers.ValidationError(
                "Instrument yoki custom_instrument kiritilishi shart"
            )
        return data

    def create(self, validated_data):
        take_profits = validated_data.pop('take_profits', None)
        instance = super().create(validated_data)
        if take_profits is not None:
            instance.set_take_profits(take_profits)
            instance.save()
        return instance

    def update(self, instance, validated_data):
        take_profits = validated_data.pop('take_profits', None)
        instance = super().update(instance, validated_data)
        if take_profits is not None:
            instance.set_take_profits(take_profits)
            instance.save()
        return instance

class SignalSerializer(serializers.ModelSerializer):
    instrument = InstrumentSerializer()
    take_profits = serializers.SerializerMethodField()

    @extend_schema_field(list)
    def get_take_profits(self, obj):
        return obj.take_profits.split(',') if obj.take_profits else []

    class Meta:
        model = Signal
        fields = '__all__'
        read_only_fields = ['created_at']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['instrument'] = {
            'id': instance.instrument.id,
            'name': instance.instrument.name,
            'symbol': instance.instrument.symbol
        }
        return data