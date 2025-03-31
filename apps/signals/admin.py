from django.contrib import admin
from .models import Signal, PricePoint

class PricePointInline(admin.TabularInline):
    """Signal admin uchun PricePoint inline"""
    model = PricePoint
    extra = 1
    fields = ['price_type', 'price', 'is_reached', 'reached_at']
    readonly_fields = ['reached_at']

@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'instrument', 'signal_type',
        'is_active', 'is_sent', 'success_rate',
        'created_at'
    ]
    list_filter = [
        'signal_type', 'is_active', 'is_sent',
        'created_at', 'instrument'
    ]
    search_fields = [
        'instrument__name',
        'description'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'closed_at',
        'success_rate',
        'is_sent'
    ]
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': (
                'instrument',
                'signal_type',
                'description',
                'image'
            )
        }),
        ('Status', {
            'fields': (
                'is_active',
                'is_sent',
                'success_rate'
            )
        }),
        ('Vaqt', {
            'fields': (
                'created_at',
                'updated_at',
                'closed_at'
            ),
            'classes': ('collapse',)
        })
    )
    inlines = [PricePointInline]

    def save_model(self, request, obj, form, change):
        if not change:  # Yangi signal yaratilayotgan bo'lsa
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(PricePoint)
class PricePointAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'signal', 'price_type',
        'price', 'is_reached', 'reached_at'
    ]
    list_filter = [
        'price_type',
        'is_reached',
        'signal__instrument'
    ]
    search_fields = [
        'signal__instrument__name',
        'price'
    ]
    readonly_fields = ['reached_at']
    raw_id_fields = ['signal']
