from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Payment
from .serializers import PaymentSerializer
from subscriptions.models import Subscription
from django.utils.timezone import now
from django.db import transaction
import asyncio
from invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot

class PaymentViewSet(viewsets.ModelViewSet):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAdminUser]
    
    @action(detail=True, methods=['patch'], url_path='approve')
    def approve_payment(self, request, pk=None):
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
    
    @action(detail=True, methods=['patch'], url_path='reject')
    def reject_payment(self, request, pk=None):
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
    
    @action(detail=False, methods=['get'], url_path='pending')
    def pending_payments(self, request):
        """Kutilayotgan to'lovlarni olish"""
        payments = Payment.objects.filter(status='pending_approval')
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='approved')
    def approved_payments(self, request):
        """Tasdiqlangan to'lovlarni olish"""
        payments = Payment.objects.filter(status='approved')
        serializer = self.get_serializer(payments, many=True)
        return Response(serializer.data)
    
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
@permission_classes([IsAdminUser])
def approve_payment_api(request, payment_id):
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment_id)
            
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
    except Payment.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'To\'lov topilmadi'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAdminUser])
def reject_payment_api(request, payment_id):
    try:
        with transaction.atomic():
            payment = Payment.objects.select_for_update().get(id=payment_id)
            
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
    except Payment.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'To\'lov topilmadi'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_payments_api(request):
    """Kutilayotgan to'lovlarni olish"""
    payments = Payment.objects.filter(status='pending_approval')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def approved_payments_api(request):
    """Tasdiqlangan to'lovlarni olish"""
    payments = Payment.objects.filter(status='approved')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def declined_payments_api(request):
    """Rad etilgan to'lovlarni olish"""
    payments = Payment.objects.filter(status='declined')
    serializer = PaymentSerializer(payments, many=True)
    return Response(serializer.data) 