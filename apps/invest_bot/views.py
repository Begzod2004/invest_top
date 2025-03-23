from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# Create your views here.

class TelegramWebhookView(APIView):
    """
    Telegram webhook uchun view.
    """
    permission_classes = []  # webhook uchun autentifikatsiya kerak emas

    def post(self, request, *args, **kwargs):
        # Webhook mantig'i
        # Telegram dan kelgan ma'lumotlarni qayta ishlash
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)
