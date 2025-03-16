from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.contrib import messages
from django.utils.html import format_html
from .models import Payment
from subscriptions.models import Subscription
from invest_bot.bot import bot
import json
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import asyncio
from invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'get_amount_display', 'payment_method', 'get_status_badge', 'created_at', 'get_admin_actions')
    list_filter = ('status', 'payment_method', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'user__phone_number')
    readonly_fields = ('created_at', 'updated_at', 'get_screenshot_preview')
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('user', 'subscription_plan', 'amount', 'payment_method', 'status')
        }),
        ('To\'lov cheki', {
            'fields': ('screenshot', 'get_screenshot_preview')
        }),
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_status_badge(self, obj):
        return obj.get_status_badge()
    get_status_badge.short_description = "Holat"
    
    def get_admin_actions(self, obj):
        return obj.get_admin_actions()
    get_admin_actions.short_description = "Amallar"
    
    def get_screenshot_preview(self, obj):
        return obj.get_screenshot_preview()
    get_screenshot_preview.short_description = "To'lov cheki"
    
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
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })

    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',)
        }
        js = ('admin/js/payment_actions.js',) 