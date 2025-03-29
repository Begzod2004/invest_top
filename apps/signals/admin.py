from django.contrib import admin
from .models import Signal, PricePoint

class PricePointInline(admin.TabularInline):
    model = PricePoint
    extra = 1

@admin.register(Signal)
class SignalAdmin(admin.ModelAdmin):
    list_display = ['id', 'instrument', 'signal_type', 'is_active', 'is_sent', 'created_at']
    list_filter = ['signal_type', 'is_active', 'is_sent', 'instrument']
    search_fields = ['instrument__name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [PricePointInline]

@admin.register(PricePoint)
class PricePointAdmin(admin.ModelAdmin):
    list_display = ['id', 'signal', 'price_type', 'price', 'is_reached', 'reached_at']
    list_filter = ['price_type', 'is_reached']
    search_fields = ['signal__instrument__name']
    readonly_fields = ['reached_at']
