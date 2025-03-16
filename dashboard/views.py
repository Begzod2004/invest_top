from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.db import transaction
import asyncio
from invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
from users.models import User
from .models import BroadcastMessage
from .serializers import BroadcastMessageSerializer

# Create your views here.

class BroadcastViewSet(viewsets.ModelViewSet):
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
