from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from apps.users.models import User
from apps.payments.models import Payment
from apps.payments.admin import PaymentAdmin
from apps.subscriptions.models import Subscription, SubscriptionPlan
from apps.signals.models import Signal
from apps.reviews.models import Review
from apps.instruments.models import Instrument
from .models import BroadcastMessage
import json
from apps.invest_bot.bot_config import BOT_TOKEN
from aiogram import Bot
import asyncio
from asgiref.sync import sync_to_async

# Register models from other apps
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

@admin.register(BroadcastMessage)
class BroadcastMessageAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_type',
        'sent_by',
        'message',
        'sent_at',
        'success_count',
        'error_count'
    ]
    list_filter = [
        'recipient_type',
        'sent_at',
    ]
    readonly_fields = [
        'recipient_type',
        'message',
        'sent_by',
        'sent_at',
        'success_count',
        'error_count'
    ]
    search_fields = ['message']
    ordering = ['-sent_at']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class CustomAdminSite(admin.AdminSite):
    site_title = "Top Invest Admin"
    site_header = "Top Invest"
    index_title = "Admin Panel"

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        if app_label is None:
            app_list += [
                {
                    "name": "Dashboard",
                    "app_label": "dashboard",
                    "models": [
                        {
                            "name": "Dashboard",
                            "object_name": "Dashboard",
                            "admin_url": "/admin/dashboard/",
                            "view_only": True,
                        },
                        {
                            "name": "Xabar yuborish",
                            "object_name": "Broadcast",
                            "admin_url": "/admin/broadcast/",
                            "view_only": True,
                        }
                    ],
                }
            ]
        return app_list

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('dashboard/', self.admin_view(self.dashboard_view), name='admin_dashboard'),
            path('broadcast/', self.admin_view(self.broadcast_view), name='admin_broadcast'),
        ]
        return custom_urls + urls
    
    def dashboard_view(self, request):
        # Statistika ma'lumotlarini olish
        total_users = User.objects.count()
        subscribed_users = User.objects.filter(is_subscribed=True).count()
        active_users = User.objects.filter(is_blocked=False).count()
        
        # Top referrallar
        top_referrers = User.objects.annotate(
            ref_count=Count('referrals')
        ).order_by('-ref_count')[:5]
        
        # Kunlik statistika (so'nggi 7 kun)
        daily_stats = (
            User.objects.extra(select={'date': 'date(created_at)'})
            .values('date')
            .annotate(count=Count('id'))
            .order_by('-date')[:7]
        )
        
        context = {
            'title': 'Dashboard',
            'total_users': total_users,
            'subscribed_users': subscribed_users,
            'active_users': active_users,
            'top_referrers': top_referrers,
            'daily_stats': json.dumps({
                'labels': [str(stat['date']) for stat in daily_stats],
                'data': [stat['count'] for stat in daily_stats]
            }),
            **self.each_context(request),
        }
        
        return render(request, 'admin/dashboard.html', context)
    
    @sync_to_async
    def get_users_by_type(self, recipient_type):
        if recipient_type == 'all':
            return list(User.objects.all())
        elif recipient_type == 'subscribed':
            return list(User.objects.filter(is_subscribed=True))
        else:
            return list(User.objects.filter(is_blocked=False))
    
    async def send_messages_async(self, users, message, bot):
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
                
        return success_count, error_count
    
    def broadcast_view(self, request):
        if request.method == 'POST':
            recipient_type = request.POST.get('recipient_type')
            message = request.POST.get('message')
            
            if not message:
                messages.error(request, "Xabar matni kiritilmagan!")
                return HttpResponseRedirect(reverse('admin:admin_broadcast'))
            
            async def send_broadcast():
                bot = Bot(token=BOT_TOKEN)
                users = await self.get_users_by_type(recipient_type)
                success_count, error_count = await self.send_messages_async(users, message, bot)
                await bot.session.close()
                return success_count, error_count
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success_count, error_count = loop.run_until_complete(send_broadcast())
            loop.close()
            
            # Xabarni saqlash
            BroadcastMessage.objects.create(
                message=message,
                recipient_type=recipient_type,
                sent_by=request.user,
                success_count=success_count,
                error_count=error_count
            )
            
            messages.success(
                request, 
                f"Xabar yuborildi: {success_count} ta muvaffaqiyatli, {error_count} ta xatolik"
            )
            
            return HttpResponseRedirect(reverse('admin:admin_broadcast'))
        
        context = {
            'title': 'Xabar yuborish',
            'recent_broadcasts': BroadcastMessage.objects.all()[:5],
            **self.each_context(request),
        }
        
        return render(request, 'admin/broadcast.html', context)

# Create admin site instance
admin_site = CustomAdminSite(name='admin')

# Register models with the custom admin site
admin_site.register(Group)
admin_site.register(User)
admin_site.register(Payment, PaymentAdmin)
admin_site.register(Subscription)
admin_site.register(SubscriptionPlan)
admin_site.register(Signal)
admin_site.register(Review)
admin_site.register(Instrument)
admin_site.register(BroadcastMessage)
