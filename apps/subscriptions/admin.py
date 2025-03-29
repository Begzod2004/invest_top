from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Subscription, SubscriptionPlan

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'description')
    search_fields = ('name', 'description')
    list_filter = ('duration_days',)
    ordering = ('duration_days',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'price', 'duration_days')
        }),
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )
    
    def has_delete_permission(self, request, obj=None):
        # Mavjud foydalanuvchilar ulangan bo'lishi mumkin, shuning uchun o'chirish imkoniyatini cheklash
        if obj and Subscription.objects.filter(plan=obj).exists():
            return False
        return super().has_delete_permission(request, obj)

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status_badge', 'amount_display', 'payment_method_display', 
                   'start_date', 'end_date', 'days_left_display', 'actions_display')
    list_filter = ('status', 'is_active', 'payment_method', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'plan__name')
    readonly_fields = ('created_at', 'updated_at', 'payment_screenshot_preview')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'plan', 'status', 'is_active')
        }),
        ('Muddat ma\'lumotlari', {
            'fields': ('start_date', 'end_date')
        }),
        ('To\'lov ma\'lumotlari', {
            'fields': ('amount_paid', 'payment_method', 'payment_date', 'payment_screenshot', 'payment_screenshot_preview')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        badges = {
            'pending': 'secondary',
            'waiting_admin': 'warning',
            'active': 'success',
            'expired': 'danger',
            'cancelled': 'danger',
            'rejected': 'danger',
        }
        color = badges.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.get_status_display())
    status_badge.short_description = 'Status'
    
    def amount_display(self, obj):
        return format_html('<b>{:,.0f} so\'m</b>', obj.amount_paid)
    amount_display.short_description = 'To\'lov summasi'
    
    def payment_method_display(self, obj):
        if not obj.payment_method:
            return '-'
        icons = {
            'uzcard': 'credit-card',
            'humo': 'credit-card',
            'visa': 'cc-visa',
            'mastercard': 'cc-mastercard',
            'crypto': 'bitcoin',
            'other': 'money-bill-alt'
        }
        icon = icons.get(obj.payment_method, 'credit-card')
        return format_html('<i class="fas fa-{}"></i> {}', icon, obj.get_payment_method_display())
    payment_method_display.short_description = 'To\'lov usuli'
    
    def days_left_display(self, obj):
        days = obj.days_left()
        if days <= 0:
            return format_html('<span class="badge bg-danger">Tugagan</span>')
        if days <= 3:
            return format_html('<span class="badge bg-warning">{} kun</span>', days)
        return format_html('<span class="badge bg-success">{} kun</span>', days)
    days_left_display.short_description = 'Qolgan kun'
    
    def payment_screenshot_preview(self, obj):
        if not obj.payment_screenshot:
            return 'Rasm yo\'q'
        return format_html('<img src="{}" width="300" height="auto" />', obj.payment_screenshot.url)
    payment_screenshot_preview.short_description = 'To\'lov skrinshotini ko\'rish'
    
    def actions_display(self, obj):
        """Admin uchun amallar tugmachalari"""
        actions = []
        
        if obj.status == 'waiting_admin':
            activate_url = reverse('admin:subscriptions_subscription_changelist')
            actions.append(
                format_html(
                    '<button onclick="approveSubscription({})" class="btn btn-success btn-sm" title="Obunani tasdiqlash">'
                    '<i class="fas fa-check"></i></button>',
                    obj.id
                )
            )
            actions.append(
                format_html(
                    '<button onclick="rejectSubscription({})" class="btn btn-danger btn-sm" title="Obunani rad etish">'
                    '<i class="fas fa-times"></i></button>',
                    obj.id
                )
            )
        
        if obj.status == 'active' and obj.is_active:
            actions.append(
                format_html(
                    '<button onclick="cancelSubscription({})" class="btn btn-warning btn-sm" title="Obunani to\'xtatish">'
                    '<i class="fas fa-ban"></i></button>',
                    obj.id
                )
            )
            
        if actions:
            return format_html('<div class="d-flex gap-1">{}</div>', mark_safe(''.join(actions)))
        return '-'
    actions_display.short_description = 'Amallar'
    
    def get_queryset(self, request):
        # Admin rolida bo'lmagan foydalanuvchilar faqat o'z obunalarini ko'rishadi
        qs = super().get_queryset(request)
        if not request.user.is_superuser and not request.user.is_staff:
            return qs.filter(user=request.user)
        return qs
    
    class Media:
        css = {
            'all': ('admin/css/subscription_admin.css', 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css',)
        }
        js = ('admin/js/subscription_admin.js',)

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(Subscription, SubscriptionAdmin)

