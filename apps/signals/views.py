from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from .models import Signal, PricePoint
from .serializers import SignalSerializer, SignalCreateSerializer, PricePointSerializer
from django.utils.timezone import now
from rest_framework.decorators import action
from rest_framework import generics
from rest_framework import filters
from django.core.exceptions import ValidationError
from .filters import SignalFilter
from django_filters.rest_framework import DjangoFilterBackend
import logging
import asyncio
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from apps.users.permissions import SignalPermission
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from rest_framework.exceptions import PermissionDenied
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes

logger = logging.getLogger(__name__)

@extend_schema(
    tags=['signals'],
    description='Signal yaratish uchun API',
    request=SignalCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=SignalSerializer,
            description='Signal muvaffaqiyatli yaratildi'
        )
    },
    examples=[
        OpenApiExample(
            'Signal yaratish',
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
class SignalCreateView(generics.CreateAPIView):
    """Signal yaratish (faqat adminlar)"""
    serializer_class = SignalCreateSerializer
    permission_classes = [IsAuthenticated, SignalPermission]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

@extend_schema(tags=['signals'])
class SignalViewSet(viewsets.ModelViewSet):
    """Signal uchun viewset"""
    queryset = Signal.objects.all()
    serializer_class = SignalSerializer
    permission_classes = [IsAuthenticated, SignalPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SignalFilter
    search_fields = ['instrument__name', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        """Foydalanuvchiga ko'ra signallarni filtrlash"""
        queryset = super().get_queryset()
        
        # Admin bo'lmagan foydalanuvchilar uchun
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_active=True)
        
        # Filterlar
        signal_type = self.request.query_params.get('signal_type')
        if signal_type:
            queryset = queryset.filter(signal_type=signal_type)
            
        instrument_id = self.request.query_params.get('instrument')
        if instrument_id:
            queryset = queryset.filter(instrument_id=instrument_id)
            
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active == 'true')
        
        return queryset

    def perform_create(self, serializer):
        """Signal yaratish"""
        serializer.save(created_by=self.request.user)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='signal_type',
                description='Signal turi (BUY/SELL)',
                required=False,
                type=str,
                enum=['BUY', 'SELL']
            ),
            OpenApiParameter(
                name='instrument',
                description='Instrument ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='is_active',
                description='Faol signallar',
                required=False,
                type=bool
            )
        ],
        responses={
            200: OpenApiResponse(
                response=SignalSerializer,
                description='Signallar ro\'yxati'
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    @extend_schema(
        description='Signalni telegram kanaliga yuborish',
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'status': 'success'}
                    )
                ]
            )
        }
    )
    async def send(self, request, pk=None):
        """Signalni telegram kanaliga yuborish"""
        signal = self.get_object()
        
        try:
            await signal.send_to_telegram()
            return Response({'status': 'success'})
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    @extend_schema(
        description='Signalni yopish',
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                examples=[
                    OpenApiExample(
                        'Success',
                        value={'status': 'success'}
                    )
                ]
            )
        }
    )
    def close(self, request, pk=None):
        """Signalni yopish"""
        signal = self.get_object()
        signal.is_active = False
        signal.closed_at = timezone.now()
        signal.save()
        return Response({'status': 'success'})

@extend_schema(tags=['price-points'])
class PricePointViewSet(viewsets.ModelViewSet):
    """Narx nuqtasi uchun viewset"""
    queryset = PricePoint.objects.all()
    serializer_class = PricePointSerializer
    permission_classes = [IsAuthenticated, SignalPermission]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['signal', 'price_type', 'is_reached']

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='signal',
                description='Signal ID',
                required=False,
                type=int
            ),
            OpenApiParameter(
                name='price_type',
                description='Narx turi (ENTRY/TP/SL)',
                required=False,
                type=str,
                enum=['ENTRY', 'TP', 'SL']
            ),
            OpenApiParameter(
                name='is_reached',
                description='Yetib borilganmi',
                required=False,
                type=bool
            )
        ],
        responses={
            200: OpenApiResponse(
                response=PricePointSerializer,
                description='Narx nuqtalari ro\'yxati'
            )
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """Signalga ko'ra narx nuqtalarini filtrlash"""
        queryset = super().get_queryset()
        signal_id = self.request.query_params.get('signal')
        if signal_id:
            queryset = queryset.filter(signal_id=signal_id)
        return queryset

    def perform_create(self, serializer):
        """Narx nuqtasi yaratish"""
        signal_id = self.request.data.get('signal')
        if signal_id:
            signal = Signal.objects.get(id=signal_id)
            if signal.created_by == self.request.user or self.request.user.is_staff:
                serializer.save()
            else:
                raise PermissionError("Sizda bu signalga narx nuqtasi qo'shish huquqi yo'q")
