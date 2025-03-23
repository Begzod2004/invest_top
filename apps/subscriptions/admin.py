from django.contrib import admin
from .models import Subscription, SubscriptionPlan
from django.utils.html import format_html

class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'description')
    search_fields = ('name', 'description')

admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active', 'plan')
    search_fields = ('user__username',)
    readonly_fields = ('start_date',)

    def get_payment_info(self, obj):
        try:
            if hasattr(obj.user, 'payments'):
                payment = obj.user.payments.filter(subscription_plan=obj.plan).first()
                if payment:
                    return format_html(
                        '<div style="display: flex; align-items: center;">'
                        '<div style="margin-right: 10px;">'
                        '<strong>To\'lov:</strong> {} so\'m<br>'
                        '<strong>Status:</strong> {}'
                        '</div>'
                        '</div>',
                        payment.amount,
                        payment.get_status_display()
                    )
            return "To'lov topilmadi"
        except:
            return "To'lov ma'lumotlarini olishda xatolik"
    
    get_payment_info.short_description = "To'lov ma'lumotlari"

admin.site.register(Subscription, SubscriptionAdmin)

