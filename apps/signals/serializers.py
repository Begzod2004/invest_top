from rest_framework import serializers
from .models import Signal, PricePoint
from apps.instruments.models import Instrument
from apps.instruments.serializers import InstrumentSerializer
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Price Point Example',
            value={
                'signal': 1,
                'price_type': 'ENTRY',
                'price': '1.2345',
                'is_reached': False
            }
        )
    ]
)
class PricePointSerializer(serializers.ModelSerializer):
    """Narx nuqtasi uchun serializer"""
    class Meta:
        model = PricePoint
        fields = [
            'id', 'signal', 'price_type', 
            'price', 'is_reached', 'reached_at'
        ]
        read_only_fields = ['reached_at']

    def validate_price(self, value):
        """Narx validatsiyasi"""
        try:
            float(value)
            return value
        except (TypeError, ValueError):
            raise serializers.ValidationError("Narx son bo'lishi kerak")

class PricePointCreateSerializer(serializers.Serializer):
    """Narx nuqtasi yaratish uchun serializer"""
    price = serializers.CharField(help_text="Narx qiymati (masalan: '1.2345')")

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Signal Create Example',
            value={
                'instrument_id': 1,
                'signal_type': 'BUY',
                'description': 'Signal tavsifi',
                'entry_points': [{'price': '1.2345'}],
                'take_profits': [{'price': '1.2345'}, {'price': '1.2400'}],
                'stop_losses': [{'price': '1.2300'}]
            }
        )
    ]
)
class SignalCreateSerializer(serializers.ModelSerializer):
    """Signal yaratish uchun serializer"""
    instrument_id = serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.all(),
        source='instrument',
        help_text='Instrument ID'
    )
    signal_type = serializers.ChoiceField(
        choices=Signal.SIGNAL_TYPES,
        help_text='Signal turi (BUY/SELL)'
    )
    description = serializers.CharField(
        required=False,
        help_text='Signal tavsifi'
    )
    image = serializers.ImageField(
        required=False,
        help_text='Signal rasmi'
    )
    entry_points = serializers.ListField(
        child=PricePointCreateSerializer(),
        write_only=True,
        required=True,
        help_text='Kirish narxlari ro\'yxati'
    )
    take_profits = serializers.ListField(
        child=PricePointCreateSerializer(),
        write_only=True,
        required=True,
        help_text='Take-profit narxlari ro\'yxati'
    )
    stop_losses = serializers.ListField(
        child=PricePointCreateSerializer(),
        write_only=True,
        required=True,
        help_text='Stop-loss narxlari ro\'yxati'
    )

    class Meta:
        model = Signal
        fields = [
            'instrument_id', 'signal_type',
            'description', 'image',
            'entry_points', 'take_profits', 'stop_losses'
        ]

    def create(self, validated_data):
        entry_points = validated_data.pop('entry_points', [])
        take_profits = validated_data.pop('take_profits', [])
        stop_losses = validated_data.pop('stop_losses', [])
        
        signal = Signal.objects.create(**validated_data)
        
        # Entry point nuqtalarini yaratish
        for i, ep in enumerate(entry_points):
            PricePoint.objects.create(
                signal=signal,
                price_type='ENTRY',
                price=ep['price'],
                order=i + 1
            )
        
        # Take-profit nuqtalarini yaratish
        for i, tp in enumerate(take_profits):
            PricePoint.objects.create(
                signal=signal,
                price_type='TP',
                price=tp['price'],
                order=i + 1
            )
        
        # Stop-loss nuqtalarini yaratish
        for i, sl in enumerate(stop_losses):
            PricePoint.objects.create(
                signal=signal,
                price_type='SL',
                price=sl['price'],
                order=i + 1
            )
        
        return signal

@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Signal Example',
            value={
                'id': 1,
                'instrument': {'id': 1, 'name': 'EUR/USD'},
                'signal_type': 'BUY',
                'description': 'Signal tavsifi',
                'entry_points': [{'price': '1.2345', 'is_reached': False}],
                'take_profits': [{'price': '1.2400', 'is_reached': False}],
                'stop_losses': [{'price': '1.2300', 'is_reached': False}],
                'is_active': True,
                'success_rate': 0.0
            }
        )
    ]
)
class SignalSerializer(serializers.ModelSerializer):
    """Signal uchun serializer"""
    instrument = InstrumentSerializer(read_only=True)
    instrument_id = serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.all(),
        source='instrument',
        write_only=True,
        help_text='Instrument ID'
    )
    signal_type = serializers.ChoiceField(
        choices=Signal.SIGNAL_TYPES,
        help_text='Signal turi (BUY/SELL)'
    )
    signal_type_display = serializers.CharField(
        source='get_signal_type_display',
        read_only=True,
        help_text='Signal turi (o\'zbekcha)'
    )
    description = serializers.CharField(
        required=False,
        help_text='Signal tavsifi'
    )
    image = serializers.ImageField(
        required=False,
        help_text='Signal rasmi'
    )
    risk_reward = serializers.SerializerMethodField(help_text='Risk/Reward nisbati')
    entry_points = PricePointSerializer(many=True, read_only=True)
    take_profits = PricePointSerializer(many=True, read_only=True)
    stop_losses = PricePointSerializer(many=True, read_only=True)
    
    class Meta:
        model = Signal
        fields = [
            'id', 'instrument', 'instrument_id',
            'signal_type', 'signal_type_display',
            'description', 'image',
            'entry_points', 'take_profits', 'stop_losses',
            'is_active', 'is_sent', 'success_rate',
            'created_at', 'updated_at', 'closed_at',
            'created_by', 'risk_reward'
        ]
        read_only_fields = [
            'created_at', 'updated_at', 'closed_at',
            'is_sent', 'success_rate', 'created_by'
        ]

    def get_risk_reward(self, obj):
        return obj.calculate_risk_reward()

    def create(self, validated_data):
        # Signalni yaratish
        signal = Signal.objects.create(**validated_data)
        
        # Price points qo'shish
        price_points_data = self.context.get('price_points', [])
        for point_data in price_points_data:
            PricePoint.objects.create(signal=signal, **point_data)
        
        return signal

    def update(self, instance, validated_data):
        # Signalni yangilash
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Price points yangilash
        price_points_data = self.context.get('price_points', [])
        if price_points_data:
            # Eski price pointlarni o'chirish
            instance.price_points.all().delete()
            # Yangilarini qo'shish
            for point_data in price_points_data:
                PricePoint.objects.create(signal=instance, **point_data)
        
        return instance

