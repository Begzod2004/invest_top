import hashlib
import hmac
import json
import time
import asyncio
from django.conf import settings
from django.utils.timezone import now
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import User
from invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot

class TelegramAuthView(APIView):
    """
    Telegram orqali autentifikatsiya qilish
    """

    def post(self, request):
        telegram_data = request.data

        # 1️⃣ Telegramdan kelgan ma'lumotni tekshiramiz
        auth_data = telegram_data.get("auth_data")
        if not auth_data:
            return Response({"error": "No authentication data provided"}, status=400)

        # 2️⃣ HMAC (sha256) orqali Telegram imzosi to'g'riligini tekshiramiz
        bot_token = settings.BOT_TOKEN.encode("utf-8")
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(json.loads(auth_data).items()) if k != "hash"
        ).encode("utf-8")

        secret_key = hashlib.sha256(bot_token).digest()
        computed_hash = hmac.new(secret_key, data_check_string, hashlib.sha256).hexdigest()

        if computed_hash != json.loads(auth_data)["hash"]:
            return Response({"error": "Invalid authentication data"}, status=400)

        # 3️⃣ Foydalanuvchini bazada qidiramiz yoki yaratamiz
        telegram_id = json.loads(auth_data)["id"]
        first_name = json.loads(auth_data).get("first_name", "")
        last_name = json.loads(auth_data).get("last_name", "")
        username = json.loads(auth_data).get("username", "")

        user, created = User.objects.get_or_create(
            telegram_user_id=telegram_id,
            defaults={"first_name": first_name, "last_name": last_name, "user_id": telegram_id, "created_at": now()},
        )

        # 4️⃣ Foydalanuvchiga JWT token yaratamiz
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Authentication successful",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "user": {
                    "id": user.id,
                    "telegram_id": user.telegram_user_id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": username,
                },
            }
        )

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_message_to_user(request, user_id):
    """Foydalanuvchiga xabar yuborish"""
    try:
        user = get_object_or_404(User, id=user_id)
        message = request.data.get('message')
        
        if not message:
            return Response({
                'status': 'error',
                'message': 'Xabar matni kiritilmagan'
            }, status=status.HTTP_400_BAD_REQUEST)
        
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
                error = str(e)
            
            await bot.session.close()
            return success, error if 'error' in locals() else None
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, error = loop.run_until_complete(send_message())
        loop.close()
        
        if success:
            return Response({
                'status': 'success',
                'message': f'Xabar {user.first_name} ga muvaffaqiyatli yuborildi'
            })
        else:
            return Response({
                'status': 'error',
                'message': f'Xabarni {user.first_name} ga yuborishda xatolik: {error}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
