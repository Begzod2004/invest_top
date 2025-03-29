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

logger = logging.getLogger(__name__)

class SignalCreateView(generics.CreateAPIView):
    """Signal yaratish (faqat adminlar)"""
    serializer_class = SignalCreateSerializer

    def perform_create(self, serializer):
        signal = serializer.save(created_by=self.request.user)
        
        # TP va SL nuqtalarini yaratish
        tp_prices = self.request.data.get('take_profits', [])
        sl_prices = self.request.data.get('stop_losses', [])

        # TP nuqtalari
        for tp in tp_prices:
            PricePoint.objects.create(
                signal=signal,
                price_type='TP',
                price=tp['price'],
                order=tp['order']
            )
        
        # SL nuqtalari
        for sl in sl_prices:
            PricePoint.objects.create(
                signal=signal,
                price_type='SL',
                price=sl['price'],
                order=sl['order']
            )

class SignalViewSet(viewsets.ModelViewSet):
    """Signallar bilan ishlash uchun API"""
    queryset = Signal.objects.all()
    serializer_class = SignalSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SignalFilter
    search_fields = ['instrument__name', 'description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SignalCreateSerializer
        return SignalSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_at=now())

    @action(detail=True, methods=['post'])
    async def send(self, request, pk=None):
        """Signalni telegram kanaliga yuborish"""
        try:
            signal = self.get_object()
            
            if signal.is_sent:
                return Response(
                    {"detail": "Signal allaqachon yuborilgan"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            await signal.send_to_telegram()
            
            return Response(
                {"detail": "Signal muvaffaqiyatli yuborildi"},
                status=status.HTTP_200_OK
            )
            
        except ValidationError as e:
            logger.error(f"Signal yuborishda xatolik: {str(e)}")
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Kutilmagan xatolik: {str(e)}")
            return Response(
                {"detail": "Serverda xatolik yuz berdi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
