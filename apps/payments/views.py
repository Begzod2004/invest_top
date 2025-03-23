from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Payment
from .serializers import PaymentSerializer, PaymentStatusSerializer
from apps.subscriptions.models import Subscription
from django.utils.timezone import now
from django.db import transaction
import asyncio
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
from apps.users.permissions import (
    CanViewPayments,
    CanApprovePayments,
    CanRejectPayments
)
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(
        tags=['payments'],
        summary="To'lovlar ro'yxati",
        description="Barcha to'lovlarni ko'rish"
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
        tags=['payments-admin'],
        summary="To'lovni yangilash",
        description="To'lov ma'lumotlarini yangilash (Admin)"
    ),
    destroy=extend_schema(
        tags=['payments-admin'],
        summary="To'lovni o'chirish",
        description="To'lovni o'chirish (Admin)"
    )
)
class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    
    def get_permissions(self):
        """
        Har bir action uchun kerakli permissionlarni qaytarish
        """
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [IsAuthenticated, CanViewPayments]
        elif self.action == 'approve_payment':
            permission_classes = [IsAuthenticated, CanApprovePayments]
        elif self.action == 'reject_payment':
            permission_classes = [IsAuthenticated, CanRejectPayments]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        tags=['payments-admin'],
        summary="To'lovni tasdiqlash",
        description="To'lovni tasdiqlash (Admin)"
    )
    @action(detail=True, methods=['patch'])
    def approve(self, request, pk=None):
        """To'lovni tasdiqlash"""
        try:
            with transaction.atomic():
                payment = self.get_object()
                
                # To'lov holatini tekshirish
                if payment.status != 'pending_approval':
                    return Response({
                        'status': 'error',
                        'message': 'Bu to\'lov allaqachon tasdiqlangan yoki rad etilgan'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
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
                
                return Response({
                    'status': 'success',
                    'message': 'To\'lov muvaffaqiyatli tasdiqlandi',
                    'payment': PaymentSerializer(payment).data
                })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @extend_schema(
        tags=['payments-admin'],
        summary="To'lovni rad etish",
        description="To'lovni rad etish (Admin)"
    )
    @action(detail=True, methods=['patch'])
    def reject(self, request, pk=None):
        """To'lovni rad etish"""
        try:
            with transaction.atomic():
                payment = self.get_object()
                
                # To'lov holatini tekshirish
                if payment.status != 'pending_approval':
                    return Response({
                        'status': 'error',
                        'message': 'Bu to\'lov allaqachon tasdiqlangan yoki rad etilgan'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
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
                
                return Response({
                    'status': 'success',
                    'message': 'To\'lov muvaffaqiyatli rad etildi',
                    'payment': PaymentSerializer(payment).data
                })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
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