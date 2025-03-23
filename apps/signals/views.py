from rest_framework import viewsets, status, generics, parsers
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import transaction
from django.utils.timezone import now
import asyncio
from .models import Signal
from .serializers import SignalSerializer, SignalCreateSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

# Signal yaratish (faqat adminlar)
@extend_schema(tags=['signals'])
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

@extend_schema_view(
    list=extend_schema(
        tags=['signals'],
        summary="Signallar ro'yxatini olish",
        description="Barcha signallarni ko'rish uchun endpoint"
    ),
    create=extend_schema(
        tags=['signals-admin'],
        summary="Yangi signal yaratish",
        description="Admin uchun yangi signal yaratish endpointi"
    ),
    retrieve=extend_schema(
        tags=['signals'],
        summary="Signal ma'lumotlarini olish",
        description="Bitta signalni ID bo'yicha ko'rish"
    ),
    update=extend_schema(
        tags=['signals-admin'],
        summary="Signalni yangilash",
        description="Admin uchun signalni yangilash endpointi"
    ),
    destroy=extend_schema(
        tags=['signals-admin'],
        summary="Signalni o'chirish",
        description="Admin uchun signalni o'chirish endpointi"
    )
)
class SignalViewSet(viewsets.ModelViewSet):
    queryset = Signal.objects.all()
    permission_classes = [IsAuthenticated]
    parser_classes = (parsers.MultiPartParser, parsers.FormParser)
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SignalCreateSerializer
        return SignalSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def send_signal(self, request, pk=None):
        signal = self.get_object()
        if not signal.is_sent:
            # Signal yuborish logikasi
            signal.is_sent = True
            signal.save()
            return Response({'status': 'signal sent'})
        return Response({'status': 'signal already sent'}, 
                       status=status.HTTP_400_BAD_REQUEST)
