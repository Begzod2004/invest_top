from django.contrib import admin
from .models import Subscription, SubscriptionPlan
from django.utils.html import format_html

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'price', 'duration_days', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title',)

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_plan', 'status', 'created_at', 'expires_at', 'get_payment_info')
    list_filter = ('status', 'subscription_plan')
    search_fields = ('user__first_name', 'user__telegram_user_id')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'expires_at', 'get_payment_info')

    def get_payment_info(self, obj):
        payment = obj.user.payments.filter(subscription_plan=obj.subscription_plan).first()
        if payment:
            return format_html(
                '<div style="display: flex; align-items: center;">'
                '<div style="margin-right: 10px;">'
                '<strong>To\'lov:</strong> {} so\'m<br>'
                '<strong>Usul:</strong> {}<br>'
                '<strong>Status:</strong> {}'
                '</div>'
                '<div>{}</div>'
                '</div>',
                payment.amount,
                payment.get_payment_method_display(),
                payment.get_status_display(),
                payment.get_screenshot_preview()
            )
        return "To'lov topilmadi"
    get_payment_info.short_description = "To'lov ma'lumotlari"

