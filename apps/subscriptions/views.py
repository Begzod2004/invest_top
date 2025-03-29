from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import transaction
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
import asyncio
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
from apps.users.models import User
from .models import Subscription, SubscriptionPlan
from .serializers import SubscriptionSerializer, SubscriptionPlanSerializer
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from apps.users.permissions import SubscriptionPermission
import logging

logger = logging.getLogger(__name__)

class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Foydalanuvchining obuna statusini olish"""
        user = request.user
        subscriptions = Subscription.objects.filter(
            user=user, 
            is_active=True, 
            end_date__gt=timezone.now()
        ).order_by('-end_date')
        
        if not subscriptions.exists():
            return Response({
                "active": False,
                "message": "Sizda aktiv obuna yo'q. Iltimos, obuna bo'ling."
            })
        
        subscription = subscriptions.first()
        days_left = (subscription.end_date - timezone.now()).days
        
        serializer = SubscriptionSerializer(subscription)
        
        return Response({
            "active": True,
            "subscription": serializer.data,
            "days_left": days_left,
            "message": f"Obunangiz {days_left} kundan so'ng tugaydi."
        })

class PaymentCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """To'lov ma'lumotlarini yaratish"""
        plan_id = request.data.get('plan_id')
        payment_method = request.data.get('payment_method')
        
        if not plan_id:
            return Response({"error": "Plan ID talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not payment_method:
            return Response({"error": "To'lov usuli talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)
            
            # Yangi obuna yaratish
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                status='pending',
                is_active=False,
                amount_paid=plan.price,
                payment_method=payment_method
            )
            
            return Response({
                "success": True,
                "subscription_id": subscription.id,
                "message": "To'lov ma'lumotlari saqlandi. Endi skrinshotni yuklang."
            })
            
        except SubscriptionPlan.DoesNotExist:
            return Response({"error": "Berilgan ID bo'yicha obuna rejasi topilmadi"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"To'lov yaratishda xatolik: {e}")
            return Response({"error": "Server xatoligi"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentUploadScreenshotView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """To'lov skrinshoti yuklash"""
        subscription_id = request.data.get('subscription_id')
        screenshot = request.FILES.get('screenshot')
        
        if not subscription_id:
            return Response({"error": "Obuna ID si talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not screenshot:
            return Response({"error": "Screenshot talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            subscription = Subscription.objects.get(id=subscription_id, user=request.user)
            subscription.payment_screenshot = screenshot
            subscription.status = 'waiting_admin'  # Admin tasdiqlashi kerak
            subscription.payment_date = timezone.now()
            subscription.save()
            
            return Response({
                "success": True,
                "message": "Screenshot muvaffaqiyatli yuklandi. Administrator tasdiqlashini kutamiz."
            })
            
        except Subscription.DoesNotExist:
            return Response({"error": "Berilgan ID bo'yicha obuna topilmadi"}, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Screenshot yuklashda xatolik: {e}")
            return Response({"error": "Server xatoligi"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Faqat o'z subscriptionlarini ko'rsin
        if self.request.user.is_staff or self.request.user.is_superuser:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        """Foydalanuvchining barcha obunalarini olish"""
        subscriptions = Subscription.objects.filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='active')
    def active_subscriptions(self, request):
        """Foydalanuvchining aktiv obunalarini olish"""
        subscriptions = Subscription.objects.filter(
            user=request.user, 
            is_active=True,
            end_date__gt=timezone.now()
        ).order_by('-end_date')
        
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='expired')
    def expired_subscriptions(self, request):
        """Foydalanuvchining tugagan obunalarini olish"""
        subscriptions = Subscription.objects.filter(
            user=request.user, 
            end_date__lt=timezone.now()
        ).order_by('-end_date')
        
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def user_subscriptions(self, request, user_id=None):
        """Berilgan foydalanuvchining obunalarini olish (faqat admin uchun)"""
        if not request.user.is_staff and not request.user.has_perm('subscriptions.view_subscription'):
            return Response({"error": "Sizda bunday ma'lumotlarni ko'rish huquqi yo'q"}, status=status.HTTP_403_FORBIDDEN)
        
        subscriptions = Subscription.objects.filter(user_id=user_id).order_by('-created_at')
        
        if not subscriptions.exists():
            return Response({"message": "Bu foydalanuvchida obuna yo'q"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='activate')
    def activate_subscription(self, request, pk=None):
        """Obunani faollashtirish (admin uchun)"""
        if not request.user.is_staff and not request.user.has_perm('subscriptions.change_subscription'):
            return Response({"error": "Sizda bunday amallarni bajarish huquqi yo'q"}, status=status.HTTP_403_FORBIDDEN)
        
        subscription = self.get_object()
        
        if subscription.status != 'waiting_admin':
            return Response({"error": "Faqat kutilayotgan obunalarni tasdiqlash mumkin"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Obunani faollashtirish
        success = subscription.activate()
        
        if not success:
            return Response({"error": "Obunani faollashtirishda xatolik yuz berdi"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Foydalanuvchiga xabar yuborish
        if subscription.user.telegram_user_id:
            try:
                async def send_message():
                    bot = Bot(token=BOT_TOKEN)
                    try:
                        # Foydalanuvchiga xabar yuborish
                        message_text = (
                            f"✅ Obunangiz muvaffaqiyatli faollashtirildi!\n\n"
                            f"📊 Tarif: {subscription.plan.name}\n"
                            f"⏳ Tugash muddati: {subscription.end_date.strftime('%d.%m.%Y')}\n"
                            f"🔄 Davomiyligi: {subscription.plan.duration_days} kun\n\n"
                            f"Maxsus kanalga qo'shilish uchun quyidagi havoladan foydalaning:\n"
                            f"🔗 {subscription.generate_invite_link()}"
                        )
                        
                        await bot.send_message(
                            chat_id=subscription.user.telegram_user_id,
                            text=message_text
                        )
                        
                        logger.info(f"Foydalanuvchiga xabar muvaffaqiyatli yuborildi: {subscription.user.username}")
                        return True
                    
                    except Exception as e:
                        logger.error(f"Xabar yuborishda xatolik: {e}")
                        return False
                    
                    finally:
                        await bot.session.close()
                
                # Asinxron funksiyani bajarish
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_message())
                
            except Exception as e:
                logger.error(f"Telegram xabar yuborishda xatolik: {e}")
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate_subscription(self, request, pk=None):
        """Obunani deaktivatsiya qilish (admin uchun)"""
        if not request.user.is_staff and not request.user.has_perm('subscriptions.change_subscription'):
            return Response({"error": "Sizda bunday amallarni bajarish huquqi yo'q"}, status=status.HTTP_403_FORBIDDEN)
        
        subscription = self.get_object()
        
        # Obunani o'chirish
        subscription.cancel()
        
        # Foydalanuvchiga xabar yuborish (agar telegram_user_id bo'lsa)
        if subscription.user.telegram_user_id:
            try:
                async def send_message():
                    bot = Bot(token=BOT_TOKEN)
                    try:
                        # Foydalanuvchiga xabar yuborish
                        message_text = (
                            f"❌ Obunangiz to'xtatildi!\n\n"
                            f"📊 Tarif: {subscription.plan.name}\n"
                            f"⚠️ Sabablarni bilish uchun administratsiyaga murojaat qiling."
                        )
                        
                        await bot.send_message(
                            chat_id=subscription.user.telegram_user_id,
                            text=message_text
                        )
                        
                        logger.info(f"Foydalanuvchiga xabar muvaffaqiyatli yuborildi: {subscription.user.username}")
                        return True
                    
                    except Exception as e:
                        logger.error(f"Xabar yuborishda xatolik: {e}")
                        return False
                    
                    finally:
                        await bot.session.close()
                
                # Asinxron funksiyani bajarish
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_message())
                
            except Exception as e:
                logger.error(f"Telegram xabar yuborishda xatolik: {e}")
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='reject')
    def reject_subscription(self, request, pk=None):
        """To'lovni rad etish (admin uchun)"""
        if not request.user.is_staff and not request.user.has_perm('subscriptions.change_subscription'):
            return Response({"error": "Sizda bunday amallarni bajarish huquqi yo'q"}, status=status.HTTP_403_FORBIDDEN)
        
        subscription = self.get_object()
        
        if subscription.status != 'waiting_admin':
            return Response({"error": "Faqat kutilayotgan to'lovlarni rad etish mumkin"}, status=status.HTTP_400_BAD_REQUEST)
        
        # To'lovni rad etish
        subscription.reject()
        
        # Foydalanuvchiga xabar yuborish (agar telegram_user_id bo'lsa)
        if subscription.user.telegram_user_id:
            try:
                async def send_message():
                    bot = Bot(token=BOT_TOKEN)
                    try:
                        # Foydalanuvchiga xabar yuborish
                        message_text = (
                            f"❌ To'lovingiz rad etildi!\n\n"
                            f"📊 Tarif: {subscription.plan.name}\n"
                            f"💰 Summa: {subscription.amount_paid}\n"
                            f"⚠️ Iltimos, to'lov ma'lumotlarini tekshirib, qayta urinib ko'ring yoki administratsiyaga murojaat qiling."
                        )
                        
                        await bot.send_message(
                            chat_id=subscription.user.telegram_user_id,
                            text=message_text
                        )
                        
                        logger.info(f"Foydalanuvchiga xabar muvaffaqiyatli yuborildi: {subscription.user.username}")
                        return True
                    
                    except Exception as e:
                        logger.error(f"Xabar yuborishda xatolik: {e}")
                        return False
                    
                    finally:
                        await bot.session.close()
                
                # Asinxron funksiyani bajarish
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_message())
                
            except Exception as e:
                logger.error(f"Telegram xabar yuborishda xatolik: {e}")
        
        serializer = self.get_serializer(subscription)
        return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_subscription_status(request, user_id):
    """Foydalanuvchining obuna statusini olish"""
    # Admin yoki o'zi bo'lsa
    if not request.user.is_staff and str(request.user.id) != user_id:
        return Response({"error": "Sizda bu ma'lumotlarni ko'rish huquqi yo'q"}, status=status.HTTP_403_FORBIDDEN)
    
    user = get_object_or_404(get_user_model(), id=user_id)
    
    subscription = Subscription.objects.filter(
        user=user, 
        is_active=True,
        end_date__gt=timezone.now()
    ).order_by('-end_date').first()
    
    if not subscription:
        return Response({
            "is_active": False,
            "message": "Aktiv obuna yo'q"
        })
    
    days_left = (subscription.end_date - timezone.now()).days
    
    return Response({
        "is_active": True,
        "plan": subscription.plan.name,
        "end_date": subscription.end_date,
        "days_left": days_left,
        "message": f"Obuna {days_left} kundan so'ng tugaydi"
    })
