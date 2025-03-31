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
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apps.users.models import User
from .models import Subscription, SubscriptionPlan, Payment, PaymentMethod
from .serializers import (
    SubscriptionSerializer,
    SubscriptionPlanSerializer,
    SubscriptionCreateSerializer,
    PaymentSerializer,
    PaymentCreateSerializer,
    PaymentMethodSerializer
)
from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from apps.users.permissions import SubscriptionPermission
import logging
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.db.models.functions import TruncDate
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.views.decorators.http import require_POST
import time

logger = logging.getLogger(__name__)


class SubscriptionStatusView(APIView):
    """Obuna holatini tekshirish"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Foydalanuvchining eng oxirgi aktiv obunasini olish
            subscription = Subscription.objects.filter(
                user=request.user,
                status='active',
                is_active=True,
                end_date__gt=timezone.now()
            ).select_related('plan').first()
            
            if not subscription:
                return Response({
                    'is_subscribed': False,
                    'message': 'Aktiv obuna topilmadi'
                }, status=status.HTTP_200_OK)
            
            # Qolgan vaqtni hisoblash
            now = timezone.now()
            remaining_time = subscription.end_date - now
            remaining_days = remaining_time.days
            remaining_hours = remaining_time.seconds // 3600
            remaining_minutes = (remaining_time.seconds % 3600) // 60
            
            return Response({
                'is_subscribed': True,
                'subscription': {
                    'id': subscription.id,
                    'plan': {
                        'id': subscription.plan.id,
                        'name': subscription.plan.name,
                        'price': subscription.plan.price,
                        'duration_days': subscription.plan.duration_days
                    },
                    'status': subscription.status,
                    'start_date': subscription.start_date,
                    'end_date': subscription.end_date,
                    'remaining_time': {
                        'days': remaining_days,
                        'hours': remaining_hours,
                        'minutes': remaining_minutes,
                        'total_seconds': int(remaining_time.total_seconds())
                    }
                },
                'message': 'Obuna faol'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PaymentCreateView(APIView):
    """To'lov ma'lumotlarini yaratish"""

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "error": "Iltimos, tizimga kiring"
            }, status=status.HTTP_401_UNAUTHORIZED)

        plan_id = request.data.get('plan_id')
        payment_method = request.data.get('payment_method')

        if not plan_id:
            return Response({"error": "Plan ID talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)

        if not payment_method:
            return Response({"error": "To'lov usuli talab qilinadi"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id)

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
    """To'lov skrinshoti yuklash"""

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                "error": "Iltimos, tizimga kiring"
            }, status=status.HTTP_401_UNAUTHORIZED)

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


@extend_schema_view(
    list=extend_schema(
        summary="Obuna rejalarini ko'rish",
        description="Barcha mavjud obuna rejalarini ko'rish"
    ),
    retrieve=extend_schema(
        summary="Obuna rejasi ma'lumotlari",
        description="Tanlangan obuna rejasi haqida to'liq ma'lumot"
    )
)
class SubscriptionPlanViewSet(viewsets.ReadOnlyModelViewSet):
    """Obuna rejalari uchun viewset"""
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer
    # permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary="To'lov usullarini ko'rish",
        description="Barcha mavjud to'lov usullarini ko'rish"
    ),
    retrieve=extend_schema(
        summary="To'lov usuli ma'lumotlari",
        description="Tanlangan to'lov usuli haqida to'liq ma'lumot"
    )
)
class PaymentMethodViewSet(viewsets.ReadOnlyModelViewSet):
    """To'lov usullari uchun viewset"""
    queryset = PaymentMethod.objects.filter(is_active=True)
    serializer_class = PaymentMethodSerializer

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"To'lov usullarini olishda xatolik: {str(e)}")
            return Response({
                "error": "To'lov usullarini olishda xatolik yuz berdi"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except PaymentMethod.DoesNotExist:
            return Response({
                "error": "Bunday to'lov usuli mavjud emas"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"To'lov usulini olishda xatolik: {str(e)}")
            return Response({
                "error": "To'lov usulini olishda xatolik yuz berdi"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        summary="Obunalarni ko'rish",
        description="Foydalanuvchining barcha obunalarini ko'rish"
    ),
    create=extend_schema(
        summary="Yangi obuna yaratish",
        description="Yangi obuna uchun so'rov yuborish"
    ),
    retrieve=extend_schema(
        summary="Obuna ma'lumotlari",
        description="Tanlangan obuna haqida to'liq ma'lumot"
    )
)
class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Subscription.objects.all()
        return Subscription.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return SubscriptionCreateSerializer
        return SubscriptionSerializer

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                subscription = serializer.save(
                    user=self.request.user,
                    status='pending',
                    start_date=timezone.now()
                )

                subscription.end_date = subscription.start_date + timezone.timedelta(
                    days=subscription.plan.duration_days
                )
                subscription.save()
        except Exception as e:
            logger.error(f"Obuna yaratishda xatolik: {str(e)}")
            raise DRFValidationError({
                "error": "Obuna yaratishda xatolik yuz berdi"
            })

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Obunalarni olishda xatolik: {str(e)}")
            return Response({
                "error": "Obunalarni olishda xatolik yuz berdi"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Subscription.DoesNotExist:
            return Response({
                "error": "Bunday obuna mavjud emas"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Obunani olishda xatolik: {str(e)}")
            return Response({
                "error": "Obunani olishda xatolik yuz berdi"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        summary="To'lovlar ro'yxati",
        description="Barcha to'lovlarni ko'rish (admin uchun to'liq, user uchun o'ziniki)"
    ),
    create=extend_schema(
        summary="To'lov yaratish",
        description="Yangi to'lov qo'shish"
    ),
    retrieve=extend_schema(
        summary="To'lov ma'lumotlari",
        description="To'lov haqida to'liq ma'lumot"
    )
)
class PaymentViewSet(viewsets.ModelViewSet):
    """To'lovlarni boshqarish uchun ViewSet"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    # permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['user__username', 'subscription_plan__name']
    ordering_fields = ['created_at', 'amount', 'status']
    ordering = ['-created_at']

    def get_queryset(self):
        """Foydalanuvchi faqat o'zining to'lovlarini ko'rishi mumkin"""
        if self.request.user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        return PaymentSerializer

    def perform_create(self, serializer):
        try:
            with transaction.atomic():
                payment = serializer.save(
                    user=self.request.user,
                    status='pending',
                    created_at=timezone.now()
                )

                # Additional logic can be added here if required.
        except Exception as e:
            logger.error(f"To'lov yaratishda xatolik: {str(e)}")
            raise DRFValidationError({
                "error": "To'lov yaratishda xatolik yuz berdi"
            })

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"To'lovlarni olishda xatolik: {str(e)}")
            return Response({
                "error": "To'lovlarni olishda xatolik yuz berdi"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        try:
            return super().retrieve(request, *args, **kwargs)
        except Payment.DoesNotExist:
            return Response({
                "error": "Bunday to'lov mavjud emas"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"To'lovni olishda xatolik: {str(e)}")
            return Response({
                "error": "To'lovni olishda xatolik yuz berdi"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def send_telegram_message(self, user_id: int, message: str, keyboard=None):
        """Telegram orqali xabar yuborish"""
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML',
                    reply_markup=keyboard
                )
            finally:
                await bot.close()
        except Exception as e:
            logger.error(f"Telegram xabarini yuborishda xatolik: {str(e)}")

    async def create_invite_link(self):
        """Kanal uchun bir martalik havola yaratish"""
        try:
            bot = Bot(token=settings.BOT_TOKEN)
            try:
                invite_link = await bot.create_chat_invite_link(
                    chat_id=settings.CHANNEL_ID,
                    member_limit=1,
                    expire_date=int(time.time()) + 86400  # 24 soat
                )
                return invite_link.invite_link
            finally:
                await bot.close()
        except Exception as e:
            logger.error(f"Kanal havolasini yaratishda xatolik: {str(e)}")
            return None

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """To'lovni tasdiqlash"""
        try:
            with transaction.atomic():
                payment = self.get_object()
                
                # Statusni tekshirish
                if payment.status != 'PENDING':
                    return Response(
                        {"error": "Faqat kutilayotgan to'lovlarni tasdiqlash mumkin"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # To'lovni tasdiqlash
                payment.status = 'COMPLETED'
                payment.save()

                # Obunani yaratish
                subscription = Subscription.objects.create(
                    user=payment.user,
                    plan=payment.subscription_plan,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timezone.timedelta(days=payment.subscription_plan.duration_days),
                    status='active',
                    is_active=True
                )

                # Web sayt uchun token
                temp_token = payment.user.get_temp_token()

                # Asosiy xabar uchun tugmalar
                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton(
                        text="🌐 Web saytga o'tish",
                        url=f"{settings.WEB_APP_URL}/activate?token={temp_token}"
                    )
                )

                # Asosiy xabar matni
                main_message = (
                    f"<b>✅ To'lov muvaffaqiyatli tasdiqlandi!</b>\n\n"
                    f"Hurmatli <b>{payment.user.first_name}</b>,\n\n"
                    f"🔰 <b>To'lov ma'lumotlari:</b>\n"
                    f"💰 Miqdor: <code>{payment.amount:,.0f}</code> so'm\n"
                    f"💳 To'lov usuli: <b>{payment.payment_method.name}</b>\n"
                    f"📅 Sana: <code>{payment.created_at.strftime('%d.%m.%Y %H:%M')}</code>\n\n"
                    f"🎉 Tabriklaymiz! Endi siz barcha imkoniyatlardan foydalanishingiz mumkin.\n\n"
                    f"⚠️ <i>Diqqat! Kanal havolasi keyingi xabarda yuboriladi.</i>"
                )

                async def send_messages():
                    # Asosiy xabarni yuborish
                    await self.send_telegram_message(
                        payment.user.telegram_user_id,
                        main_message,
                        keyboard
                    )

                    # Kanal havolasini yaratish va yuborish
                    invite_link = await self.create_invite_link()
                    if invite_link:
                        invite_message = (
                            f"<b>🔐 Maxfiy kanal havolasi</b>\n\n"
                            f"📎 Havola: {invite_link}\n\n"
                            f"⚠️ <i>Ushbu havola:</i>\n"
                            f"• Faqat bir marta ishlatish uchun\n"
                            f"• 24 soat davomida amal qiladi\n\n"
                            f"❗️ Iltimos, havola muddati tugashidan oldin kanalga qo'shiling."
                        )
                        await self.send_telegram_message(
                            payment.user.telegram_user_id,
                            invite_message
                        )

                # Xabarlarni yuborish
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(send_messages())
                finally:
                    loop.close()

                return Response({"status": "success"})

        except Payment.DoesNotExist:
            return Response(
                {"error": "To'lov topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"To'lovni tasdiqlashda xatolik: {str(e)}")
            return Response(
                {"error": "To'lovni tasdiqlashda xatolik yuz berdi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """To'lovni rad etish"""
        try:
            with transaction.atomic():
                payment = self.get_object()

                # Statusni tekshirish
                if payment.status != 'PENDING':
                    return Response(
                        {"error": "Faqat kutilayotgan to'lovlarni rad etish mumkin"},
                        status=status.HTTP_400_BAD_REQUEST
                    )

                # To'lovni rad etish
                payment.status = 'FAILED'
                payment.save()

                # Tugmalar
                keyboard = InlineKeyboardMarkup()
                keyboard.add(
                    InlineKeyboardButton(
                        text="🔄 Qayta urinish",
                        url=f"{settings.WEB_APP_URL}/payment"
                    )
                )

                # Xabar matni
                message = (
                    f"<b>❌ To'lov rad etildi</b>\n\n"
                    f"Hurmatli <b>{payment.user.first_name}</b>,\n\n"
                    f"🔰 <b>To'lov ma'lumotlari:</b>\n"
                    f"💰 Miqdor: <code>{payment.amount:,.0f}</code> so'm\n"
                    f"💳 To'lov usuli: <b>{payment.payment_method.name}</b>\n"
                    f"📅 Sana: <code>{payment.created_at.strftime('%d.%m.%Y %H:%M')}</code>\n\n"
                    f"❗️ To'lovingiz rad etildi. Buning sabablari:\n"
                    f"• To'lov ma'lumotlari noto'g'ri\n"
                    f"• Skrinshot sifati past\n"
                    f"• Boshqa texnik sabablarga ko'ra\n\n"
                    f"Iltimos, qayta urinib ko'ring."
                )

                # Xabarni yuborish
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        self.send_telegram_message(
                            payment.user.telegram_user_id,
                            message,
                            keyboard
                        )
                    )
                finally:
                    loop.close()

                return Response({"status": "success"})

        except Payment.DoesNotExist:
            return Response(
                {"error": "To'lov topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"To'lovni rad etishda xatolik: {str(e)}")
            return Response(
                {"error": "To'lovni rad etishda xatolik yuz berdi"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
