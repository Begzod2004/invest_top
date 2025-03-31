from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .serializers import (
    UserSerializer, UserVerifySerializer, BroadcastMessageSerializer,
    UserStatsSerializer, PaymentStatsSerializer, SubscriptionStatsSerializer,
    SignalSerializer, SignalStatsSerializer, SubscriptionSerializer,
    SubscriptionStatsSerializer, ReviewSerializer, ReviewStatsSerializer
)
from .models import BroadcastMessage
from .filters import (
    UserFilter, SignalFilter, SubscriptionFilter,
    ReviewFilter, InstrumentFilter
)

from apps.users.models import User
from apps.signals.models import Signal
from apps.subscriptions.models import Subscription, Payment
from apps.subscriptions.serializers import SubscriptionSerializer, PaymentSerializer
from apps.reviews.models import Review
from apps.instruments.models import Instrument
from apps.signals.serializers import SignalSerializer
from apps.reviews.serializers import ReviewSerializer
from apps.instruments.serializers import InstrumentSerializer

from apps.invest_bot.bot import send_message_to_user
from apps.users.permissions import (
    IsAdmin,
    CanViewUsers,
    CanViewSignals,
    CanViewSubscriptions,
    CanViewReviews,
    CanSendBroadcasts,
)

# Create your views here.

@extend_schema(tags=['broadcast'])
class BroadcastViewSet(viewsets.ViewSet):
    """Foydalanuvchilarga xabar yuborish uchun API"""
    permission_classes = [IsAuthenticated, CanSendBroadcasts]
    serializer_class = BroadcastMessageSerializer

    @action(detail=False, methods=['post'])
    def send_message(self, request):
        """Xabarni yuborish"""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            message = serializer.validated_data['message']
            users = serializer.validated_data.get('users', [])
            
            # Agar users bo'sh bo'lsa, barcha foydalanuvchilarga yuborish
            if not users:
                users = User.objects.filter(is_active=True)
            
            # Xabarni yuborish
            success_count = 0
            error_count = 0
            for user in users:
                try:
                    user.send_message(message)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"Xabar yuborishda xatolik: {str(e)}")

            # Broadcast xabarni saqlash
            BroadcastMessage.objects.create(
                message=message,
                recipient_type=recipient_type,
                sent_by=request.user,
                success_count=success_count,
                error_count=error_count
            )

            return Response({
                'status': 'success',
                'message': f'Xabar {success_count} ta foydalanuvchiga yuborildi. {error_count} ta xatolik.',
                'success_count': success_count,
                'error_count': error_count
            })
        
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
    permission_classes = [IsAuthenticated, CanViewUsers]
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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Foydalanuvchilar statistikasi"""
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        blocked_users = User.objects.filter(is_blocked=True).count()
        verified_users = User.objects.filter(is_verified=True).count()
        
        # Oxirgi 30 kun ichida qo'shilgan foydalanuvchilar
        last_month = timezone.now() - timezone.timedelta(days=30)
        new_users = User.objects.filter(created_at__gte=last_month).count()
        
        data = {
            'total_users': total_users,
            'active_users': active_users,
            'blocked_users': blocked_users,
            'verified_users': verified_users,
            'new_users': new_users,
        }
        
        serializer = UserStatsSerializer(data)
        return Response(serializer.data)

@extend_schema(tags=['signals'])
class SignalViewSet(viewsets.ModelViewSet):
    """
    Signallar bilan ishlash uchun API
    """
    queryset = Signal.objects.all()
    serializer_class = SignalSerializer
    permission_classes = [IsAuthenticated, CanViewSignals]
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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Signallar statistikasi"""
        total_signals = Signal.objects.count()
        active_signals = Signal.objects.filter(is_active=True).count()
        sent_signals = Signal.objects.filter(is_sent=True).count()
        
        # Oxirgi 30 kun ichida yaratilgan signallar
        last_month = timezone.now() - timezone.timedelta(days=30)
        new_signals = Signal.objects.filter(created_at__gte=last_month).count()
        
        # O'rtacha muvaffaqiyat darajasi
        avg_success_rate = Signal.objects.filter(
            success_rate__gt=0
        ).aggregate(avg_rate=Avg('success_rate'))['avg_rate'] or 0
        
        data = {
            'total_signals': total_signals,
            'active_signals': active_signals,
            'sent_signals': sent_signals,
            'new_signals': new_signals,
            'avg_success_rate': round(avg_success_rate, 2),
        }
        
        serializer = SignalStatsSerializer(data)
        return Response(serializer.data)

@extend_schema(tags=['subscriptions'])
class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    Obunalar bilan ishlash uchun API
    """
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated, CanViewSubscriptions]
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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obunalar statistikasi"""
        total_subscriptions = Subscription.objects.count()
        active_subscriptions = Subscription.objects.filter(is_active=True).count()
        
        # Oxirgi 30 kun ichida qo'shilgan obunalar
        last_month = timezone.now() - timezone.timedelta(days=30)
        new_subscriptions = Subscription.objects.filter(created_at__gte=last_month).count()
        
        data = {
            'total_subscriptions': total_subscriptions,
            'active_subscriptions': active_subscriptions,
            'new_subscriptions': new_subscriptions,
        }
        
        serializer = SubscriptionStatsSerializer(data)
        return Response(serializer.data)

@extend_schema(tags=['reviews'])
class ReviewViewSet(viewsets.ModelViewSet):
    """
    Sharhlar bilan ishlash uchun API
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated, CanViewReviews]
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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Sharhlar statistikasi"""
        total_reviews = Review.objects.count()
        approved_reviews = Review.objects.filter(is_approved=True).count()
        
        # Oxirgi 30 kun ichida qo'shilgan sharhlar
        last_month = timezone.now() - timezone.timedelta(days=30)
        new_reviews = Review.objects.filter(created_at__gte=last_month).count()
        
        # O'rtacha reyting
        avg_rating = Review.objects.filter(
            is_approved=True
        ).aggregate(avg_rate=Avg('rating'))['avg_rate'] or 0
        
        data = {
            'total_reviews': total_reviews,
            'approved_reviews': approved_reviews,
            'new_reviews': new_reviews,
            'avg_rating': round(avg_rating, 2),
        }
        
        serializer = ReviewStatsSerializer(data)
        return Response(serializer.data)

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
class PaymentStatsViewSet(viewsets.ViewSet):
    """To'lovlar statistikasi"""
    permission_classes = [IsAdminUser]
    serializer_class = PaymentStatsSerializer

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """To'lovlar statistikasi"""
        total_payments = Payment.objects.count()
        successful_payments = Payment.objects.filter(status='COMPLETED').count()
        total_amount = Payment.objects.filter(
            status='COMPLETED'
        ).aggregate(
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
    def stats(self, request):
        """Obunalar statistikasi"""
        total_subs = Subscription.objects.count()
        active_subs = Subscription.objects.filter(
            status='active'
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
            active=Count('id', filter=Q(
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now()
            ))
        )
        
        return Response(subscriptions)
