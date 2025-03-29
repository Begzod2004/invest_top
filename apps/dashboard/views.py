from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import transaction
import asyncio
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
from apps.users.models import User
from .models import BroadcastMessage
from .serializers import BroadcastMessageSerializer, UserVerifySerializer, UserSerializer, SignalSerializer, SubscriptionSerializer, PaymentSerializer, ReviewSerializer, InstrumentSerializer, UserStatsSerializer, PaymentStatsSerializer, SubscriptionStatsSerializer
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from .filters import (UserFilter, SignalFilter, SubscriptionFilter, 
                     PaymentFilter, ReviewFilter, InstrumentFilter)
from apps.signals.models import Signal
from apps.subscriptions.models import Subscription
from apps.payments.models import Payment
from apps.reviews.models import Review
from apps.instruments.models import Instrument
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from apps.invest_bot.bot import broadcast_message
import logging
from django.utils import timezone
from django.db.models import Count, Sum
from datetime import timedelta
from django.db import models

logger = logging.getLogger(__name__)

# Create your views here.

@extend_schema(tags=['broadcast'])
class BroadcastViewSet(viewsets.ViewSet):
    """Foydalanuvchilarga xabar yuborish uchun API"""
    permission_classes = [IsAdminUser]
    serializer_class = BroadcastMessageSerializer

    @action(detail=False, methods=['post'])
    async def send(self, request):
        """Foydalanuvchilarga ommaviy xabar yuborish"""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            user_ids = serializer.validated_data.get('user_ids', [])
            
            if not user_ids:
                users = User.objects.filter(telegram_user_id__isnull=False)
                user_ids = [user.telegram_user_id for user in users]
            
            try:
                stats = await broadcast_message(user_ids, message)
                return Response({
                    'status': 'success',
                    'message': 'Xabar yuborish yakunlandi',
                    'stats': stats
                })
            except Exception as e:
                logger.error(f"Broadcast error: {str(e)}")
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=['auth'])
class VerifyUserView(APIView):
    """Foydalanuvchi autentifikatsiyasini tekshirish"""
    permission_classes = [IsAuthenticated]
    serializer_class = UserVerifySerializer
    
    def get(self, request):
        serializer = self.serializer_class(request.user)
        return Response(serializer.data)

@extend_schema(tags=['users'])
class UserViewSet(viewsets.ModelViewSet):
    """
    Foydalanuvchilar bilan ishlash uchun API
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = UserFilter
    search_fields = ['username', 'first_name', 'last_name', 'phone_number', 'telegram_user_id']
    ordering_fields = ['date_joined', 'username', 'first_name', 'last_name', 'balance']
    ordering = ['-date_joined']

    def get_queryset(self):
        """Foydalanuvchilar ro'yxatini olish"""
        queryset = User.objects.all()
        
        # Faqat telegram foydalanuvchilarini olish
        telegram_only = self.request.query_params.get('telegram_only', False)
        if telegram_only and telegram_only.lower() == 'true':
            queryset = queryset.filter(telegram_user_id__isnull=False)
            
        # Faol foydalanuvchilarni olish
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)

        # Admin foydalanuvchilarni olish
        is_admin = self.request.query_params.get('is_admin')
        if is_admin is not None:
            is_admin = is_admin.lower() == 'true'
            queryset = queryset.filter(is_admin=is_admin)
            
        return queryset

    @extend_schema(
        summary="Foydalanuvchilar ro'yxati",
        description="Barcha foydalanuvchilarni ko'rish. Telegram foydalanuvchilarini ko'rish uchun ?telegram_only=true parametrini qo'shing",
        parameters=[
            OpenApiParameter(name='telegram_only', type=bool, description='Faqat Telegram foydalanuvchilarini ko\'rish'),
            OpenApiParameter(name='is_active', type=bool, description='Faol foydalanuvchilarni ko\'rish'),
            OpenApiParameter(name='is_admin', type=bool, description='Admin foydalanuvchilarni ko\'rish')
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

@extend_schema(tags=['signals'])
class SignalViewSet(viewsets.ModelViewSet):
    """
    Signallar bilan ishlash uchun API
    """
    queryset = Signal.objects.all()
    serializer_class = SignalSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SignalFilter
    search_fields = ['instrument__name', 'description']
    ordering_fields = ['created_at', 'entry_price', 'take_profit', 'stop_loss']
    ordering = ['-created_at']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='signal_type', type=str, description='Signal turi (BUY/SELL)'),
            OpenApiParameter(name='entry_price_min', type=float, description='Minimal kirish narxi'),
            OpenApiParameter(name='entry_price_max', type=float, description='Maksimal kirish narxi'),
            OpenApiParameter(name='is_active', type=bool, description='Faol signallar'),
            OpenApiParameter(name='search', type=str, description='Qidirish'),
            OpenApiParameter(name='ordering', type=str, description='Tartiblash (-created_at, entry_price)'),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

@extend_schema(tags=['subscriptions'])
class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    Obunalar bilan ishlash uchun API
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = SubscriptionFilter
    search_fields = ['user__username', 'plan__name']
    ordering_fields = ['start_date', 'end_date', 'created_at']
    ordering = ['-created_at']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='is_active', type=bool, description='Faol obunalar'),
            OpenApiParameter(name='start_date', type=str, description='Boshlanish sanasi'),
            OpenApiParameter(name='end_date', type=str, description='Tugash sanasi'),
            OpenApiParameter(name='search', type=str, description='Qidirish'),
            OpenApiParameter(name='ordering', type=str, description='Tartiblash (-created_at, start_date)'),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

@extend_schema(tags=['payments'])
class PaymentViewSet(viewsets.ModelViewSet):
    """
    To'lovlar bilan ishlash uchun API
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = PaymentFilter
    search_fields = ['user__username', 'subscription_plan__name']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='status', type=str, description='To\'lov holati'),
            OpenApiParameter(name='payment_type', type=str, description='To\'lov turi'),
            OpenApiParameter(name='amount_min', type=float, description='Minimal summa'),
            OpenApiParameter(name='amount_max', type=float, description='Maksimal summa'),
            OpenApiParameter(name='search', type=str, description='Qidirish'),
            OpenApiParameter(name='ordering', type=str, description='Tartiblash (-created_at, amount)'),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

@extend_schema(tags=['reviews'])
class ReviewViewSet(viewsets.ModelViewSet):
    """
    Sharhlar bilan ishlash uchun API
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ReviewFilter
    search_fields = ['user__username', 'comment']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='rating', type=int, description='Reyting bo\'yicha filtrlash'),
            OpenApiParameter(name='is_approved', type=bool, description='Tasdiqlangan sharhlar'),
            OpenApiParameter(name='comment', type=str, description='Izoh bo\'yicha qidirish'),
            OpenApiParameter(name='search', type=str, description='Qidirish'),
            OpenApiParameter(name='ordering', type=str, description='Tartiblash (-created_at, rating)'),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

@extend_schema(tags=['instruments'])
class InstrumentViewSet(viewsets.ModelViewSet):
    """
    Instrumentlar bilan ishlash uchun API
    """
    queryset = Instrument.objects.all()
    serializer_class = InstrumentSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InstrumentFilter
    search_fields = ['name', 'symbol', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @extend_schema(
        parameters=[
            OpenApiParameter(name='name', type=str, description='Nom bo\'yicha filtrlash'),
            OpenApiParameter(name='symbol', type=str, description='Symbol bo\'yicha filtrlash'),
            OpenApiParameter(name='is_active', type=bool, description='Faol instrumentlar'),
            OpenApiParameter(name='search', type=str, description='Qidirish'),
            OpenApiParameter(name='ordering', type=str, description='Tartiblash (name, -created_at)'),
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

@extend_schema(tags=['stats'])
class UserStatsViewSet(viewsets.ViewSet):
    """Foydalanuvchilar statistikasi"""
    permission_classes = [IsAdminUser]
    serializer_class = UserStatsSerializer

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Umumiy statistika"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        telegram_users = User.objects.filter(telegram_user_id__isnull=False).count()
            
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'telegram_users': telegram_users
        })

    @action(detail=False, methods=['get'])
    def growth(self, request):
        """O'sish statistikasi"""
        days = int(request.query_params.get('days', 7))
        data = []
        
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            count = User.objects.filter(date_joined__date=date).count()
            data.append({
                'date': date,
                'new_users': count
            })
            
        return Response(data)

@extend_schema(tags=['stats'])
class PaymentStatsViewSet(viewsets.ViewSet):
    """To'lovlar statistikasi"""
    permission_classes = [IsAdminUser]
    serializer_class = PaymentStatsSerializer

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Umumiy statistika"""
        total_payments = Payment.objects.count()
        successful_payments = Payment.objects.filter(status='completed').count()
        total_amount = Payment.objects.filter(status='completed').aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        return Response({
            'total_payments': total_payments,
            'successful_payments': successful_payments,
            'total_amount': total_amount
        })

    @action(detail=False, methods=['get'])
    def daily(self, request):
        """Kunlik statistika"""
        days = int(request.query_params.get('days', 7))
        data = []
        
        for i in range(days):
            date = timezone.now().date() - timedelta(days=i)
            payments = Payment.objects.filter(created_at__date=date)
            
            data.append({
                'date': date,
                'count': payments.count(),
                'amount': payments.filter(status='completed').aggregate(
                    total=Sum('amount')
                )['total'] or 0
            })
            
        return Response(data)

@extend_schema(tags=['stats'])
class SubscriptionStatsViewSet(viewsets.ViewSet):
    """Obunalar statistikasi"""
    permission_classes = [IsAdminUser]
    serializer_class = SubscriptionStatsSerializer

    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Umumiy statistika"""
        total_subs = Subscription.objects.count()
        active_subs = Subscription.objects.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).count()
        
        return Response({
            'total_subscriptions': total_subs,
            'active_subscriptions': active_subs
        })

    @action(detail=False, methods=['get'])
    def by_plan(self, request):
        """Tarif rejalar bo'yicha statistika"""
        subscriptions = Subscription.objects.values(
            'plan__name'
        ).annotate(
            total=Count('id'),
            active=Count('id', filter=models.Q(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ))
        )
        
        return Response(subscriptions)
