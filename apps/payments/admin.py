from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.contrib import messages
from django.utils.html import format_html
from .models import Payment
from apps.subscriptions.models import Subscription
from apps.invest_bot.bot import bot
import json
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import asyncio
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'payment_type', 'status', 'created_at', 'get_status_actions')
    list_filter = ('status', 'payment_type', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'subscription_plan__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('To\'lov ma\'lumotlari', {
            'fields': ('user', 'subscription_plan', 'amount', 'payment_type')
        }),
        ('Holat', {
            'fields': ('status', 'transaction_id')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_status_actions(self, obj):
        """To'lov holatini o'zgartirish uchun tugmalar"""
        if obj.status == 'PENDING':
            return format_html(
                '<button onclick="approvePayment({})" class="button">Tasdiqlash</button>'
                '<button onclick="rejectPayment({})" class="button" style="margin-left: 10px;">Rad etish</button>',
                obj.id, obj.id
            )
        return '-'
    get_status_actions.short_description = 'Amallar'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:payment_id>/approve/',
                self.admin_site.admin_view(self.approve_payment),
                name='payment-approve'
            ),
            path(
                '<int:payment_id>/reject/',
                self.admin_site.admin_view(self.reject_payment),
                name='payment-reject'
            ),
        ]
        return custom_urls + urls

    @method_decorator(require_POST)
    def approve_payment(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.approve()
            
            # Foydalanuvchini obunachi qilish
            user = payment.user
            user.is_subscribed = True
            user.save()
            
            # Telegram xabarini yuborish
            async def send_message():
                bot = Bot(token=BOT_TOKEN)
                text = (
                    f"✅ Hurmatli {payment.user.full_name},\n\n"
                    f"Sizning to'lovingiz tasdiqlandi!\n"
                    f"To'lov miqdori: {payment.amount} so'm\n"
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
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    @method_decorator(require_POST)
    def reject_payment(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            payment.reject()
            
            # Telegram xabarini yuborish
            async def send_message():
                bot = Bot(token=BOT_TOKEN)
                text = (
                    f"❌ Hurmatli {payment.user.full_name},\n\n"
                    f"Sizning to'lovingiz rad etildi.\n"
                    f"To'lov miqdori: {payment.amount} so'm\n"
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
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    async def send_telegram_message(self, user_id, message):
        """Telegram xabar yuborish"""
        bot = Bot(token=BOT_TOKEN)
        try:
            await bot.send_message(chat_id=user_id, text=message)
        finally:
            await bot.session.close()

    def send_notification(self, user_id, message):
        """Telegram xabar yuborishni boshqarish"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.send_telegram_message(user_id, message))
        finally:
            loop.close()

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',)
        }
        js = ('admin/js/payment_actions.js',)
        css = {
            'all': ('admin/css/payment_actions.css',)
        } 