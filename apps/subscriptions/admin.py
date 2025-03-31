from django.contrib import admin
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.urls import path
from django.shortcuts import redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.views.decorators.http import require_POST
from .models import SubscriptionPlan, Subscription, Payment, PaymentMethod, PaymentType

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'description')
    search_fields = ('name', 'description')
    list_filter = ('duration_days',)
    ordering = ('duration_days',)
    
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'price', 'duration_days')
        }),
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Mavjud foydalanuvchilar ulangan bo'lishi mumkin, shuning uchun o'chirish imkoniyatini cheklash
        return False

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'start_date', 'end_date', 'is_active')
    list_filter = ('status', 'is_active', 'start_date', 'end_date')
    search_fields = ('user__username', 'plan__name')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'card_holder', 'is_default', 'is_active')
    list_filter = ('is_default', 'is_active')
    search_fields = ('name', 'number', 'card_holder')

@admin.register(PaymentType)
class PaymentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'subscription_plan', 'amount', 'status', 'created_at', 'get_screenshot_preview', 'get_action_buttons')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    
    def get_screenshot_preview(self, obj):
        if obj.screenshot:
            return format_html(
                '<img src="{}" class="payment-screenshot" alt="Payment Screenshot" />',
                obj.screenshot.url
            )
        return "Rasm yuklanmagan"
    get_screenshot_preview.short_description = "To'lov rasmi"
    
    def get_action_buttons(self, obj):
        """To'lov uchun amal tugmalarini ko'rsatish"""
        if not obj:
            return "-"
            
        if obj.status == 'PENDING':
            return format_html(
                '<button onclick="approvePayment({})" class="action-button approve-button">Tasdiqlash</button>'
                '&nbsp;'
                '<button onclick="rejectPayment({})" class="action-button reject-button">Rad etish</button>',
                obj.id, obj.id
            )
        
        status_colors = {
            'COMPLETED': '#28a745',
            'FAILED': '#dc3545',
            'CANCELLED': '#dc3545'
        }
        
        return format_html(
            '<span style="color: {};">{}</span>',
            status_colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    get_action_buttons.short_description = "Amallar"
    
    class Media:
        css = {
            'all': ('admin/css/payment_admin.css',)
        }
        js = ('admin/js/payment_actions.js',)

