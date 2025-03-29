from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from django.template.response import TemplateResponse
from django.contrib import messages
from django.utils.html import format_html
from .models import Payment
from apps.subscriptions.models import Subscription
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
import asyncio
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
from django.utils.timezone import now, timedelta

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'payment_type', 'status', 'created_at')
    list_filter = ('status', 'payment_type', 'created_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Asosiy', {
            'fields': ('user', 'subscription_plan', 'amount', 'payment_type', 'status')
        }),
        ('To\'lov tasdiqlovchi', {
            'fields': ('screenshot',)
        }),
        ('Vaqt', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_status_actions(self, obj):
        """To'lov holatini o'zgartirish uchun tugmalar"""
        if obj.status == 'PENDING':
            return format_html(
                '<div style="display:flex;justify-content:flex-start;">'
                '<button onclick="approvePayment({})" class="button" '
                'style="background-color:#28a745;color:white;padding:5px 10px;'
                'border:none;border-radius:4px;cursor:pointer;font-size:12px;">'
                'Tasdiqlash</button>'
                '<button onclick="rejectPayment({})" class="button" '
                'style="background-color:#dc3545;color:white;padding:5px 10px;'
                'margin-left:10px;border:none;border-radius:4px;cursor:pointer;font-size:12px;">'
                'Rad etish</button>'
                '</div>',
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
            
            if payment.status != 'PENDING':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Bu to\'lov allaqachon tasdiqlangan yoki rad etilgan'
                }, status=400)
            
            # To'lovni tasdiqlash - model metodini ishlatamiz
            payment.approve()
            
            # Telegram xabarini yuborish
            try:
                async def send_message():
                    bot = Bot(token=BOT_TOKEN)
                    text = (
                        f"✅ Hurmatli {payment.user.first_name},\n\n"
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
            except Exception as e:
                # Telegram xabar yuborishdagi xatolarni e'tiborsiz qoldiramiz,
                # to'lovni baribir qabul qilamiz
                print(f"Telegram xabar yuborishdagi xato: {e}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'To\'lov muvaffaqiyatli tasdiqlandi'
            })
        except Payment.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'To\'lov topilmadi'
            }, status=404)
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            print(f"Approve payment error: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'Xatolik yuz berdi: {str(e)}'
            }, status=500)

    @method_decorator(require_POST)
    def reject_payment(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
            
            if payment.status != 'PENDING':
                return JsonResponse({
                    'status': 'error',
                    'message': 'Bu to\'lov allaqachon tasdiqlangan yoki rad etilgan'
                }, status=400)
            
            # To'lovni rad etish - model metodini ishlatamiz
            payment.reject()
            
            # Telegram xabarini yuborish
            try:
                async def send_message():
                    bot = Bot(token=BOT_TOKEN)
                    text = (
                        f"❌ Hurmatli {payment.user.first_name},\n\n"
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
            except Exception as e:
                # Telegram xabar yuborishdagi xatolarni e'tiborsiz qoldiramiz,
                # to'lovni baribir rad qilamiz
                print(f"Telegram xabar yuborishdagi xato: {e}")
            
            return JsonResponse({
                'status': 'success',
                'message': 'To\'lov muvaffaqiyatli rad etildi'
            })
        except Payment.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'To\'lov topilmadi'
            }, status=404)
        except ValueError as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
        except Exception as e:
            print(f"Reject payment error: {e}")
            return JsonResponse({
                'status': 'error',
                'message': f'Xatolik yuz berdi: {str(e)}'
            }, status=500)

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
            'all': ('admin/css/payment_actions.css', 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',)
        }
        js = ('admin/js/payment_actions.js',) 