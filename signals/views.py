from rest_framework import viewsets, status, generics
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import transaction
from django.utils.timezone import now
import asyncio
from .models import Signal
from .serializers import SignalSerializer, SignalCreateSerializer

# Signal yaratish (faqat adminlar)
class SignalCreateView(generics.CreateAPIView):
    serializer_class = SignalCreateSerializer
    permission_classes = [IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(admin=self.request.user)

# Signalni ko'rish (foydalanuvchilar uchun)
class SignalListView(generics.ListAPIView):
    serializer_class = SignalSerializer
    permission_classes = [IsAuthenticated]
    queryset = Signal.objects.all().order_by('-created_at')

# Signalni yangilash va o'chirish (faqat adminlar)
class SignalDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SignalSerializer
    permission_classes = [IsAdminUser]
    queryset = Signal.objects.all()

    def perform_update(self, serializer):
        serializer.save(updated_at=now())

class SignalViewSet(viewsets.ModelViewSet):
    queryset = Signal.objects.all().order_by('-created_at')
    serializer_class = SignalSerializer
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SignalCreateSerializer
        return SignalSerializer
    
    @action(detail=False, methods=['get'], url_path='latest')
    def latest_signals(self, request):
        """So'nggi signallarni olish"""
        signals = Signal.objects.filter(is_posted=True).order_by('-created_at')[:10]
        serializer = self.get_serializer(signals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending_signals(self, request):
        """Yuborilmagan signallarni olish"""
        signals = Signal.objects.filter(is_posted=False).order_by('-created_at')
        serializer = self.get_serializer(signals, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='send')
    def send_signal(self, request, pk=None):
        """Signalni Telegram kanalga yuborish"""
        try:
            signal = self.get_object()
            
            if signal.is_posted:
                return Response({
                    'status': 'error',
                    'message': 'Bu signal allaqachon yuborilgan'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Signalni yuborish
            async def send_signal():
                return await signal.send_to_telegram()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(send_signal())
            loop.close()
            
            if success:
                signal.is_posted = True
                signal.save(update_fields=['is_posted'])
                
                return Response({
                    'status': 'success',
                    'message': 'Signal muvaffaqiyatli yuborildi',
                    'signal': self.get_serializer(signal).data
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Signalni yuborishda xatolik yuz berdi'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
