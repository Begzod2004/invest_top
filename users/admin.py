from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import User
import json

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'is_admin', 'is_blocked', 
                   'is_subscribed', 'created_at')
    list_filter = ('is_admin', 'is_blocked', 'is_subscribed', 'created_at')
    search_fields = ('first_name', 'last_name', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('broadcast/', self.admin_site.admin_view(self.broadcast_view), name='user-broadcast'),
        ]
        return custom_urls + urls

    def referral_count(self, obj):
        return obj.referrals.count()
    referral_count.short_description = "Referrallar soni"

    def user_statistics(self, obj):
        total_users = User.objects.count()
        subscribed_users = User.objects.filter(is_subscribed=True).count()
        active_users = User.objects.filter(is_blocked=False).count()
        referral_stats = User.objects.annotate(ref_count=Count('referrals')).order_by('-ref_count')[:5]
        
        html = f"""
        <div style="padding: 10px; background-color: #f9f9f9; border-radius: 5px; margin: 10px 0;">
            <h3 style="color: #2c3e50;">📊 Statistika</h3>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 20px;">
                <div style="background: #3498db; color: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <h4>Jami foydalanuvchilar</h4>
                    <p style="font-size: 24px; margin: 5px;">{total_users}</p>
                </div>
                <div style="background: #2ecc71; color: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <h4>Obuna bo'lganlar</h4>
                    <p style="font-size: 24px; margin: 5px;">{subscribed_users}</p>
                </div>
                <div style="background: #e74c3c; color: white; padding: 15px; border-radius: 5px; text-align: center;">
                    <h4>Faol foydalanuvchilar</h4>
                    <p style="font-size: 24px; margin: 5px;">{active_users}</p>
                </div>
            </div>
            <div style="background: white; padding: 15px; border-radius: 5px; margin-top: 20px;">
                <h4 style="color: #2c3e50;">🏆 Top 5 Referrallar</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr style="background: #f2f2f2;">
                        <th style="padding: 10px; text-align: left;">Foydalanuvchi</th>
                        <th style="padding: 10px; text-align: right;">Referrallar soni</th>
                    </tr>
        """
        
        for user in referral_stats:
            html += f"""
                    <tr style="border-bottom: 1px solid #eee;">
                        <td style="padding: 10px;">{user.first_name} {user.last_name or ''}</td>
                        <td style="padding: 10px; text-align: right;">{user.ref_count}</td>
                    </tr>
            """
            
        html += """
                </table>
            </div>
        </div>
        """
        return format_html(html)
    user_statistics.short_description = "Statistika"

    def broadcast_form(self, obj):
        return format_html(
            '''
            <div style="padding: 10px; background-color: #f9f9f9; border-radius: 5px; margin: 10px 0;">
                <h3 style="color: #2c3e50;">📨 Xabar yuborish</h3>
                <form action="{}" method="post">
                    <input type="hidden" name="csrfmiddlewaretoken" value="">
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px;">Qabul qiluvchilar:</label>
                        <select name="recipient_type" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ddd;">
                            <option value="all">Barcha foydalanuvchilarga</option>
                            <option value="subscribed">Faqat obunachilarga</option>
                            <option value="active">Start bosgan foydalanuvchilarga</option>
                        </select>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <label style="display: block; margin-bottom: 5px;">Xabar matni:</label>
                        <textarea name="message" rows="5" style="width: 100%; padding: 8px; border-radius: 4px; border: 1px solid #ddd;"></textarea>
                    </div>
                    <button type="submit" style="background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer;">
                        Xabarni yuborish
                    </button>
                </form>
            </div>
            ''',
            reverse('admin:user-broadcast')
        )
    broadcast_form.short_description = "Xabar yuborish"

    def broadcast_view(self, request):
        if request.method == 'POST':
            recipient_type = request.POST.get('recipient_type')
            message = request.POST.get('message')
            
            if not message:
                self.message_user(request, "Xabar matni kiritilmagan!", messages.ERROR)
                return HttpResponseRedirect("../")
            
            users = []
            if recipient_type == 'all':
                users = User.objects.all()
            elif recipient_type == 'subscribed':
                users = User.objects.filter(is_subscribed=True)
            elif recipient_type == 'active':
                users = User.objects.filter(is_blocked=False)
            
            success_count = 0
            error_count = 0
            
            from invest_bot.bot_config import BOT_TOKEN
            from aiogram import Bot
            import asyncio
            
            async def send_messages():
                bot = Bot(token=BOT_TOKEN)
                for user in users:
                    try:
                        await bot.send_message(
                            chat_id=int(user.telegram_user_id),
                            text=message
                        )
                        nonlocal success_count
                        success_count += 1
                    except Exception as e:
                        nonlocal error_count
                        error_count += 1
                await bot.session.close()
            
            # Run async function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_messages())
            loop.close()
            
            self.message_user(
                request, 
                f"Xabar yuborildi: {success_count} ta muvaffaqiyatli, {error_count} ta xatolik",
                messages.SUCCESS if error_count == 0 else messages.WARNING
            )
            
            return HttpResponseRedirect("../")
        
        return HttpResponseRedirect("../")

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        
        # Kunlik statistika (so'nggi 7 kun)
        daily_stats = (
            User.objects.extra(select={'date': 'date(created_at)'})
            .values('date')
            .annotate(count=Count('id'))
            .order_by('-date')[:7]
        )
        
        # Statistika ma'lumotlarini JSON formatga o'tkazish
        stats_data = {
            'labels': [str(stat['date']) for stat in daily_stats],
            'data': [stat['count'] for stat in daily_stats]
        }
        
        extra_context['daily_stats'] = json.dumps(stats_data)
        return super().changelist_view(request, extra_context=extra_context)

    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.css',)
        }
        js = ('https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.js',)
