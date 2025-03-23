from rest_framework import viewsets, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.db import transaction
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
import asyncio
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
from apps.users.models import User
from .models import Subscription, SubscriptionPlan
from .serializers import SubscriptionSerializer, SubscriptionPlanSerializer

class SubscriptionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        subscription = Subscription.objects.filter(user=user, status="active", expires_at__gte=now()).first()

        if subscription:
            remaining_days = (subscription.expires_at - now()).days
            return Response({
                "status": "active",
                "remaining_days": remaining_days,
                "plan": subscription.subscription_plan.title
            })
        return Response({"status": "expired", "remaining_days": 0, "plan": None})

class PaymentCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        plan_id = request.data.get("plan_id")
        plan = get_object_or_404(SubscriptionPlan, id=plan_id)

        subscription = Subscription.objects.create(
            user=user,
            subscription_plan=plan,
            amount_paid=plan.price,
            status="waiting_admin"
        )

        return Response({"message": "To'lov qabul qilindi, admin tasdiqlashini kuting.", "subscription_id": subscription.id})

class PaymentUploadScreenshotView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        subscription_id = request.data.get("subscription_id")
        screenshot = request.FILES.get("screenshot")

        subscription = get_object_or_404(Subscription, id=subscription_id, user=request.user)
        subscription.payment_screenshot = screenshot
        subscription.save()

        return Response({"message": "To'lov skrinshoti yuklandi, admin tekshirib tasdiqlaydi."})

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
        if not self.request.user.is_staff:
            return Subscription.objects.filter(user=self.request.user)
        return Subscription.objects.all()
    
    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        subscriptions = Subscription.objects.filter(user=request.user)
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='active')
    def active_subscriptions(self, request):
        """Faol obunalarni olish"""
        subscriptions = Subscription.objects.filter(status='active', expires_at__gt=now())
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='expired')
    def expired_subscriptions(self, request):
        """Muddati tugagan obunalarni olish"""
        subscriptions = Subscription.objects.filter(status='expired')
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='user/(?P<user_id>[^/.]+)')
    def user_subscriptions(self, request, user_id=None):
        """Foydalanuvchining obunalarini olish"""
        try:
            user = User.objects.get(id=user_id)
            subscriptions = Subscription.objects.filter(user=user).order_by('-created_at')
            serializer = self.get_serializer(subscriptions, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Foydalanuvchi topilmadi'
            }, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'], url_path='activate')
    def activate_subscription(self, request, pk=None):
        """Obunani faollashtirish"""
        try:
            with transaction.atomic():
                subscription = self.get_object()
                
                if subscription.status == 'active':
                    return Response({
                        'status': 'error',
                        'message': 'Bu obuna allaqachon faol'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Obunani faollashtirish
                subscription.activate()
                
                # Foydalanuvchini obunachi qilish
                user = subscription.user
                user.is_subscribed = True
                user.save()
                
                # Telegram xabarini yuborish
                async def send_message():
                    bot = Bot(token=BOT_TOKEN)
                    text = (
                        f"✅ Hurmatli {user.first_name},\n\n"
                        f"Sizning obunangiz faollashtirildi!\n"
                        f"Obuna turi: {subscription.subscription_plan.title}\n"
                        f"Muddat: {subscription.subscription_plan.duration_days} kun\n\n"
                        f"Obuna muddati: {subscription.expires_at.strftime('%Y-%m-%d %H:%M')}"
                    )
                    
                    await bot.send_message(
                        chat_id=int(user.telegram_user_id),
                        text=text
                    )
                    await bot.session.close()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_message())
                loop.close()
                
                return Response({
                    'status': 'success',
                    'message': 'Obuna muvaffaqiyatli faollashtirildi',
                    'subscription': self.get_serializer(subscription).data
                })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'], url_path='deactivate')
    def deactivate_subscription(self, request, pk=None):
        """Obunani bekor qilish"""
        try:
            with transaction.atomic():
                subscription = self.get_object()
                
                if subscription.status != 'active':
                    return Response({
                        'status': 'error',
                        'message': 'Bu obuna faol emas'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Obunani bekor qilish
                subscription.status = 'expired'
                subscription.save()
                
                # Foydalanuvchining boshqa faol obunalari bor-yo'qligini tekshirish
                active_subscriptions = Subscription.objects.filter(
                    user=subscription.user,
                    status='active',
                    expires_at__gt=now()
                ).exists()
                
                if not active_subscriptions:
                    # Foydalanuvchini obunachi emas deb belgilash
                    user = subscription.user
                    user.is_subscribed = False
                    user.save()
                
                # Telegram xabarini yuborish
                async def send_message():
                    bot = Bot(token=BOT_TOKEN)
                    text = (
                        f"❌ Hurmatli {subscription.user.first_name},\n\n"
                        f"Sizning obunangiz bekor qilindi.\n"
                        f"Obuna turi: {subscription.subscription_plan.title}\n\n"
                        f"Iltimos, yangi obuna sotib oling."
                    )
                    
                    await bot.send_message(
                        chat_id=int(subscription.user.telegram_user_id),
                        text=text
                    )
                    await bot.session.close()
                
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(send_message())
                loop.close()
                
                return Response({
                    'status': 'success',
                    'message': 'Obuna muvaffaqiyatli bekor qilindi',
                    'subscription': self.get_serializer(subscription).data
                })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_subscription_status(request, user_id):
    """Foydalanuvchining obuna holatini olish"""
    try:
        user = User.objects.get(id=user_id)
        active_subscription = Subscription.objects.filter(
            user=user,
            status='active',
            expires_at__gt=now()
        ).order_by('-expires_at').first()
        
        if active_subscription:
            delta = active_subscription.expires_at - now()
            remaining_days = max(0, delta.days)
            
            return Response({
                'status': 'active',
                'subscription': SubscriptionSerializer(active_subscription).data,
                'remaining_days': remaining_days
            })
        else:
            return Response({
                'status': 'inactive',
                'message': 'Foydalanuvchining faol obunasi yo\'q'
            })
    except User.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Foydalanuvchi topilmadi'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
