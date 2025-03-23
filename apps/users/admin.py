from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Permission, Group
from django.utils.html import format_html
from django.db.models import Count
from django.urls import path
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import User, Role
import json

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'content_type']
    list_filter = ['content_type__app_label']
    search_fields = ['name', 'codename']
    ordering = ['content_type__app_label', 'codename']

admin.site.unregister(Group)
@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_permissions']
    search_fields = ['name']
    filter_horizontal = ['permissions']
    
    def get_permissions(self, obj):
        return ", ".join([p.codename for p in obj.permissions.all()])
    get_permissions.short_description = 'Ruxsatlar'

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'username', 'full_name', 'phone_number', 
        'telegram_user_id', 'is_active', 'is_admin', 
        'balance', 'get_groups'
    ]
    list_filter = [
        'is_active', 'is_admin', 'is_blocked', 
        'is_staff', 'groups', 'date_joined'
    ]
    search_fields = [
        'username', 'first_name', 'last_name', 
        'phone_number', 'telegram_user_id'
    ]
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Shaxsiy ma\'lumotlar', {
            'fields': ('first_name', 'last_name', 'phone_number', 'image_url')
        }),
        ('Telegram ma\'lumotlari', {
            'fields': ('user_id', 'telegram_user_id')
        }),
        ('Ruxsatlar', {
            'fields': (
                'is_active', 'is_admin', 'is_blocked',
                'is_staff', 'is_superuser', 
                'groups', 'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Balans', {
            'fields': ('balance',)
        }),
        ('Muhim sanalar', {
            'fields': ('date_joined', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('date_joined', 'updated_at')
    filter_horizontal = ('groups', 'user_permissions')

    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = 'To\'liq ismi'

    def get_groups(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    get_groups.short_description = 'Guruhlar'

    def save_model(self, request, obj, form, change):
        if not change:  # Yangi user yaratilayotganda
            if not obj.password:  # Agar parol berilmagan bo'lsa
                obj.set_password(User.objects.make_random_password())
        super().save_model(request, obj, form, change)

    def response_change(self, request, obj):
        if "_block-user" in request.POST:
            obj.is_blocked = True
            obj.save()
            self.message_user(request, f"{obj.username} bloklandi")
            return HttpResponseRedirect(".")
        elif "_unblock-user" in request.POST:
            obj.is_blocked = False
            obj.save()
            self.message_user(request, f"{obj.username} blokdan chiqarildi")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('broadcast/', self.admin_site.admin_view(self.broadcast_view), name='user-broadcast'),
        ]
        return custom_urls + urls
    
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
                users = User.objects.filter(is_active=True)
            
            success_count = 0
            error_count = 0
            
            # Xabar yuborish kodi
            self.message_user(
                request, 
                f"Xabar yuborildi: {success_count} ta muvaffaqiyatli, {error_count} ta xatolik",
                messages.SUCCESS if error_count == 0 else messages.WARNING
            )
            
            return HttpResponseRedirect("../")
        
        return HttpResponseRedirect("../")

    def referral_count(self, obj):
        # If the model has a referrals related_name
        if hasattr(obj, 'referrals'):
            return obj.referrals.count()
        return 0
    referral_count.short_description = "Referrallar soni"

    def user_statistics(self, obj):
        total_users = User.objects.count()
        subscribed_users = User.objects.filter(is_active=True).count()
        active_users = User.objects.filter(is_active=True).count()
        
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
    
    class Media:
        css = {
            'all': ('https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.css', 'admin/css/forms.css')
        }
        js = ('https://cdn.jsdelivr.net/npm/chart.js@3.7.0/dist/chart.min.js',)
