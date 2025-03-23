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
from .serializers import BroadcastMessageSerializer, UserVerifySerializer, UserSerializer, SignalSerializer, SubscriptionSerializer, PaymentSerializer, ReviewSerializer, InstrumentSerializer
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

# Create your views here.

@extend_schema(tags=['broadcast'])
class BroadcastViewSet(viewsets.ModelViewSet):
    """
    Xabarlarni yuborish uchun API
    """
    queryset = BroadcastMessage.objects.all()
    serializer_class = BroadcastMessageSerializer
    permission_classes = [IsAdminUser]
    
    def perform_create(self, serializer):
        serializer.save(sent_by=self.request.user)
    
    @action(detail=False, methods=['post'], url_path='send')
    def send_broadcast(self, request):
        """Xabar yuborish"""
        try:
            recipient_type = request.data.get('recipient_type')
            message = request.data.get('message')
            
            if not message:
                return Response({
                    'status': 'error',
                    'message': 'Xabar matni kiritilmagan'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Foydalanuvchilarni olish
            if recipient_type == 'all':
                users = User.objects.all()
            elif recipient_type == 'subscribed':
                users = User.objects.filter(is_subscribed=True)
            elif recipient_type == 'active':
                users = User.objects.filter(is_blocked=False)
            else:
                return Response({
                    'status': 'error',
                    'message': 'Noto\'g\'ri recipient_type'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Xabarni saqlash
            broadcast = BroadcastMessage.objects.create(
                message=message,
                recipient_type=recipient_type,
                sent_by=request.user
            )
            
            # Xabarni yuborish
            async def send_messages():
                bot = Bot(token=BOT_TOKEN)
                success_count = 0
                error_count = 0
                
                for user in users:
                    try:
                        await bot.send_message(
                            chat_id=int(user.telegram_user_id),
                            text=message
                        )
                        success_count += 1
                    except Exception as e:
                        error_count += 1
                
                await bot.session.close()
                return success_count, error_count
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success_count, error_count = loop.run_until_complete(send_messages())
            loop.close()
            
            # Natijalarni saqlash
            broadcast.success_count = success_count
            broadcast.error_count = error_count
            broadcast.save()
            
            return Response({
                'status': 'success',
                'message': f'Xabar yuborildi: {success_count} ta muvaffaqiyatli, {error_count} ta xatolik',
                'broadcast': BroadcastMessageSerializer(broadcast).data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='user_id',
                type=int,
                location=OpenApiParameter.PATH,
                description='Foydalanuvchi ID si'
            ),
        ]
    )
    @action(detail=False, methods=['post'], url_path='send-to-user/(?P<user_id>[^/.]+)')
    def send_to_user(self, request, user_id=None):
        """Bitta foydalanuvchiga xabar yuborish"""
        try:
            message = request.data.get('message')
            
            if not message:
                return Response({
                    'status': 'error',
                    'message': 'Xabar matni kiritilmagan'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Foydalanuvchini olish
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Foydalanuvchi topilmadi'
                }, status=status.HTTP_404_NOT_FOUND)
            
            # Xabarni yuborish
            async def send_message():
                bot = Bot(token=BOT_TOKEN)
                try:
                    await bot.send_message(
                        chat_id=int(user.telegram_user_id),
                        text=message
                    )
                    success = True
                except Exception as e:
                    success = False
                
                await bot.session.close()
                return success
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(send_message())
            loop.close()
            
            if success:
                return Response({
                    'status': 'success',
                    'message': f'Xabar {user.first_name} ga muvaffaqiyatli yuborildi'
                })
            else:
                return Response({
                    'status': 'error',
                    'message': f'Xabarni {user.first_name} ga yuborishda xatolik yuz berdi'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='send-all')
    def send_to_all(self, request):
        """Barcha foydalanuvchilarga xabar yuborish"""
        request.data['recipient_type'] = 'all'
        return self.send_broadcast(request)
    
    @action(detail=False, methods=['post'], url_path='send-active')
    def send_to_active(self, request):
        """Faol foydalanuvchilarga xabar yuborish"""
        request.data['recipient_type'] = 'active'
        return self.send_broadcast(request)
    
    @action(detail=False, methods=['post'], url_path='send-subscribed')
    def send_to_subscribed(self, request):
        """Obuna bo'lgan foydalanuvchilarga xabar yuborish"""
        request.data['recipient_type'] = 'subscribed'
        return self.send_broadcast(request)

@extend_schema(
    tags=['auth'],
    responses={200: UserVerifySerializer}
)
class VerifyUserView(APIView):
    """
    Foydalanuvchi autentifikatsiyasini tekshirish
    """
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

    @extend_schema(
        parameters=[
            OpenApiParameter(name='username', type=str, description='Username bo\'yicha filtrlash'),
            OpenApiParameter(name='is_active', type=bool, description='Faol foydalanuvchilar'),
            OpenApiParameter(name='is_admin', type=bool, description='Admin foydalanuvchilar'),
            OpenApiParameter(name='balance_min', type=float, description='Minimal balans'),
            OpenApiParameter(name='balance_max', type=float, description='Maksimal balans'),
            OpenApiParameter(name='search', type=str, description='Qidirish'),
            OpenApiParameter(name='ordering', type=str, description='Tartiblash (-date_joined, username)'),
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
