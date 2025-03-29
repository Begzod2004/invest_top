from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from .models import Payment
from .serializers import PaymentSerializer, PaymentStatusSerializer
from apps.subscriptions.models import Subscription
from django.utils.timezone import now, timedelta
from django.db import transaction
import asyncio
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
from apps.users.permissions import (
    CanViewPayments,
    CanApprovePayments,
    CanRejectPayments,
    PaymentPermission,
    IsAdmin
)
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.urls import reverse
from asgiref.sync import sync_to_async
from apps.invest_bot.bot import send_message_to_user
from ..users.models import User
from django.conf import settings

@extend_schema_view(
    list=extend_schema(
        tags=['payments'],
        summary="To'lovlar ro'yxati",
        description="Barcha to'lovlarni ko'rish (admin uchun to'liq, user uchun o'ziniki)"
    ),
    create=extend_schema(
        tags=['payments'],
        summary="To'lov yaratish",
        description="Yangi to'lov qo'shish"
    ),
    retrieve=extend_schema(
        tags=['payments'],
        summary="To'lov ma'lumotlari",
        description="To'lov haqida to'liq ma'lumot"
    ),
    update=extend_schema(
        tags=['payments'],
        summary="To'lovni yangilash",
        description="To'lov ma'lumotlarini yangilash (Admin yoki o'zi pending holatda)"
    ),
    destroy=extend_schema(
        tags=['payments'],
        summary="To'lovni o'chirish",
        description="To'lovni o'chirish (Admin yoki o'zi pending holatda)"
    )
)
class PaymentViewSet(viewsets.ModelViewSet):
    """To'lovlar bilan ishlash uchun API"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [PaymentPermission]
    
    def get_queryset(self):
        """User o'zining to'lovlarini ko'rishi, admin hammani ko'rishi"""
        user = self.request.user
        if user.is_admin or user.has_permission('can_view_payments'):
            return Payment.objects.all()
        return Payment.objects.filter(user=user)
        
    def perform_create(self, serializer):
        """Yangi to'lov yaratish"""
        serializer.save(user=self.request.user)
    
    def get_permissions(self):
        """
        Har bir action uchun kerakli permissionlarni qaytarish
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [IsAuthenticated, CanViewPayments]
        elif self.action == 'approve':
            permission_classes = [IsAuthenticated, CanApprovePayments]
        elif self.action == 'reject':
            permission_classes = [IsAuthenticated, CanRejectPayments]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    async def send_bot_message(self, user_id: int, message: str):
        """Send message via Telegram bot"""
        bot = Bot(token=settings.BOT_TOKEN)
        try:
            await bot.send_message(chat_id=user_id, text=message)
        finally:
            await bot.session.close()

    @extend_schema(
        request=PaymentStatusSerializer,
        responses={200: PaymentStatusSerializer},
        description='Approve a pending payment',
        summary='Approve payment'
    )
    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        payment = self.get_object()
        if payment.status != 'PENDING':
            return Response(
                {'detail': 'Only pending payments can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PaymentStatusSerializer(data={'status': 'COMPLETED'})
        serializer.is_valid(raise_exception=True)
        
        payment.status = 'COMPLETED'
        payment.save()
        
        # Generate temporary token
        temp_token = payment.user.get_temp_token()
        
        # Send confirmation message via bot
        message = (
            f"✅ Dear {payment.user.first_name},\n\n"
            f"Your payment has been approved!\n"
            f"Amount: {payment.amount}\n"
            f"Payment method: {payment.get_payment_type_display()}\n\n"
            f"Your subscription has been activated. You can now access all features!\n\n"
            f"Click here to access your subscription (valid for 24 hours):\n"
            f"{settings.WEB_APP_URL}/activate?token={temp_token}"
        )
        
        # Run bot message sending in async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            self.send_bot_message(int(payment.user.telegram_user_id), message)
        )
        loop.close()
        
        return Response(serializer.data)

    @extend_schema(
        request=PaymentStatusSerializer,
        responses={200: PaymentStatusSerializer},
        description='Reject a pending payment',
        summary='Reject payment'
    )
    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        payment = self.get_object()
        if payment.status != 'PENDING':
            return Response(
                {'detail': 'Only pending payments can be rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PaymentStatusSerializer(data={'status': 'FAILED'})
        serializer.is_valid(raise_exception=True)
        
        payment.status = 'FAILED'
        payment.save()
        
        # Send rejection message via bot
        message = (
            f"❌ Dear {payment.user.first_name},\n\n"
            f"Your payment has been rejected.\n"
            f"Amount: {payment.amount}\n"
            f"Payment method: {payment.get_payment_type_display()}\n\n"
            f"Please contact support for more information."
        )
        
        # Run bot message sending in async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            self.send_bot_message(int(payment.user.telegram_user_id), message)
        )
        loop.close()
        
        return Response(serializer.data)
    
    @extend_schema(
        tags=['payments'],
        summary="Kutilayotgan to'lovlar",
        description="Tasdiqlash kutilayotgan to'lovlar ro'yxati"
    )
    @action(detail=False, methods=['get'], url_path='pending')
    def pending_payments(self, request):
        """Kutilayotgan to'lovlarni olish"""
        payments = Payment.objects.filter(status='pending_approval')
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['payments'],
        summary="Tasdiqlangan to'lovlar",
        description="Tasdiqlangan to'lovlar ro'yxati"
    )
    @action(detail=False, methods=['get'], url_path='approved')
    def approved_payments(self, request):
        """Tasdiqlangan to'lovlarni olish"""
        payments = Payment.objects.filter(status='approved')
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['payments'],
        summary="Rad etilgan to'lovlar",
        description="Rad etilgan to'lovlar ro'yxati"
    )
    @action(detail=False, methods=['get'], url_path='declined')
    def declined_payments(self, request):
        """Rad etilgan to'lovlarni olish"""
        payments = Payment.objects.filter(status='declined')
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)

@require_POST
@login_required
def approve_payment(request, payment_id):
    try:
        with transaction.atomic():
            # To'lovni olish
            payment = Payment.objects.select_for_update().get(id=payment_id)
            
            # To'lov holatini tekshirish
            if payment.status != 'pending_approval':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Bu to\'lov allaqachon tasdiqlangan yoki rad etilgan'
                }, status=400)
            
            # To'lovni tasdiqlash
            payment.approve()
            
            # Foydalanuvchini obunachi qilish
            user = payment.user
            user.is_subscribed = True
            user.save()
            
            # Telegram xabarini yuborish
            async def send_message():
                bot = Bot(token=BOT_TOKEN)
                text = (
                    f"✅ Hurmatli {payment.user.first_name},\n\n"
                    f"Sizning to'lovingiz tasdiqlandi!\n"
                    f"To'lov miqdori: {payment.amount} so'm\n"
                    f"To'lov usuli: {payment.get_payment_method_display()}\n\n"
                    f"Obunangiz faollashtirildi. Endi siz barcha imkoniyatlardan foydalanishingiz mumkin!"
                )
                
                await bot.send_message(
                    chat_id=int(payment.user.telegram_user_id),
                    text=text
                )
                await bot.session.close()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_message())
            loop.close()
            
            return JsonResponse({
                'status': 'success',
                'message': 'To\'lov muvaffaqiyatli tasdiqlandi'
            })
            
    except Payment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'To\'lov topilmadi'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@require_POST
@login_required
def reject_payment(request, payment_id):
    try:
        with transaction.atomic():
            # To'lovni olish
            payment = Payment.objects.select_for_update().get(id=payment_id)
            
            # To'lov holatini tekshirish
            if payment.status != 'pending_approval':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Bu to\'lov allaqachon tasdiqlangan yoki rad etilgan'
                }, status=400)
            
            # To'lovni rad etish
            payment.reject()
            
            # Telegram xabarini yuborish
            async def send_message():
                bot = Bot(token=BOT_TOKEN)
                text = (
                    f"❌ Hurmatli {payment.user.first_name},\n\n"
                    f"Sizning to'lovingiz rad etildi.\n"
                    f"To'lov miqdori: {payment.amount} so'm\n"
                    f"To'lov usuli: {payment.get_payment_method_display()}\n\n"
                    f"Iltimos, to'lov ma'lumotlarini tekshirib, qayta urinib ko'ring."
                )
                
                await bot.send_message(
                    chat_id=int(payment.user.telegram_user_id),
                    text=text
                )
                await bot.session.close()
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_message())
            loop.close()
            
            return JsonResponse({
                'status': 'success',
                'message': 'To\'lov muvaffaqiyatli rad etildi'
            })
            
    except Payment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'To\'lov topilmadi'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def pending_payments_api(request):
    """Kutilayotgan to'lovlarni olish"""
    payments = Payment.objects.filter(status='pending_approval')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approved_payments_api(request):
    """Tasdiqlangan to'lovlarni olish"""
    payments = Payment.objects.filter(status='approved')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def declined_payments_api(request):
    """Rad etilgan to'lovlarni olish"""
    payments = Payment.objects.filter(status='declined')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@extend_schema(
    request=PaymentStatusSerializer,
    responses={200: PaymentStatusSerializer}
)
@api_view(['POST'])
def update_payment_status(request):
    serializer = PaymentStatusSerializer(data=request.data)
    if serializer.is_valid():
        payment = get_object_or_404(Payment, id=serializer.data['payment_id'])
        status = serializer.data['status']
        
        if status not in ['COMPLETED', 'REJECTED']:
            return Response({
                'success': False,
                'message': 'Noto\'g\'ri status'
            }, status=400)
        
        payment.status = status
        payment.save()
        
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def redirect_to_payment_list(request):
    return HttpResponseRedirect(reverse('payment-list')) 